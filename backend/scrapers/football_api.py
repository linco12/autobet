"""
Fetches match fixtures, results and team stats from API-Football via RapidAPI.
Free tier: 100 requests/day.
"""
import httpx
import logging
from datetime import datetime, date
from backend.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"
HEADERS = {
    "X-RapidAPI-Key": settings.API_FOOTBALL_KEY,
    "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com",
}

# Top leagues by ID
LEAGUE_IDS = [
    39,    # Premier League
    140,   # La Liga
    135,   # Serie A
    78,    # Bundesliga
    61,    # Ligue 1
    2,     # UEFA Champions League
    3,     # UEFA Europa League
    848,   # UEFA Conference League
    1,     # World Cup
]


async def fetch_fixtures_today(league_id: int, season: int = 2024) -> list[dict]:
    if not settings.API_FOOTBALL_KEY:
        return []

    today = date.today().isoformat()
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(
                f"{BASE_URL}/fixtures",
                headers=HEADERS,
                params={"league": league_id, "season": season, "date": today},
            )
            resp.raise_for_status()
            return resp.json().get("response", [])
        except httpx.HTTPError as e:
            logger.error(f"API-Football error (league={league_id}): {e}")
            return []


async def fetch_head_to_head(team1_id: int, team2_id: int, last: int = 10) -> list[dict]:
    if not settings.API_FOOTBALL_KEY:
        return []

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(
                f"{BASE_URL}/fixtures/headtohead",
                headers=HEADERS,
                params={"h2h": f"{team1_id}-{team2_id}", "last": last},
            )
            resp.raise_for_status()
            return resp.json().get("response", [])
        except httpx.HTTPError as e:
            logger.error(f"H2H fetch error: {e}")
            return []


async def fetch_team_form(team_id: int, league_id: int, season: int = 2024, last: int = 5) -> list[dict]:
    if not settings.API_FOOTBALL_KEY:
        return []

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(
                f"{BASE_URL}/fixtures",
                headers=HEADERS,
                params={"team": team_id, "league": league_id, "season": season, "last": last},
            )
            resp.raise_for_status()
            return resp.json().get("response", [])
        except httpx.HTTPError as e:
            logger.error(f"Team form fetch error: {e}")
            return []


def calculate_form_score(fixtures: list[dict], team_id: int) -> float:
    """Returns form score 0-1 based on last N results (W=1, D=0.5, L=0)."""
    if not fixtures:
        return 0.5

    points = []
    for f in fixtures:
        home = f["teams"]["home"]
        away = f["teams"]["away"]
        goals = f["goals"]
        if goals["home"] is None:
            continue

        is_home = home["id"] == team_id
        team_goals = goals["home"] if is_home else goals["away"]
        opp_goals = goals["away"] if is_home else goals["home"]

        if team_goals > opp_goals:
            points.append(1.0)
        elif team_goals == opp_goals:
            points.append(0.5)
        else:
            points.append(0.0)

    return sum(points) / len(points) if points else 0.5
