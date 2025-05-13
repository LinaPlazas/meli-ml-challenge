from fastapi import FastAPI
from app.api.v1.endpoints import health,classify
import uvicorn

app = FastAPI()

app.include_router(health.router, prefix="/api/v1")
app.include_router(classify.router, prefix="/api/v1")
