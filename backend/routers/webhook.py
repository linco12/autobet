"""
Twilio WhatsApp inbound webhook.
Receives messages sent to +263787001363 and replies with prediction menus.

Twilio must be configured to POST to: https://your-domain/api/webhook/whatsapp
"""
import logging
from fastapi import APIRouter, Form, Response
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.services.data_sync import get_todays_top_predictions
from backend.services.whatsapp import send_whatsapp_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhook", tags=["Webhook"])

HELP_TEXT = (
    "Welcome to *AutoBet* ⚽\n\n"
    "Send one of these commands:\n"
    "  *Bet* — Today's top predictions\n"
    "  *Value* — Value bets only\n"
    "  *Help* — Show this menu"
)


@router.post("/whatsapp")
async def whatsapp_inbound(
    From: str = Form(...),
    Body: str = Form(...),
):
    """Receives inbound WhatsApp messages from Twilio."""
    sender = From.replace("whatsapp:", "")
    text = Body.strip().lower()
    logger.info(f"Inbound WhatsApp from {sender}: {Body!r}")

    db: Session = SessionLocal()
    try:
        if text == "bet":
            reply = _build_bet_menu(db, value_only=False)
        elif text == "value":
            reply = _build_bet_menu(db, value_only=True)
        elif text in ("help", "hi", "hello", "menu"):
            reply = HELP_TEXT
        else:
            reply = HELP_TEXT

        send_whatsapp_message(sender, reply)
    finally:
        db.close()

    # Return empty 200 — we already sent via API, no TwiML needed
    return Response(content="", media_type="text/plain", status_code=200)


def _build_bet_menu(db: Session, value_only: bool = False) -> str:
    predictions = get_todays_top_predictions(db, limit=8)

    if value_only:
        predictions = [p for p in predictions if p.get("value_bet")]
        header = "🎯 *AutoBet Value Bets Today*"
    else:
        header = "⚽ *AutoBet — Today's Top Picks*"

    if not predictions:
        return (
            f"{header}\n\n"
            "No high-confidence predictions for today yet.\n"
            "Odds are updated every 30 minutes — try again soon."
        )

    outcome_emoji = {"home_win": "🏠", "draw": "🤝", "away_win": "✈️"}
    lines = [header, ""]

    for i, p in enumerate(predictions[:6], 1):
        emoji = outcome_emoji.get(p.get("predicted_outcome", ""), "⚽")
        outcome = p.get("predicted_outcome", "").replace("_", " ").title()
        conf = p.get("confidence", 0)
        conf_bar = "🟢" if conf >= 75 else "🟡" if conf >= 60 else "🔴"

        lines.append(f"*{i}. {p.get('home_team')} vs {p.get('away_team')}*")
        lines.append(f"   🏆 {p.get('league', '')}")
        lines.append(f"   {emoji} {outcome} {conf_bar} {conf:.0f}%")

        if p.get("best_odds"):
            lines.append(f"   💰 Odds: {p.get('best_odds')} @ {p.get('best_bookmaker', '')}")
        if p.get("value_bet"):
            lines.append("   🔥 *VALUE BET*")
        if p.get("predicted_goals"):
            goals = p.get("predicted_goals", "").replace("_", " ")
            lines.append(f"   ⚽ Goals: {goals} ({p.get('goals_confidence', 0):.0f}%)")

        lines.append("")

    lines.append("─" * 28)
    lines.append("Reply *Value* for value bets only")
    lines.append("⚠️ _Bet responsibly — AutoBet_")

    return "\n".join(lines)
