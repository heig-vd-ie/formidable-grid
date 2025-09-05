FROM lfenergy/arras:latest

RUN apt-get update && apt-get install -y --no-install-recommends python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY gridlabd/requirements.txt /app

# Create a virtual environment
RUN python3 -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir -r requirements.txt

COPY gridlabd/. /app

EXPOSE ${SERVER_PORT}

WORKDIR /app/src

CMD gunicorn --bind 0.0.0.0:${SERVER_PORT} main:app
