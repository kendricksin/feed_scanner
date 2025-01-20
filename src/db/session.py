import sqlite3
from contextlib import contextmanager
from typing import Generator
from src.core.config import config
from src.core.logging import get_logger

logger = get_logger(__name__)

def init_db():
    """Initialize database with schema"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Create announcements table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                link TEXT NOT NULL,
                description TEXT,
                dept_id TEXT,
                status TEXT DEFAULT 'pending',
                budget_amount REAL,
                quantity INTEGER,
                duration_years INTEGER,
                duration_months INTEGER,
                submission_date TEXT,
                submission_time TEXT,
                contact_phone TEXT,
                contact_email TEXT,
                pdf_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes - execute each separately
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_project_id ON announcements(project_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_dept_id ON announcements(dept_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status ON announcements(status)
        """)
        
        conn.commit()
        logger.info("Database initialized successfully")

@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Database connection context manager"""
    conn = None
    try:
        conn = sqlite3.connect(str(config.db_path))
        # Enable foreign key support
        conn.execute("PRAGMA foreign_keys = ON")
        # Return dictionary-like rows
        conn.row_factory = sqlite3.Row
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def dict_factory(cursor: sqlite3.Cursor, row: tuple) -> dict:
    """Convert database row to dictionary"""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d