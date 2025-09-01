FROM lfenergy/arras:latest

ENV POETRY_VERSION=2.1.3 \
    SERVER_PORT=4600 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    PYTHONWARNINGS="ignore::SyntaxWarning"

WORKDIR /app


RUN apt-get update && apt-get install -y python3-pip pipx build-essential libpq-dev gcc nano python3-dev direnv \
    && rm -rf /var/lib/apt/lists/*

RUN pipx install "poetry==$POETRY_VERSION" \
    && ln -s /root/.local/bin/poetry /usr/local/bin/poetry

COPY pyproject.toml poetry.lock /app/
RUN poetry install --extras "internal"

COPY backend-arras/main.py /app/src/

RUN mkdir -p /app/models && chown -R 1000:1000 /app/models

EXPOSE ${SERVER_PORT}

CMD ["/app/.venv/bin/uvicorn", "src.main:api", "--host", "0.0.0.0", "--port", "4600"]
