FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/

RUN mkdir -p /app/data

ENV DATABASE_URL=sqlite:///./data/autobet.db

CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
