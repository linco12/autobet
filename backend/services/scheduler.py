"""
Background scheduler — runs odds sync every 30 minutes and sends
daily WhatsApp predictions at the configured hour (default 08:00 UTC).
"""
import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from backend.config import settings
from backend.services.data_sync import sync_odds_and_predictions
from backend.database import SessionLocal
from backend.services.whatsapp import send_daily_predictions

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def _run_sync():
    logger.info("Scheduled odds sync started")
    try:
        count = await sync_odds_and_predictions()
        logger.info(f"Scheduled sync done — {count} matches updated")
    except Exception as e:
        logger.error(f"Scheduled sync error: {e}")


def _run_daily_whatsapp():
    logger.info("Running AI refresh then sending daily WhatsApp predictions")
    from backend.services.ai_refresh import ai_refresh_todays_matches
    try:
        updated = ai_refresh_todays_matches()
        logger.info(f"AI refresh done: {updated} matches updated")
    except Exception as e:
        logger.error(f"AI refresh error: {e}")

    db = SessionLocal()
    try:
        result = send_daily_predictions(db)
        logger.info(f"Daily WhatsApp result: {result}")
    except Exception as e:
        logger.error(f"Daily WhatsApp error: {e}")
    finally:
        db.close()


def start_scheduler():
    global _scheduler
    _scheduler = AsyncIOScheduler()

    # Sync odds every 30 minutes
    _scheduler.add_job(
        _run_sync,
        trigger=IntervalTrigger(minutes=30),
        id="odds_sync",
        name="Odds & Predictions Sync",
        replace_existing=True,
        max_instances=1,
    )

    # Send WhatsApp daily digest
    _scheduler.add_job(
        _run_daily_whatsapp,
        trigger=CronTrigger(hour=settings.DAILY_SEND_HOUR, minute=0),
        id="daily_whatsapp",
        name="Daily WhatsApp Predictions",
        replace_existing=True,
        max_instances=1,
    )

    _scheduler.start()
    logger.info(f"Scheduler started — sync every 30min, WhatsApp daily at {settings.DAILY_SEND_HOUR:02d}:00 UTC")


def stop_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")


def get_scheduler_status() -> dict:
    if not _scheduler:
        return {"running": False, "jobs": []}
    jobs = []
    for job in _scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": str(job.next_run_time),
        })
    return {"running": _scheduler.running, "jobs": jobs}
