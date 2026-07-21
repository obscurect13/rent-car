"""AutoLoc Pro - FastAPI Backend Entry Point"""
import sys
import os

# Add the backend directory to Python path so 'api' package is found
# This works both in Docker and locally
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import database FIRST to trigger init_db()
from api.database import init_db
from api.cars import router as cars_router
from api.bookings import router as bookings_router
from api.customers import router as customers_router
from api.payments import router as payments_router
from api.exports import router as exports_router
from api.inspections import router as inspections_router
from api.insurance import router as insurance_router
from api.stats import router as stats_router
from api.auth import router as auth_router
from api.user_portal import router as portal_router

# Initialize database on startup
init_db()

app = FastAPI(title="AutoLoc Pro API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(cars_router)
app.include_router(bookings_router)
app.include_router(customers_router)
app.include_router(payments_router)
app.include_router(exports_router)
app.include_router(inspections_router)
app.include_router(insurance_router)
app.include_router(stats_router)
app.include_router(auth_router)
app.include_router(portal_router)

@app.get("/health", tags=["health"])
def health():
    """Public health check — no auth required."""
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "AutoLoc Pro API v2.0", "status": "running"}
