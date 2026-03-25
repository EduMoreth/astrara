import os
import uuid
from database import get_connection


def generate_referral_code(user_id: str) -> str:
    """Generate or get existing referral code for a user."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT referral_code FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()

    if user and user["referral_code"]:
        cur.close()
        conn.close()
        return user["referral_code"]

    # Generate unique code
    code = uuid.uuid4().hex[:8].upper()
    cur.execute("UPDATE users SET referral_code = %s WHERE id = %s", (code, user_id))
    conn.commit()
    cur.close()
    conn.close()
    return code


def process_referral(referred_user_id: str, referral_code: str) -> dict:
    """Process a referral when a new user signs up with a code."""
    conn = get_connection()
    cur = conn.cursor()

    # Find referrer
    cur.execute("SELECT id, name FROM users WHERE referral_code = %s", (referral_code,))
    referrer = cur.fetchone()

    if not referrer:
        cur.close()
        conn.close()
        return {"success": False, "reason": "Codigo de indicacao invalido"}

    if str(referrer["id"]) == referred_user_id:
        cur.close()
        conn.close()
        return {"success": False, "reason": "Voce nao pode usar seu proprio codigo"}

    # Check if already referred
    cur.execute("SELECT id FROM referrals WHERE referred_id = %s", (referred_user_id,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return {"success": False, "reason": "Usuario ja foi indicado anteriormente"}

    # Get credits reward from config
    cur.execute("SELECT value FROM system_config WHERE key = 'referral_credits'")
    config = cur.fetchone()
    credits_reward = int(config["value"]) if config else 1

    # Record referral
    cur.execute("""
        INSERT INTO referrals (referrer_id, referred_id, referral_code, credits_awarded, status)
        VALUES (%s, %s, %s, %s, 'completed')
    """, (referrer["id"], referred_user_id, referral_code, credits_reward))

    # Award credits to referrer
    cur.execute("""
        INSERT INTO user_credits (user_id, credits_balance, total_purchased, total_used)
        VALUES (%s, %s, %s, 0)
        ON CONFLICT (user_id) DO UPDATE SET
            credits_balance = user_credits.credits_balance + %s,
            total_purchased = user_credits.total_purchased + %s,
            updated_at = NOW()
    """, (referrer["id"], credits_reward, credits_reward, credits_reward, credits_reward))

    # Log transaction
    cur.execute("""
        INSERT INTO credit_transactions (user_id, type, amount, description)
        VALUES (%s, 'referral', %s, %s)
    """, (referrer["id"], credits_reward, f"Indicacao de novo usuario"))

    # Mark referred user
    cur.execute("UPDATE users SET referred_by = %s WHERE id = %s", (referrer["id"], referred_user_id))

    conn.commit()
    cur.close()
    conn.close()

    return {"success": True, "credits_awarded": credits_reward, "referrer_name": referrer["name"]}


def get_referral_stats(user_id: str) -> dict:
    """Get referral statistics for a user."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT referral_code FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    code = user["referral_code"] if user else None

    if not code:
        code = generate_referral_code(user_id)

    cur.execute("""
        SELECT COUNT(*) as total, COALESCE(SUM(credits_awarded), 0) as credits
        FROM referrals WHERE referrer_id = %s AND status = 'completed'
    """, (user_id,))
    stats = cur.fetchone()

    cur.close()
    conn.close()

    return {
        "referral_code": code,
        "referral_link": f"https://www.astrara.online/auth/register?ref={code}",
        "total_referrals": stats["total"],
        "total_credits_earned": stats["credits"],
    }
