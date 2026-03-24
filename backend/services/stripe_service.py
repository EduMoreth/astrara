import stripe
import os
from datetime import datetime

stripe.api_key = os.getenv("STRIPE_API_KEY")


# ── Products ─────────────────────────────────────────────────
def create_stripe_product(name: str, description: str):
    return stripe.Product.create(name=name, description=description or "")


def update_stripe_product(stripe_product_id: str, name: str, description: str):
    return stripe.Product.modify(stripe_product_id, name=name, description=description or "")


def archive_stripe_product(stripe_product_id: str):
    return stripe.Product.modify(stripe_product_id, active=False)


# ── Prices ───────────────────────────────────────────────────
def create_stripe_price(product_id: str, amount_cents: int, currency: str = "brl"):
    return stripe.Price.create(
        product=product_id,
        unit_amount=amount_cents,
        currency=currency,
    )


def deactivate_stripe_price(stripe_price_id: str):
    return stripe.Price.modify(stripe_price_id, active=False)


# ── Checkout ─────────────────────────────────────────────────
def create_checkout_session(
    stripe_price_id: str,
    user_id: str,
    product_id: str,
    success_url: str,
    cancel_url: str,
    customer_email: str = None,
):
    params = {
        "payment_method_types": ["card"],
        "line_items": [{"price": stripe_price_id, "quantity": 1}],
        "mode": "payment",
        "success_url": success_url + "?session_id={CHECKOUT_SESSION_ID}",
        "cancel_url": cancel_url,
        "metadata": {"user_id": user_id, "product_id": product_id},
    }
    if customer_email:
        params["customer_email"] = customer_email
    return stripe.checkout.Session.create(**params)


# ── Payment Verification ────────────────────────────────────
def get_checkout_session(session_id: str):
    return stripe.checkout.Session.retrieve(session_id)


def verify_payment(session_id: str) -> dict:
    """Check payment status directly via Stripe API."""
    session = stripe.checkout.Session.retrieve(session_id)
    return {
        "status": session.payment_status,
        "user_id": session.metadata.get("user_id"),
        "product_id": session.metadata.get("product_id"),
        "amount_total": session.amount_total,
        "currency": session.currency,
    }


# ── Revenue / Reports ───────────────────────────────────────
def get_balance_transactions(limit: int = 100):
    return stripe.BalanceTransaction.list(limit=limit)


def get_payment_intents(limit: int = 50):
    return stripe.PaymentIntent.list(limit=limit)


def get_monthly_revenue():
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0)
    transactions = stripe.BalanceTransaction.list(
        created={"gte": int(start_of_month.timestamp())},
        limit=100,
        type="charge",
    )
    total = sum(
        t.amount for t in transactions.auto_paging_iter() if t.status == "available"
    )
    return total


def get_yearly_revenue():
    start_of_year = datetime.now().replace(month=1, day=1, hour=0, minute=0, second=0)
    transactions = stripe.BalanceTransaction.list(
        created={"gte": int(start_of_year.timestamp())},
        limit=100,
        type="charge",
    )
    total = sum(
        t.amount for t in transactions.auto_paging_iter() if t.status == "available"
    )
    return total
