# src/api/app.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.pipeline.scheduler import scheduler
from .routes import announcements, pipeline

app = FastAPI(
    title="EGP Pipeline API",
    description="API for EGP announcement processing pipeline",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(announcements.router, prefix="/api/announcements", tags=["announcements"])
app.include_router(pipeline.router, prefix="/api/pipeline", tags=["pipeline"])

@app.on_event("startup")
async def startup_event():
    """Start scheduler on application startup"""
    scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    """Stop scheduler on application shutdown"""
    scheduler.stop()