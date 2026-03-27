import logging
from datetime import date
from services.astral_content_service import get_daily_transits, generate_daily_content
from services.image_generator_service import generate_post_image
from services.instagram_service import publish_daily_post
from database import get_connection

logger = logging.getLogger("daily_post")


def run_daily_all_platforms(target_date: date = None):
    """
    Master orchestrator: generates content ONCE and publishes to ALL platforms.
    Called daily at 7am Brasilia. Ensures identical content everywhere.
    """
    if target_date is None:
        target_date = date.today()

    logger.info(f"Starting daily content generation for {target_date}")

    # Early check: skip if both platforms already published (avoids wasting AI calls)
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT status FROM instagram_posts WHERE post_date = %s", (target_date,))
        ig_row = cur.fetchone()
        cur.execute("SELECT status FROM twitter_posts WHERE post_date = %s", (target_date,))
        tw_row = cur.fetchone()
        cur.close()
        conn.close()
        ig_done = ig_row and ig_row["status"] in ("published", "pending")
        tw_done = tw_row and tw_row["status"] in ("published", "pending")
        if ig_done and tw_done:
            logger.info(f"Both platforms already handled for {target_date}. Skipping content generation.")
            return {"date": str(target_date), "instagram": {"status": ig_row["status"]}, "twitter": {"status": tw_row["status"]}}
    except Exception as e:
        logger.warning(f"Early dedup check failed, proceeding anyway: {e}")

    # 1. Calculate transits (shared across all platforms)
    transits = get_daily_transits(target_date)
    logger.info("Transits calculated.")

    # 2. Generate content ONCE with Claude (shared across all platforms)
    content = generate_daily_content(transits)
    logger.info(f"Content generated: {content.get('titulo', 'N/A')}")

    # 3. Generate image ONCE (shared by Instagram + Twitter)
    image_path = generate_post_image(content, target_date)
    logger.info(f"Image generated: {image_path}")

    # 4. Publish to each platform
    ig_result = _publish_instagram(target_date, content, image_path)
    tw_result = _publish_twitter(target_date, content, image_path)

    return {
        "date": str(target_date),
        "instagram": ig_result,
        "twitter": tw_result,
    }


def run_daily_instagram_post(target_date: date = None):
    """Legacy function for backward compatibility with existing cron."""
    return run_daily_all_platforms(target_date)


def _publish_instagram(target_date: date, content: dict, image_path: str) -> dict:
    """Publish to Instagram."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Atomically claim the slot with a 'pending' record to prevent race conditions
        cur.execute("""
            INSERT INTO instagram_posts (post_date, status)
            VALUES (%s, 'pending')
            ON CONFLICT (post_date) DO NOTHING
        """, (target_date,))
        conn.commit()

        if cur.rowcount == 0:
            # Record already exists — check its status
            cur.execute("SELECT status FROM instagram_posts WHERE post_date = %s", (target_date,))
            existing = cur.fetchone()
            if existing and existing["status"] in ("published", "pending"):
                cur.close()
                conn.close()
                status = existing["status"]
                logger.info(f"Instagram for {target_date}: {status}. Skipping.")
                return {"status": "already_published" if status == "published" else "in_progress"}
            # Status is 'failed' — retry by updating to 'pending'
            cur.execute("""
                UPDATE instagram_posts SET status = 'pending', error_message = NULL
                WHERE post_date = %s AND status = 'failed'
            """, (target_date,))
            conn.commit()
            if cur.rowcount == 0:
                # Another process already retrying
                cur.close()
                conn.close()
                return {"status": "in_progress"}

        caption = content.get("legenda_instagram", "")
        if content.get("hashtags"):
            caption += "\n\n" + content["hashtags"]

        result = publish_daily_post(image_path, caption)

        cur.execute("""
            INSERT INTO instagram_posts
                (post_date, horoscope_text, transits_text, image_path,
                 instagram_media_id, instagram_permalink, status, published_at)
            VALUES (%s, %s, %s, %s, %s, %s, 'published', NOW())
            ON CONFLICT (post_date) DO UPDATE SET
                horoscope_text = EXCLUDED.horoscope_text,
                transits_text = EXCLUDED.transits_text,
                image_path = EXCLUDED.image_path,
                instagram_media_id = EXCLUDED.instagram_media_id,
                instagram_permalink = EXCLUDED.instagram_permalink,
                status = 'published', published_at = NOW(), error_message = NULL
        """, (target_date, content.get("horoscopo", ""), content.get("transitos", ""),
              image_path, result.get("media_id", ""), result.get("permalink", "")))
        conn.commit()
        logger.info(f"Instagram published: {result.get('permalink', '')}")
        return {"status": "published"}

    except Exception as e:
        logger.error(f"Instagram failed: {e}")
        try:
            cur.execute("""
                INSERT INTO instagram_posts (post_date, status, error_message)
                VALUES (%s, 'failed', %s)
                ON CONFLICT (post_date) DO UPDATE SET status = 'failed', error_message = EXCLUDED.error_message
            """, (target_date, str(e)))
            conn.commit()
        except Exception:
            pass
        return {"status": "failed", "error": str(e)}
    finally:
        cur.close()
        conn.close()


def _publish_twitter(target_date: date, content: dict, image_path: str) -> dict:
    """Publish to Twitter with the SAME content and image."""
    import os
    TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "")
    if not TWITTER_API_KEY:
        return {"status": "skipped", "reason": "no_credentials"}

    conn = get_connection()
    cur = conn.cursor()

    try:
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
                cur.close()
                conn.close()
                status = existing["status"]
                logger.info(f"Twitter for {target_date}: {status}. Skipping.")
                return {"status": "already_published" if status == "published" else "in_progress"}
            # Status is 'failed' — retry
            cur.execute("""
                UPDATE twitter_posts SET status = 'pending', error_message = NULL
                WHERE post_date = %s AND status = 'failed'
            """, (target_date,))
            conn.commit()
            if cur.rowcount == 0:
                cur.close()
                conn.close()
                return {"status": "in_progress"}

        # Build tweet from same content (shortened for 280 char limit)
        horoscopo = content.get("horoscopo", "")
        titulo = content.get("titulo", "")
        energia = content.get("energia_do_dia", "")

        # Compose tweet: emoji + title + short horoscope + link + hashtags
        tweet = f"✨ {titulo}\n\n"
        # Truncate horoscope to fit
        remaining = 280 - len(tweet) - 40  # reserve space for link + hashtags
        if len(horoscopo) > remaining:
            horoscopo = horoscopo[:remaining-3] + "..."
        tweet += horoscopo + "\n\n"
        tweet += "astrara.online\n"
        tweet += "#Astrologia #Horoscopo"

        if len(tweet) > 280:
            tweet = tweet[:277] + "..."

        # Post tweet with image using tweepy
        from services.twitter_service import post_tweet_with_image
        result = post_tweet_with_image(tweet, image_path)
        twitter_id = result.get("data", {}).get("id", "")

        cur.execute("""
            INSERT INTO twitter_posts (post_date, tweet_text, twitter_post_id, status, published_at)
            VALUES (%s, %s, %s, 'published', NOW())
            ON CONFLICT (post_date) DO UPDATE SET
                tweet_text = EXCLUDED.tweet_text, twitter_post_id = EXCLUDED.twitter_post_id,
                status = 'published', published_at = NOW()
        """, (target_date, tweet, twitter_id))
        conn.commit()
        logger.info(f"Twitter published: {twitter_id}")
        return {"status": "published"}

    except Exception as e:
        logger.error(f"Twitter failed: {e}")
        try:
            cur.execute("""
                INSERT INTO twitter_posts (post_date, status, error_message)
                VALUES (%s, 'failed', %s)
                ON CONFLICT (post_date) DO UPDATE SET status = 'failed', error_message = EXCLUDED.error_message
            """, (target_date, str(e)))
            conn.commit()
        except Exception:
            pass
        return {"status": "failed", "error": str(e)}
    finally:
        cur.close()
        conn.close()
