# tests/test_services/test_pdf_processor.py

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import argparse
from typing import Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.pipeline.processors.pdf import PDFProcessor
from src.db.session import init_db, get_db
from src.core.logging import get_logger
from src.core.constants import Status
from src.db.models.announcement import Announcement

logger = get_logger(__name__)

def create_test_announcement(cursor, project_id: str, link: Optional[str] = None):
    """Create a test announcement record with a link if it doesn't exist"""
    # Check if announcement exists
    cursor.execute(
        "SELECT * FROM announcements WHERE project_id = ?",
        (project_id,)
    )
    existing_announcement = cursor.fetchone()
    
    if existing_announcement:
        logger.info(f"Announcement {project_id} already exists")
        return
    
    # If no link provided, use sample EGP link format
    if not link:
        link = f"https://process3.gprocurement.go.th/egp2procmainWeb/procsearch.sch?proc_id=FPRO9965_1&mode=LINK&temp_projectId={project_id}"
    
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
        f"Test Procurement Announcement {project_id}",
        link,
        "Test procurement document download",
        Status.PENDING,
        datetime.now(),
        datetime.now()
    ))
    logger.info(f"Created test announcement for project {project_id}")

def format_extracted_data(data: dict) -> str:
    """Format extracted data for logging"""
    formatted = "Extracted Data:\n"
    for key, value in data.items():
        formatted += f"- {key}: {value}\n"
    return formatted

async def test_pdf_processor(project_ids: list):
    """Test the PDF processor functionality"""
    try:
        # Initialize database
        init_db()
        logger.info("Database initialized")
        
        # Create PDF processor
        processor = PDFProcessor()
        logger.info("PDF processor created")
        
        # Create test announcements if needed
        with get_db() as conn:
            cursor = conn.cursor()
            for project_id in project_ids:
                create_test_announcement(cursor, project_id)
            conn.commit()
        
        # Fetch announcements with links
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT project_id, link 
                FROM announcements 
                WHERE project_id IN ({seq})
            """.format(seq=','.join(['?']*len(project_ids))), 
            project_ids)
            announcements = cursor.fetchall()
        
        # Process each announcement
        for announcement in announcements:
            logger.info(f"\nProcessing project: {announcement['project_id']}")
            
            try:
                # Use the processor to download and extract PDF
                pdf_path = await processor._download_pdf(
                    announcement['link'], 
                    announcement['project_id']
                )
                
                if pdf_path and pdf_path.exists():
                    logger.info(f"PDF downloaded successfully to: {pdf_path}")
                    
                    # Extract data from PDF
                    extracted_data = await processor._extract_pdf_data(pdf_path)
                    
                    if extracted_data:
                        # Log extracted data
                        logger.info(format_extracted_data(extracted_data))
                        
                        # Optionally update announcement in database
                        with get_db() as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE announcements 
                                SET budget_amount = ?, 
                                    quantity = ?, 
                                    duration_years = ?, 
                                    duration_months = ?, 
                                    submission_date = ?, 
                                    contact_phone = ?, 
                                    contact_email = ?,
                                    status = ?
                                WHERE project_id = ?
                            """, (
                                extracted_data.get('budget_amount'),
                                extracted_data.get('quantity'),
                                extracted_data.get('duration_years'),
                                extracted_data.get('duration_months'),
                                extracted_data.get('submission_date'),
                                extracted_data.get('contact_phone'),
                                extracted_data.get('contact_email'),
                                Status.COMPLETED,
                                announcement['project_id']
                            ))
                            conn.commit()
                        
                        logger.info("Announcement updated in database")
                    else:
                        logger.warning("No data extracted from PDF")
                else:
                    logger.error("Failed to download PDF")
                    
            except Exception as e:
                logger.error(f"Error processing project {announcement['project_id']}: {e}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

def parse_args():
    parser = argparse.ArgumentParser(description='Test PDF processor')
    parser.add_argument('project_ids', nargs='+', help='Project IDs to test')
    parser.add_argument('--link', help='Optional PDF link for the project', default=None)
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    logger.info(f"Starting PDF processor test at {datetime.now()}")
    
    # If a specific link is provided, create the announcement with that link
    with get_db() as conn:
        cursor = conn.cursor()
        if args.link:
            # If link is provided, use it for the first project ID
            create_test_announcement(cursor, args.project_ids[0], args.link)
        else:
            for project_id in args.project_ids:
                create_test_announcement(cursor, project_id)
        conn.commit()
    
    asyncio.run(test_pdf_processor(args.project_ids))