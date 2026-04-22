"""
Orchestrates fetching odds, persisting matches, and generating predictions.
Called by the scheduler on each monitoring cycle.
"""
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from backend import models
from backend.database import SessionLocal
from backend.scrapers.odds_api import fetch_all_sports_odds, parse_odds_response
from backend.predictions.engine import predict, rank_predictions
from backend.predictions.ai_engine import analyse_match_with_ai

logger = logging.getLogger(__name__)


async def sync_odds_and_predictions():
    """Main sync loop: fetch odds → upsert matches → run predictions."""
    db: Session = SessionLocal()
    try:
        raw_matches = await fetch_all_sports_odds()
        logger.info(f"Fetched {len(raw_matches)} raw match records from odds API")

        synced = 0
        for raw in raw_matches:
            parsed = parse_odds_response(raw)
            if not parsed:
                continue

            # Upsert match
            match = db.query(models.Match).filter(
                models.Match.external_id == parsed["external_id"]
            ).first()

            if not match:
                match = models.Match(
                    external_id=parsed["external_id"],
                    home_team=parsed["home_team"],
                    away_team=parsed["away_team"],
                    league=parsed["league"],
                    match_date=parsed["match_date"],
                    status="upcoming",
                )
                db.add(match)
                db.flush()

            # Upsert odds record
            odds = models.Odds(
                match_id=match.id,
                bookmaker=parsed["bookmaker"],
                home_win=parsed["home_win"],
                draw=parsed["draw"],
                away_win=parsed["away_win"],
                over_2_5=parsed.get("over_2_5"),
                under_2_5=parsed.get("under_2_5"),
                btts_yes=parsed.get("btts_yes"),
                btts_no=parsed.get("btts_no"),
            )
            db.add(odds)
            db.flush()

            # Use AI analysis only for today's matches — Poisson for the rest
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            is_today = today_start <= parsed["match_date"].replace(tzinfo=timezone.utc) < today_end

            ai = None
            if is_today:
                ai = analyse_match_with_ai(
                    home_team=parsed["home_team"],
                    away_team=parsed["away_team"],
                    league=parsed["league"],
                    home_odds=parsed["home_win"],
                    draw_odds=parsed.get("draw"),
                    away_odds=parsed["away_win"],
                    over_2_5_odds=parsed.get("over_2_5"),
                    under_2_5_odds=parsed.get("under_2_5"),
                    best_bookmaker=parsed["bookmaker"],
                )

            if ai:
                from backend.predictions.engine import rank_predictions as _rank
                from dataclasses import dataclass

                @dataclass
                class _R:
                    predicted_outcome: str
                    confidence: float
                    value_bet: bool
                    home_win_prob: float
                    draw_prob: float
                    away_win_prob: float
                    predicted_goals: object
                    goals_confidence: object
                    btts_prediction: object
                    btts_confidence: object
                    best_odds: object
                    best_bookmaker: object
                    reasoning: str

                result = _R(
                    predicted_outcome=ai.get("predicted_outcome", "home_win"),
                    confidence=float(ai.get("confidence", 55)),
                    value_bet=bool(ai.get("value_bet", False)),
                    home_win_prob=float(ai.get("home_win_prob", 0.33)),
                    draw_prob=float(ai.get("draw_prob", 0.33)),
                    away_win_prob=float(ai.get("away_win_prob", 0.33)),
                    predicted_goals=ai.get("predicted_goals"),
                    goals_confidence=ai.get("goals_confidence"),
                    btts_prediction=ai.get("btts_prediction"),
                    btts_confidence=ai.get("btts_confidence"),
                    best_odds=ai.get("best_odds") or parsed["home_win"],
                    best_bookmaker=parsed["bookmaker"],
                    reasoning=ai.get("reasoning", ""),
                )
            else:
                result = predict(
                    home_odds=parsed["home_win"],
                    draw_odds=parsed["draw"] or 3.5,
                    away_odds=parsed["away_win"],
                    over_2_5_odds=parsed.get("over_2_5"),
                    under_2_5_odds=parsed.get("under_2_5"),
                    btts_yes_odds=parsed.get("btts_yes"),
                    btts_no_odds=parsed.get("btts_no"),
                    best_bookmaker=parsed["bookmaker"],
                )

            pred = db.query(models.Prediction).filter(
                models.Prediction.match_id == match.id
            ).first()

            if pred:
                pred.predicted_outcome = result.predicted_outcome
                pred.confidence = result.confidence
                pred.value_bet = result.value_bet
                pred.home_win_prob = result.home_win_prob
                pred.draw_prob = result.draw_prob
                pred.away_win_prob = result.away_win_prob
                pred.predicted_goals = result.predicted_goals
                pred.goals_confidence = result.goals_confidence
                pred.btts_prediction = result.btts_prediction
                pred.btts_confidence = result.btts_confidence
                pred.best_odds = result.best_odds
                pred.best_bookmaker = result.best_bookmaker
                pred.reasoning = result.reasoning
                pred.updated_at = datetime.utcnow()
            else:
                pred = models.Prediction(
                    match_id=match.id,
                    predicted_outcome=result.predicted_outcome,
                    confidence=result.confidence,
                    value_bet=result.value_bet,
                    home_win_prob=result.home_win_prob,
                    draw_prob=result.draw_prob,
                    away_win_prob=result.away_win_prob,
                    predicted_goals=result.predicted_goals,
                    goals_confidence=result.goals_confidence,
                    btts_prediction=result.btts_prediction,
                    btts_confidence=result.btts_confidence,
                    best_odds=result.best_odds,
                    best_bookmaker=result.best_bookmaker,
                    reasoning=result.reasoning,
                )
                db.add(pred)

            synced += 1

        db.commit()
        logger.info(f"Sync complete: {synced} matches processed")
        return synced

    except Exception as e:
        db.rollback()
        logger.error(f"Sync failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


def get_todays_top_predictions(db: Session, limit: int = 10) -> list[dict]:
    """Return top predictions for matches happening today only (UTC calendar day)."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    rows = (
        db.query(models.Match, models.Prediction)
        .join(models.Prediction)
        .filter(
            models.Match.match_date >= today_start,
            models.Match.match_date < today_end,
            models.Prediction.confidence >= 55,
        )
        .order_by(models.Prediction.value_bet.desc(), models.Prediction.confidence.desc())
        .limit(limit)
        .all()
    )

    results = []
    for match, pred in rows:
        results.append({
            "match_id": match.id,
            "home_team": match.home_team,
            "away_team": match.away_team,
            "league": match.league,
            "match_date": match.match_date.strftime("%d %b %Y %H:%M UTC"),
            "predicted_outcome": pred.predicted_outcome,
            "confidence": pred.confidence,
            "value_bet": pred.value_bet,
            "best_odds": pred.best_odds,
            "best_bookmaker": pred.best_bookmaker,
            "predicted_goals": pred.predicted_goals,
            "goals_confidence": pred.goals_confidence,
            "btts_prediction": pred.btts_prediction,
            "btts_confidence": pred.btts_confidence,
        })

    return rank_predictions(results)
