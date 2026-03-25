import os
import anthropic
import tweepy
from datetime import date
from database import get_connection

TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET", "")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET", "")

anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def post_tweet(text: str) -> dict:
    """Post a tweet using tweepy (Twitter API v2 + OAuth 1.0a)."""
    client = tweepy.Client(
        consumer_key=TWITTER_API_KEY,
        consumer_secret=TWITTER_API_SECRET,
        access_token=TWITTER_ACCESS_TOKEN,
        access_token_secret=TWITTER_ACCESS_SECRET,
    )
    response = client.create_tweet(text=text)
    tweet_id = response.data["id"]
    return {"data": {"id": tweet_id}}


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
- Maximo 270 caracteres (para seguranca)
- Tom poetico e inspirador
- Inclua 2-3 hashtags de astrologia em portugues
- Inclua o link astrara.online
- Em portugues brasileiro
- Use 1-2 emojis com moderacao

Retorne APENAS o texto do tweet, nada mais."""

    message = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text.strip().strip('"')


def run_daily_tweet(target_date: date = None):
    """Full flow: generate + post + save to DB."""
    if not target_date:
        target_date = date.today()

    if not TWITTER_API_KEY or not TWITTER_ACCESS_TOKEN:
        print("Twitter API keys not configured. Skipping.")
        return

    conn = get_connection()
    cur = conn.cursor()

    # Check if already posted today
    cur.execute("SELECT status FROM twitter_posts WHERE post_date = %s", (target_date,))
    existing = cur.fetchone()
    if existing and existing["status"] == "published":
        print(f"Tweet for {target_date} already published. Skipping.")
        cur.close()
        conn.close()
        return

    try:
        tweet_text = generate_daily_tweet()
        print(f"Generated tweet: {tweet_text[:80]}...")

        result = post_tweet(tweet_text)
        twitter_id = result.get("data", {}).get("id", "")
        print(f"Tweet posted! ID: {twitter_id}")

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

    except Exception as e:
        error_msg = str(e)
        print(f"Tweet failed: {error_msg}")

        cur.execute("""
            INSERT INTO twitter_posts (post_date, status, error_message)
            VALUES (%s, 'failed', %s)
            ON CONFLICT (post_date) DO UPDATE SET
                status = 'failed', error_message = EXCLUDED.error_message
        """, (target_date, error_msg))
        conn.commit()
        raise

    finally:
        cur.close()
        conn.close()
