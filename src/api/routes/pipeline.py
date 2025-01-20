# src/api/routes/pipeline.py

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from src.services.pipeline_service import PipelineService

router = APIRouter()
service = PipelineService()

@router.post("/start")
async def start_pipeline(dept_ids: Optional[List[str]] = None):
    """Start pipeline run"""
    try:
        results = await service.start_pipeline(dept_ids)
        return {
            "message": "Pipeline started successfully",
            "results": results
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_status():
    """Get pipeline status"""
    try:
        return service.get_pipeline_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))