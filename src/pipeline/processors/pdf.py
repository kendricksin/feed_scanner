# src/pipeline/processors/pdf.py

import aiohttp
import aiofiles
from typing import Dict, Any, Optional
from pathlib import Path
import PyPDF2
import re
from datetime import datetime

from .base import BaseProcessor
from src.core.config import config
from src.db.repositories.announcement import AnnouncementRepository
from src.core.constants import Status, PDF_DOWNLOAD_TIMEOUT, ERROR_MESSAGES

class PDFProcessor(BaseProcessor):
    """Processor for downloading and extracting PDF content"""
    
    def __init__(self):
        super().__init__()
        self.repository = AnnouncementRepository()
    
    @property
    def name(self) -> str:
        return "PDFProcessor"
    
    async def process(self, dept_id: str) -> Dict[str, Any]:
        """Process PDFs for department announcements"""
        # Get pending announcements
        announcements = self.repository.get_pending_processing()
        
        results = {
            "total": len(announcements),
            "downloaded": 0,
            "processed": 0,
            "failed": 0
        }
        
        for announcement in announcements:
            try:
                # Download PDF
                pdf_path = await self._download_pdf(
                    announcement.link,
                    announcement.project_id
                )
                
                if not pdf_path:
                    self.logger.error(
                        f"Failed to download PDF for {announcement.project_id}"
                    )
                    continue
                
                results["downloaded"] += 1
                
                # Extract data from PDF
                extracted_data = await self._extract_pdf_data(pdf_path)
                
                if extracted_data:
                    # Update announcement with extracted data
                    announcement.update(**extracted_data)
                    announcement.status = Status.COMPLETED
                    announcement.pdf_path = str(pdf_path)
                    
                    self.repository.update(announcement)
                    results["processed"] += 1
                else:
                    announcement.status = Status.FAILED
                    self.repository.update_status(
                        announcement.id,
                        Status.FAILED
                    )
                    results["failed"] += 1
                    
            except Exception as e:
                self.logger.error(
                    f"Error processing {announcement.project_id}: {e}"
                )
                results["failed"] += 1
                announcement.status = Status.FAILED
                self.repository.update_status(announcement.id, Status.FAILED)
        
        return results
    
    async def _download_pdf(self, url: str, project_id: str) -> Optional[Path]:
        """Download PDF file"""
        pdf_dir = config.pdf_dir / project_id
        pdf_dir.mkdir(parents=True, exist_ok=True)
        
        pdf_path = pdf_dir / f"{project_id}.pdf"
        
        # Skip if already downloaded
        if pdf_path.exists():
            return pdf_path
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/pdf"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    timeout=PDF_DOWNLOAD_TIMEOUT
                ) as response:
                    if response.status == 200:
                        async with aiofiles.open(pdf_path, 'wb') as f:
                            await f.write(await response.read())
                        return pdf_path
                    else:
                        self.logger.error(
                            f"PDF download failed: {response.status}"
                        )
                        return None
        except Exception as e:
            self.logger.error(f"Error downloading PDF: {e}")
            return None
    
    async def _extract_pdf_data(self, pdf_path: Path) -> Optional[Dict[str, Any]]:
        """Extract data from PDF"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ''
                for page in reader.pages:
                    text += page.extract_text()
                
                return {
                    'budget_amount': self._extract_budget(text),
                    'quantity': self._extract_quantity(text),
                    'duration_years': self._extract_duration_years(text),
                    'duration_months': self._extract_duration_months(text),
                    'submission_date': self._extract_submission_date(text),
                    'contact_phone': self._extract_phone(text),
                    'contact_email': self._extract_email(text)
                }
        except Exception as e:
            self.logger.error(f"Error extracting PDF data: {e}")
            return None
    
    def _extract_budget(self, text: str) -> Optional[float]:
        """Extract budget amount"""
        pattern = r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*บาท'
        match = re.search(pattern, text)
        if match:
            amount_str = match.group(1).replace(',', '')
            return float(amount_str)
        return None
    
    def _extract_quantity(self, text: str) -> Optional[int]:
        """Extract quantity"""
        pattern = r'จำนวน\s*(\d+)'
        match = re.search(pattern, text)
        return int(match.group(1)) if match else None
    
    def _extract_duration_years(self, text: str) -> Optional[int]:
        """Extract contract duration in years"""
        pattern = r'(\d+)\s*ปี'
        match = re.search(pattern, text)
        return int(match.group(1)) if match else None
    
    def _extract_duration_months(self, text: str) -> Optional[int]:
        """Extract contract duration in months"""
        pattern = r'(\d+)\s*เดือน'
        match = re.search(pattern, text)
        return int(match.group(1)) if match else None
    
    def _extract_submission_date(self, text: str) -> Optional[datetime]:
        """Extract submission date"""
        # Common Thai months
        thai_months = {
            'มกราคม': '01', 'กุมภาพันธ์': '02', 'มีนาคม': '03',
            'เมษายน': '04', 'พฤษภาคม': '05', 'มิถุนายน': '06',
            'กรกฎาคม': '07', 'สิงหาคม': '08', 'กันยายน': '09',
            'ตุลาคม': '10', 'พฤศจิกายน': '11', 'ธันวาคม': '12'
        }
        
        pattern = r'วันที่\s*(\d{1,2})\s*(มกราคม|กุมภาพันธ์|มีนาคม|เมษายน|พฤษภาคม|มิถุนายน|กรกฎาคม|สิงหาคม|กันยายน|ตุลาคม|พฤศจิกายน|ธันวาคม)\s*(\d{4})'
        match = re.search(pattern, text)
        
        if match:
            day = match.group(1).zfill(2)
            month = thai_months[match.group(2)]
            year = str(int(match.group(3)) - 543)  # Convert Buddhist Era to CE
            date_str = f"{year}-{month}-{day}"
            
            try:
                return datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                self.logger.error(f"Invalid date: {date_str}")
                return None
                
        return None
    
    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number"""
        pattern = r'โทรศัพท์\s*:?\s*([\d\s-]+)'
        match = re.search(pattern, text)
        if match:
            # Clean up phone number
            phone = re.sub(r'\s+', '', match.group(1))
            return phone
        return None
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email address"""
        pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        match = re.search(pattern, text)
        return match.group(0) if match else None