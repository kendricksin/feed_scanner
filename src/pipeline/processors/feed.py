# src/pipeline/processors/feed.py

import aiohttp
import xml.etree.ElementTree as ET
from typing import Dict, Any, List
from datetime import datetime
from .base import BaseProcessor
from src.core.config import config
from src.db.repositories.announcement import AnnouncementRepository
from src.db.models.announcement import Announcement
from src.core.constants import FEED_PARAMS, ERROR_MESSAGES

class FeedProcessor(BaseProcessor):
    """Processor for EGP RSS feed"""
    
    def __init__(self):
        super().__init__()
        self.repository = AnnouncementRepository()
    
    @property
    def name(self) -> str:
        return "FeedProcessor"
    
    async def process(self, dept_id: str) -> Dict[str, Any]:
        """Process feed for department"""
        feed_content = await self._fetch_feed(dept_id)
        if not feed_content:
            return {"error": ERROR_MESSAGES["feed_unavailable"]}
        
        announcements = self._parse_feed(feed_content)
        processed = await self._process_announcements(announcements, dept_id)
        
        return {
            "processed": len(processed),
            "new": len([a for a in processed if a.get("is_new", False)]),
            "updated": len([a for a in processed if not a.get("is_new", False)])
        }
    
    async def _fetch_feed(self, dept_id: str) -> str:
        """Fetch feed content from EGP"""
        params = {
            FEED_PARAMS["dept_id"]: dept_id,
            FEED_PARAMS["count_by_day"]: ""
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/xml",
            "Accept-Language": "en-US,en;q=0.9,th;q=0.8"
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
                        return await response.text(encoding='utf-8')
                    else:
                        self.logger.error(
                            f"Feed request failed: {response.status}"
                        )
                        return None
        except Exception as e:
            self.logger.error(f"Error fetching feed: {e}")
            return None
    
    def _parse_feed(self, content: str) -> List[Dict[str, Any]]:
        """Parse XML feed content"""
        try:
            root = ET.fromstring(content)
            announcements = []
            
            for item in root.findall(".//item"):
                announcement = {
                    "title": self._get_text(item, "title"),
                    "link": self._get_text(item, "link"),
                    "description": self._get_text(item, "description"),
                    "published_date": self._parse_date(
                        self._get_text(item, "pubDate")
                    )
                }
                
                # Extract project_id from description
                if announcement["description"]:
                    parts = announcement["description"].split(",")
                    if parts:
                        announcement["project_id"] = parts[0].strip()
                
                announcements.append(announcement)
            
            return announcements
            
        except ET.ParseError as e:
            self.logger.error(f"Error parsing XML: {e}")
            return []
    
    def _get_text(self, element: ET.Element, tag: str) -> str:
        """Safely get element text"""
        child = element.find(tag)
        return child.text.strip() if child is not None and child.text else ""
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime"""
        try:
            return datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
        except (ValueError, TypeError):
            return datetime.now()
    
    async def _process_announcements(
        self,
        announcements: List[Dict[str, Any]],
        dept_id: str
    ) -> List[Dict[str, Any]]:
        """Process and store announcements"""
        results = []
        
        for data in announcements:
            try:
                # Create announcement instance
                announcement = Announcement(
                    project_id=data.get("project_id"),
                    title=data.get("title"),
                    link=data.get("link"),
                    description=data.get("description"),
                    dept_id=dept_id
                )
                
                # Check if announcement exists
                existing = self.repository.get_by_project_id(
                    announcement.project_id
                )
                
                # Store announcement
                saved = self.repository.upsert(announcement)
                
                if saved:
                    results.append({
                        "project_id": saved.project_id,
                        "is_new": not existing
                    })
                    
            except Exception as e:
                self.logger.error(
                    f"Error processing announcement {data.get('project_id')}: {e}"
                )
        
        return results