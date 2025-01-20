# src/services/pipeline_service.py

from typing import Dict, List, Optional
from src.pipeline.scheduler import scheduler
from src.core.logging import get_logger
from src.core.constants import DEPARTMENTS

logger = get_logger(__name__)

class PipelineService:
    async def start_pipeline(self, dept_ids: Optional[List[str]] = None) -> Dict:
        """Start pipeline run"""
        try:
            # Validate department IDs
            if dept_ids:
                invalid_depts = [d for d in dept_ids if d not in DEPARTMENTS]
                if invalid_depts:
                    raise ValueError(f"Invalid department IDs: {invalid_depts}")
            
            # Run pipeline
            results = await scheduler.run_manual(dept_ids)
            return results
            
        except Exception as e:
            logger.error(f"Error starting pipeline: {e}")
            raise
    
    def get_pipeline_status(self) -> Dict:
        """Get current pipeline status"""
        try:
            return {
                "scheduler_running": scheduler.scheduler.running,
                "next_run": self._get_next_run_time(),
                "pipeline_status": scheduler.orchestrator.status,
                "last_run_results": scheduler.orchestrator.results
            }
        except Exception as e:
            logger.error(f"Error getting pipeline status: {e}")
            raise
    
    def _get_next_run_time(self) -> Optional[str]:
        """Get next scheduled run time"""
        try:
            next_run = None
            for job in scheduler.scheduler.get_jobs():
                job_next_run = job.next_run_time
                if not next_run or (job_next_run and job_next_run < next_run):
                    next_run = job_next_run
            
            return next_run.strftime("%Y-%m-%d %H:%M:%S") if next_run else None
            
        except Exception as e:
            logger.error(f"Error getting next run time: {e}")
            return None