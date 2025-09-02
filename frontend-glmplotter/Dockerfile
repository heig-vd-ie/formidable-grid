FROM python:3.12.3-slim

WORKDIR /app

COPY frontend-glmplotter/. /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE ${SERVER_PORT}

WORKDIR /app/glm-plotter

CMD gunicorn --bind $SERVER_HOST:$SERVER_PORT glm-plotter:app
