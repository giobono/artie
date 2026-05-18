"""
ArtIE Platform API — entry point.

Mounts platform-wide routes (/health) and per-application routers.
Configures CORS from the ARTIE_CORS_ORIGINS environment variable.
"""

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.gioianie import router as gioianie_router

# Load .env in local development; harmless in dev/prod where env vars come
# from systemd's EnvironmentFile and .env may not exist.
load_dotenv()

from apps.corres.api import llm as corres_llm

app = FastAPI(title="ArtIE Platform API", version="0.1.0")
app.include_router(gioianie_router, prefix="/v1/gioianie")

# CORS allow-list comes from the environment so each deployment declares
# which frontend origins are permitted. Comma-separated.
allowed_origins = [
    o.strip()
    for o in os.environ.get("ARTIE_CORS_ORIGINS", "http://localhost:8000").split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Request-Id"],
    allow_credentials=False,
)


@app.get("/health")
async def health() -> dict[str, str]:
    """
    Liveness probe. Returns 200 when the process is up and reachable.

    Per hosting contract §9: no authentication, no dependency checks. A
    separate /readiness endpoint will be added when the platform acquires
    checkable dependencies.
    """
    return {"status": "ok"}


app.include_router(corres_llm.router)
