from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # <-- Add this import

from app.api.auth import api
from app.api.projects import api_proj
from app.api.tasks import api_task

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local testing
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PATCH, etc.)
    allow_headers=["*"],  # Allows all headers
)

app.include_router(api, prefix="/api/v1", tags=["auth"])
app.include_router(api_proj, prefix="/api/v1", tags=["Projects"])
app.include_router(api_task, prefix="/api/v1", tags=["Tasks"])
