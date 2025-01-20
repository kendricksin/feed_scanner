# src/db/repositories/base.py

from typing import TypeVar, Generic, Optional, List, Dict, Any
from datetime import datetime
from ..session import get_db
from src.core.logging import get_logger
import sqlite3

T = TypeVar('T')

class BaseRepository(Generic[T]):
    def __init__(self, model_class: T):
        self.model_class = model_class
        self.logger = get_logger(__name__)
        
    def _execute_query(self, query: str, params: tuple = ()) -> Optional[sqlite3.Cursor]:
        """Execute SQL query and handle errors"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor
        except Exception as e:
            self.logger.error(f"Query execution error: {e}")
            self.logger.error(f"Query: {query}")
            self.logger.error(f"Params: {params}")
            raise
    
    def get_by_id(self, id: int) -> Optional[T]:
        """Get single record by ID"""
        query = f"SELECT * FROM {self.table_name} WHERE id = ?"
        cursor = self._execute_query(query, (id,))
        row = cursor.fetchone()
        return self.model_class.from_dict(dict(row)) if row else None
    
    def get_all(self) -> List[T]:
        """Get all records"""
        query = f"SELECT * FROM {self.table_name}"
        cursor = self._execute_query(query)
        return [self.model_class.from_dict(dict(row)) for row in cursor.fetchall()]
    
    def create(self, model: T) -> Optional[T]:
        """Create new record"""
        data = model.to_dict()
        if 'id' in data:
            del data['id']  # Remove ID for insertion
            
        columns = ', '.join(data.keys())
        placeholders = ', '.join('?' * len(data))
        query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        
        cursor = self._execute_query(query, tuple(data.values()))
        if cursor and cursor.lastrowid:
            return self.get_by_id(cursor.lastrowid)
        return None
    
    def update(self, model: T) -> Optional[T]:
        """Update existing record"""
        data = model.to_dict()
        if 'id' not in data:
            raise ValueError("Cannot update model without ID")
            
        id_value = data.pop('id')
        if 'created_at' in data:
            del data['created_at']  # Don't update created_at
            
        # Always update updated_at
        data['updated_at'] = datetime.now()
        
        set_clause = ', '.join(f"{k} = ?" for k in data.keys())
        query = f"UPDATE {self.table_name} SET {set_clause} WHERE id = ?"
        
        values = list(data.values()) + [id_value]
        self._execute_query(query, tuple(values))
        return self.get_by_id(id_value)
    
    def delete(self, id: int) -> bool:
        """Delete record by ID"""
        query = f"DELETE FROM {self.table_name} WHERE id = ?"
        cursor = self._execute_query(query, (id,))
        return cursor.rowcount > 0
    
    def find_by(self, **kwargs) -> List[T]:
        """Find records by arbitrary conditions"""
        conditions = ' AND '.join(f"{k} = ?" for k in kwargs.keys())
        query = f"SELECT * FROM {self.table_name} WHERE {conditions}"
        
        cursor = self._execute_query(query, tuple(kwargs.values()))
        return [self.model_class.from_dict(dict(row)) for row in cursor.fetchall()]