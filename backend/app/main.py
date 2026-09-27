"""
IntelliIncident FastAPI Application Entry Point
Academic Title: AI/ML and Soft Computing Based Intelligent Incident Detection,
Risk Assessment and Root Cause Analysis System
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.db.database import init_db
from backend.app.api.routes import health, incidents, analysis, analytics, fuzzy, root_cause, reports

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    init_db()
    print("IntelliIncident database verified and initialized.")
    yield
    # Shutdown actions
    print("IntelliIncident backend shutting down.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI/ML and Soft Computing Based Intelligent Incident Detection, Risk Assessment and Root Cause Analysis System",
    version=settings.VERSION,
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers with /api prefix
app.include_router(health.router, prefix="/api")
app.include_router(incidents.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(fuzzy.router, prefix="/api")
app.include_router(root_cause.router, prefix="/api")
app.include_router(reports.router, prefix="/api")

@app.get("/")
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "title": "AI/ML and Soft Computing Based Intelligent Incident Detection, Risk Assessment and Root Cause Analysis System",
        "version": settings.VERSION,
        "docs": "/docs",
        "status": "operational",
    }
