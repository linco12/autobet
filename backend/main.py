from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import init_db
from backend.services.scheduler import start_scheduler, stop_scheduler, get_scheduler_status
from backend.services.data_sync import sync_odds_and_predictions
from backend.routers import matches, predictions, recipients, webhook
from backend.config import settings
from backend.database import SessionLocal
from backend.services.whatsapp import send_daily_predictions
from backend import models

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AutoBet starting up")
    init_db()
    _seed_default_recipient()
    start_scheduler()
    yield

    stop_scheduler()
    logger.info("AutoBet shut down")


def _seed_default_recipient():
    """Ensure the owner's number is always in the recipients table."""
    db = SessionLocal()
    try:
        exists = db.query(models.WhatsAppRecipient).filter(
            models.WhatsAppRecipient.phone_number == settings.DEFAULT_RECIPIENT
        ).first()
        if not exists:
            db.add(models.WhatsAppRecipient(
                name="Owner",
                phone_number=settings.DEFAULT_RECIPIENT,
                active=True,
            ))
            db.commit()
            logger.info(f"Default recipient {settings.DEFAULT_RECIPIENT} seeded")
    finally:
        db.close()


app = FastAPI(
    title="AutoBet API",
    description="Football odds monitoring, prediction engine & WhatsApp alerts",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(matches.router)
app.include_router(predictions.router)
app.include_router(recipients.router)
app.include_router(webhook.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "scheduler": get_scheduler_status()}


@app.post("/api/admin/send-whatsapp-now")
def manual_whatsapp_send():
    """Manually trigger the daily WhatsApp broadcast."""
    db = SessionLocal()
    try:
        result = send_daily_predictions(db)
        return result
    finally:
        db.close()
