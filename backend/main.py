import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from database import init_db, get_connection
from routers import auth, chart, user, admin, checkout, support

load_dotenv()

app = FastAPI(
    title="Astrara API",
    description="API para geracao de mapas astrais",
    version="1.0.0",
)

FRONTEND_URL = os.getenv("FRONTEND_URL", "https://www.astrara.online")
ALLOWED_ORIGINS = [
    FRONTEND_URL,
    "https://astrara.online",
    "https://www.astrara.online",
    "http://localhost:3000",  # dev
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chart.router)
app.include_router(user.router)
app.include_router(admin.router)
app.include_router(checkout.router)
app.include_router(support.router)


def create_admin_if_needed():
    """Create admin user from env vars if it doesn't exist."""
    admin_email = os.getenv("SUPERADMIN_EMAIL")
    admin_password = os.getenv("SUPERADMIN_PSW")

    if not admin_email or not admin_password:
        return

    from routers.auth import hash_password

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT id FROM users WHERE email = %s", (admin_email,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return

        hashed = hash_password(admin_password)
        cur.execute(
            "INSERT INTO users (name, email, password_hash, plan, status) VALUES (%s, %s, %s, %s, %s)",
            ("Super Admin", admin_email, hashed, "superadmin", "active"),
        )
        conn.commit()
        cur.close()
        conn.close()
        print(f"Admin user created: {admin_email}")
    except Exception as e:
        print(f"Warning: Could not create admin user: {e}")


def seed_default_products():
    """Create default interpretation product if none exists. Also creates in Stripe."""
    try:
        conn = get_connection()
        cur = conn.cursor()

        # Check if product already exists
        cur.execute("SELECT id, stripe_price_id FROM products WHERE type = 'one_time' AND name ILIKE '%%interpreta%%' LIMIT 1")
        existing = cur.fetchone()

        if existing and existing.get("stripe_price_id"):
            cur.close()
            conn.close()
            return

        name = "Interpretacao Completa do Mapa Astral"
        description = "Analise profunda de cada planeta, casa e aspecto do seu mapa natal gerada por IA. Inclui PDF para download."
        price_cents = 2990

        # Create in Stripe
        stripe_product_id = None
        stripe_price_id = None
        try:
            from services.stripe_service import create_stripe_product, create_stripe_price
            sp = create_stripe_product(name, description)
            stripe_product_id = sp.id
            price = create_stripe_price(sp.id, price_cents, "brl")
            stripe_price_id = price.id
            print(f"Stripe product created: {stripe_product_id} / price: {stripe_price_id}")
        except Exception as e:
            print(f"Warning: Could not create Stripe product: {e}")

        if existing:
            # Update existing product with Stripe IDs
            cur.execute("""
                UPDATE products SET stripe_product_id = %s, stripe_price_id = %s, updated_at = NOW()
                WHERE id = %s
            """, (stripe_product_id, stripe_price_id, existing["id"]))
        else:
            # Insert new product
            cur.execute("""
                INSERT INTO products (name, description, type, price_cents, credits, stripe_product_id, stripe_price_id, active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, true)
            """, (name, description, "one_time", price_cents, 1, stripe_product_id, stripe_price_id))

        conn.commit()
        cur.close()
        conn.close()
        print(f"Default interpretation product ready (R$ 29,90)")
    except Exception as e:
        print(f"Warning: Could not seed products: {e}")


# Serve temp images for Instagram Meta API
os.makedirs("/tmp/astrara_posts", exist_ok=True)
app.mount("/media/temp", StaticFiles(directory="/tmp/astrara_posts"), name="temp_media")


@app.on_event("startup")
async def startup():
    try:
        init_db()
        create_admin_if_needed()
        seed_default_products()
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")
        print("Running without database connection.")

    # Start Instagram scheduler
    try:
        from scheduler import start_scheduler
        start_scheduler()
        print("Instagram scheduler started (daily at 7am Brasilia)")
    except Exception as e:
        print(f"Warning: Could not start scheduler: {e}")


@app.get("/")
async def root():
    return {"message": "Astrara API", "status": "online"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/debug/fonts")
async def debug_fonts():
    """Temporary endpoint to debug font loading on server."""
    import os
    from PIL import ImageFont

    results = {}
    font_dirs = ["/app/fonts", "/app/backend/fonts"]

    for d in font_dirs:
        results[d] = {
            "exists": os.path.isdir(d),
            "files": os.listdir(d) if os.path.isdir(d) else [],
        }

    # Try loading
    test_fonts = {}
    for d in font_dirs:
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if f.endswith(".ttf"):
                path = os.path.join(d, f)
                try:
                    font = ImageFont.truetype(path, 40)
                    test_fonts[f] = {"status": "OK", "path": path, "size": os.path.getsize(path)}
                except Exception as e:
                    test_fonts[f] = {"status": "FAILED", "path": path, "error": str(e)}

    # Check CWD
    cwd = os.getcwd()
    cwd_files = os.listdir(cwd) if os.path.isdir(cwd) else []

    return {
        "cwd": cwd,
        "cwd_contents": cwd_files[:20],
        "font_dirs": results,
        "font_loading": test_fonts,
    }
