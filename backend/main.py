"""
main.py
-------
The FastAPI application entry point.

This file does three things:
  1. Creates the FastAPI app instance
  2. Configures CORS (so React on port 3000 can talk to FastAPI on port 8000)
  3. Registers all routers (areas, risk, crimes)

To run the server:
  uvicorn backend.main:app --reload

  backend.main  = the Python module path (backend/main.py)
  app           = the FastAPI instance defined below
  --reload      = auto-restart when you save a file (dev mode only)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import areas as areas_router
from backend.routers import risk as risk_router
from backend.routers import crimes as crimes_router

# ── APP INSTANCE ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Mumbai Safety Risk API",
    description=(
        "Serves area-wise crime risk scores and breakdowns for Mumbai's 24 wards. "
        "Data is simulated based on NCRB crime categories and realistic ward-level "
        "risk profiles. Designed to be replaced with real data."
    ),
    version="1.0.0",
)

# ── CORS MIDDLEWARE ───────────────────────────────────────────────────────────
# CORS = Cross-Origin Resource Sharing.
# Without this, browsers BLOCK requests from one origin (localhost:3000)
# to a different origin (localhost:8000) as a security measure.
# We explicitly allow our React dev server so the two can communicate.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # React dev server address
    allow_credentials=True,
    allow_methods=["GET"],          # We only need GET for this project
    allow_headers=["*"],
)

# ── ROUTERS ───────────────────────────────────────────────────────────────────
# Each router handles one group of URLs.
# Including them here "mounts" their routes onto the main app.
app.include_router(areas_router.router)
app.include_router(risk_router.router)
app.include_router(crimes_router.router)

# ── HEALTH CHECK ─────────────────────────────────────────────────────────────
# A simple endpoint to confirm the server is running.
# Visit http://localhost:8000/ in your browser to see this.
@app.get("/")
def root():
    return {
        "status": "online",
        "message": "Mumbai Safety Risk API is running.",
        "docs": "Visit /docs for interactive API documentation.",
    }