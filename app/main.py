from fastapi import FastAPI
from app.api.auth import api
from app.api.projects import api_proj
from app.api.tasks import api_task

app = FastAPI()

app.include_router(api, prefix="/api/v1", tags=["auth"])


app.include_router(api_proj, prefix="/api/v1", tags=["Projects"])

app.include_router(api_task, prefix="/api/v1", tags=["Tasks"])
