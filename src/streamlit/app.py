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
from src.pipeline.orchestrator import PipelineOrchestrator
from src.core.logging import get_logger

logger = get_logger(__name__)

def load_latest_announcements(
    limit: int = 50, 
    dept_filter: str = None, 
    budget_min: float = None, 
    budget_max: float = None, 
    # submission_date_start: datetime = None, 
    # submission_date_end: datetime = None
):
    """Load latest announcements from database with advanced filtering"""
    with get_db() as conn:
        # Base query
        query = """
        SELECT 
            a.project_id,
            a.dept_id,
            a.title,
            a.submission_date,
            a.budget_amount
        FROM announcements a
        WHERE 1=1
        """
        
        # Prepare parameters and conditions
        params = []
        conditions = []
        
        # Department filter
        if dept_filter:
            conditions.append("a.dept_id = ?")
            params.append(dept_filter)
        
        # Budget range filter
        if budget_min is not None:
            conditions.append("a.budget_amount >= ?")
            params.append(budget_min)
        
        if budget_max is not None:
            conditions.append("a.budget_amount <= ?")
            params.append(budget_max)
        
        # # Submission date range filter
        # if submission_date_start:
        #     conditions.append("a.submission_date >= ?")
        #     params.append(submission_date_start)
        
        # if submission_date_end:
        #     conditions.append("a.submission_date <= ?")
        #     params.append(submission_date_end)
        
        # Combine conditions
        if conditions:
            query += " AND " + " AND ".join(conditions)
        
        # Execute query
        df = pd.read_sql_query(query, conn, params=params)
        
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

async def run_test_orchestrator():
    """Run the test orchestrator"""
    orchestrator = PipelineOrchestrator()
    test_departments = [
        "0703", "0708", "0806", "0807", "1507", "1509", 
        "2502", "S315", "S505", "S506", "S601"
    ]
    return await orchestrator.run(test_departments)

def run_orchestrator_and_update():
    """Run orchestrator and return results"""
    return asyncio.run(run_test_orchestrator())

def get_binary_file_downloader_html(bin_file, file_label='File'):
    """Generate download link for file"""
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{Path(bin_file).name}">Download {file_label}</a>'
    return href

def show_announcement_tab():
    """Show announcements list tab with advanced filtering"""
    st.subheader("Procurement Announcements")
    
    # Add pipeline controls to sidebar
    st.sidebar.header("Pipeline Controls")
    
    # Add run pipeline button
    if st.sidebar.button("🚀 Run Pipeline"):
        with st.sidebar.status("Running pipeline...", expanded=True) as status:
            try:
                results = run_orchestrator_and_update()
                
                # Display results
                st.sidebar.success("Pipeline completed successfully!")
                
                # Show summary statistics
                st.sidebar.markdown("### Pipeline Results")
                for dept_id, dept_results in results.get('details', {}).items():
                    st.sidebar.markdown(f"**Department {dept_id}:**")
                    
                    # FeedProcessor results
                    feed_results = dept_results.get('FeedProcessor', {}).get('result', {})
                    if feed_results:
                        st.sidebar.markdown(f"- Announcements processed: {feed_results.get('processed', 0)}")
                        st.sidebar.markdown(f"- New entries: {feed_results.get('new', 0)}")
                    
                    # PDFProcessor results
                    pdf_results = dept_results.get('PDFProcessor', {}).get('result', {})
                    if pdf_results:
                        st.sidebar.markdown(f"- PDFs processed: {pdf_results.get('processed', 0)}")
                
                # Automatically refresh the page after pipeline completes
                status.update(label="Refreshing page...", state="complete", expanded=False)
                st.rerun()
                
            except Exception as e:
                st.sidebar.error(f"Error running pipeline: {str(e)}")
    
    # Add refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        st.rerun()
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Department filter
    with get_db() as conn:
        departments = pd.read_sql_query(
            "SELECT DISTINCT dept_id FROM announcements", 
            conn
        )['dept_id'].tolist()
    
    dept_filter = st.sidebar.selectbox(
        "Filter by Department", 
        options=['All'] + departments,
        index=0
    )
    
    # Budget range filter
    with get_db() as conn:
        budget_stats = pd.read_sql_query(
            "SELECT MIN(budget_amount) as min_budget, MAX(budget_amount) as max_budget FROM announcements", 
            conn
        )
    
    min_budget = budget_stats['min_budget'].iloc[0] or 0
    max_budget = budget_stats['max_budget'].iloc[0] or 1000000
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        budget_min = st.number_input(
            "Min Budget", 
            min_value=min_budget, 
            max_value=max_budget, 
            value=min_budget
        )
    with col2:
        budget_max = st.number_input(
            "Max Budget", 
            min_value=min_budget, 
            max_value=max_budget, 
            value=max_budget
        )
    
    # Submission date range filter
    # with get_db() as conn:
    #     date_range = pd.read_sql_query(
    #         "SELECT MIN(submission_date) as min_date, MAX(submission_date) as max_date FROM announcements", 
    #         conn
    #     )
    
    # min_date = pd.to_datetime(date_range['min_date'].iloc[0]) or datetime.now()
    # max_date = pd.to_datetime(date_range['max_date'].iloc[0]) or datetime.now()
    
    # submission_date_start = st.sidebar.date_input(
    #     "Submission Date Start", 
    #     value=min_date.date(),
    #     min_value=min_date.date(),
    #     max_value=max_date.date()
    # )
    # submission_date_end = st.sidebar.date_input(
    #     "Submission Date End", 
    #     value=max_date.date(),
    #     min_value=min_date.date(),
    #     max_value=max_date.date()
    # )
    
    # Prepare filters
    dept_param = dept_filter if dept_filter != 'All' else None
    
    # Load data with filters
    df = load_latest_announcements(
        limit=50,
        dept_filter=dept_param,
        budget_min=budget_min,
        budget_max=budget_max,
        # submission_date_start=submission_date_start,
        # submission_date_end=submission_date_end
    )
    
    # Show last refresh time
    st.sidebar.write(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Show summary stats in sidebar
    st.sidebar.subheader("Summary Statistics")
    st.sidebar.write(f"Total rows: {len(df)}")
    st.sidebar.write(f"Unique departments: {df['dept_id'].nunique()}")
    
    # Main data display
    st.dataframe(
        df,
        use_container_width=True,
        column_config={
            "project_id": "Project ID",
            "dept_id": "Department",
            "title": "Title",
            # "status": "Status",
            # "created_at": "Created",
            # "updated_at": "Updated",
            "submission_date": "Submission Date",
            "budget_amount": "Budget Amount (THB)"
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
                # Create file buttons layout
                st.write("Available Documents:")
                
                # Create columns for button grid
                cols = st.columns(3)  # Show 3 buttons per row
                
                # Sort files by modification time
                files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                
                # Create buttons for each file
                selected_file = None
                for idx, file in enumerate(files):
                    col_idx = idx % 3
                    with cols[col_idx]:
                        file_name = file.relative_to(project_dir)
                        
                        # Get file icon based on type
                        file_type = file.suffix.lower()
                        if file_type == '.pdf':
                            icon = "📄"
                        elif file_type in ['.jpg', '.jpeg', '.png', '.gif']:
                            icon = "🖼️"
                        elif file_type in ['.xlsx', '.xls']:
                            icon = "📊"
                        elif file_type == '.docx':
                            icon = "📝"
                        else:
                            icon = "📎"
                        
                        # Create button with icon and file info
                        if st.button(
                            f"{icon} {file_name}\n{file.stat().st_size / 1024:.1f} KB",
                            key=f"file_{idx}"
                        ):
                            selected_file = file_name
                
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