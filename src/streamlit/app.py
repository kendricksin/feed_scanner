# src/streamlit/app.py

import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime
import base64
from streamlit_pdf_viewer import pdf_viewer
import docx2txt
import fitz  # PyMuPDF
from PIL import Image
import io
import asyncio

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.core.config import config
from src.db.session import get_db
from src.pipeline.processors.document import DocumentProcessor
from src.core.logging import get_logger

logger = get_logger(__name__)

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

def create_test_announcement(project_id: str):
    """Create a test announcement record if it doesn't exist"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if announcement exists
        cursor.execute(
            "SELECT * FROM announcements WHERE project_id = ?",
            (project_id,)
        )
        if cursor.fetchone():
            return False
            
        # Create new announcement
        announcement_link = f"https://process3.gprocurement.go.th/egp2procmainWeb/procsearch.sch?announceType=2&servlet=FPRO9965Servlet&proc_id=FPRO9965_1&proc_name=Procure&processFlows=Procure&mode=LINK&homeflag=A&temp_projectId={project_id}"
        
        cursor.execute("""
            INSERT INTO announcements (
                project_id,
                title,
                link,
                description,
                status,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id,
            f"Test Announcement {project_id}",
            announcement_link,
            "Test Description",
            "pending",
            datetime.now(),
            datetime.now()
        ))
        conn.commit()
        return True

def get_binary_file_downloader_html(bin_file, file_label='File'):
    """Generate download link for file"""
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{Path(bin_file).name}">Download {file_label}</a>'
    return href

def show_announcement_tab():
    """Show announcements list tab"""
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

async def show_document_tab():
    """Show document management tab"""
    st.subheader("Project Document Management")
    
    # Project ID input
    project_id = st.text_input("Enter Project ID")
    
    if project_id:
        # Check/create announcement
        is_new = create_test_announcement(project_id)
        if is_new:
            st.success(f"Created new test announcement for project {project_id}")
        
        # Initialize document processor
        doc_processor = DocumentProcessor()
        
        # Check project directory
        project_dir = config.base_dir / "data" / "projects" / project_id
        
        if not project_dir.exists():
            st.warning("Project documents not found. Attempting to fetch...")
            try:
                # Fetch document info
                doc_info = await doc_processor._fetch_document_info(project_id)
                
                if doc_info and doc_info.get("zipId"):
                    # Process ZIP file
                    project_dir = await doc_processor._process_zip_file(
                        project_id,
                        doc_info["zipId"]
                    )
                    if project_dir:
                        st.success("Documents downloaded successfully!")
                    else:
                        st.error("Failed to process documents")
                else:
                    st.error("No documents found for this project")
            except Exception as e:
                st.error(f"Error fetching documents: {str(e)}")
        
        # Show document preview if directory exists
        if project_dir.exists():
            st.subheader("Project Documents")
            
            # List all files
            files = list(project_dir.rglob('*'))
            files = [f for f in files if f.is_file()]
            
            if files:
                # Create file selection
                file_names = [f.relative_to(project_dir) for f in files]
                selected_file = st.selectbox(
                    "Select document to preview",
                    options=file_names,
                    format_func=str
                )
                
                if selected_file:
                    selected_path = project_dir / selected_file
                    
                    # Show file info
                    st.write(f"File size: {selected_path.stat().st_size / 1024:.2f} KB")
                    st.write(f"Last modified: {datetime.fromtimestamp(selected_path.stat().st_mtime)}")
                    
                    # Generate download link
                    st.markdown(
                        get_binary_file_downloader_html(selected_path, selected_file),
                        unsafe_allow_html=True
                    )
                    
                    # Preview based on file type
                    try:
                        if selected_path.suffix.lower() in ['.txt', '.csv', '.md']:
                            with open(selected_path, 'r', encoding='utf-8', errors='replace') as f:
                                st.text_area("File Preview", f.read(), height=300)
                        
                        elif selected_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
                            # Enhanced image preview with PIL
                            with Image.open(selected_path) as img:
                                # Get image info
                                st.write(f"Image dimensions: {img.size}")
                                st.write(f"Image mode: {img.mode}")
                                # Display image
                                st.image(img, caption=f"Preview of {selected_file}")
                        
                        elif selected_path.suffix.lower() == '.pdf':
                            
                            # Show number of pages using PyMuPDF
                            with fitz.open(selected_path) as doc:
                                num_pages = len(doc)
                                st.write(f"Number of pages: {num_pages}")
                            
                            # Initial annotations - could be loaded from a database or generated
                            annotations = [
                                {
                                    "x": 100,
                                    "y": 100,
                                    "height": 5,
                                    "width": 16,
                                    "color": "red"
                                }
                            ]
                            
                            # Show PDF using the component
                            pdf_viewer(
                                str(selected_path),  # Path to PDF file
                                annotations=annotations
                            )
                            
                            # Add download button
                            with open(selected_path, "rb") as f:
                                st.download_button(
                                    "Download PDF",
                                    f,
                                    file_name=selected_path.name,
                                    mime="application/pdf"
                                )
                        
                        elif selected_path.suffix.lower() == '.docx':
                            # Preview Word documents
                            text = docx2txt.process(selected_path)
                            st.text_area("Document Preview", text, height=300)
                        
                        elif selected_path.suffix.lower() in ['.xlsx', '.xls']:
                            # Preview Excel files
                            df = pd.read_excel(selected_path)
                            st.dataframe(df)
                        
                        else:
                            st.warning("Preview not available for this file type. Please download to view.")

                    except Exception as e:
                        st.error(f"Error previewing file: {str(e)}")

            else:
                st.info("No files found in project directory")

# Set page config
st.set_page_config(
    page_title="EGP Announcements",
    page_icon="📊",
    layout="wide"
)

# Title
st.title("EGP Announcements Dashboard")

# Create tabs
tab1, tab2 = st.tabs(["Announcements", "Document Management"])

# Show content based on selected tab
with tab1:
    show_announcement_tab()
with tab2:
    asyncio.run(show_document_tab())