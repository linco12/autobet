from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from backend.database import get_db
from backend import models
from backend.services.data_sync import get_todays_top_predictions, sync_odds_and_predictions

router = APIRouter(prefix="/api/predictions", tags=["Predictions"])


@router.get("/top")
def top_predictions(
    limit: int = Query(default=10, le=50),
    value_only: bool = False,
    db: Session = Depends(get_db),
):
    preds = get_todays_top_predictions(db, limit=limit)
    if value_only:
        preds = [p for p in preds if p.get("value_bet")]
    return preds


@router.get("/stats")
def prediction_stats(db: Session = Depends(get_db)):
    total = db.query(models.Prediction).count()
    value_bets = db.query(models.Prediction).filter(models.Prediction.value_bet == True).count()  # noqa
    high_conf = db.query(models.Prediction).filter(models.Prediction.confidence >= 70).count()

    outcomes = {}
    for row in db.query(models.Prediction.predicted_outcome, models.Prediction.id).all():
        outcomes[row[0]] = outcomes.get(row[0], 0) + 1

    return {
        "total_predictions": total,
        "value_bets": value_bets,
        "high_confidence": high_conf,
        "by_outcome": outcomes,
    }


@router.post("/refresh")
async def trigger_refresh(background_tasks: BackgroundTasks):
    """Manually trigger an odds & prediction refresh."""
    background_tasks.add_task(sync_odds_and_predictions)
    return {"message": "Odds sync started in background"}


@router.post("/ai-refresh")
async def trigger_ai_refresh(background_tasks: BackgroundTasks):
    """Re-run Claude AI analysis on today's matches using existing odds data."""
    from backend.services.ai_refresh import ai_refresh_todays_matches
    background_tasks.add_task(ai_refresh_todays_matches)
    return {"message": "AI analysis started for today's matches"}


@router.get("/{match_id}")
def get_prediction(match_id: int, db: Session = Depends(get_db)):
    pred = (
        db.query(models.Prediction)
        .options(joinedload(models.Prediction.match))
        .filter(models.Prediction.match_id == match_id)
        .first()
    )
    if not pred:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Prediction not found")

    return {
        "match_id": match_id,
        "home_team": pred.match.home_team,
        "away_team": pred.match.away_team,
        "league": pred.match.league,
        "match_date": pred.match.match_date.isoformat(),
        "predicted_outcome": pred.predicted_outcome,
        "confidence": pred.confidence,
        "value_bet": pred.value_bet,
        "home_win_prob": pred.home_win_prob,
        "draw_prob": pred.draw_prob,
        "away_win_prob": pred.away_win_prob,
        "predicted_goals": pred.predicted_goals,
        "goals_confidence": pred.goals_confidence,
        "btts_prediction": pred.btts_prediction,
        "btts_confidence": pred.btts_confidence,
        "best_odds": pred.best_odds,
        "best_bookmaker": pred.best_bookmaker,
        "reasoning": pred.reasoning,
        "updated_at": pred.updated_at.isoformat(),
    }
