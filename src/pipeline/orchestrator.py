from typing import List, Optional
from .processors.base import BaseProcessor
from core.logging import logger

class PipelineOrchestrator:
    def __init__(self, processors: List[BaseProcessor] = None):
        self.processors = processors or []
    
    async def process_department(self, dept_id: str) -> dict:
        results = {}
        for processor in self.processors:
            try:
                result = await processor.process(dept_id)
                results[processor.name] = result
            except Exception as e:
                logger.error(f"Error in {processor.name}: {e}")
                results[processor.name] = {"error": str(e)}
        return results
