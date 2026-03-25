import logging
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger("scheduler")
BRT = pytz.timezone("America/Sao_Paulo")


def start_scheduler():
    """Start all scheduled jobs."""
    scheduler = BackgroundScheduler(timezone=BRT)

    # Instagram daily post at 7:00 AM BRT
    try:
        from services.daily_post_orchestrator import run_daily_instagram_post
        scheduler.add_job(
            func=run_daily_instagram_post,
            trigger=CronTrigger(hour=7, minute=0, timezone=BRT),
            id="daily_instagram_post",
            name="Post diario Instagram",
            replace_existing=True,
            misfire_grace_time=3600,
        )
        logger.info("Scheduled: Instagram daily at 7:00 BRT")
    except Exception as e:
        logger.error(f"Failed to schedule Instagram: {e}")

    # Twitter daily post at 7:15 AM BRT (15 min after Instagram)
    try:
        from services.twitter_service import run_daily_tweet
        scheduler.add_job(
            func=run_daily_tweet,
            trigger=CronTrigger(hour=7, minute=15, timezone=BRT),
            id="daily_twitter_post",
            name="Tweet diario",
            replace_existing=True,
            misfire_grace_time=3600,
        )
        logger.info("Scheduled: Twitter daily at 7:15 BRT")
    except Exception as e:
        logger.error(f"Failed to schedule Twitter: {e}")

    # Weekly newsletter on Mondays at 8:00 AM BRT
    try:
        from services.newsletter_service import send_weekly_newsletter
        scheduler.add_job(
            func=send_weekly_newsletter,
            trigger=CronTrigger(day_of_week="mon", hour=8, minute=0, timezone=BRT),
            id="weekly_newsletter",
            name="Newsletter semanal",
            replace_existing=True,
            misfire_grace_time=7200,
        )
        logger.info("Scheduled: Newsletter weekly on Mondays 8:00 BRT")
    except Exception as e:
        logger.error(f"Failed to schedule Newsletter: {e}")

    # Blog post twice a week (Wednesday and Saturday at 9:00 AM BRT)
    try:
        from services.blog_service import generate_and_publish_blog_post
        scheduler.add_job(
            func=generate_and_publish_blog_post,
            trigger=CronTrigger(day_of_week="wed,sat", hour=9, minute=0, timezone=BRT),
            id="blog_post_generation",
            name="Blog post automatico",
            replace_existing=True,
            misfire_grace_time=7200,
        )
        logger.info("Scheduled: Blog posts Wed+Sat at 9:00 BRT")
    except Exception as e:
        logger.error(f"Failed to schedule Blog: {e}")

    scheduler.start()
    logger.info("All schedulers started successfully")
    return scheduler
