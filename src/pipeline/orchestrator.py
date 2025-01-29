# src/pipeline/orchestrator.py

from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
from src.core.logging import get_logger
from src.core.constants import DEPARTMENTS, Status
from .processors.base import BaseProcessor
from .processors.feed import FeedProcessor
from .processors.pdf import PDFProcessor

logger = get_logger(__name__)

# src/pipeline/orchestrator.py

class PipelineOrchestrator:
    """Orchestrates the execution of pipeline processors"""
    
    def __init__(self):
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self._status = Status.PENDING
        self._results: Dict[str, Any] = {}
        # Store processor count directly
        self._processor_count = 2  # FeedProcessor and PDFProcessor
    
    @property
    def processors(self) -> List[BaseProcessor]:
        """Get list of processors"""
        return [
            FeedProcessor(),
            PDFProcessor()
        ]
    
    async def run(self, dept_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run the pipeline for specified departments"""
        self.start_time = datetime.now()
        self._status = Status.PROCESSING
        
        try:
            # Use provided department IDs or all configured departments
            departments = dept_ids or list(DEPARTMENTS.keys())
            
            results = await asyncio.gather(*[
                self._process_department(dept_id)
                for dept_id in departments
            ])
            
            self._results = {
                dept_id: result
                for dept_id, result in zip(departments, results)
            }
            
            self._status = Status.COMPLETED
            return self.get_summary()
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            self._status = Status.FAILED
            raise
            
        finally:
            self.end_time = datetime.now()
            self.log_execution_time()
    
    async def _process_department(self, dept_id: str) -> Dict[str, Any]:
        """Process single department through all processors"""
        dept_results = {}
        
        try:
            for processor in self.processors:  # Now gets fresh processor instances
                logger.info(f"Running {processor.name} for department {dept_id}")
                result = await processor.execute(dept_id)
                dept_results[processor.name] = {
                    "status": processor.status,
                    "execution_time": processor.execution_time,
                    "result": result
                }
                
                # Stop processing if a processor fails
                if processor.status == Status.FAILED:
                    logger.error(
                        f"{processor.name} failed for department {dept_id}"
                    )
                    break
                    
            return dept_results
            
        except Exception as e:
            logger.error(f"Error processing department {dept_id}: {e}")
            return {"error": str(e)}
    
    def get_summary(self) -> Dict[str, Any]:
        """Get pipeline execution summary"""
        if not self._results:
            return {"status": self._status}
            
        summary = {
            "status": self._status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "execution_time": self.execution_time,
            "departments": len(self._results),
            "processors": self._processor_count,  # Use stored count instead of len(processors)
            "details": self._results
        }
        
        # Add processor-specific statistics
        processor_names = ["FeedProcessor", "PDFProcessor"]  # Hardcode processor names
        for processor_name in processor_names:
            stats = {
                "successful": sum(
                    1 for dept_results in self._results.values()
                    if dept_results.get(processor_name, {}).get("status") == Status.COMPLETED
                ),
                "failed": sum(
                    1 for dept_results in self._results.values()
                    if dept_results.get(processor_name, {}).get("status") == Status.FAILED
                ),
                "total_time": sum(
                    float(dept_results.get(processor_name, {}).get("execution_time", 0) or 0)
                    for dept_results in self._results.values()
                )
            }
            summary[processor_name] = stats
        
        return summary
    
    def log_execution_time(self):
        """Log total execution time"""
        if self.start_time and self.end_time:
            duration = self.execution_time
            logger.info(f"Pipeline executed in {duration:.2f} seconds")
    
    @property
    def execution_time(self) -> Optional[float]:
        """Get total execution time in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def status(self) -> Status:
        """Get current pipeline status"""
        return self._status
    
    @property
    def results(self) -> Dict[str, Any]:
        """Get pipeline results"""
        return self._results