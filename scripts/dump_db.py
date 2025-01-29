import sys
from pathlib import Path
import sqlite3

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.db.session import get_db
from src.core.logging import get_logger

logger = get_logger(__name__)

def clear_database():
    """Clear all data from the database"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get table names
            cursor.execute("""
                SELECT name 
                FROM sqlite_master 
                WHERE type='table' AND name != 'sqlite_sequence'
            """)
            
            tables = cursor.fetchall()
            
            # Delete data from each table
            for table in tables:
                table_name = table['name']
                try:
                    cursor.execute(f"DELETE FROM {table_name}")
                    cursor.execute(f"DELETE FROM sqlite_sequence WHERE name=?", (table_name,))
                    logger.info(f"Cleared table: {table_name}")
                except sqlite3.Error as e:
                    logger.error(f"Error clearing table {table_name}: {e}")
            
            conn.commit()
            logger.info("Database cleared successfully")
            
    except Exception as e:
        logger.error(f"Error clearing database: {e}")
        raise

if __name__ == "__main__":
    logger.info("Starting database clear")
    clear_database()