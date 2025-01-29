# src/pipeline/processors/feed.py

import aiohttp
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
from datetime import datetime
from .base import BaseProcessor
from src.core.config import config
from src.db.repositories.announcement import AnnouncementRepository
from src.db.models.announcement import Announcement
from src.db.session import get_db
from src.core.logging import get_logger

logger = get_logger(__name__)

class FeedProcessor(BaseProcessor):
    """Processor for EGP RSS feed"""
    def __init__(self):
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)

    @property
    def name(self) -> str:
        return "FeedProcessor"
    
    async def process(self, dept_id: str) -> Dict[str, Any]:
        """Process feed for department"""
        try:
            feed_content = await self._fetch_feed(dept_id)
            if not feed_content:
                return {"processed": 0, "error": "Failed to fetch feed"}
            
            announcements = self._parse_feed(feed_content)
            processed_results = []
            
            async with AnnouncementRepository() as repository:
                for data in announcements:
                    try:
                        if not data.get("project_id"):
                            continue
                            
                        announcement = Announcement(
                            project_id=data["project_id"],
                            title=data.get("title", ""),
                            link=data.get("link", ""),
                            description=data.get("description", ""),
                            dept_id=dept_id
                        )
                        
                        existing = await repository.get_by_project_id(announcement.project_id)
                        saved = await repository.upsert(announcement)
                        
                        if saved:
                            processed_results.append({
                                "project_id": saved.project_id,
                                "is_new": not existing
                            })
                            
                    except Exception as e:
                        self.logger.error(
                            f"Error processing announcement {data.get('project_id')}: {e}"
                        )
                        continue
            
            return {
                "processed": len(processed_results),
                "new": len([a for a in processed_results if a.get("is_new", False)]),
                "updated": len([a for a in processed_results if not a.get("is_new", False)])
            }
            
        except Exception as e:
            self.logger.error(f"Error processing feed: {e}")
            return {"processed": 0, "error": str(e)}

    async def _fetch_feed(self, dept_id: str) -> Optional[str]:
        """Fetch feed content from EGP"""
        params = {
            "deptId": dept_id,
            "countbyday": ""
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
            "Accept-Language": "en-US,en;q=0.9,th;q=0.8",
            "Accept-Charset": "windows-874,utf-8;q=0.7,*;q=0.3"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    config.feed_base_url,
                    params=params,
                    headers=headers,
                    timeout=config.feed_timeout
                ) as response:
                    if response.status == 200:
                        content = await response.read()
                        try:
                            return content.decode('cp874')
                        except UnicodeDecodeError:
                            try:
                                return content.decode('utf-8')
                            except UnicodeDecodeError:
                                return content.decode('utf-8', errors='replace')
                    else:
                        logger.error(f"Feed request failed with status {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error fetching feed: {e}")
            return None

    def _parse_feed(self, content: str) -> List[Dict[str, Any]]:
        """Parse XML feed content"""
        try:
            if content.startswith('\ufeff'):
                content = content[1:]
                
            root = ET.fromstring(content)
            announcements = []
            
            for item in root.findall(".//item"):
                try:
                    announcement = {
                        "title": self._get_text(item, "title"),
                        "link": self._get_text(item, "link"),
                        "description": self._get_text(item, "description"),
                        "published_date": self._parse_date(
                            self._get_text(item, "pubDate")
                        )
                    }
                    
                    if announcement["description"]:
                        parts = announcement["description"].split(",")
                        if parts:
                            announcement["project_id"] = parts[0].strip()
                    
                    if announcement.get("project_id"):
                        announcements.append(announcement)
                        
                except Exception as e:
                    logger.error(f"Error parsing announcement: {e}")
                    continue
            
            return announcements
            
        except ET.ParseError as e:
            logger.error(f"Error parsing XML: {e}")
            return []

    def _get_text(self, element: ET.Element, tag: str) -> str:
        """Safely get element text"""
        try:
            child = element.find(tag)
            return child.text.strip() if child is not None and child.text else ""
        except Exception as e:
            logger.error(f"Error getting text for tag {tag}: {e}")
            return ""

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime"""
        try:
            return datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
        except (ValueError, TypeError):
            return datetime.now()

    async def _process_announcements(
        self,
        announcements: List[Dict[str, Any]],
        dept_id: str,
        repository: AnnouncementRepository
    ) -> List[Dict[str, Any]]:
        """Process and store announcements"""
        results = []
        
        for data in announcements:
            try:
                if not data.get("project_id"):
                    continue
                    
                announcement = Announcement(
                    project_id=data["project_id"],
                    title=data.get("title", ""),
                    link=data.get("link", ""),
                    description=data.get("description", ""),
                    dept_id=dept_id
                )
                
                # Using the same repository instance with open connection
                existing = repository.get_by_project_id(announcement.project_id)
                saved = repository.upsert(announcement)
                
                if saved:
                    results.append({
                        "project_id": saved.project_id,
                        "is_new": not existing
                    })
                    
            except Exception as e:
                logger.error(
                    f"Error processing announcement {data.get('project_id')}: {e}"
                )
                continue
        
        return results