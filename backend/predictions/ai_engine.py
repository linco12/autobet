"""
Claude AI-powered prediction engine.
Uses Claude claude-sonnet-4-6 to analyse odds, form, and market data to produce
detailed betting recommendations with full reasoning.
"""
import logging
import json
from typing import Optional
import anthropic
from backend.config import settings

logger = logging.getLogger(__name__)

_client: Optional[anthropic.Anthropic] = None


def get_client() -> Optional[anthropic.Anthropic]:
    global _client
    if not settings.ANTHROPIC_API_KEY:
        return None
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


SYSTEM_PROMPT = """You are AutoBet, an expert football betting analyst with deep knowledge of:
- Statistical betting models (Poisson, Elo, Dixon-Coles)
- Value betting and expected value calculations
- League-specific trends (home advantage, goal averages, form cycles)
- Market efficiency and bookmaker margin analysis
- Risk management and bankroll principles

Your job is to analyse a football match and produce a precise betting recommendation.
You MUST respond with valid JSON only — no prose outside the JSON block.

JSON schema to follow exactly:
{
  "predicted_outcome": "home_win" | "draw" | "away_win",
  "confidence": <float 0-100>,
  "value_bet": <boolean>,
  "home_win_prob": <float 0-1>,
  "draw_prob": <float 0-1>,
  "away_win_prob": <float 0-1>,
  "predicted_goals": "over_2_5" | "under_2_5" | null,
  "goals_confidence": <float 0-100> | null,
  "btts_prediction": "yes" | "no" | null,
  "btts_confidence": <float 0-100> | null,
  "best_odds": <float> | null,
  "reasoning": "<concise multi-line analysis covering: odds implied probs, value assessment, key factors, risk level>"
}"""


def analyse_match_with_ai(
    home_team: str,
    away_team: str,
    league: str,
    home_odds: float,
    draw_odds: Optional[float],
    away_odds: float,
    over_2_5_odds: Optional[float] = None,
    under_2_5_odds: Optional[float] = None,
    best_bookmaker: Optional[str] = None,
) -> Optional[dict]:
    client = get_client()
    if not client:
        logger.warning("ANTHROPIC_API_KEY not set — skipping AI analysis")
        return None

    # Build implied probabilities for context
    raw_home = 1 / home_odds if home_odds else 0
    raw_draw = 1 / draw_odds if draw_odds else 0
    raw_away = 1 / away_odds if away_odds else 0
    overround = raw_home + raw_draw + raw_away

    imp_home = round(raw_home / overround * 100, 1)
    imp_draw = round(raw_draw / overround * 100, 1)
    imp_away = round(raw_away / overround * 100, 1)
    margin = round((overround - 1) * 100, 1)

    prompt = f"""Analyse this football match and provide a betting recommendation.

MATCH: {home_team} vs {away_team}
LEAGUE: {league}

MARKET ODDS ({best_bookmaker or 'Best available'}):
  Home Win: {home_odds}  →  Implied {imp_home}%
  Draw:     {draw_odds or 'N/A'}  →  Implied {imp_draw}%
  Away Win: {away_odds}  →  Implied {imp_away}%
  Over 2.5 goals: {over_2_5_odds or 'N/A'}
  Under 2.5 goals: {under_2_5_odds or 'N/A'}
  Bookmaker margin: {margin}%

INSTRUCTIONS:
1. Strip the overround to find true implied probabilities
2. Apply your knowledge of {league} — typical home advantage, scoring rates, current season context
3. Identify if any outcome offers VALUE (your prob > implied prob by >4%)
4. Give a confident single recommendation with clear reasoning
5. Keep reasoning under 6 lines but cover: value assessment, key factors, confidence rationale

Respond with JSON only."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        result = json.loads(raw.strip())
        logger.info(f"AI analysis done: {home_team} vs {away_team} → {result.get('predicted_outcome')} ({result.get('confidence')}%)")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"AI returned invalid JSON for {home_team} vs {away_team}: {e}")
        return None
    except Exception as e:
        logger.error(f"AI analysis failed for {home_team} vs {away_team}: {e}")
        return None
