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


def _get_client():
    """Get tweepy Client (v2) for posting."""
    return tweepy.Client(
        consumer_key=TWITTER_API_KEY,
        consumer_secret=TWITTER_API_SECRET,
        access_token=TWITTER_ACCESS_TOKEN,
        access_token_secret=TWITTER_ACCESS_SECRET,
    )


def _get_api_v1():
    """Get tweepy API (v1.1) for media upload."""
    auth = tweepy.OAuth1UserHandler(
        TWITTER_API_KEY, TWITTER_API_SECRET,
        TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET,
    )
    return tweepy.API(auth)


def post_tweet(text: str) -> dict:
    """Post a text-only tweet."""
    client = _get_client()
    response = client.create_tweet(text=text)
    tweet_id = response.data["id"]
    return {"data": {"id": tweet_id}}


def post_tweet_with_image(text: str, image_path: str) -> dict:
    """Post a tweet with image. Upload via v1.1 API, post via v2."""
    # Upload media via v1.1 (v2 doesn't support media upload directly)
    api_v1 = _get_api_v1()
    media = api_v1.media_upload(filename=image_path)
    media_id = media.media_id

    # Post tweet with media via v2
    client = _get_client()
    response = client.create_tweet(text=text, media_ids=[media_id])
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

    # Atomically claim the slot with a 'pending' record to prevent race conditions
    cur.execute("""
        INSERT INTO twitter_posts (post_date, status)
        VALUES (%s, 'pending')
        ON CONFLICT (post_date) DO NOTHING
    """, (target_date,))
    conn.commit()

    if cur.rowcount == 0:
        cur.execute("SELECT status FROM twitter_posts WHERE post_date = %s", (target_date,))
        existing = cur.fetchone()
        if existing and existing["status"] in ("published", "pending"):
            print(f"Tweet for {target_date}: {existing['status']}. Skipping.")
            cur.close()
            conn.close()
            return
        # Status is 'failed' — retry
        cur.execute("""
            UPDATE twitter_posts SET status = 'pending', error_message = NULL
            WHERE post_date = %s AND status = 'failed'
        """, (target_date,))
        conn.commit()
        if cur.rowcount == 0:
            print(f"Tweet for {target_date}: already being retried. Skipping.")
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
