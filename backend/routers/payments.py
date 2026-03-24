import os
import stripe
from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel
from typing import Optional
from database import get_connection
from routers.auth import verify_token

router = APIRouter(prefix="/payments", tags=["payments"])

stripe.api_key = os.getenv("STRIPE_API_KEY")

# Product prices in cents
PRODUCTS = {
    "interpretation": {
        "name": "Interpretacao Completa do Mapa Astral",
        "description": "Analise profunda de cada planeta, casa e aspecto do seu mapa natal com IA.",
        "amount_cents": 2990,  # R$ 29,90
        "currency": "brl",
    },
    "interpretation_pro": {
        "name": "Interpretacao Pro + Previsoes",
        "description": "Interpretacao completa + previsoes para os proximos 12 meses.",
        "amount_cents": 5990,  # R$ 59,90
        "currency": "brl",
    },
}


class CheckoutRequest(BaseModel):
    product_type: str
    chart_id: Optional[str] = None


def get_user_from_token(authorization: Optional[str]) -> Optional[dict]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.replace("Bearer ", "")
    try:
        return verify_token(token)
    except Exception:
        return None


@router.get("/products")
async def list_products():
    """List available products and prices."""
    return {
        key: {
            "name": p["name"],
            "description": p["description"],
            "price": p["amount_cents"] / 100,
            "currency": p["currency"],
        }
        for key, p in PRODUCTS.items()
    }


@router.post("/create-checkout")
async def create_checkout(
    data: CheckoutRequest,
    authorization: Optional[str] = Header(None),
):
    """Create a Stripe Checkout session."""
    user = get_user_from_token(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Login necessario para comprar")

    product = PRODUCTS.get(data.product_type)
    if not product:
        raise HTTPException(status_code=400, detail="Produto invalido")

    frontend_url = os.getenv("FRONTEND_URL", "https://astrara.online")

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": product["currency"],
                        "product_data": {
                            "name": product["name"],
                            "description": product["description"],
                        },
                        "unit_amount": product["amount_cents"],
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=f"{frontend_url}/chart?payment=success&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{frontend_url}/chart?payment=cancelled",
            metadata={
                "user_id": user["sub"],
                "product_type": data.product_type,
                "chart_id": data.chart_id or "",
            },
            customer_email=user.get("email"),
        )
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=f"Erro Stripe: {str(e)}")

    # Create pending purchase
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO purchases (user_id, chart_id, product_type, stripe_payment_id, amount_cents, status)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (
                user["sub"],
                data.chart_id if data.chart_id else None,
                data.product_type,
                session.id,
                product["amount_cents"],
                "pending",
            ),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Warning: Could not save purchase record: {e}")

    return {"checkout_url": session.url, "session_id": session.id}


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    if webhook_secret and sig_header:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        except (ValueError, stripe.error.SignatureVerificationError):
            raise HTTPException(status_code=400, detail="Webhook signature invalid")
    else:
        import json
        event = json.loads(payload)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        stripe_session_id = session["id"]
        payment_status = session.get("payment_status", "")

        if payment_status == "paid":
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute(
                    "UPDATE purchases SET status = 'completed' WHERE stripe_payment_id = %s",
                    (stripe_session_id,),
                )
                conn.commit()
                cur.close()
                conn.close()
                print(f"Payment completed: {stripe_session_id}")
            except Exception as e:
                print(f"Error updating purchase: {e}")

    return {"received": True}


@router.get("/check/{session_id}")
async def check_payment(
    session_id: str,
    authorization: Optional[str] = Header(None),
):
    """Check if a payment was completed."""
    user = get_user_from_token(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Login necessario")

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT status, product_type FROM purchases WHERE stripe_payment_id = %s AND user_id = %s",
            (session_id, user["sub"]),
        )
        purchase = cur.fetchone()
        cur.close()
        conn.close()

        if not purchase:
            return {"paid": False}

        return {"paid": purchase["status"] == "completed", "product_type": purchase["product_type"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
