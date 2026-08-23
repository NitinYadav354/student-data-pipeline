"""
Student Data Pipeline & UI — backend entrypoint.

This service is deliberately kept separate from the frontend: it is the
"background process" that does the heavy lifting (cleaning, validation,
eligibility checks) and exposes it over a small REST API. The Next.js
frontend is a pure consumer of this API and holds no cleaning logic itself.
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.students import router as students_router

# Comma-separated list of allowed frontend origins.
# Local dev defaults to the Next.js dev server; production origin(s)
# are injected via env var at deploy time (see .env.example).
_allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000")
ALLOWED_ORIGINS = [origin.strip() for origin in _allowed_origins.split(",")]

app = FastAPI(
    title="Student Data Pipeline API",
    description=(
        "Cleans raw student CSV uploads, validates and recalculates scores, "
        "and serves live shortlist/eligibility queries."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(students_router)


@app.get("/health")
def health_check() -> dict:
    """Basic liveness check — also used by the frontend to confirm the
    backend is reachable before offering the upload UI."""
    return {"status": "ok", "service": "student-data-pipeline-backend"}
