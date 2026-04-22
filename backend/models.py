from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True)
    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)
    league = Column(String)
    country = Column(String)
    match_date = Column(DateTime, nullable=False)
    status = Column(String, default="upcoming")  # upcoming, live, finished
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    odds = relationship("Odds", back_populates="match", cascade="all, delete-orphan")
    prediction = relationship("Prediction", back_populates="match", uselist=False, cascade="all, delete-orphan")


class Odds(Base):
    __tablename__ = "odds"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    bookmaker = Column(String, nullable=False)
    home_win = Column(Float)
    draw = Column(Float)
    away_win = Column(Float)
    over_2_5 = Column(Float, nullable=True)
    under_2_5 = Column(Float, nullable=True)
    btts_yes = Column(Float, nullable=True)   # Both Teams To Score
    btts_no = Column(Float, nullable=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)

    match = relationship("Match", back_populates="odds")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False, unique=True)

    # Predicted outcome
    predicted_outcome = Column(String)      # home_win | draw | away_win
    confidence = Column(Float)              # 0-100%
    value_bet = Column(Boolean, default=False)

    # Probabilities
    home_win_prob = Column(Float)
    draw_prob = Column(Float)
    away_win_prob = Column(Float)

    # Secondary markets
    predicted_goals = Column(String, nullable=True)     # over_2_5 | under_2_5
    goals_confidence = Column(Float, nullable=True)
    btts_prediction = Column(String, nullable=True)     # yes | no
    btts_confidence = Column(Float, nullable=True)

    # Best odds found for the prediction
    best_odds = Column(Float, nullable=True)
    best_bookmaker = Column(String, nullable=True)

    reasoning = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    match = relationship("Match", back_populates="prediction")


class WhatsAppRecipient(Base):
    __tablename__ = "whatsapp_recipients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False, unique=True)  # E.164 format: +263785186616
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    logs = relationship("NotificationLog", back_populates="recipient", cascade="all, delete-orphan")


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(Integer, ForeignKey("whatsapp_recipients.id"), nullable=False)
    message = Column(Text)
    status = Column(String)     # sent | failed
    twilio_sid = Column(String, nullable=True)
    sent_at = Column(DateTime, default=datetime.utcnow)
    error = Column(Text, nullable=True)

    recipient = relationship("WhatsAppRecipient", back_populates="logs")
