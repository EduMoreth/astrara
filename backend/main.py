import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from database import init_db, get_connection
from routers import auth, chart, user

load_dotenv()

app = FastAPI(
    title="Astrara API",
    description="API para geração de mapas astrais",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chart.router)
app.include_router(user.router)


def create_admin_if_needed():
    """Create admin user from env vars if it doesn't exist."""
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if not admin_email or not admin_password:
        return

    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT id FROM users WHERE email = %s", (admin_email,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return

        hashed = pwd_context.hash(admin_password)
        cur.execute(
            "INSERT INTO users (name, email, password_hash, plan) VALUES (%s, %s, %s, %s)",
            ("Admin", admin_email, hashed, "admin"),
        )
        conn.commit()
        cur.close()
        conn.close()
        print(f"Admin user created: {admin_email}")
    except Exception as e:
        print(f"Warning: Could not create admin user: {e}")


@app.on_event("startup")
async def startup():
    try:
        init_db()
        create_admin_if_needed()
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")
        print("Running without database connection.")


@app.get("/")
async def root():
    return {"message": "Astrara API", "status": "online"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
