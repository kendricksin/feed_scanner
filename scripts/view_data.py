# scripts/view_data.py

import sys
from pathlib import Path
import pandas as pd
import sqlite3
import argparse

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.core.logging import get_logger
from src.core.config import config
from src.db.session import get_db

logger = get_logger(__name__)

def view_announcements(limit: int = 20):
    """View last X announcements from database
    
    Args:
        limit (int): Number of most recent rows to display
    """
    try:
        # Get database connection
        with get_db() as conn:
            # Create query with parameterized limit
            query = """
            SELECT *
            FROM announcements 
            ORDER BY created_at DESC
            LIMIT ?
            """
            
            # Read into pandas DataFrame
            df = pd.read_sql_query(query, conn, params=(limit,))
            
            if df.empty:
                logger.info("No announcements found in database!")
                return
            
            # Format datetime columns
            for col in ['created_at', 'updated_at']:
                df[col] = pd.to_datetime(df[col])
                df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Limit title length for display
            df['title'] = df['title'].str.slice(0, 50) + '...'
            
            # Set display options for pandas
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', None)
            pd.set_option('display.max_colwidth', None)
            
            # Log DataFrame
            logger.info(f"\nLast {limit} announcements in database:")
            logger.info("\n" + str(df))
            
            # Log summary stats
            logger.info("\nSummary statistics:")
            logger.info(f"Total rows displayed: {len(df)}")
            logger.info(f"Unique departments: {df['dept_id'].nunique()}")
            logger.info("\nStatus counts:")
            logger.info(df['status'].value_counts().to_string())
            
            # Show date range
            if len(df) > 0:
                newest = df['created_at'].iloc[0]
                oldest = df['created_at'].iloc[-1]
                logger.info(f"\nDate range: {oldest} to {newest}")
            
    except Exception as e:
        logger.error(f"Error viewing announcements: {e}")
        raise

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='View recent announcements from database')
    parser.add_argument('limit', 
                       type=int,
                       nargs='?',  # Make argument optional
                       default=20, 
                       help='Number of rows to display (default: 20)')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    # Validate input
    if args.limit <= 0:
        logger.error("Limit must be a positive number")
        sys.exit(1)
    
    logger.info(f"Fetching last {args.limit} announcements...")
    view_announcements(args.limit)