FROM python:3.12.3-slim

ENV POETRY_VERSION=2.1.3 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    SERVER_PY_PORT=8000 \
    PYTHONPATH=/app/src \
    PYTHONWARNINGS="ignore::SyntaxWarning"

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    python3-dev \
    build-essential \
    direnv \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

WORKDIR /app

COPY pyproject.toml poetry.lock /app/
COPY external-dist/ /app/external-dist/
COPY backend-arras-api/ /app/

RUN poetry install --extras "internal"


EXPOSE ${SERVER_PORT}

CMD poetry run uvicorn main:app --host 0.0.0.0 --port $SERVER_PORT