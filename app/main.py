from app.api.auth import router as auth_router
from fastapi import FastAPI

app = FastAPI(
    title="OZOCO AI Citizen Service Platform",
    version="1.0.0"
)


@app.get("/")
def root():
    return {"message": "OZOCO API is running"}

app.include_router(auth_router)