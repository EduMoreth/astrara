import os
from typing import Optional
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from database import get_connection
from routers.auth import verify_token
from services.stripe_service import create_checkout_session, verify_payment

router = APIRouter(prefix="/checkout", tags=["checkout"])


def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Login necessario")
    token = authorization.replace("Bearer ", "")
    return verify_token(token)


class CheckoutCreateRequest(BaseModel):
    product_id: str


@router.post("/create")
async def create_checkout(data: CheckoutCreateRequest,
                          authorization: Optional[str] = Header(None)):
    user = get_current_user(authorization)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE id = %s AND active = true", (data.product_id,))
    product = cur.fetchone()
    cur.close()
    conn.close()

    if not product:
        raise HTTPException(status_code=404, detail="Produto nao encontrado ou inativo")

    if not product["stripe_price_id"]:
        raise HTTPException(status_code=400, detail="Produto sem preco configurado no Stripe")

    frontend_url = os.getenv("FRONTEND_URL", "https://astrara.online")

    try:
        session = create_checkout_session(
            stripe_price_id=product["stripe_price_id"],
            user_id=user["sub"],
            product_id=str(product["id"]),
            success_url=f"{frontend_url}/checkout/success",
            cancel_url=f"{frontend_url}/checkout/cancel",
            customer_email=user.get("email"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar checkout: {str(e)}")

    # Record pending purchase
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO purchases (user_id, product_type, stripe_payment_id, amount_cents, status)
            VALUES (%s, %s, %s, %s, 'pending')
        """, (user["sub"], product["type"], session.id, product["price_cents"]))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Warning: Could not save purchase: {e}")

    return {"checkout_url": session.url, "session_id": session.id}


@router.get("/verify/{session_id}")
async def verify_checkout(session_id: str, authorization: Optional[str] = Header(None)):
    user = get_current_user(authorization)

    result = verify_payment(session_id)

    if result["status"] == "paid":
        conn = get_connection()
        cur = conn.cursor()

        # Update purchase status
        cur.execute(
            "UPDATE purchases SET status = 'completed' WHERE stripe_payment_id = %s",
            (session_id,),
        )

        # Get product credits
        product_id = result.get("product_id")
        credits_to_add = 0
        if product_id:
            cur.execute("SELECT credits FROM products WHERE id = %s", (product_id,))
            product = cur.fetchone()
            if product:
                credits_to_add = product["credits"]

        # Add credits
        if credits_to_add > 0:
            cur.execute("""
                INSERT INTO user_credits (user_id, credits_balance, total_purchased, total_used)
                VALUES (%s, %s, %s, 0)
                ON CONFLICT (user_id) DO UPDATE SET
                    credits_balance = user_credits.credits_balance + %s,
                    total_purchased = user_credits.total_purchased + %s,
                    updated_at = NOW()
            """, (user["sub"], credits_to_add, credits_to_add, credits_to_add, credits_to_add))

            cur.execute("""
                INSERT INTO credit_transactions (user_id, type, amount, description, reference_id)
                VALUES (%s, 'purchase', %s, 'Compra via Stripe', %s)
            """, (user["sub"], credits_to_add, session_id))

        conn.commit()
        cur.close()
        conn.close()

        return {"success": True, "credits_added": credits_to_add}

    return {"success": False, "status": result["status"]}


@router.get("/products")
async def list_available_products():
    """List active products for the storefront."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, description, type, price_cents, credits
        FROM products
        WHERE active = true
        ORDER BY price_cents ASC
    """)
    products = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": str(p["id"]), **{k: v for k, v in p.items() if k != "id"}} for p in products]
