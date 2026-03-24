import logging
from datetime import date
from services.astral_content_service import get_daily_transits, generate_daily_content
from services.image_generator_service import generate_post_image
from services.instagram_service import publish_daily_post
from database import get_connection

logger = logging.getLogger("daily_post")


def run_daily_instagram_post(target_date: date = None):
    """
    Complete daily flow executed at 7am Brasilia time:
    1. Calculate daily transits
    2. Generate content with Claude
    3. Generate image with Astrara branding
    4. Publish to Instagram
    5. Record in database
    """
    if target_date is None:
        target_date = date.today()

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Check if already published today
        cur.execute(
            "SELECT id, status FROM instagram_posts WHERE post_date = %s",
            (target_date,),
        )
        existing = cur.fetchone()
        if existing and existing["status"] == "published":
            logger.info(f"Post de {target_date} ja publicado. Pulando.")
            cur.close()
            conn.close()
            return {"status": "already_published"}

        logger.info(f"Iniciando geracao do post para {target_date}")

        # 1. Transits
        transits = get_daily_transits(target_date)
        logger.info("Transitos calculados.")

        # 2. Content via Claude
        content = generate_daily_content(transits)
        logger.info(f"Conteudo gerado: {content.get('titulo', 'N/A')}")

        # 3. Image
        image_path = generate_post_image(content, target_date)
        logger.info(f"Imagem gerada: {image_path}")

        # 4. Publish to Instagram
        caption = content.get("legenda_instagram", "")
        if content.get("hashtags"):
            caption += "\n\n" + content["hashtags"]

        result = publish_daily_post(image_path, caption)
        logger.info(f"Post publicado: {result.get('permalink', 'N/A')}")

        # 5. Record in database
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
                status = 'published',
                published_at = NOW(),
                error_message = NULL
        """, (
            target_date,
            content.get("horoscopo", ""),
            content.get("transitos", ""),
            image_path,
            result.get("media_id", ""),
            result.get("permalink", ""),
        ))
        conn.commit()
        logger.info("Post registrado no banco com sucesso.")

        return {"status": "published", "permalink": result.get("permalink", "")}

    except Exception as e:
        logger.error(f"Erro no post diario: {e}")
        try:
            cur.execute("""
                INSERT INTO instagram_posts (post_date, status, error_message)
                VALUES (%s, 'failed', %s)
                ON CONFLICT (post_date) DO UPDATE SET
                    status = 'failed', error_message = EXCLUDED.error_message
            """, (target_date, str(e)))
            conn.commit()
        except Exception:
            pass
        return {"status": "failed", "error": str(e)}

    finally:
        cur.close()
        conn.close()
