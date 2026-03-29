import os
import json
import secrets
import stripe
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from jose import jwt
from pydantic import BaseModel
from database import get_connection
from services.stripe_service import (
    create_stripe_product,
    update_stripe_product,
    archive_stripe_product,
    create_stripe_price,
    deactivate_stripe_price,
    get_monthly_revenue,
    get_yearly_revenue,
    get_payment_intents,
)
from services.email_service import send_refund_email, send_ticket_reply_email

stripe.api_key = os.getenv("STRIPE_API_KEY")

router = APIRouter(prefix="/admin/api", tags=["admin"])
security = HTTPBasic()

ADMIN_JWT_SECRET = os.getenv("ADMIN_JWT_SECRET") or os.getenv("SECRET_KEY")
if not ADMIN_JWT_SECRET:
    import warnings
    warnings.warn("ADMIN_JWT_SECRET not set! Using insecure default.")
    ADMIN_JWT_SECRET = "INSECURE-ADMIN-DEFAULT-" + str(os.getpid())
ADMIN_JWT_ALGORITHM = "HS256"
ADMIN_TOKEN_HOURS = 8


# ── Auth Helpers ─────────────────────────────────────────────

def verify_admin_basic(credentials: HTTPBasicCredentials = Depends(security)):
    correct_email = os.getenv("SUPERADMIN_EMAIL", "")
    correct_psw = os.getenv("SUPERADMIN_PSW", "")
    email_ok = secrets.compare_digest(credentials.username, correct_email)
    psw_ok = secrets.compare_digest(credentials.password, correct_psw)
    if not (email_ok and psw_ok):
        raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Basic"})
    return credentials.username


def create_admin_token(email: str) -> str:
    payload = {
        "sub": email,
        "role": "admin",
        "exp": datetime.utcnow() + timedelta(hours=ADMIN_TOKEN_HOURS),
    }
    return jwt.encode(payload, ADMIN_JWT_SECRET, algorithm=ADMIN_JWT_ALGORITHM)


def verify_admin_token(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token admin necessario")
    token = auth.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, ADMIN_JWT_SECRET, algorithms=[ADMIN_JWT_ALGORITHM])
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Acesso negado")
        return payload["sub"]
    except Exception:
        raise HTTPException(status_code=401, detail="Token admin invalido ou expirado")


def log_action(admin_email: str, action: str, target_type: str = None,
               target_id: str = None, details: dict = None, ip: str = None):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO admin_logs (admin_email, action, target_type, target_id, details, ip_address)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (admin_email, action, target_type, target_id,
             json.dumps(details) if details else None, ip),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Log error: {e}")


# ── Login ────────────────────────────────────────────────────

class AdminLoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
async def admin_login(data: AdminLoginRequest, request: Request):
    correct_email = os.getenv("SUPERADMIN_EMAIL", "")
    correct_psw = os.getenv("SUPERADMIN_PSW", "")
    email_ok = secrets.compare_digest(data.email, correct_email)
    psw_ok = secrets.compare_digest(data.password, correct_psw)
    if not (email_ok and psw_ok):
        raise HTTPException(status_code=401, detail="Credenciais invalidas")
    token = create_admin_token(data.email)
    log_action(data.email, "admin_login", ip=request.client.host if request.client else None)
    return {"access_token": token, "token_type": "bearer", "expires_in": ADMIN_TOKEN_HOURS * 3600}


# ── Dashboard Stats ──────────────────────────────────────────

@router.get("/stats")
async def get_stats(admin: str = Depends(verify_admin_token)):
    conn = get_connection()
    cur = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")

    cur.execute("SELECT COUNT(*) as total FROM users")
    total_users = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) as total FROM users WHERE created_at::date = %s", (today,))
    users_today = cur.fetchone()["total"]

    # Saved charts
    cur.execute("SELECT COUNT(*) as total FROM charts")
    total_saved_charts = cur.fetchone()["total"]

    # Generated charts (all, including unsaved)
    cur.execute("SELECT COUNT(*) as total FROM chart_generations")
    total_generations = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) as total FROM chart_generations WHERE created_at::date = %s", (today,))
    generations_today = cur.fetchone()["total"]

    cur.execute("SELECT COALESCE(SUM(credits_balance), 0) as total FROM user_credits")
    credits_circulation = cur.fetchone()["total"]

    cur.execute("SELECT COALESCE(SUM(total_purchased), 0) as total FROM user_credits")
    credits_sold = cur.fetchone()["total"]

    cur.execute("SELECT COALESCE(SUM(total_used), 0) as total FROM user_credits")
    credits_used = cur.fetchone()["total"]

    # Open tickets
    cur.execute("SELECT COUNT(*) as total FROM tickets WHERE status = 'open'")
    open_tickets = cur.fetchone()["total"]

    # Monthly revenue from DB (accurate)
    cur.execute("""
        SELECT COALESCE(SUM(amount_cents), 0) as total FROM purchases
        WHERE status = 'completed' AND created_at >= DATE_TRUNC('month', NOW())
    """)
    monthly_revenue = cur.fetchone()["total"]

    cur.close()
    conn.close()

    return {
        "total_users": total_users,
        "users_today": users_today,
        "total_generations": total_generations,
        "generations_today": generations_today,
        "total_saved_charts": total_saved_charts,
        "monthly_revenue": monthly_revenue,
        "credits_circulation": credits_circulation,
        "credits_sold": credits_sold,
        "credits_used": credits_used,
        "open_tickets": open_tickets,
    }


@router.get("/stats/users-daily")
async def users_daily(days: int = 30, admin: str = Depends(verify_admin_token)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT created_at::date as date, COUNT(*) as count
        FROM users
        WHERE created_at >= NOW() - make_interval(days => %s)
        GROUP BY created_at::date
        ORDER BY date
    """, (days,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"date": str(r["date"]), "count": r["count"]} for r in rows]


@router.get("/stats/revenue-daily")
async def revenue_daily(admin: str = Depends(verify_admin_token)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT created_at::date as date, COALESCE(SUM(amount_cents), 0) as total
        FROM purchases
        WHERE status = 'completed' AND created_at >= NOW() - INTERVAL '30 days'
        GROUP BY created_at::date
        ORDER BY date
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"date": str(r["date"]), "total": r["total"]} for r in rows]


# ── Users ────────────────────────────────────────────────────

@router.get("/users")
async def list_users(
    page: int = 1, limit: int = 20,
    search: str = "", plan: str = "", status: str = "",
    admin: str = Depends(verify_admin_token),
):
    conn = get_connection()
    cur = conn.cursor()
    offset = (page - 1) * limit

    where_clauses = []
    params = []

    if search:
        where_clauses.append("(u.name ILIKE %s OR u.email ILIKE %s)")
        params.extend([f"%{search}%", f"%{search}%"])
    if plan:
        where_clauses.append("u.plan = %s")
        params.append(plan)
    if status:
        where_clauses.append("u.status = %s")
        params.append(status)

    where = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    cur.execute(f"""
        SELECT u.*, COALESCE(uc.credits_balance, 0) as credits,
               (SELECT COUNT(*) FROM charts c WHERE c.user_id = u.id) as chart_count
        FROM users u
        LEFT JOIN user_credits uc ON uc.user_id = u.id
        {where}
        ORDER BY u.created_at DESC
        LIMIT %s OFFSET %s
    """, params + [limit, offset])
    users = cur.fetchall()

    cur.execute(f"SELECT COUNT(*) as total FROM users u {where}", params)
    total = cur.fetchone()["total"]

    cur.close()
    conn.close()

    return {
        "users": [{**u, "id": str(u["id"]), "password_hash": "***"} for u in users],
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
    }


@router.get("/users/{user_id}")
async def get_user(user_id: str, admin: str = Depends(verify_admin_token)):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    if not user:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")

    cur.execute("SELECT * FROM user_credits WHERE user_id = %s", (user_id,))
    credits = cur.fetchone()

    cur.execute("SELECT * FROM charts WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
    charts = cur.fetchall()

    cur.execute("""
        SELECT p.*, pr.name as product_name
        FROM purchases p
        LEFT JOIN products pr ON pr.type = p.product_type
        WHERE p.user_id = %s ORDER BY p.created_at DESC
    """, (user_id,))
    purchases = cur.fetchall()

    cur.execute("SELECT * FROM credit_transactions WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
    transactions = cur.fetchall()

    # Chart generations (all, including unsaved)
    cur.execute("SELECT * FROM chart_generations WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
    generations = cur.fetchall()

    cur.close()
    conn.close()

    return {
        "user": {**user, "id": str(user["id"]), "password_hash": "***"},
        "credits": credits or {"credits_balance": 0, "total_purchased": 0, "total_used": 0},
        "charts": [{**c, "id": str(c["id"])} for c in charts],
        "purchases": [{**p, "id": str(p["id"])} for p in purchases],
        "credit_transactions": [{**t, "id": str(t["id"])} for t in transactions],
        "generations": [{**g, "id": str(g["id"])} for g in generations],
    }


class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    plan: Optional[str] = None
    status: Optional[str] = None


@router.patch("/users/{user_id}")
async def update_user(user_id: str, data: UserUpdateRequest, request: Request,
                      admin: str = Depends(verify_admin_token)):
    conn = get_connection()
    cur = conn.cursor()

    updates = []
    params = []
    for field in ["name", "email", "plan", "status"]:
        val = getattr(data, field)
        if val is not None:
            updates.append(f"{field} = %s")
            params.append(val)

    if not updates:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

    updates.append("updated_at = NOW()")
    params.append(user_id)

    cur.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = %s", params)
    conn.commit()
    cur.close()
    conn.close()

    log_action(admin, "update_user", "user", user_id, data.dict(exclude_none=True),
               request.client.host if request.client else None)
    return {"success": True}


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, request: Request, admin: str = Depends(verify_admin_token)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()
    log_action(admin, "delete_user", "user", user_id, ip=request.client.host if request.client else None)
    return {"success": True}


@router.post("/users/{user_id}/ban")
async def ban_user(user_id: str, request: Request, admin: str = Depends(verify_admin_token)):
    body = await request.json()
    reason = body.get("reason", "")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET status = 'banned', updated_at = NOW() WHERE id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()
    log_action(admin, "ban_user", "user", user_id, {"reason": reason},
               request.client.host if request.client else None)
    return {"success": True}


class CreditRequest(BaseModel):
    type: str  # 'add' or 'remove'
    amount: int
    reason: str


@router.post("/users/{user_id}/credits")
async def manage_credits(user_id: str, data: CreditRequest, request: Request,
                         admin: str = Depends(verify_admin_token)):
    conn = get_connection()
    cur = conn.cursor()

    amount = data.amount if data.type == "add" else -data.amount

    # Ensure user_credits row exists
    cur.execute("""
        INSERT INTO user_credits (user_id, credits_balance, total_purchased, total_used)
        VALUES (%s, 0, 0, 0)
        ON CONFLICT (user_id) DO NOTHING
    """, (user_id,))

    if data.type == "add":
        cur.execute("""
            UPDATE user_credits SET credits_balance = credits_balance + %s,
                                    total_purchased = total_purchased + %s,
                                    updated_at = NOW()
            WHERE user_id = %s
        """, (data.amount, data.amount, user_id))
    else:
        cur.execute("""
            UPDATE user_credits SET credits_balance = GREATEST(credits_balance - %s, 0),
                                    total_used = total_used + %s,
                                    updated_at = NOW()
            WHERE user_id = %s
        """, (data.amount, data.amount, user_id))

    cur.execute("""
        INSERT INTO credit_transactions (user_id, type, amount, description, reference_id)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, "manual_add" if data.type == "add" else "manual_remove", amount,
          f"{data.reason} (admin: {admin})", admin))

    conn.commit()
    cur.close()
    conn.close()

    log_action(admin, "manage_credits", "user", user_id,
               {"type": data.type, "amount": data.amount, "reason": data.reason},
               request.client.host if request.client else None)
    return {"success": True}


@router.post("/users/{user_id}/force-reset-password")
async def force_reset_password(user_id: str, request: Request,
                               admin: str = Depends(verify_admin_token)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET force_password_reset = true, updated_at = NOW() WHERE id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()
    log_action(admin, "force_password_reset", "user", user_id,
               ip=request.client.host if request.client else None)
    return {"success": True}


# ── Products ─────────────────────────────────────────────────

@router.get("/products")
async def list_products(admin: str = Depends(verify_admin_token)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products ORDER BY created_at DESC")
    products = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": str(p["id"]), **{k: v for k, v in p.items() if k != "id"}} for p in products]


class ProductCreateRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    type: str  # 'credits' (pack), 'one_time', 'subscription' (premium)
    price_cents: int
    credits: int = 0
    max_saved_charts: int = 0
    recurrence: str = "none"  # 'none', 'monthly', 'yearly'
    create_in_stripe: bool = True


@router.post("/products")
async def create_product(data: ProductCreateRequest, request: Request,
                         admin: str = Depends(verify_admin_token)):
    stripe_product_id = None
    stripe_price_id = None

    if data.create_in_stripe:
        try:
            sp = create_stripe_product(data.name, data.description)
            stripe_product_id = sp.id

            if data.type == "subscription" and data.recurrence in ("monthly", "yearly"):
                # Create recurring price for subscriptions
                interval = "month" if data.recurrence == "monthly" else "year"
                price = stripe.Price.create(
                    product=sp.id,
                    unit_amount=data.price_cents,
                    currency="brl",
                    recurring={"interval": interval},
                )
            else:
                price = create_stripe_price(sp.id, data.price_cents)

            stripe_price_id = price.id
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro Stripe: {str(e)}")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO products (name, description, type, price_cents, credits,
                              max_saved_charts, recurrence, stripe_product_id, stripe_price_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
    """, (data.name, data.description, data.type, data.price_cents, data.credits,
          data.max_saved_charts, data.recurrence, stripe_product_id, stripe_price_id))
    product_id = str(cur.fetchone()["id"])
    conn.commit()
    cur.close()
    conn.close()

    log_action(admin, "create_product", "product", product_id, data.dict(),
               request.client.host if request.client else None)
    return {"success": True, "id": product_id}


class ProductUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price_cents: Optional[int] = None
    credits: Optional[int] = None


@router.patch("/products/{product_id}")
async def update_product_endpoint(product_id: str, data: ProductUpdateRequest, request: Request,
                                  admin: str = Depends(verify_admin_token)):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cur.fetchone()
    if not product:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Produto nao encontrado")

    updates = []
    params = []
    for field in ["name", "description", "price_cents", "credits"]:
        val = getattr(data, field)
        if val is not None:
            updates.append(f"{field} = %s")
            params.append(val)

    if updates:
        updates.append("updated_at = NOW()")
        params.append(product_id)
        cur.execute(f"UPDATE products SET {', '.join(updates)} WHERE id = %s", params)

    # Update in Stripe too
    if product["stripe_product_id"] and (data.name or data.description):
        try:
            update_stripe_product(
                product["stripe_product_id"],
                data.name or product["name"],
                data.description or product["description"],
            )
        except Exception:
            pass

    # If price changed, create a new Stripe Price (Stripe prices are immutable)
    if data.price_cents is not None and data.price_cents != product["price_cents"] and product["stripe_product_id"]:
        try:
            new_price = create_stripe_price(product["stripe_product_id"], data.price_cents)
            cur2 = conn.cursor()
            cur2.execute("UPDATE products SET stripe_price_id = %s WHERE id = %s",
                         (new_price.id, product_id))
            cur2.close()
            # Deactivate the old Stripe Price
            if product["stripe_price_id"]:
                try:
                    deactivate_stripe_price(product["stripe_price_id"])
                except Exception:
                    pass
        except Exception as e:
            print(f"Warning: Could not update Stripe price: {e}")

    conn.commit()
    cur.close()
    conn.close()

    log_action(admin, "update_product", "product", product_id, data.dict(exclude_none=True),
               request.client.host if request.client else None)
    return {"success": True}


@router.patch("/products/{product_id}/toggle")
async def toggle_product(product_id: str, request: Request,
                         admin: str = Depends(verify_admin_token)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT active, stripe_product_id FROM products WHERE id = %s", (product_id,))
    product = cur.fetchone()
    if not product:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Produto nao encontrado")

    new_state = not product["active"]
    cur.execute("UPDATE products SET active = %s, updated_at = NOW() WHERE id = %s",
                (new_state, product_id))
    conn.commit()
    cur.close()
    conn.close()

    if product["stripe_product_id"] and not new_state:
        try:
            archive_stripe_product(product["stripe_product_id"])
        except Exception:
            pass

    log_action(admin, "toggle_product", "product", product_id, {"active": new_state},
               request.client.host if request.client else None)
    return {"success": True, "active": new_state}


@router.delete("/products/{product_id}")
async def delete_product(product_id: str, request: Request,
                         admin: str = Depends(verify_admin_token)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT stripe_product_id FROM products WHERE id = %s", (product_id,))
    product = cur.fetchone()

    cur.execute("UPDATE products SET active = false, updated_at = NOW() WHERE id = %s", (product_id,))
    conn.commit()
    cur.close()
    conn.close()

    if product and product["stripe_product_id"]:
        try:
            archive_stripe_product(product["stripe_product_id"])
        except Exception:
            pass

    log_action(admin, "archive_product", "product", product_id,
               ip=request.client.host if request.client else None)
    return {"success": True}


# ── Transactions ─────────────────────────────────────────────

@router.get("/transactions")
async def list_transactions(page: int = 1, limit: int = 20, status: str = "",
                            admin: str = Depends(verify_admin_token)):
    conn = get_connection()
    cur = conn.cursor()
    offset = (page - 1) * limit

    where = "WHERE p.status = %s" if status else ""
    params = [status] if status else []

    cur.execute(f"""
        SELECT p.*, u.name as user_name, u.email as user_email
        FROM purchases p
        LEFT JOIN users u ON u.id = p.user_id
        {where}
        ORDER BY p.created_at DESC
        LIMIT %s OFFSET %s
    """, params + [limit, offset])
    rows = cur.fetchall()

    cur.execute(f"SELECT COUNT(*) as total FROM purchases p {where}", params)
    total = cur.fetchone()["total"]

    cur.close()
    conn.close()

    return {
        "transactions": [{**r, "id": str(r["id"])} for r in rows],
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
    }


@router.get("/revenue")
async def get_revenue(admin: str = Depends(verify_admin_token)):
    conn = get_connection()
    cur = conn.cursor()

    # Monthly revenue from DB (accurate)
    cur.execute("""
        SELECT COALESCE(SUM(amount_cents), 0) as total FROM purchases
        WHERE status = 'completed'
        AND created_at >= DATE_TRUNC('month', NOW())
    """)
    monthly = cur.fetchone()["total"]

    # Yearly revenue from DB
    cur.execute("""
        SELECT COALESCE(SUM(amount_cents), 0) as total FROM purchases
        WHERE status = 'completed'
        AND created_at >= DATE_TRUNC('year', NOW())
    """)
    yearly = cur.fetchone()["total"]

    # Total refunded
    cur.execute("SELECT COALESCE(SUM(amount_cents), 0) as total FROM refunds WHERE status = 'completed'")
    refunded = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) as total FROM purchases WHERE status = 'completed'")
    total_tx = cur.fetchone()["total"]

    cur.close()
    conn.close()

    return {
        "monthly": monthly,
        "yearly": yearly,
        "total_transactions": total_tx,
        "total_refunded": refunded,
    }


# ── Charts ───────────────────────────────────────────────────

@router.get("/charts")
async def list_charts(page: int = 1, limit: int = 20,
                      admin: str = Depends(verify_admin_token)):
    conn = get_connection()
    cur = conn.cursor()
    offset = (page - 1) * limit

    cur.execute("""
        SELECT c.*, u.name as user_name, u.email as user_email
        FROM charts c
        LEFT JOIN users u ON u.id = c.user_id
        ORDER BY c.created_at DESC
        LIMIT %s OFFSET %s
    """, (limit, offset))
    charts = cur.fetchall()

    cur.execute("SELECT COUNT(*) as total FROM charts")
    total = cur.fetchone()["total"]

    cur.close()
    conn.close()

    return {
        "charts": [{**c, "id": str(c["id"]), "positions_json": None, "svg_data": None} for c in charts],
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
    }


@router.get("/generations")
async def list_generations(page: int = 1, limit: int = 20,
                           admin: str = Depends(verify_admin_token)):
    """List ALL chart generations (including non-saved, anonymous)."""
    conn = get_connection()
    cur = conn.cursor()
    offset = (page - 1) * limit

    cur.execute("""
        SELECT cg.*, u.name as user_name, u.email as user_email
        FROM chart_generations cg
        LEFT JOIN users u ON u.id = cg.user_id
        ORDER BY cg.created_at DESC
        LIMIT %s OFFSET %s
    """, (limit, offset))
    gens = cur.fetchall()

    cur.execute("SELECT COUNT(*) as total FROM chart_generations")
    total = cur.fetchone()["total"]

    cur.close()
    conn.close()

    return {
        "generations": [{**g, "id": str(g["id"])} for g in gens],
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
    }


@router.delete("/charts/{chart_id}")
async def delete_chart(chart_id: str, request: Request,
                       admin: str = Depends(verify_admin_token)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM charts WHERE id = %s", (chart_id,))
    conn.commit()
    cur.close()
    conn.close()
    log_action(admin, "delete_chart", "chart", chart_id,
               ip=request.client.host if request.client else None)
    return {"success": True}


# ── Config ───────────────────────────────────────────────────

@router.get("/config")
async def get_config(admin: str = Depends(verify_admin_token)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM system_config ORDER BY key")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {r["key"]: {"value": r["value"], "description": r["description"]} for r in rows}


class ConfigUpdateRequest(BaseModel):
    configs: dict


@router.patch("/config")
async def update_config(data: ConfigUpdateRequest, request: Request,
                        admin: str = Depends(verify_admin_token)):
    conn = get_connection()
    cur = conn.cursor()
    for key, value in data.configs.items():
        cur.execute(
            "UPDATE system_config SET value = %s, updated_at = NOW() WHERE key = %s",
            (str(value), key),
        )
    conn.commit()
    cur.close()
    conn.close()
    log_action(admin, "update_config", "system", None, data.configs,
               request.client.host if request.client else None)
    return {"success": True}


# ── Logs ─────────────────────────────────────────────────────

@router.get("/logs")
async def get_logs(page: int = 1, limit: int = 50, action: str = "",
                   admin: str = Depends(verify_admin_token)):
    conn = get_connection()
    cur = conn.cursor()
    offset = (page - 1) * limit

    where = "WHERE action ILIKE %s" if action else ""
    params = [f"%{action}%"] if action else []

    cur.execute(f"""
        SELECT * FROM admin_logs {where}
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
    """, params + [limit, offset])
    logs = cur.fetchall()

    cur.execute(f"SELECT COUNT(*) as total FROM admin_logs {where}", params)
    total = cur.fetchone()["total"]

    cur.close()
    conn.close()

    return {
        "logs": [{**l, "id": str(l["id"])} for l in logs],
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
    }


# ── Refunds / Churn ──────────────────────────────────────────

class RefundRequest(BaseModel):
    reason: str = ""


@router.post("/transactions/{purchase_id}/refund")
async def refund_transaction(purchase_id: str, data: RefundRequest, request: Request,
                             admin: str = Depends(verify_admin_token)):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT p.*, u.name as user_name, u.email as user_email
        FROM purchases p
        LEFT JOIN users u ON u.id = p.user_id
        WHERE p.id = %s
    """, (purchase_id,))
    purchase = cur.fetchone()

    if not purchase:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Transacao nao encontrada")

    if purchase["status"] == "refunded":
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Transacao ja foi reembolsada")

    # Refund via Stripe
    stripe_refund_id = None
    if purchase.get("stripe_payment_id"):
        try:
            # Get payment intent from checkout session
            session = stripe.checkout.Session.retrieve(purchase["stripe_payment_id"])
            if session.payment_intent:
                refund = stripe.Refund.create(payment_intent=session.payment_intent, reason="requested_by_customer")
                stripe_refund_id = refund.id
        except Exception as e:
            cur.close()
            conn.close()
            raise HTTPException(status_code=500, detail=f"Erro ao estornar no Stripe: {str(e)}")

    # Update purchase status
    cur.execute("UPDATE purchases SET status = 'refunded' WHERE id = %s", (purchase_id,))

    # Remove credits that were added
    if purchase.get("user_id"):
        cur.execute("""
            UPDATE user_credits SET credits_balance = GREATEST(credits_balance - 1, 0),
                                    updated_at = NOW()
            WHERE user_id = %s
        """, (str(purchase["user_id"]),))

        cur.execute("""
            INSERT INTO credit_transactions (user_id, type, amount, description, reference_id)
            VALUES (%s, 'refund', -1, %s, %s)
        """, (str(purchase["user_id"]), f"Reembolso: {data.reason}", stripe_refund_id))

    # Record refund
    cur.execute("""
        INSERT INTO refunds (purchase_id, user_id, admin_email, amount_cents, reason, stripe_refund_id, status)
        VALUES (%s, %s, %s, %s, %s, %s, 'completed')
    """, (purchase_id, str(purchase["user_id"]) if purchase.get("user_id") else None,
          admin, purchase.get("amount_cents", 0), data.reason, stripe_refund_id))

    conn.commit()
    cur.close()
    conn.close()

    # Send refund email to user
    if purchase.get("user_email"):
        send_refund_email(
            purchase["user_email"],
            purchase.get("user_name", ""),
            purchase.get("amount_cents", 0),
            data.reason,
        )

    log_action(admin, "refund_transaction", "purchase", purchase_id,
               {"amount_cents": purchase.get("amount_cents"), "reason": data.reason, "stripe_refund_id": stripe_refund_id},
               request.client.host if request.client else None)

    return {"success": True, "stripe_refund_id": stripe_refund_id}


@router.get("/refunds")
async def list_refunds(page: int = 1, limit: int = 20, admin: str = Depends(verify_admin_token)):
    conn = get_connection()
    cur = conn.cursor()
    offset = (page - 1) * limit

    cur.execute("""
        SELECT r.*, u.name as user_name, u.email as user_email
        FROM refunds r
        LEFT JOIN users u ON u.id = r.user_id
        ORDER BY r.created_at DESC
        LIMIT %s OFFSET %s
    """, (limit, offset))
    refunds = cur.fetchall()

    cur.execute("SELECT COUNT(*) as total FROM refunds")
    total = cur.fetchone()["total"]

    cur.close()
    conn.close()

    return {
        "refunds": [{**r, "id": str(r["id"])} for r in refunds],
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
    }


# ── Admin Ticket Management ──────────────────────────────────

@router.get("/tickets")
async def admin_list_tickets(page: int = 1, limit: int = 20, status: str = "",
                             admin: str = Depends(verify_admin_token)):
    conn = get_connection()
    cur = conn.cursor()
    offset = (page - 1) * limit

    where = "WHERE t.status = %s" if status else ""
    params = [status] if status else []

    cur.execute(f"""
        SELECT t.*, u.name as user_name, u.email as user_email,
               (SELECT COUNT(*) FROM ticket_messages tm WHERE tm.ticket_id = t.id) as message_count
        FROM tickets t
        LEFT JOIN users u ON u.id = t.user_id
        {where}
        ORDER BY t.updated_at DESC
        LIMIT %s OFFSET %s
    """, params + [limit, offset])
    tickets = cur.fetchall()

    cur.execute(f"SELECT COUNT(*) as total FROM tickets t {where}", params)
    total = cur.fetchone()["total"]

    cur.close()
    conn.close()

    return {
        "tickets": [{**t, "id": str(t["id"])} for t in tickets],
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
    }


@router.get("/tickets/{ticket_id}")
async def admin_get_ticket(ticket_id: str, admin: str = Depends(verify_admin_token)):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT t.*, u.name as user_name, u.email as user_email
        FROM tickets t
        LEFT JOIN users u ON u.id = t.user_id
        WHERE t.id = %s
    """, (ticket_id,))
    ticket = cur.fetchone()
    if not ticket:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Ticket nao encontrado")

    cur.execute("SELECT * FROM ticket_messages WHERE ticket_id = %s ORDER BY created_at ASC", (ticket_id,))
    messages = cur.fetchall()

    cur.close()
    conn.close()

    return {
        "ticket": {**ticket, "id": str(ticket["id"])},
        "messages": [{**m, "id": str(m["id"])} for m in messages],
    }


class AdminTicketReply(BaseModel):
    message: str


@router.post("/tickets/{ticket_id}/reply")
async def admin_reply_ticket(ticket_id: str, data: AdminTicketReply, request: Request,
                             admin: str = Depends(verify_admin_token)):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT t.subject, u.email as user_email, u.name as user_name
        FROM tickets t
        LEFT JOIN users u ON u.id = t.user_id
        WHERE t.id = %s
    """, (ticket_id,))
    ticket = cur.fetchone()
    if not ticket:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404)

    cur.execute("""
        INSERT INTO ticket_messages (ticket_id, sender_type, sender_id, sender_name, message)
        VALUES (%s, 'admin', NULL, %s, %s)
    """, (ticket_id, "Equipe Astrara", data.message))

    cur.execute("UPDATE tickets SET updated_at = NOW() WHERE id = %s", (ticket_id,))
    conn.commit()
    cur.close()
    conn.close()

    # Notify user by email
    if ticket.get("user_email"):
        send_ticket_reply_email(
            ticket["user_email"],
            ticket.get("user_name", ""),
            ticket.get("subject", ""),
            data.message,
        )

    log_action(admin, "reply_ticket", "ticket", ticket_id, ip=request.client.host if request.client else None)
    return {"success": True}


@router.patch("/tickets/{ticket_id}/status")
async def admin_update_ticket_status(ticket_id: str, request: Request,
                                     admin: str = Depends(verify_admin_token)):
    body = await request.json()
    new_status = body.get("status", "closed")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE tickets SET status = %s, updated_at = NOW() WHERE id = %s", (new_status, ticket_id))
    conn.commit()
    cur.close()
    conn.close()

    log_action(admin, "update_ticket_status", "ticket", ticket_id, {"status": new_status},
               request.client.host if request.client else None)
    return {"success": True}


# ── Financial Reports ────────────────────────────────────────

@router.get("/reports/financial")
async def financial_report(
    date_from: str = "", date_to: str = "",
    admin: str = Depends(verify_admin_token),
):
    """Financial report with optional date range filter.
    date_from, date_to: YYYY-MM-DD format. Empty = all time.
    """
    conn = get_connection()
    cur = conn.cursor()

    # Build date filter
    date_filter_p = ""
    date_filter_r = ""
    date_params_p: list = []
    date_params_r: list = []

    if date_from and date_to:
        date_filter_p = "AND p.created_at >= %s AND p.created_at < %s::date + 1"
        date_filter_r = "AND r.created_at >= %s AND r.created_at < %s::date + 1"
        date_params_p = [date_from, date_to]
        date_params_r = [date_from, date_to]
    elif date_from:
        date_filter_p = "AND p.created_at >= %s"
        date_filter_r = "AND r.created_at >= %s"
        date_params_p = [date_from]
        date_params_r = [date_from]
    elif date_to:
        date_filter_p = "AND p.created_at < %s::date + 1"
        date_filter_r = "AND r.created_at < %s::date + 1"
        date_params_p = [date_to]
        date_params_r = [date_to]

    # Total revenue in period
    cur.execute(f"""
        SELECT COALESCE(SUM(amount_cents), 0) as total FROM purchases p
        WHERE status = 'completed' {date_filter_p}
    """, date_params_p)
    total_revenue = cur.fetchone()["total"]

    # Total refunded in period
    cur.execute(f"""
        SELECT COALESCE(SUM(amount_cents), 0) as total FROM refunds r
        WHERE status = 'completed' {date_filter_r}
    """, date_params_r)
    total_refunded = cur.fetchone()["total"]

    net_revenue = total_revenue - total_refunded

    # Daily breakdown (for charts)
    cur.execute(f"""
        SELECT created_at::date as day,
               COALESCE(SUM(amount_cents), 0) as revenue,
               COUNT(*) as transactions
        FROM purchases p
        WHERE status = 'completed' {date_filter_p}
        GROUP BY created_at::date
        ORDER BY day DESC
        LIMIT 365
    """, date_params_p)
    daily = cur.fetchall()

    # Monthly breakdown
    cur.execute(f"""
        SELECT DATE_TRUNC('month', created_at) as month,
               COALESCE(SUM(amount_cents), 0) as revenue,
               COUNT(*) as transactions
        FROM purchases p
        WHERE status = 'completed' {date_filter_p}
        GROUP BY DATE_TRUNC('month', created_at)
        ORDER BY month DESC
    """, date_params_p)
    monthly = cur.fetchall()

    # Counts
    cur.execute(f"SELECT COUNT(*) as total FROM purchases p WHERE status = 'completed' {date_filter_p}", date_params_p)
    total_purchases = cur.fetchone()["total"]
    cur.execute(f"SELECT COUNT(*) as total FROM refunds r WHERE status = 'completed' {date_filter_r}", date_params_r)
    total_refund_count = cur.fetchone()["total"]
    refund_rate = (total_refund_count / total_purchases * 100) if total_purchases > 0 else 0

    # Top products
    cur.execute(f"""
        SELECT COALESCE(pr.name, p.product_type) as name,
               COUNT(p.id) as sales,
               COALESCE(SUM(p.amount_cents), 0) as revenue
        FROM purchases p
        LEFT JOIN products pr ON pr.type = p.product_type
        WHERE p.status = 'completed' {date_filter_p}
        GROUP BY COALESCE(pr.name, p.product_type)
        ORDER BY revenue DESC
        LIMIT 10
    """, date_params_p)
    top_products = cur.fetchall()

    cur.close()
    conn.close()

    return {
        "total_revenue": total_revenue,
        "total_refunded": total_refunded,
        "net_revenue": net_revenue,
        "refund_rate": round(refund_rate, 2),
        "total_purchases": total_purchases,
        "total_refunds": total_refund_count,
        "daily_breakdown": [{"day": str(d["day"]), "revenue": d["revenue"], "transactions": d["transactions"]} for d in daily],
        "monthly_breakdown": [{"month": str(m["month"])[:7], "revenue": m["revenue"], "transactions": m["transactions"]} for m in monthly],
        "top_products": [{"name": p["name"] or "N/A", "sales": p["sales"], "revenue": p["revenue"]} for p in top_products],
    }


# ── Email Logs ───────────────────────────────────────────────

@router.get("/emails")
async def list_emails(page: int = 1, limit: int = 20, admin: str = Depends(verify_admin_token)):
    conn = get_connection()
    cur = conn.cursor()
    offset = (page - 1) * limit
    cur.execute("SELECT * FROM email_logs ORDER BY created_at DESC LIMIT %s OFFSET %s", (limit, offset))
    emails = cur.fetchall()
    cur.execute("SELECT COUNT(*) as total FROM email_logs")
    total = cur.fetchone()["total"]
    cur.close()
    conn.close()
    return {
        "emails": [{**e, "id": str(e["id"])} for e in emails],
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
    }


# ── Instagram Posts ──────────────────────────────────────────

@router.get("/instagram/posts")
async def list_instagram_posts(page: int = 1, limit: int = 20,
                               admin: str = Depends(verify_admin_token)):
    conn = get_connection()
    cur = conn.cursor()
    offset = (page - 1) * limit
    cur.execute("""
        SELECT * FROM instagram_posts ORDER BY post_date DESC LIMIT %s OFFSET %s
    """, (limit, offset))
    posts = cur.fetchall()
    cur.execute("SELECT COUNT(*) as total FROM instagram_posts")
    total = cur.fetchone()["total"]
    cur.close()
    conn.close()
    return {
        "posts": [{**p, "id": str(p["id"]), "post_date": str(p["post_date"])} for p in posts],
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
    }


@router.post("/instagram/posts/trigger")
async def trigger_instagram_post(request: Request, admin: str = Depends(verify_admin_token)):
    """Manually trigger the daily Instagram post."""
    from datetime import date as date_type

    try:
        body = await request.json()
    except Exception:
        body = {}

    target_str = body.get("date", str(date_type.today()))

    try:
        target = date_type.fromisoformat(target_str)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Data invalida: {target_str}. Use formato YYYY-MM-DD.")

    try:
        # Delete any existing failed/pending record for this date so it can be re-triggered
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM instagram_posts WHERE post_date = %s AND status != 'published'", (target,))
        conn.commit()
        cur.close()
        conn.close()

        from services.daily_post_orchestrator import run_daily_instagram_post
        result = run_daily_instagram_post(target)
    except Exception as e:
        result = {"status": "failed", "error": str(e)}

    log_action(admin, "trigger_instagram_post", "instagram", target_str,
               result, ip=request.client.host if request.client else None)

    return {"success": result.get("status") != "failed", **result}


@router.get("/instagram/test")
async def test_instagram_credentials(admin: str = Depends(verify_admin_token)):
    """Test if Instagram credentials are valid."""
    import requests as req
    ig_id = os.getenv("INSTAGRAM_ACCOUNT_ID")
    token = os.getenv("META_ACCESS_TOKEN") or os.getenv("META_ACESS_TOKEN")
    backend_url = os.getenv("BACKEND_URL", "https://astrara-production.up.railway.app")

    results = {
        "instagram_account_id": ig_id[:6] + "..." if ig_id else "NOT SET",
        "meta_token": token[:10] + "..." if token else "NOT SET",
        "backend_url": backend_url,
    }

    if ig_id and token:
        try:
            r = req.get(f"https://graph.facebook.com/v21.0/{ig_id}?fields=username,name&access_token={token}", timeout=10)
            data = r.json()
            if "error" in data:
                results["status"] = "error"
                results["error"] = data["error"].get("message", str(data["error"]))
            else:
                results["status"] = "ok"
                results["instagram_username"] = data.get("username", "")
                results["instagram_name"] = data.get("name", "")
        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
    else:
        results["status"] = "missing_credentials"

    return results


@router.get("/instagram/posts/{post_date}")
async def get_instagram_post(post_date: str, admin: str = Depends(verify_admin_token)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM instagram_posts WHERE post_date = %s", (post_date,))
    post = cur.fetchone()
    cur.close()
    conn.close()
    if not post:
        raise HTTPException(status_code=404, detail="Post nao encontrado")
    return {**post, "id": str(post["id"]), "post_date": str(post["post_date"])}


@router.post("/purchases/recover-pending")
async def recover_pending_purchases(request: Request, admin: str = Depends(verify_admin_token)):
    """
    Recover pending purchases by checking Stripe for payment status.
    Finds all purchases with status 'pending' and verifies them against Stripe.
    Fulfills any that are actually paid.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT p.id, p.user_id, p.stripe_payment_id, p.product_type, p.status
        FROM purchases p
        WHERE p.status = 'pending'
        ORDER BY p.created_at DESC
        LIMIT 50
    """)
    pending = cur.fetchall()
    cur.close()
    conn.close()

    recovered = 0
    errors = []

    for purchase in pending:
        session_id = purchase.get("stripe_payment_id")
        user_id = str(purchase["user_id"]) if purchase.get("user_id") else None
        if not session_id or not user_id:
            continue

        try:
            from services.stripe_service import verify_payment
            result = verify_payment(session_id)
            if result["status"] == "paid":
                from routers.checkout import _fulfill_purchase
                credits = _fulfill_purchase(
                    session_id=session_id,
                    user_id=user_id,
                    product_id=result.get("product_id", ""),
                )
                recovered += 1
                print(f"[Recovery] Fulfilled purchase {session_id} for user {user_id}, credits: {credits}")
        except Exception as e:
            errors.append({"session_id": session_id, "error": str(e)})

    log_action(admin, "recover_pending_purchases", "purchase", "",
               {"recovered": recovered, "total_pending": len(pending), "errors": errors},
               request.client.host if request.client else None)

    return {
        "success": True,
        "total_pending": len(pending),
        "recovered": recovered,
        "errors": errors,
    }


@router.delete("/instagram/posts/{post_date}")
async def delete_instagram_post(post_date: str, request: Request,
                                admin: str = Depends(verify_admin_token)):
    """Delete an Instagram post record (allows re-triggering for that date)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM instagram_posts WHERE post_date = %s", (post_date,))
    conn.commit()
    cur.close()
    conn.close()
    log_action(admin, "delete_instagram_post", "instagram", post_date,
               ip=request.client.host if request.client else None)
    return {"success": True}
