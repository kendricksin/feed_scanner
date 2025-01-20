from abc import ABC, abstractmethod

class BaseProcessor(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @abstractmethod
    async def process(self, dept_id: str) -> dict:
        pass
