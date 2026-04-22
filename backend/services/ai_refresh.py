"""
Runs Claude AI analysis on all today's matches already in the database,
without needing a fresh odds API fetch.
"""
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from backend import models
from backend.database import SessionLocal
from backend.predictions.ai_engine import analyse_match_with_ai

logger = logging.getLogger(__name__)


def ai_refresh_todays_matches():
    """Re-analyse all of today's matches using Claude AI."""
    db: Session = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        matches = (
            db.query(models.Match, models.Prediction, models.Odds)
            .join(models.Prediction)
            .join(models.Odds, models.Odds.match_id == models.Match.id)
            .filter(
                models.Match.match_date >= today_start,
                models.Match.match_date < today_end,
            )
            .all()
        )

        # Deduplicate — take latest odds per match
        seen = {}
        for match, pred, odds in matches:
            if match.id not in seen or odds.fetched_at > seen[match.id][2].fetched_at:
                seen[match.id] = (match, pred, odds)

        logger.info(f"AI refreshing {len(seen)} today's matches")
        updated = 0

        for match, pred, odds in seen.values():
            ai = analyse_match_with_ai(
                home_team=match.home_team,
                away_team=match.away_team,
                league=match.league or "",
                home_odds=odds.home_win,
                draw_odds=odds.draw,
                away_odds=odds.away_win,
                over_2_5_odds=odds.over_2_5,
                under_2_5_odds=odds.under_2_5,
                best_bookmaker=odds.bookmaker,
            )
            if not ai:
                continue

            pred.predicted_outcome = ai.get("predicted_outcome", pred.predicted_outcome)
            pred.confidence = float(ai.get("confidence", pred.confidence))
            pred.value_bet = bool(ai.get("value_bet", pred.value_bet))
            pred.home_win_prob = float(ai.get("home_win_prob", pred.home_win_prob))
            pred.draw_prob = float(ai.get("draw_prob", pred.draw_prob))
            pred.away_win_prob = float(ai.get("away_win_prob", pred.away_win_prob))
            pred.predicted_goals = ai.get("predicted_goals", pred.predicted_goals)
            pred.goals_confidence = ai.get("goals_confidence", pred.goals_confidence)
            pred.btts_prediction = ai.get("btts_prediction", pred.btts_prediction)
            pred.btts_confidence = ai.get("btts_confidence", pred.btts_confidence)
            pred.best_odds = ai.get("best_odds", pred.best_odds)
            pred.reasoning = ai.get("reasoning", "")
            pred.updated_at = datetime.utcnow()
            updated += 1

        db.commit()
        logger.info(f"AI refresh complete: {updated} matches updated")
        return updated

    except Exception as e:
        db.rollback()
        logger.error(f"AI refresh failed: {e}", exc_info=True)
        return 0
    finally:
        db.close()
