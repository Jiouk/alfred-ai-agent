"""
AI Agent SaaS Platform - Main FastAPI Application
"""

from contextlib import asynccontextmanager
import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models import create_db_and_tables
from app.routers import admin, billing, onboarding, webhooks

# Load environment variables
load_dotenv()

# Configuration
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting AI Agent SaaS Platform...")
    create_db_and_tables()
    print("✅ Database initialized")
    yield
    # Shutdown
    print("👋 Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="AI Agent SaaS Platform",
    description="Backend API for AI Agent SaaS - Zero-dashboard configuration via conversation",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "environment": "production" if not DEBUG else "development"
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Agent SaaS Platform API",
        "docs": "/docs",
        "version": "0.1.0"
    }


# Include routers
app.include_router(onboarding.router, prefix="/onboarding", tags=["Onboarding"])
app.include_router(webhooks.router, prefix="/webhook", tags=["Webhooks"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(billing.router, prefix="/credits", tags=["Billing"])


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=DEBUG
    )
