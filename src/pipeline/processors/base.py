# src/pipeline/processors/base.py

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime
from src.core.logging import get_logger
from src.core.constants import Status

class BaseProcessor(ABC):
    """Base class for pipeline processors"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self._status = Status.PENDING
        self._error: Optional[str] = None
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Processor name"""
        pass
    
    @abstractmethod
    async def process(self, dept_id: str) -> Dict[str, Any]:
        """Process data for department"""
        pass
    
    async def execute(self, dept_id: str) -> Dict[str, Any]:
        """Execute processor with timing and error handling"""
        self.start_time = datetime.now()
        self._status = Status.PROCESSING
        
        try:
            self.logger.info(f"Starting {self.name} for department {dept_id}")
            result = await self.process(dept_id)
            self._status = Status.COMPLETED
            return result
            
        except Exception as e:
            self._status = Status.FAILED
            self._error = str(e)
            self.logger.error(f"Error in {self.name}: {e}")
            raise
            
        finally:
            self.end_time = datetime.now()
            self.log_execution_time()
    
    def log_execution_time(self):
        """Log execution time"""
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
            self.logger.info(f"{self.name} executed in {duration:.2f} seconds")
    
    @property
    def execution_time(self) -> Optional[float]:
        """Get execution time in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def status(self) -> Status:
        """Get current status"""
        return self._status
    
    @property
    def error(self) -> Optional[str]:
        """Get error message if any"""
        return self._error
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processor statistics"""
        return {
            "name": self.name,
            "status": self.status,
            "error": self.error,
            "execution_time": self.execution_time,
            "start_time": self.start_time,
            "end_time": self.end_time
        }