from fastapi import APIRouter, HTTPException
from typing import List, Optional

router = APIRouter()

@router.get("/")
async def get_announcements(
    dept_id: Optional[str] = None,
    limit: int = 10
):
    """Get recent announcements"""
    pass
