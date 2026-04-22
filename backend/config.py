from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./autobet.db"

    # Football Data APIs
    ODDS_API_KEY: str = ""          # https://the-odds-api.com (free tier: 500 req/month)
    API_FOOTBALL_KEY: str = ""      # https://rapidapi.com/api-sports/api/api-football (free)

    # Twilio WhatsApp (same account as VOLWSZIM Land system)
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_FROM: str = "whatsapp:+263787001363"  # TronicVolt Electronics WhatsApp Business
    TWILIO_MESSAGING_SERVICE_SID: str = "MGd30465409bd246572d5e76e3b0fcc466"
    TWILIO_CONTENT_SID: str = ""         # Approved WhatsApp template SID (HX...)

    # Claude AI
    ANTHROPIC_API_KEY: str = ""

    # App
    SECRET_KEY: str = "autobet-secret-change-in-prod"
    DAILY_SEND_HOUR: int = 8        # Hour (UTC) to send daily WhatsApp predictions
    DEFAULT_RECIPIENT: str = "+263785186616"

    class Config:
        env_file = ".env"


settings = Settings()
