"""
WhatsApp notification service via Twilio.
Uses the same Twilio account credentials as the VOLWSZIM Land system (Mugagau Park).
"""
import logging
from datetime import datetime
from typing import Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from sqlalchemy.orm import Session
from backend.config import settings
from backend import models

logger = logging.getLogger(__name__)


def get_twilio_client() -> Optional[Client]:
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        logger.error("Twilio credentials not configured")
        return None
    return Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


def send_whatsapp_message(
    to_number: str,
    message: str,
    content_variables: Optional[dict] = None,
) -> tuple[bool, Optional[str], Optional[str]]:
    """
    Send a WhatsApp message via Twilio.
    If content_variables provided and TWILIO_CONTENT_SID is set, uses the approved template.
    Returns (success, message_sid, error_string).
    """
    import json

    client = get_twilio_client()
    if not client:
        return False, None, "Twilio client not initialised — check credentials"

    to_wa = f"whatsapp:{to_number}" if not to_number.startswith("whatsapp:") else to_number

    try:
        if content_variables and settings.TWILIO_CONTENT_SID:
            msg = client.messages.create(
                messaging_service_sid=settings.TWILIO_MESSAGING_SERVICE_SID,
                content_sid=settings.TWILIO_CONTENT_SID,
                content_variables=json.dumps(content_variables),
                to=to_wa,
            )
        else:
            msg = client.messages.create(
                messaging_service_sid=settings.TWILIO_MESSAGING_SERVICE_SID,
                body=message,
                to=to_wa,
            )
        logger.info(f"WhatsApp sent to {to_number} | SID={msg.sid}")
        return True, msg.sid, None
    except TwilioRestException as e:
        logger.error(f"Twilio error sending to {to_number}: {e}")
        return False, None, str(e)


def build_daily_predictions_message(predictions: list[dict], date_str: str) -> str:
    """Format the daily prediction digest for WhatsApp."""
    lines = [
        f"⚽ *AutoBet Daily Predictions* — {date_str}",
        f"{'─' * 30}",
        "",
    ]

    if not predictions:
        lines.append("No high-confidence predictions found for today.")
        return "\n".join(lines)

    value_bets = [p for p in predictions if p.get("value_bet")]
    regular = [p for p in predictions if not p.get("value_bet")]

    if value_bets:
        lines.append("🔥 *VALUE BETS* (Best Edge Today)")
        lines.append("")
        for p in value_bets[:3]:
            lines.extend(_format_prediction(p))
            lines.append("")

    if regular:
        lines.append("📊 *High-Confidence Picks*")
        lines.append("")
        for p in regular[:5]:
            lines.extend(_format_prediction(p))
            lines.append("")

    lines.extend([
        "─" * 30,
        "⚠️ _Bet responsibly. Predictions are analysis-based, not guaranteed._",
        "_AutoBet System_",
    ])
    return "\n".join(lines)


def _format_prediction(p: dict) -> list[str]:
    outcome_emoji = {"home_win": "🏠", "draw": "🤝", "away_win": "✈️"}
    outcome_label = p.get("predicted_outcome", "").replace("_", " ").title()
    emoji = outcome_emoji.get(p.get("predicted_outcome", ""), "⚽")

    lines = [
        f"{emoji} *{p.get('home_team')} vs {p.get('away_team')}*",
        f"   🏆 {p.get('league', 'Unknown League')}",
        f"   🕐 {p.get('match_date', '')}",
        f"   📌 Prediction: *{outcome_label}*",
        f"   📈 Confidence: {p.get('confidence', 0):.1f}%",
    ]
    if p.get("best_odds"):
        lines.append(f"   💰 Best Odds: {p.get('best_odds')} ({p.get('best_bookmaker', '')})")
    if p.get("value_bet"):
        lines.append("   🎯 *VALUE BET DETECTED*")
    if p.get("predicted_goals"):
        goals_label = p.get("predicted_goals", "").replace("_", " ")
        lines.append(f"   ⚽ Goals: {goals_label} ({p.get('goals_confidence', 0):.0f}%)")
    if p.get("btts_prediction"):
        lines.append(f"   🔄 BTTS: {p.get('btts_prediction').upper()} ({p.get('btts_confidence', 0):.0f}%)")
    return lines


def send_daily_predictions(db: Session) -> dict:
    """Send today's top predictions to all active WhatsApp recipients."""
    from backend.services.data_sync import get_todays_top_predictions

    recipients = db.query(models.WhatsAppRecipient).filter(
        models.WhatsAppRecipient.active == True  # noqa: E712
    ).all()

    if not recipients:
        logger.warning("No active WhatsApp recipients configured")
        return {"sent": 0, "failed": 0, "skipped": 0}

    predictions = get_todays_top_predictions(db)
    date_str = datetime.utcnow().strftime("%A %d %B %Y")
    message = build_daily_predictions_message(predictions, date_str)

    # Build template variables from top prediction
    top = predictions[0] if predictions else None
    content_vars = None
    if top and settings.TWILIO_CONTENT_SID:
        outcome_label = top.get("predicted_outcome", "").replace("_", " ").title()
        odds_str = str(top.get("best_odds", "N/A"))
        if top.get("best_bookmaker"):
            odds_str += f" ({top['best_bookmaker']})"
        content_vars = {
            "1": top.get("home_team", ""),
            "2": top.get("away_team", ""),
            "3": top.get("league", ""),
            "4": outcome_label,
            "5": f"{top.get('confidence', 0):.1f}",
            "6": odds_str,
        }

    results = {"sent": 0, "failed": 0, "skipped": 0}

    for recipient in recipients:
        success, sid, error = send_whatsapp_message(recipient.phone_number, message, content_variables=content_vars)

        log = models.NotificationLog(
            recipient_id=recipient.id,
            message=message,
            status="sent" if success else "failed",
            twilio_sid=sid,
            error=error,
        )
        db.add(log)

        if success:
            results["sent"] += 1
        else:
            results["failed"] += 1

    db.commit()
    logger.info(f"Daily predictions sent: {results}")
    return results
