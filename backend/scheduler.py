import logging
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from services.daily_post_orchestrator import run_daily_instagram_post

logger = logging.getLogger("scheduler")


def start_scheduler():
    """Start the scheduler for daily Instagram post at 7am Brasilia time."""
    scheduler = BackgroundScheduler(timezone=pytz.timezone("America/Sao_Paulo"))

    scheduler.add_job(
        func=run_daily_instagram_post,
        trigger=CronTrigger(
            hour=7, minute=0,
            timezone=pytz.timezone("America/Sao_Paulo"),
        ),
        id="daily_instagram_post",
        name="Post diario Instagram - Astrara",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    scheduler.start()
    logger.info("Scheduler iniciado - post diario as 7h (Brasilia)")
    return scheduler
