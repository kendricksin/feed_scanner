# scripts/migrations/create_ai_analysis_table.py

import sqlite3
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.core.config import config
from src.core.logging import get_logger

logger = get_logger(__name__)

def qwen_table():
    """Create table for AI-analyzed PDF content"""
    try:
        with sqlite3.connect(config.db_path) as conn:
            cursor = conn.cursor()
            
            # Create table for AI analysis results
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects_qwen (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT UNIQUE NOT NULL,
                    document_title TEXT,
                    project_title TEXT,
                    department_name TEXT,
                    budget_amount REAL,
                    announcement_date TEXT,
                    submission_date TEXT,
                    contact_phone TEXT,
                    contact_email TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES announcements (project_id)
                )
            """)
            
            # Add indices
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_ai_analysis_project_id 
                ON ai_pdf_analysis (project_id)
            """)
            
            conn.commit()
            logger.info("AI analysis table created successfully")
            
    except Exception as e:
        logger.error(f"Error creating AI analysis table: {e}")
        raise

if __name__ == "__main__":
    qwen_table()