import sqlite3
from pathlib import Path
from src.core.config import config
from src.core.logging import get_logger

logger = get_logger(__name__)

def init_db():
    """Initialize database with schema"""
    try:
        # Ensure data directory exists
        config.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Connect to database
        conn = sqlite3.connect(config.db_path)
        cursor = conn.cursor()
        
        # Drop existing tables
        cursor.execute("DROP TABLE IF EXISTS announcements")
        
        # Create announcements table
        cursor.execute("""
        CREATE TABLE announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            link TEXT NOT NULL,
            description TEXT,
            dept_id TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create indices
        cursor.execute("""
        CREATE INDEX idx_project_id 
        ON announcements(project_id)
        """)
        
        cursor.execute("""
        CREATE INDEX idx_dept_id 
        ON announcements(dept_id)
        """)
        
        cursor.execute("""
        CREATE INDEX idx_status 
        ON announcements(status)
        """)
        
        conn.commit()
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    init_db()