# src/db/repositories/base.py

from typing import TypeVar, Generic, Optional, List, Type
from datetime import datetime
import sqlite3
import asyncio
from contextlib import asynccontextmanager
from src.core.logging import get_logger

T = TypeVar('T')

class BaseRepository(Generic[T]):
    """Base repository with common database operations"""
    MAX_RETRIES = 3
    RETRY_DELAY = 0.1  # seconds
    _write_lock = asyncio.Lock()  # Changed to Lock instead of Semaphore

    def __init__(self, model_class: Type[T], table_name: str):
        self.model_class = model_class
        self.table_name = table_name
        self.conn = None
        self.logger = get_logger(self.__class__.__name__)

    async def execute_query(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute SQL query with retries"""
        retries = 0
        last_error = None
        
        while retries < self.MAX_RETRIES:
            try:
                cursor = self.conn.cursor()
                cursor.execute(query, params)
                return cursor
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    last_error = e
                    retries += 1
                    if retries < self.MAX_RETRIES:
                        await asyncio.sleep(self.RETRY_DELAY * (2 ** retries))
                        continue
                raise
            except Exception as e:
                self.logger.error(f"Query execution error: {e}")
                self.logger.error(f"Query: {query}")
                self.logger.error(f"Params: {params}")
                raise
                
        self.logger.error(f"Max retries reached. Last error: {last_error}")
        raise last_error

    async def execute_write_query(self, query: str, params: tuple = ()):
        """Execute write query with locking"""
        async with self._write_lock:
            try:
                cursor = await self.execute_query(query, params)
                self.conn.commit()
                return cursor
            except Exception as e:
                self.conn.rollback()
                raise

    async def get_by_id(self, id: int) -> Optional[T]:
        """Get single record by ID"""
        query = f"SELECT * FROM {self.table_name} WHERE id = ?"
        cursor = await self.execute_query(query, (id,))
        row = cursor.fetchone()
        return self.model_class.from_dict(dict(row)) if row else None

    async def get_all(self) -> List[T]:
        """Get all records"""
        query = f"SELECT * FROM {self.table_name}"
        cursor = await self.execute_query(query)
        return [self.model_class.from_dict(dict(row)) for row in cursor.fetchall()]

    async def create(self, model: T) -> Optional[T]:
        """Create new record"""
        data = model.to_dict()
        if 'id' in data:
            del data['id']
        
        columns = ', '.join(data.keys())
        placeholders = ', '.join('?' * len(data))
        query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        
        cursor = await self.execute_write_query(query, tuple(data.values()))
        if cursor and cursor.lastrowid:
            return await self.get_by_id(cursor.lastrowid)
        return None

    async def update(self, model: T) -> Optional[T]:
        """Update existing record"""
        data = model.to_dict()
        if 'id' not in data:
            raise ValueError("Cannot update model without ID")
        
        id_value = data.pop('id')
        if 'created_at' in data:
            del data['created_at']
        
        data['updated_at'] = datetime.now()
        
        set_clause = ', '.join(f"{k} = ?" for k in data.keys())
        query = f"UPDATE {self.table_name} SET {set_clause} WHERE id = ?"
        
        values = list(data.values()) + [id_value]
        await self.execute_write_query(query, tuple(values))
        return await self.get_by_id(id_value)

    async def delete(self, id: int) -> bool:
        """Delete record by ID"""
        query = f"DELETE FROM {self.table_name} WHERE id = ?"
        cursor = await self.execute_write_query(query, (id,))
        return cursor.rowcount > 0

    async def find_by(self, **kwargs) -> List[T]:
        """Find records by arbitrary conditions"""
        conditions = ' AND '.join(f"{k} = ?" for k in kwargs.keys())
        query = f"SELECT * FROM {self.table_name} WHERE {conditions}"
        
        cursor = await self.execute_query(query, tuple(kwargs.values()))
        return [self.model_class.from_dict(dict(row)) for row in cursor.fetchall()]

    @asynccontextmanager
    async def transaction(self):
        """Async transaction context manager"""
        async with self._write_lock:
            try:
                yield self
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise