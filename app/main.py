from fastapi import FastAPI
from app.api.v1.endpoints import health_controller,document_controller
import uvicorn

app = FastAPI()

app.include_router(health_controller.router, prefix="/api/v1")
app.include_router(document_controller.router, prefix="/api/v1")
