# src/db/session.py

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator
import asyncio
from src.core.config import config
from src.core.logging import get_logger

logger = get_logger(__name__)

def init_db():
    """Initialize database with schema"""
    try:
        with sqlite3.connect(config.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Drop existing table if needed
            cursor.execute("DROP TABLE IF EXISTS announcements")
            
            # Create announcements table with proper types
            cursor.execute("""
                CREATE TABLE announcements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT UNIQUE NOT NULL,
                    dept_id TEXT,
                    title TEXT,
                    link TEXT,
                    description TEXT,
                    status TEXT DEFAULT 'pending',
                    pdf_path TEXT,
                    budget_amount REAL,  -- Using REAL for floating point numbers
                    quantity INTEGER,
                    duration_years INTEGER,
                    duration_months INTEGER,
                    submission_date TIMESTAMP,
                    contact_phone TEXT,
                    contact_email TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_project_id 
                ON announcements(project_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_dept_id 
                ON announcements(dept_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_status 
                ON announcements(status)
            """)
            
            conn.commit()
            logger.info("Database initialized successfully")
            
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise

@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Get database connection"""
    conn = None
    try:
        conn = sqlite3.connect(config.db_path)
        conn.row_factory = sqlite3.Row
        yield conn
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()

class AsyncDBConnection:
    """Async database connection wrapper"""
    def __init__(self):
        self.conn = None
        self._lock = asyncio.Lock()

    async def __aenter__(self):
        await self._lock.acquire()
        self.conn = sqlite3.connect(config.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            if exc_type:
                self.conn.rollback()
            else:
                self.conn.commit()
            self.conn.close()
        self._lock.release()

async def get_async_db():
    """Get async database connection"""
    return AsyncDBConnection()