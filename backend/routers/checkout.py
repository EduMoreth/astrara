import os
import stripe
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel
from database import get_connection
from routers.auth import verify_token
from services.stripe_service import create_checkout_session, verify_payment

router = APIRouter(prefix="/checkout", tags=["checkout"])

stripe.api_key = os.getenv("STRIPE_API_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")


def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Login necessario")
    token = authorization.replace("Bearer ", "")
    return verify_token(token)


class CheckoutCreateRequest(BaseModel):
    product_id: str


def _fulfill_purchase(session_id: str, user_id: str, product_id: str) -> int:
    """
    Idempotent credit fulfillment.
    Checks if the purchase was already completed before adding credits.
    Returns the number of credits added (0 if already fulfilled).
    """
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Check if already fulfilled (idempotent guard)
        cur.execute(
            "SELECT status FROM purchases WHERE stripe_payment_id = %s",
            (session_id,),
        )
        purchase = cur.fetchone()

        if purchase and purchase["status"] == "completed":
            # Already fulfilled — don't add credits again
            return 0

        # Update purchase status
        if purchase:
            cur.execute(
                "UPDATE purchases SET status = 'completed' WHERE stripe_payment_id = %s",
                (session_id,),
            )
        else:
            # Purchase record might not exist (e.g. webhook arrived before create finished)
            cur.execute("""
                INSERT INTO purchases (user_id, product_type, stripe_payment_id, amount_cents, status)
                VALUES (%s, 'one_time', %s, 0, 'completed')
                ON CONFLICT DO NOTHING
            """, (user_id, session_id))

        # Get product credits
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
            """, (user_id, credits_to_add, credits_to_add, credits_to_add, credits_to_add))

            # Check for duplicate transaction before inserting
            cur.execute(
                "SELECT id FROM credit_transactions WHERE reference_id = %s AND user_id = %s AND type = 'purchase'",
                (session_id, user_id),
            )
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO credit_transactions (user_id, type, amount, description, reference_id)
                    VALUES (%s, 'purchase', %s, 'Compra via Stripe', %s)
                """, (user_id, credits_to_add, session_id))

        conn.commit()
        return credits_to_add
    except Exception as e:
        conn.rollback()
        print(f"Error fulfilling purchase {session_id}: {e}")
        raise
    finally:
        cur.close()
        conn.close()


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
        print(f"Checkout creation error: {e}")
        raise HTTPException(status_code=500, detail="Erro ao criar checkout. Tente novamente.")

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
    """Verify payment and add credits. Idempotent — safe to call multiple times.

    Fulfillment uses the user_id stored in the Stripe session metadata (set at
    creation), so it works even when the caller's auth token is missing — e.g. the
    post-payment redirect landing on a different subdomain (apex vs www) where
    localStorage isn't shared. The session_id is a Stripe-issued secret tied to the
    payment, so this is safe and cannot grant credits to an arbitrary user.
    """
    try:
        result = verify_payment(session_id)
    except Exception as e:
        print(f"Verify payment error for {session_id}: {e}")
        raise HTTPException(status_code=502, detail="Nao foi possivel verificar o pagamento.")

    if result["status"] != "paid":
        return {"success": False, "status": result["status"]}

    # Authoritative user is the one recorded in the session metadata at creation.
    user_id = result.get("user_id")

    # Fall back to the authenticated caller only if metadata is somehow absent.
    if not user_id and authorization and authorization.startswith("Bearer "):
        try:
            user_id = verify_token(authorization.replace("Bearer ", ""))["sub"]
        except Exception:
            user_id = None

    if not user_id:
        raise HTTPException(status_code=400, detail="Pagamento sem usuario associado.")

    credits_added = _fulfill_purchase(
        session_id=session_id,
        user_id=user_id,
        product_id=result.get("product_id", ""),
    )
    return {"success": True, "credits_added": credits_added}


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """
    Stripe webhook endpoint for reliable credit delivery.
    Handles checkout.session.completed events.
    This is the PRIMARY mechanism for adding credits — the verify endpoint
    is a fallback for immediate UI feedback.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    # Verify webhook signature if secret is configured
    if STRIPE_WEBHOOK_SECRET:
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
        except stripe.SignatureVerificationError:
            print("Webhook signature verification failed")
            raise HTTPException(status_code=400, detail="Invalid signature")
        except Exception as e:
            print(f"Webhook error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    else:
        print("CRITICAL: STRIPE_WEBHOOK_SECRET not configured — rejecting webhook")
        raise HTTPException(
            status_code=500,
            detail="Webhook secret not configured. Set STRIPE_WEBHOOK_SECRET."
        )

    # Handle checkout.session.completed
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        session_id = session["id"]
        payment_status = session.get("payment_status", "")
        metadata = session.get("metadata", {})
        user_id = metadata.get("user_id", "")
        product_id = metadata.get("product_id", "")
        customer_email = session.get("customer_email") or session.get("customer_details", {}).get("email", "")

        print(f"[Webhook] checkout.session.completed: session={session_id}, "
              f"user_id={user_id}, product_id={product_id}, "
              f"payment_status={payment_status}, email={customer_email}")

        if payment_status == "paid" and user_id:
            try:
                credits_added = _fulfill_purchase(
                    session_id=session_id,
                    user_id=user_id,
                    product_id=product_id,
                )
                print(f"[Webhook] Credits added: {credits_added} for user {user_id}")
            except Exception as e:
                print(f"[Webhook] Error fulfilling purchase: {e}")
                # Return 500 so Stripe retries
                raise HTTPException(status_code=500, detail="Fulfillment error")

        elif payment_status == "paid" and not user_id and customer_email:
            # Fallback: find user by email if metadata is missing
            print(f"[Webhook] No user_id in metadata, trying email lookup: {customer_email}")
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("SELECT id FROM users WHERE email = %s", (customer_email,))
                user_row = cur.fetchone()
                cur.close()
                conn.close()

                if user_row:
                    found_user_id = str(user_row["id"])
                    credits_added = _fulfill_purchase(
                        session_id=session_id,
                        user_id=found_user_id,
                        product_id=product_id,
                    )
                    print(f"[Webhook] Credits added via email lookup: {credits_added} for user {found_user_id}")
                else:
                    print(f"[Webhook] No user found with email {customer_email}")
            except Exception as e:
                print(f"[Webhook] Email lookup error: {e}")
                raise HTTPException(status_code=500, detail="Fulfillment error")

    return {"received": True}


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
