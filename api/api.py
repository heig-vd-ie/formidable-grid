import time
from flask import Flask
from api.konfig import *

app = Flask(__name__)
app.secret_key = SECRET_KEY


@app.route("/")
def index():
    return "Hello, World!"


@app.route("/api/time")
def get_current_time():
    return {"time": time.time()}
