# Migration script (scripts/migrate_pdfs.py)
import asyncio
import shutil
from pathlib import Path
import sys
from typing import List, Tuple
import logging

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.core.config import config
from src.core.logging import get_logger

logger = get_logger(__name__)

def find_pdf_files(pdfs_dir: Path) -> List[Tuple[Path, str]]:
    """Find all PDF files in the old structure and their project IDs"""
    pdf_files = []
    
    # Look for directories that contain PDFs
    for project_dir in pdfs_dir.iterdir():
        if not project_dir.is_dir():
            continue
            
        project_id = project_dir.name
        pdf_path = project_dir / f"{project_id}.pdf"
        
        if pdf_path.exists():
            pdf_files.append((pdf_path, project_id))
            
    return pdf_files

def migrate_pdfs() -> None:
    """Migrate PDFs from old to new structure"""
    pdfs_dir = config.pdf_dir
    
    try:
        # Find all PDFs in old structure
        pdf_files = find_pdf_files(pdfs_dir)
        logger.info(f"Found {len(pdf_files)} PDFs to migrate")
        
        # Process each PDF
        for old_path, project_id in pdf_files:
            try:
                # New path directly in pdfs directory
                new_path = pdfs_dir / f"{project_id}.pdf"
                
                # Skip if file already exists at new location
                if new_path.exists():
                    logger.warning(
                        f"PDF for project {project_id} already exists at new location"
                    )
                    continue
                
                # Move the file
                shutil.move(old_path, new_path)
                logger.info(f"Moved PDF for project {project_id}")
                
                # Remove empty project directory
                project_dir = old_path.parent
                if not any(project_dir.iterdir()):
                    project_dir.rmdir()
                    logger.info(f"Removed empty directory for project {project_id}")
                    
            except Exception as e:
                logger.error(f"Error migrating PDF for project {project_id}: {e}")
                
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    logger.info("Starting PDF migration")
    migrate_pdfs()
    logger.info("PDF migration completed")