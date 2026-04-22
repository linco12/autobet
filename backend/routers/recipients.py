from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
import re
from backend.database import get_db
from backend import models
from backend.services.whatsapp import send_whatsapp_message

router = APIRouter(prefix="/api/recipients", tags=["WhatsApp Recipients"])


class RecipientCreate(BaseModel):
    name: str
    phone_number: str

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = re.sub(r"[\s\-\(\)]", "", v)
        if not re.match(r"^\+\d{7,15}$", cleaned):
            raise ValueError("Phone number must be in E.164 format (e.g. +263785186616)")
        return cleaned


class RecipientUpdate(BaseModel):
    name: str | None = None
    active: bool | None = None


@router.get("/")
def list_recipients(db: Session = Depends(get_db)):
    recipients = db.query(models.WhatsAppRecipient).all()
    return [_serialize(r) for r in recipients]


@router.post("/", status_code=201)
def add_recipient(body: RecipientCreate, db: Session = Depends(get_db)):
    existing = db.query(models.WhatsAppRecipient).filter(
        models.WhatsAppRecipient.phone_number == body.phone_number
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Phone number already registered")

    r = models.WhatsAppRecipient(name=body.name, phone_number=body.phone_number)
    db.add(r)
    db.commit()
    db.refresh(r)
    return _serialize(r)


@router.patch("/{recipient_id}")
def update_recipient(recipient_id: int, body: RecipientUpdate, db: Session = Depends(get_db)):
    r = db.query(models.WhatsAppRecipient).filter(models.WhatsAppRecipient.id == recipient_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Recipient not found")
    if body.name is not None:
        r.name = body.name
    if body.active is not None:
        r.active = body.active
    db.commit()
    db.refresh(r)
    return _serialize(r)


@router.delete("/{recipient_id}", status_code=204)
def delete_recipient(recipient_id: int, db: Session = Depends(get_db)):
    r = db.query(models.WhatsAppRecipient).filter(models.WhatsAppRecipient.id == recipient_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Recipient not found")
    db.delete(r)
    db.commit()


@router.post("/{recipient_id}/test")
def send_test_message(recipient_id: int, db: Session = Depends(get_db)):
    r = db.query(models.WhatsAppRecipient).filter(models.WhatsAppRecipient.id == recipient_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Recipient not found")

    success, sid, error = send_whatsapp_message(
        r.phone_number,
        "✅ AutoBet test message — your WhatsApp notifications are working!"
    )
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to send: {error}")
    return {"message": "Test sent", "sid": sid}


@router.get("/logs")
def notification_logs(limit: int = 50, db: Session = Depends(get_db)):
    logs = (
        db.query(models.NotificationLog)
        .order_by(models.NotificationLog.sent_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": l.id,
            "recipient_id": l.recipient_id,
            "status": l.status,
            "sent_at": l.sent_at.isoformat(),
            "twilio_sid": l.twilio_sid,
            "error": l.error,
        }
        for l in logs
    ]


def _serialize(r: models.WhatsAppRecipient) -> dict:
    return {
        "id": r.id,
        "name": r.name,
        "phone_number": r.phone_number,
        "active": r.active,
        "created_at": r.created_at.isoformat(),
    }
