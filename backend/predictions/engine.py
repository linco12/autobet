"""
Prediction engine — converts odds + form data into betting recommendations.

Strategy:
  1. Convert bookmaker odds to implied probabilities (removing overround).
  2. Apply a Poisson-based adjustment using team form scores.
  3. Flag value bets where our probability > implied probability by threshold.
  4. Rank predictions by confidence × value margin.
"""
import math
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

VALUE_BET_THRESHOLD = 0.05   # 5% edge over bookmaker implied probability
MIN_CONFIDENCE = 55.0         # Only recommend bets above this confidence %


@dataclass
class PredictionResult:
    predicted_outcome: str        # home_win | draw | away_win
    confidence: float             # 0-100
    value_bet: bool

    home_win_prob: float
    draw_prob: float
    away_win_prob: float

    predicted_goals: Optional[str]    # over_2_5 | under_2_5
    goals_confidence: Optional[float]
    btts_prediction: Optional[str]    # yes | no
    btts_confidence: Optional[float]

    best_odds: Optional[float]
    best_bookmaker: Optional[str]
    reasoning: str


def _remove_overround(home_odds: float, draw_odds: float, away_odds: float) -> tuple[float, float, float]:
    """Normalise implied probabilities to sum to 1.0."""
    raw_home = 1 / home_odds
    raw_draw = 1 / draw_odds if draw_odds else 0
    raw_away = 1 / away_odds
    total = raw_home + raw_draw + raw_away
    return raw_home / total, raw_draw / total, raw_away / total


def _poisson_goal_prob(lambda_: float, k: int) -> float:
    return (math.exp(-lambda_) * lambda_ ** k) / math.factorial(k)


def _expected_goals(form_attack: float, form_defense: float, league_avg: float = 1.35) -> float:
    """Rough expected goals using form-adjusted Poisson."""
    return max(0.3, league_avg * form_attack * (1 - form_defense * 0.3))


def predict(
    home_odds: float,
    draw_odds: float,
    away_odds: float,
    home_form: float = 0.5,     # 0-1 from last 5 results
    away_form: float = 0.5,
    over_2_5_odds: Optional[float] = None,
    under_2_5_odds: Optional[float] = None,
    btts_yes_odds: Optional[float] = None,
    btts_no_odds: Optional[float] = None,
    best_bookmaker: Optional[str] = None,
) -> PredictionResult:

    # --- 1. Implied probabilities from odds ---
    imp_home, imp_draw, imp_away = _remove_overround(home_odds, draw_odds or 999, away_odds)

    # --- 2. Form-adjusted probabilities ---
    # Blend 70% odds-implied + 30% form signal
    form_home = home_form
    form_away = away_form
    form_total = form_home + form_away + 0.5  # draw baseline

    adj_home = 0.7 * imp_home + 0.3 * (form_home / form_total)
    adj_away = 0.7 * imp_away + 0.3 * (form_away / form_total)
    adj_draw = max(0.01, 1 - adj_home - adj_away)

    # Re-normalise
    total = adj_home + adj_draw + adj_away
    adj_home /= total
    adj_draw /= total
    adj_away /= total

    # --- 3. Determine prediction ---
    probs = {"home_win": adj_home, "draw": adj_draw, "away_win": adj_away}
    best_outcome = max(probs, key=probs.get)
    best_prob = probs[best_outcome]

    # Map outcome to bookmaker implied prob for value check
    imp_probs = {"home_win": imp_home, "draw": imp_draw, "away_win": imp_away}
    odds_map = {"home_win": home_odds, "draw": draw_odds, "away_win": away_odds}

    value_margin = best_prob - imp_probs[best_outcome]
    is_value = value_margin >= VALUE_BET_THRESHOLD

    confidence = min(99.0, best_prob * 100)

    # --- 4. Goals market ---
    exp_home_goals = _expected_goals(form_home, form_away)
    exp_away_goals = _expected_goals(form_away, form_home)
    exp_total = exp_home_goals + exp_away_goals

    goals_pred: Optional[str] = None
    goals_conf: Optional[float] = None
    if over_2_5_odds and under_2_5_odds:
        prob_over = 1 - sum(
            _poisson_goal_prob(exp_total, k) for k in range(3)
        )
        prob_under = 1 - prob_over
        if prob_over > prob_under:
            goals_pred = "over_2_5"
            goals_conf = round(prob_over * 100, 1)
        else:
            goals_pred = "under_2_5"
            goals_conf = round(prob_under * 100, 1)

    # --- 5. BTTS ---
    btts_pred: Optional[str] = None
    btts_conf: Optional[float] = None
    if btts_yes_odds and btts_no_odds:
        prob_btts = (1 - _poisson_goal_prob(exp_home_goals, 0)) * (1 - _poisson_goal_prob(exp_away_goals, 0))
        if prob_btts > 0.5:
            btts_pred = "yes"
            btts_conf = round(prob_btts * 100, 1)
        else:
            btts_pred = "no"
            btts_conf = round((1 - prob_btts) * 100, 1)

    # --- 6. Reasoning ---
    outcome_label = best_outcome.replace("_", " ").title()
    reasons = [
        f"Predicted: {outcome_label} ({confidence:.1f}% confidence)",
        f"Implied odds probability: {imp_probs[best_outcome]*100:.1f}% | Our model: {best_prob*100:.1f}%",
        f"Home form: {home_form:.0%} | Away form: {away_form:.0%}",
        f"Expected goals: {exp_home_goals:.2f} vs {exp_away_goals:.2f} (total {exp_total:.2f})",
    ]
    if is_value:
        reasons.append(f"VALUE BET detected — edge of {value_margin*100:.1f}% over bookmaker at {odds_map.get(best_outcome)}")
    if goals_pred:
        reasons.append(f"Goals market: {goals_pred.replace('_',' ')} ({goals_conf:.1f}%)")
    if btts_pred:
        reasons.append(f"BTTS: {btts_pred} ({btts_conf:.1f}%)")

    return PredictionResult(
        predicted_outcome=best_outcome,
        confidence=round(confidence, 1),
        value_bet=is_value,
        home_win_prob=round(adj_home, 4),
        draw_prob=round(adj_draw, 4),
        away_win_prob=round(adj_away, 4),
        predicted_goals=goals_pred,
        goals_confidence=goals_conf,
        btts_prediction=btts_pred,
        btts_confidence=btts_conf,
        best_odds=odds_map.get(best_outcome),
        best_bookmaker=best_bookmaker,
        reasoning="\n".join(reasons),
    )


def rank_predictions(predictions: list[dict]) -> list[dict]:
    """Sort predictions: value bets first, then by confidence descending."""
    return sorted(
        predictions,
        key=lambda p: (p.get("value_bet", False), p.get("confidence", 0)),
        reverse=True,
    )
