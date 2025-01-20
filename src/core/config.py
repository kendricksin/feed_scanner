# src/core/config.py

from pathlib import Path
from typing import Dict, Any
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent.parent
        self.load_config()
        
    def load_config(self):
        """Load configuration from environment variables"""
        # Database
        self.db_path = self.base_dir / "data" / "egp.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # API Configuration
        self.api_host = os.getenv("API_HOST", "0.0.0.0")
        self.api_port = int(os.getenv("API_PORT", "8000"))
        
        # EGP Feed Configuration
        self.feed_base_url = os.getenv(
            "FEED_BASE_URL",
            "http://process3.gprocurement.go.th/EPROCRssFeedWeb/egpannouncerss.xml"
        )
        self.feed_timeout = int(os.getenv("FEED_TIMEOUT", "30"))
        
        # PDF Storage
        self.pdf_dir = self.base_dir / "data" / "pdfs"
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        
        # Logging
        self.log_dir = self.base_dir / "data" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # Schedule Configuration
        self.morning_run_time = os.getenv("MORNING_RUN_TIME", "08:30")
        self.evening_run_time = os.getenv("EVENING_RUN_TIME", "17:30")
        
    def as_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary"""
        return {
            "db_path": str(self.db_path),
            "api_host": self.api_host,
            "api_port": self.api_port,
            "feed_base_url": self.feed_base_url,
            "feed_timeout": self.feed_timeout,
            "pdf_dir": str(self.pdf_dir),
            "log_dir": str(self.log_dir),
            "log_level": self.log_level,
            "morning_run_time": self.morning_run_time,
            "evening_run_time": self.evening_run_time
        }
        
    def __str__(self) -> str:
        """String representation of configuration"""
        return json.dumps(self.as_dict(), indent=2)

# Create global config instance
config = Config()