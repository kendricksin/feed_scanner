# src/tests/test_services/test_feed_scanner.py

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Ensure UTF-8 encoding for Windows
if sys.platform == 'win32':
    import os
    os.system('chcp 65001 >NUL')
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.pipeline.processors.feed import FeedProcessor
from src.db.session import init_db, get_db
from src.core.constants import Status
from src.core.logging import get_logger

logger = get_logger(__name__)

def format_announcement(ann: Dict[str, Any]) -> str:
    """Format announcement for display"""
    return f"""
{'='*80}
Project ID: {ann['project_id']}
Title: {ann['title']}
Status: {ann['status']}
Created: {ann['created_at']}
{'='*80}"""

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
        dept_ids = ["1507", "0304", "0307", "1509"]
        
        for dept_id in dept_ids:
            logger.info(f"\nProcessing department {dept_id}")
            
            try:
                # Process feed
                result = await processor.process(dept_id)
                logger.info(f"Processing results for {dept_id}:")
                logger.info(f"- Total processed: {result.get('processed', 0)}")
                logger.info(f"- New entries: {result.get('new', 0)}")
                logger.info(f"- Updated entries: {result.get('updated', 0)}")
                
                # Check database for results
                with get_db() as conn:
                    cursor = conn.cursor()
                    
                    # Get counts
                    cursor.execute("""
                        SELECT COUNT(*) as count,
                               COUNT(DISTINCT project_id) as unique_projects,
                               COUNT(CASE WHEN status = ? THEN 1 END) as failed_count
                        FROM announcements
                        WHERE dept_id = ?
                    """, (Status.FAILED, dept_id))
                    
                    stats = cursor.fetchone()
                    
                    logger.info("\nDatabase statistics:")
                    logger.info(f"- Total announcements: {stats['count']}")
                    logger.info(f"- Unique projects: {stats['unique_projects']}")
                    
                    if stats['failed_count'] > 0:
                        logger.warning(f"- Failed announcements: {stats['failed_count']}")
                    
                    # Get recent announcements
                    if stats['count'] > 0:
                        cursor.execute("""
                            SELECT project_id, title, status, created_at
                            FROM announcements
                            WHERE dept_id = ?
                            ORDER BY created_at DESC
                            LIMIT 5
                        """, (dept_id,))
                        
                        logger.info("\nMost recent announcements:")
                        for ann in cursor.fetchall():
                            logger.info(format_announcement(ann))
                
            except Exception as e:
                logger.error(f"Error processing department {dept_id}: {e}")
                raise
                
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

if __name__ == "__main__":
    logger.info(f"Starting feed scanner test at {datetime.now()}")
    asyncio.run(test_feed_scanner())