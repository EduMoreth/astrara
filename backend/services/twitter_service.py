import os
import json
import hmac
import hashlib
import base64
import time
import urllib.parse
import httpx
import anthropic
from datetime import date
from database import get_connection

TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET", "")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET", "")

anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def _oauth_signature(method: str, url: str, params: dict) -> str:
    """Generate OAuth 1.0a signature."""
    sorted_params = "&".join(f"{k}={urllib.parse.quote(str(v), safe='')}"
                             for k, v in sorted(params.items()))
    base_string = f"{method}&{urllib.parse.quote(url, safe='')}&{urllib.parse.quote(sorted_params, safe='')}"
    signing_key = f"{urllib.parse.quote(TWITTER_API_SECRET, safe='')}&{urllib.parse.quote(TWITTER_ACCESS_SECRET, safe='')}"
    signature = base64.b64encode(
        hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha256).digest()
    ).decode()
    return signature


def post_tweet(text: str) -> dict:
    """Post a tweet using Twitter API v2 with OAuth 1.0a."""
    url = "https://api.twitter.com/2/tweets"

    oauth_params = {
        "oauth_consumer_key": TWITTER_API_KEY,
        "oauth_nonce": base64.b64encode(os.urandom(32)).decode().replace("=", "").replace("+", "").replace("/", ""),
        "oauth_signature_method": "HMAC-SHA256",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": TWITTER_ACCESS_TOKEN,
        "oauth_version": "1.0",
    }

    signature = _oauth_signature("POST", url, oauth_params)
    oauth_params["oauth_signature"] = signature

    auth_header = "OAuth " + ", ".join(
        f'{k}="{urllib.parse.quote(v, safe="")}"' for k, v in sorted(oauth_params.items())
    )

    response = httpx.post(
        url,
        json={"text": text},
        headers={
            "Authorization": auth_header,
            "Content-Type": "application/json",
        },
        timeout=30,
    )

    if response.status_code not in (200, 201):
        raise Exception(f"Twitter API error: {response.status_code} {response.text}")

    return response.json()


def generate_daily_tweet(transits: dict = None) -> str:
    """Generate daily horoscope tweet using Claude."""
    from services.astral_content_service import get_daily_transits

    if not transits:
        transits = get_daily_transits(date.today())

    prompt = f"""Gere um tweet de horoscopo diario para a conta @Astrara_Online.

TRANSITOS DE HOJE ({transits['date']}):
- Sol: {transits['sun']['deg']} em {transits['sun']['sign']}
- Lua: {transits['moon']['deg']} em {transits['moon']['sign']}
- Mercurio: {transits['mercury']['deg']} em {transits['mercury']['sign']}
- Venus: {transits['venus']['deg']} em {transits['venus']['sign']}

REGRAS:
- Maximo 280 caracteres
- Tom poetico e inspirador
- Inclua 2-3 hashtags de astrologia
- Inclua o link astrara.online
- Em portugues
- Use emojis com moderacao (1-2)

Retorne APENAS o texto do tweet, nada mais."""

    message = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text.strip()


def run_daily_tweet(target_date: date = None):
    """Full flow: generate + post + save to DB."""
    if not target_date:
        target_date = date.today()

    if not TWITTER_API_KEY:
        print("Twitter API keys not configured. Skipping.")
        return

    conn = get_connection()
    cur = conn.cursor()

    # Check if already posted
    cur.execute("SELECT status FROM twitter_posts WHERE post_date = %s", (target_date,))
    existing = cur.fetchone()
    if existing and existing["status"] == "published":
        cur.close()
        conn.close()
        return

    try:
        tweet_text = generate_daily_tweet()
        result = post_tweet(tweet_text)
        twitter_id = result.get("data", {}).get("id", "")

        cur.execute("""
            INSERT INTO twitter_posts (post_date, tweet_text, twitter_post_id, status, published_at)
            VALUES (%s, %s, %s, 'published', NOW())
            ON CONFLICT (post_date) DO UPDATE SET
                tweet_text = EXCLUDED.tweet_text,
                twitter_post_id = EXCLUDED.twitter_post_id,
                status = 'published',
                published_at = NOW()
        """, (target_date, tweet_text, twitter_id))
        conn.commit()
        print(f"Tweet posted: {tweet_text[:50]}...")

    except Exception as e:
        cur.execute("""
            INSERT INTO twitter_posts (post_date, status, error_message)
            VALUES (%s, 'failed', %s)
            ON CONFLICT (post_date) DO UPDATE SET
                status = 'failed', error_message = EXCLUDED.error_message
        """, (target_date, str(e)))
        conn.commit()
        print(f"Tweet failed: {e}")

    finally:
        cur.close()
        conn.close()
