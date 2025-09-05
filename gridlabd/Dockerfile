FROM python:3.12.3-slim

WORKDIR /app

COPY frontend-gridlabd/. /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE ${SERVER_PORT}

WORKDIR /app/src

CMD gunicorn --bind 0.0.0.0:$SERVER_PORT main:app
