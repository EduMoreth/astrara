import os
import json
import secrets
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

router = APIRouter(prefix="/admin/api", tags=["admin"])
security = HTTPBasic()

ADMIN_JWT_SECRET = os.getenv("ADMIN_JWT_SECRET", os.getenv("SECRET_KEY", "admin-secret"))
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

    cur.execute("SELECT COUNT(*) as total FROM charts")
    total_charts = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) as total FROM charts WHERE created_at::date = %s", (today,))
    charts_today = cur.fetchone()["total"]

    cur.execute("SELECT COALESCE(SUM(credits_balance), 0) as total FROM user_credits")
    credits_circulation = cur.fetchone()["total"]

    cur.execute("SELECT COALESCE(SUM(total_purchased), 0) as total FROM user_credits")
    credits_sold = cur.fetchone()["total"]

    cur.execute("SELECT COALESCE(SUM(total_used), 0) as total FROM user_credits")
    credits_used = cur.fetchone()["total"]

    cur.close()
    conn.close()

    try:
        monthly_revenue = get_monthly_revenue()
    except Exception:
        monthly_revenue = 0

    return {
        "total_users": total_users,
        "users_today": users_today,
        "total_charts": total_charts,
        "charts_today": charts_today,
        "monthly_revenue": monthly_revenue,
        "credits_circulation": credits_circulation,
        "credits_sold": credits_sold,
        "credits_used": credits_used,
    }


@router.get("/stats/users-daily")
async def users_daily(days: int = 30, admin: str = Depends(verify_admin_token)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT created_at::date as date, COUNT(*) as count
        FROM users
        WHERE created_at >= NOW() - INTERVAL '%s days'
        GROUP BY created_at::date
        ORDER BY date
    """ % days)
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

    cur.execute("SELECT * FROM purchases WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
    purchases = cur.fetchall()

    cur.execute("SELECT * FROM credit_transactions WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
    transactions = cur.fetchall()

    cur.close()
    conn.close()

    return {
        "user": {**user, "id": str(user["id"]), "password_hash": "***"},
        "credits": credits or {"credits_balance": 0, "total_purchased": 0, "total_used": 0},
        "charts": [{**c, "id": str(c["id"])} for c in charts],
        "purchases": [{**p, "id": str(p["id"])} for p in purchases],
        "credit_transactions": [{**t, "id": str(t["id"])} for t in transactions],
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
        INSERT INTO credit_transactions (user_id, admin_id, type, amount, description)
        VALUES (%s, NULL, %s, %s, %s)
    """, (user_id, "manual_add" if data.type == "add" else "manual_remove", amount, data.reason))

    conn.commit()
    cur.close()
    conn.close()

    log_action(admin, "manage_credits", "user", user_id,
               {"type": data.type, "amount": data.amount, "reason": data.reason},
               request.client.host if request.client else None)
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
    type: str
    price_cents: int
    credits: int = 0
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
            price = create_stripe_price(sp.id, data.price_cents)
            stripe_price_id = price.id
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro Stripe: {str(e)}")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO products (name, description, type, price_cents, credits, stripe_product_id, stripe_price_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
    """, (data.name, data.description, data.type, data.price_cents, data.credits,
          stripe_product_id, stripe_price_id))
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
    try:
        monthly = get_monthly_revenue()
        yearly = get_yearly_revenue()
    except Exception:
        monthly = 0
        yearly = 0

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as total FROM purchases WHERE status = 'completed'")
    total_tx = cur.fetchone()["total"]
    cur.close()
    conn.close()

    return {"monthly": monthly, "yearly": yearly, "total_transactions": total_tx}


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
