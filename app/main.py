from fastapi import FastAPI
from app.api.v1.endpoints import health
import uvicorn

app = FastAPI()

app.include_router(health.router, prefix="/api/v1")
