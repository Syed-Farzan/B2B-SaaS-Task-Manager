from fastapi import FastAPI
from app.api.auth import api

app = FastAPI()

app.include_router(api, prefix="/api/v1", tags=["auth"])
