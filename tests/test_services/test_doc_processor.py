# tests/test_services/test_doc_processor.py

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import argparse

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.pipeline.processors.document import DocumentProcessor
from src.db.session import init_db, get_db
from src.core.logging import get_logger
from src.core.constants import Status
from src.db.models.announcement import Announcement

logger = get_logger(__name__)

def create_test_announcement(cursor, project_id: str):
    """Create a test announcement record"""
    announcement_link = f"https://process3.gprocurement.go.th/egp2procmainWeb/procsearch.sch?announceType=2&servlet=FPRO9965Servlet&proc_id=FPRO9965_1&proc_name=Procure&processFlows=Procure&mode=LINK&homeflag=A&temp_projectId={project_id}"
    
    # First check if announcement exists
    cursor.execute(
        "SELECT * FROM announcements WHERE project_id = ?",
        (project_id,)
    )
    if cursor.fetchone():
        logger.info(f"Announcement {project_id} already exists")
        return
    
    cursor.execute("""
        INSERT INTO announcements (
            project_id,
            title,
            link,
            description,
            status,
            created_at,
            updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        project_id,
        f"Test Announcement {project_id}",
        announcement_link,
        "Test Description",
        "pending",
        datetime.now(),
        datetime.now()
    ))
    logger.info(f"Created test announcement for project {project_id}")

async def test_document_processor(project_id: str):
    """Test the document processor functionality"""
    try:
        # Initialize database
        init_db()
        logger.info("Database initialized")
        
        # Create document processor
        processor = DocumentProcessor()
        logger.info("Document processor created")
        
        # Create test announcement if needed
        with get_db() as conn:
            cursor = conn.cursor()
            create_test_announcement(cursor, project_id)
            conn.commit()
        
        # First test document info API
        logger.info("\nTesting document info API...")
        doc_info = await processor._fetch_document_info(project_id)
        
        if doc_info:
            logger.info("Document info retrieved successfully:")
            logger.info(f"ZIP ID: {doc_info.get('zipId')}")
            logger.info(f"Build Name: {doc_info.get('buildName1')}")
            
            # Test ZIP download and extraction
            logger.info("\nTesting ZIP download and extraction...")
            project_dir = await processor._process_zip_file(
                project_id,
                doc_info['zipId']
            )
            
            if project_dir:
                logger.info(f"Files extracted to: {project_dir}")
                
                # List extracted files
                files = list(project_dir.rglob('*'))
                file_count = sum(1 for f in files if f.is_file())
                logger.info(f"\nExtracted {file_count} files:")
                for file_path in files:
                    if file_path.is_file():
                        logger.info(f"- {file_path.relative_to(project_dir)}")
            else:
                logger.error("Failed to process ZIP file")
        else:
            logger.error("Failed to get document info from API")
        
        # Run full processor
        # logger.info("\nRunning full document processor...")
        # results = await processor.process("test_dept")  # dept_id doesn't matter for test
        # logger.info("Processing results:")
        # for key, value in results.items():
        #     logger.info(f"{key}: {value}")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

def parse_args():
    parser = argparse.ArgumentParser(description='Test document processor')
    parser.add_argument('project_id', help='Project ID to test')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    logger.info(f"Starting document processor test at {datetime.now()}")
    asyncio.run(test_document_processor(args.project_id))