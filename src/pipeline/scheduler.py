# src/pipeline/scheduler.py

from typing import Optional, List
import asyncio
from datetime import datetime, time
import signal
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from src.core.logging import get_logger
from src.core.config import config
from .orchestrator import PipelineOrchestrator

logger = get_logger(__name__)

class PipelineScheduler:
    """Scheduler for pipeline execution"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.orchestrator = PipelineOrchestrator()
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        """Setup handlers for graceful shutdown"""
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self._handle_shutdown)
    
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals"""
        logger.info("Received shutdown signal, stopping scheduler...")
        self.stop()
    
    def parse_time(self, time_str: str) -> time:
        """Parse time string to time object"""
        try:
            hour, minute = map(int, time_str.split(':'))
            return time(hour, minute)
        except ValueError as e:
            logger.error(f"Invalid time format: {time_str}")
            raise
    
    def start(self):
        """Start the scheduler"""
        try:
            # Schedule morning run
            morning_time = self.parse_time(config.morning_run_time)
            self.scheduler.add_job(
                self.run_pipeline,
                CronTrigger(
                    hour=morning_time.hour,
                    minute=morning_time.minute
                ),
                id='morning_run'
            )
            
            # Schedule evening run
            evening_time = self.parse_time(config.evening_run_time)
            self.scheduler.add_job(
                self.run_pipeline,
                CronTrigger(
                    hour=evening_time.hour,
                    minute=evening_time.minute
                ),
                id='evening_run'
            )
            
            logger.info(
                f"Scheduled runs at {config.morning_run_time} and "
                f"{config.evening_run_time}"
            )
            
            self.scheduler.start()
            
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            raise
    
    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")
    
    async def run_pipeline(self, dept_ids: Optional[List[str]] = None):
        """Run the pipeline"""
        try:
            logger.info(
                f"Starting scheduled pipeline run at {datetime.now()}"
            )
            results = await self.orchestrator.run(dept_ids)
            
            logger.info("Pipeline run completed")
            logger.info(f"Results: {results}")
            
        except Exception as e:
            logger.error(f"Scheduled pipeline run failed: {e}")
    
    async def run_manual(self, dept_ids: Optional[List[str]] = None):
        """Run the pipeline manually"""
        try:
            logger.info(
                f"Starting manual pipeline run for departments: {dept_ids}"
            )
            return await self.orchestrator.run(dept_ids)
            
        except Exception as e:
            logger.error(f"Manual pipeline run failed: {e}")
            raise

# Create scheduler instance
scheduler = PipelineScheduler()