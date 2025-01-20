# src/api/routes/announcements.py

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from src.core.constants import Status
from src.services.feed_service import FeedService

router = APIRouter()
service = FeedService()

@router.get("")
async def get_announcements(
    dept_id: Optional[str] = None,
    status: Optional[Status] = None,
    days: int = 7,
    limit: int = 50
):
    """Get announcements with filters"""
    try:
        announcements = await service.get_announcements(dept_id, status, days, limit)
        return {
            "count": len(announcements),
            "results": announcements
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics")
async def get_statistics(days: int = 7):
    """Get announcement statistics"""
    try:
        return await service.get_statistics(days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{project_id}")
async def get_announcement(project_id: str):
    """Get announcement details"""
    try:
        announcement = await service.get_announcement_details(project_id)
        if not announcement:
            raise HTTPException(status_code=404, detail="Announcement not found")
        return announcement
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))