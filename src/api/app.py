from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import announcements, status

app = FastAPI(title="EGP Pipeline API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(announcements.router, prefix="/api/v1/announcements")
app.include_router(status.router, prefix="/api/v1/status")