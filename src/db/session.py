import sqlite3
from contextlib import contextmanager
from pathlib import Path

@contextmanager
def get_db():
    db_path = Path("data/egp.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(db_path))
    try:
        yield conn
    finally:
        conn.close()
