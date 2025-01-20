# src/core/logging.py

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from .config import config

class CustomFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    
    FORMATS = {
        logging.DEBUG: grey + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + reset,
        logging.INFO: grey + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + reset,
        logging.WARNING: yellow + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + reset,
        logging.ERROR: red + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + reset,
        logging.CRITICAL: bold_red + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + reset
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)

def setup_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """Set up logger with console and file handlers"""
    logger = logging.getLogger(name)
    logger.setLevel(config.log_level)
    
    # Remove existing handlers
    logger.handlers = []
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(CustomFormatter())
    logger.addHandler(console_handler)
    
    # File handler if log_file is specified
    if log_file:
        # Create log filename with date
        date_str = datetime.now().strftime("%Y-%m-%d")
        log_path = config.log_dir / f"{log_file}_{date_str}.log"
        
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        )
        logger.addHandler(file_handler)
    
    return logger

# Create main application logger
logger = setup_logger("egp_pipeline", "pipeline")

def get_logger(name: str) -> logging.Logger:
    """Get logger for specific module"""
    return setup_logger(f"egp_pipeline.{name}")

# Example usage in other modules:
# from core.logging import get_logger
# logger = get_logger(__name__)