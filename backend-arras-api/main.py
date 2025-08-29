from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def hello():
    return {"message": "Welcome from arras apis!"}


@app.patch("/run")
def run(payload: dict):
    return {"message": "Run endpoint called", "payload": payload}
