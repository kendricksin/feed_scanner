# src/tests/test_services/test_feed_scanner.py

import asyncio
import sys
from pathlib import Path
import pytest
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.pipeline.processors.feed import FeedProcessor
from src.db.session import init_db, get_db
from src.core.constants import Status
from src.core.logging import get_logger

logger = get_logger(__name__)

async def test_feed_scanner():
    """Test the feed scanner functionality"""
    try:
        # Initialize database
        init_db()
        logger.info("Database initialized")
        
        # Create feed processor
        processor = FeedProcessor()
        logger.info("Feed processor created")
        
        # Test departments
        dept_ids = ["1507","0304","0307","1509"]  # Add more department IDs as needed
        
        for dept_id in dept_ids:
            logger.info(f"\nTesting feed scanner for department {dept_id}")
            
            try:
                # Process feed
                result = await processor.process(dept_id)
                logger.info(f"Feed processing result: {result}")
                
                # Check database for results
                with get_db() as conn:
                    cursor = conn.cursor()
                    
                    # Get count of announcements
                    cursor.execute("""
                        SELECT COUNT(*) as count,
                               COUNT(DISTINCT project_id) as unique_projects
                        FROM announcements
                        WHERE dept_id = ?
                    """, (dept_id,))
                    counts = cursor.fetchone()
                    
                    logger.info(f"Total announcements: {counts['count']}")
                    logger.info(f"Unique projects: {counts['unique_projects']}")
                    
                    # Get some sample announcements
                    cursor.execute("""
                        SELECT project_id, title, status, created_at
                        FROM announcements
                        WHERE dept_id = ?
                        ORDER BY created_at DESC
                        LIMIT 5
                    """, (dept_id,))
                    
                    recent = cursor.fetchall()
                    
                    logger.info("\nRecent announcements:")
                    for ann in recent:
                        logger.info(f"""
Project ID: {ann['project_id']}
Title: {ann['title']}
Status: {ann['status']}
Created: {ann['created_at']}
{"="*50}""")
                    
                    # Check for any errors
                    cursor.execute("""
                        SELECT COUNT(*) as error_count
                        FROM announcements
                        WHERE dept_id = ? AND status = ?
                    """, (dept_id, Status.FAILED))
                    
                    error_count = cursor.fetchone()['error_count']
                    if error_count > 0:
                        logger.warning(f"Found {error_count} failed announcements")
                
            except Exception as e:
                logger.error(f"Error processing department {dept_id}: {e}")
                raise
                
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

if __name__ == "__main__":
    # Run the test
    logger.info("Starting feed scanner test")
    logger.info(f"Time: {datetime.now()}")
    
    asyncio.run(test_feed_scanner())