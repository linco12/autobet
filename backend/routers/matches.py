from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from datetime import datetime, timedelta, timezone
from backend.database import get_db
from backend import models

router = APIRouter(prefix="/api/matches", tags=["Matches"])


@router.get("/")
def list_matches(
    status: str = Query(default="upcoming", description="upcoming | live | finished | all"),
    limit: int = Query(default=20, le=100),
    offset: int = 0,
    search: str = Query(default=""),
    db: Session = Depends(get_db),
):
    q = db.query(models.Match).options(
        joinedload(models.Match.prediction),
        joinedload(models.Match.odds),
    )

    if status != "all":
        q = q.filter(models.Match.status == status)

    if search:
        q = q.filter(
            or_(
                models.Match.home_team.ilike(f"%{search}%"),
                models.Match.away_team.ilike(f"%{search}%"),
                models.Match.league.ilike(f"%{search}%"),
            )
        )

    total = q.count()
    matches = q.order_by(models.Match.match_date.asc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "matches": [_serialize_match(m) for m in matches],
    }


@router.get("/today")
def todays_matches(db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    end = now + timedelta(hours=24)
    matches = (
        db.query(models.Match)
        .options(joinedload(models.Match.prediction), joinedload(models.Match.odds))
        .filter(models.Match.match_date >= now, models.Match.match_date <= end)
        .order_by(models.Match.match_date.asc())
        .all()
    )
    return [_serialize_match(m) for m in matches]


@router.get("/{match_id}")
def get_match(match_id: int, db: Session = Depends(get_db)):
    match = (
        db.query(models.Match)
        .options(joinedload(models.Match.prediction), joinedload(models.Match.odds))
        .filter(models.Match.id == match_id)
        .first()
    )
    if not match:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Match not found")
    return _serialize_match(match)


def _serialize_match(m: models.Match) -> dict:
    latest_odds = sorted(m.odds, key=lambda o: o.fetched_at, reverse=True)[0] if m.odds else None
    pred = m.prediction

    return {
        "id": m.id,
        "home_team": m.home_team,
        "away_team": m.away_team,
        "league": m.league,
        "country": m.country,
        "match_date": m.match_date.isoformat(),
        "status": m.status,
        "home_score": m.home_score,
        "away_score": m.away_score,
        "odds": {
            "home_win": latest_odds.home_win,
            "draw": latest_odds.draw,
            "away_win": latest_odds.away_win,
            "over_2_5": latest_odds.over_2_5,
            "under_2_5": latest_odds.under_2_5,
            "btts_yes": latest_odds.btts_yes,
            "btts_no": latest_odds.btts_no,
            "bookmaker": latest_odds.bookmaker,
        } if latest_odds else None,
        "prediction": {
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
        } if pred else None,
    }
