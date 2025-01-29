# src/streamlit/app.py

import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.core.config import config
from src.db.session import get_db

def load_latest_announcements(limit: int = 50):
    """Load latest announcements from database"""
    with get_db() as conn:
        query = """
        SELECT 
            project_id,
            dept_id,
            title,
            status,
            created_at,
            updated_at
        FROM announcements 
        ORDER BY created_at DESC
        LIMIT ?
        """
        
        df = pd.read_sql_query(query, conn, params=(limit,))
        
        # Format datetime columns
        for col in ['created_at', 'updated_at']:
            df[col] = pd.to_datetime(df[col])
        
        return df

# Set page config
st.set_page_config(
    page_title="EGP Announcements",
    page_icon="📊",
    layout="wide"
)

# Title
st.title("EGP Announcements Dashboard")
st.subheader("Latest 50 Announcements")

# Load data
df = load_latest_announcements(50)

# Show last refresh time
st.sidebar.write(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Show summary stats in sidebar
st.sidebar.subheader("Summary Statistics")
st.sidebar.write(f"Total rows: {len(df)}")
st.sidebar.write(f"Unique departments: {df['dept_id'].nunique()}")
st.sidebar.write("Status counts:")
st.sidebar.dataframe(df['status'].value_counts())

# Show date range
if not df.empty:
    newest = df['created_at'].max().strftime('%Y-%m-%d %H:%M:%S')
    oldest = df['created_at'].min().strftime('%Y-%m-%d %H:%M:%S')
    st.sidebar.write(f"Date range: {oldest} to {newest}")

# Main data display
st.dataframe(
    df,
    use_container_width=True,
    column_config={
        "project_id": "Project ID",
        "dept_id": "Department",
        "title": "Title",
        "status": "Status",
        "created_at": "Created",
        "updated_at": "Updated"
    }
)