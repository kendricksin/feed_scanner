# src/pipeline/processors/document.py

import aiohttp
import aiofiles
import ssl
from typing import Dict, Any, Optional
from pathlib import Path
import json
import zipfile
import shutil

from .base import BaseProcessor
from src.core.config import config
from src.db.repositories.announcement import AnnouncementRepository
from src.core.constants import Status, ERROR_MESSAGES

class DocumentProcessor(BaseProcessor):
    """Processor for downloading and extracting project related documents"""
    
    INFO_API_URL = "https://process5.gprocurement.go.th/egp-approval-service/apv-common/infoProcureDocAnnounZipTemp"
    DOWNLOAD_API_URL = "https://process5.gprocurement.go.th/egp-upload-service/v1/downloadFileTest"
    
    def __init__(self):
        super().__init__()
        self.repository = AnnouncementRepository()
    
    @property
    def name(self) -> str:
        return "DocumentProcessor"
    
    async def process(self, dept_id: str) -> Dict[str, Any]:
            """Process document downloads for department announcements"""
            announcements_rows = self.repository.get_pending_processing()
            announcements = [announcement(row) for row in announcements_rows]
            
            results = {
                "total": len(announcements),
                "processed": 0,
                "failed": 0,
                "skipped": 0,
                "files_extracted": 0
            }
            
            for announcement in announcements:
                try:
                    # Get document info
                    doc_info = await self._fetch_document_info(announcement.project_id)
                    
                    if not doc_info or not doc_info.get("zipId"):
                        self.logger.info(f"No documents available for project {announcement.project_id}")
                        results["skipped"] += 1
                        continue
                except Exception as e:
                    self.logger.error(f"Error fetching document info for project {announcement.project_id}: {e}")
                    results["failed"] += 1
                    continue
    
    async def _fetch_document_info(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Fetch document information from API"""
        params = {"projectId": project_id}
        
        # Create SSL context that ignores verification
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        try:
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(self.INFO_API_URL, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data["response"]["responseCode"] == "0":
                            return data["data"]
                        else:
                            self.logger.warning(
                                f"API error for project {project_id}: "
                                f"{data['response']['description']}"
                            )
                    else:
                        self.logger.error(
                            f"Failed to fetch document info: {response.status}"
                        )
                    
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error fetching document info: {e}")
            return None

    async def _process_zip_file(
        self,
        project_id: str,
        zip_id: str
    ) -> Optional[Path]:
        """Download and extract ZIP file"""
        # Create project directory
        project_dir = config.base_dir / "data" / "projects" / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Temporary ZIP file path
        temp_zip = project_dir / f"{project_id}_temp.zip"
        
        try:
            # Download ZIP file
            params = {"fileId": zip_id}
            
            # Create SSL context that ignores verification
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(self.DOWNLOAD_API_URL, params=params) as response:
                    if response.status != 200:
                        self.logger.error(f"Failed to download ZIP: {response.status}")
                        return None
                    
                    # Save ZIP file
                    async with aiofiles.open(temp_zip, 'wb') as f:
                        await f.write(await response.read())
            
            # Extract ZIP file
            with zipfile.ZipFile(temp_zip) as zip_ref:
                # Check for malicious paths (path traversal)
                for zip_info in zip_ref.filelist:
                    if '..' in zip_info.filename or zip_info.filename.startswith('/'):
                        raise ValueError(f"Malicious path in ZIP: {zip_info.filename}")
                
                # Extract all files
                zip_ref.extractall(project_dir)
            
            # Clean up temporary ZIP file
            temp_zip.unlink()
            
            return project_dir
            
        except Exception as e:
            self.logger.error(f"Error processing ZIP file: {e}")
            # Clean up on error
            if temp_zip.exists():
                temp_zip.unlink()
            return None