"""
Fetches live odds from The-Odds-API (https://the-odds-api.com).
Free tier: 500 requests/month. Each call returns odds for a sport.
"""
import httpx
import logging
from datetime import datetime
from typing import Optional
from backend.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.the-odds-api.com/v4"

TRACKED_SPORTS = [
    "soccer_epl",
    "soccer_uefa_champs_league",
    "soccer_spain_la_liga",
    "soccer_germany_bundesliga",
    "soccer_italy_serie_a",
    "soccer_france_ligue_one",
    "soccer_africa_cup_of_nations",
    "soccer_conmebol_copa_libertadores",
]


async def fetch_upcoming_odds(sport: str) -> list[dict]:
    if not settings.ODDS_API_KEY:
        logger.warning("ODDS_API_KEY not set — skipping odds fetch")
        return []

    url = f"{BASE_URL}/sports/{sport}/odds"
    params = {
        "apiKey": settings.ODDS_API_KEY,
        "regions": "eu",
        "markets": "h2h,totals",
        "oddsFormat": "decimal",
        "dateFormat": "iso",
    }

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            logger.info(f"Fetched {len(data)} matches for {sport}. Remaining requests: {resp.headers.get('x-requests-remaining')}")
            return data
        except httpx.HTTPError as e:
            logger.error(f"Odds API error for {sport}: {e}")
            return []


async def fetch_all_sports_odds() -> list[dict]:
    all_matches = []
    for sport in TRACKED_SPORTS:
        matches = await fetch_upcoming_odds(sport)
        for m in matches:
            m["sport_key"] = sport
        all_matches.extend(matches)
    return all_matches


def parse_odds_response(raw: dict) -> Optional[dict]:
    """Normalise a single match record from The-Odds-API into our internal format."""
    try:
        bookmakers = raw.get("bookmakers", [])
        if not bookmakers:
            return None

        home = raw["home_team"]
        away = raw["away_team"]
        commence = raw["commence_time"]
        match_dt = datetime.fromisoformat(commence.replace("Z", "+00:00"))

        # Aggregate best odds across bookmakers
        best_home = best_draw = best_away = None
        best_over = best_under = best_btts_yes = best_btts_no = None
        bookmaker_name = bookmakers[0]["title"] if bookmakers else "Unknown"

        for bm in bookmakers:
            for market in bm.get("markets", []):
                outcomes = {o["name"]: o["price"] for o in market.get("outcomes", [])}
                if market["key"] == "h2h":
                    h = outcomes.get(home)
                    d = outcomes.get("Draw")
                    a = outcomes.get(away)
                    if h and (best_home is None or h > best_home):
                        best_home, best_draw, best_away = h, d, a
                        bookmaker_name = bm["title"]
                elif market["key"] == "totals":
                    o = outcomes.get("Over")
                    u = outcomes.get("Under")
                    if o and (best_over is None or o > best_over):
                        best_over = o
                    if u and (best_under is None or u > best_under):
                        best_under = u
                elif market["key"] in ("btts", "both_teams_to_score"):
                    y = outcomes.get("Yes")
                    n = outcomes.get("No")
                    if y and (best_btts_yes is None or y > best_btts_yes):
                        best_btts_yes = y
                    if n and (best_btts_no is None or n > best_btts_no):
                        best_btts_no = n

        if not best_home:
            return None

        return {
            "external_id": raw["id"],
            "home_team": home,
            "away_team": away,
            "league": raw.get("sport_title", raw.get("sport_key", "")),
            "match_date": match_dt,
            "bookmaker": bookmaker_name,
            "home_win": best_home,
            "draw": best_draw,
            "away_win": best_away,
            "over_2_5": best_over,
            "under_2_5": best_under,
            "btts_yes": best_btts_yes,
            "btts_no": best_btts_no,
        }
    except Exception as e:
        logger.error(f"Failed to parse odds record: {e} | raw={raw.get('id')}")
        return None
