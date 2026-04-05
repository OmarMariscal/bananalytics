from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "API Gateway de BanAnalytics en línea"}