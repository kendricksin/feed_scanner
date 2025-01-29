# src/core/logging.py

import logging
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from .config import config

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    # Force UTF-8 encoding for console output
    import ctypes
    
    # Get the console output handle
    handle = ctypes.windll.kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
    
    # Set console mode to enable virtual terminal processing
    mode = ctypes.c_ulong()
    ctypes.windll.kernel32.GetConsoleMode(handle, ctypes.byref(mode))
    mode.value |= 0x0004  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
    ctypes.windll.kernel32.SetConsoleMode(handle, mode)
    
    # Set console code page to UTF-8
    if hasattr(sys, 'frozen'):
        # Running as executable
        os.system('chcp 65001 >NUL')
    else:
        # Running as script
        os.system('chcp 65001 >NUL')
    
    # Set environment variable for Python IO encoding
    os.environ['PYTHONIOENCODING'] = 'utf-8'

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

class ThaiStreamHandler(logging.StreamHandler):
    """Custom handler for Thai character support"""
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            
            if stream in (sys.stdout, sys.stderr):
                try:
                    if isinstance(msg, str):
                        msg = msg.encode('utf-8', errors='replace').decode('utf-8')
                    stream.write(msg + self.terminator)
                except Exception:
                    # Fallback for any encoding issues
                    stream.buffer.write(msg.encode('utf-8', errors='replace'))
                    stream.buffer.write(self.terminator.encode('utf-8'))
            else:
                stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

# Rest of the logging.py code remains the same...

def setup_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """Set up logger with console and file handlers"""
    logger = logging.getLogger(name)
    
    # Only configure if handlers haven't been set up
    if not logger.handlers:
        logger.setLevel(config.log_level)
        
        # Console handler with colors
        console_handler = ThaiStreamHandler(sys.stdout)
        console_handler.setFormatter(CustomFormatter())
        logger.addHandler(console_handler)
        
        # File handler if log_file is specified
        if log_file:
            # Create log filename with date
            date_str = datetime.now().strftime("%Y-%m-%d")
            log_path = config.log_dir / f"{log_file}_{date_str}.log"
            
            file_handler = logging.FileHandler(log_path, encoding='utf-8')
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S"
                )
            )
            logger.addHandler(file_handler)
        
        # Prevent logging from propagating to the root logger
        logger.propagate = False
    
    return logger

# Create main application logger
logger = setup_logger("egp_pipeline", "pipeline")

def get_logger(name: str) -> logging.Logger:
    """Get logger for specific module"""
    return setup_logger(f"egp_pipeline.{name}")