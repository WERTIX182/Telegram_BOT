FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DATABASE_URL=sqlite+aiosqlite:////data/bot_database.db

WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

RUN useradd --create-home --uid 1000 bot \
    && mkdir -p /data \
    && chown -R bot:bot /srv /data
USER bot
VOLUME /data

CMD ["python", "run.py"]
