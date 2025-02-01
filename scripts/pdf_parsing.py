# scripts/analyze_pdfs.py

import argparse
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import PyPDF2
from openai import OpenAI
import os
import sys
from dotenv import load_dotenv
from datetime import datetime

# Configure UTF-8 encoding for output streams
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

class UTFFormatter(logging.Formatter):
    """Custom formatter that ensures proper UTF-8 encoding"""
    def format(self, record):
        # Ensure message is a string
        if isinstance(record.msg, (dict, list)):
            record.msg = json.dumps(record.msg, ensure_ascii=False, indent=2)
        return super().format(record)

def setup_logging():
    """Set up logging with proper UTF-8 encoding"""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Clear any existing handlers
    logger.handlers = []

    # Console handler with UTF-8 encoding
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(UTFFormatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)

    # File handler with UTF-8 encoding
    file_handler = logging.FileHandler('pdf_analysis.log', encoding='utf-8')
    file_handler.setFormatter(UTFFormatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)

    return logger

# Load environment variables
load_dotenv()

# Initialize logging
logger = setup_logging()

# Initialize OpenAI client
client = OpenAI(
        api_key=os.getenv('OPENAI_API_KEY'), 
        base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    )

# The prompt template for GPT
ANALYSIS_PROMPT = """
Your task is to analyze project announcements and return it in a structured JSON format.

Please extract the following information if available:
- document_title: title of the pdf document (in Thai)
- เรื่อง: long project title (in Thai)
- department_name: Name of the department (in Thai)
- budget_amount: The budget amount in Thai Baht (as float)
- announcement_date: Announcement date (YYYY-MM-DD Buddhist calendar)
- submission_date: (YYYY-MM-DD Buddhist calendar)
- contact:
-- phone: (Arabic integers)
-- email: (String)

Return only the JSON object with these fields. If a field is not found, set it to null.
Here's the document text:

{text}
"""

def extract_text_from_pdf(pdf_path: Path) -> Optional[str]:
    """Extract text content from a PDF file."""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ''
            for page in reader.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path}: {e}")
        return None

def analyze_text_with_gpt(text: str) -> Optional[Dict[str, Any]]:
    """Send text to OpenAI API and get structured response."""
    try:
        # Prepare the prompt
        prompt = ANALYSIS_PROMPT.format(text=text)
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="qwen-turbo", 
            messages=[
                {"role": "system", "content": "You are a procurement document analyzer. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}  # Enforce JSON response
        )
        
        # Parse the response
        response_text = response.choices[0].message.content
        return json.loads(response_text)
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        logger.error(f"Raw response: {response_text}")
        return None
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        return None

def process_pdf(pdf_path: Path) -> None:
    """Process a single PDF file."""
    project_id = pdf_path.stem
    
    # Extract text
    text = extract_text_from_pdf(pdf_path)
    if not text:
        logger.error(f"{project_id}.pdf: Failed to extract text")
        return
    
    # Analyze with GPT
    result = analyze_text_with_gpt(text)
    if not result:
        logger.error(f"{project_id}.pdf: Failed to analyze text")
        return
    
    # Save result
    save_result(project_id, result)
    logger.info(f"{project_id}.pdf: Parsed successfully")

def process_directory(directory: Path) -> None:
    """Process all PDF files in a directory."""
    pdf_files = list(directory.glob('*.pdf'))
    total = len(pdf_files)
    logger.info(f"Found {total} PDF files")
    
    for i, pdf_path in enumerate(pdf_files, 1):
        logger.info(f"Processing file {i}/{total}")
        process_pdf(pdf_path)

RESULTS_FILE = "pdf_analysis_results.json"

def load_existing_results() -> Dict[str, Any]:
    """Load existing results from JSON file"""
    try:
        if Path(RESULTS_FILE).exists():
            with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading existing results: {e}")
    return {}

def save_result(project_id: str, result: Dict[str, Any]) -> None:
    """Save result to JSON file"""
    try:
        # Load existing results
        results = load_existing_results()
        
        # Add new result with timestamp
        results[project_id] = {
            "data": result,
            "parsed_at": datetime.now().isoformat()
        }
        
        # Write to temporary file first
        temp_file = f"{RESULTS_FILE}.tmp"
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # Rename temporary file to actual file (atomic operation)
        os.replace(temp_file, RESULTS_FILE)
        
    except Exception as e:
        logger.error(f"Error saving results: {e}")
        if os.path.exists(temp_file):
            os.remove(temp_file)

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Analyze procurement PDFs using OpenAI')
    parser.add_argument('path', type=str, help='Path to PDF file or directory')
    args = parser.parse_args()

    if not os.getenv('OPENAI_API_KEY'):
        logger.error("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
        return
    
    path = Path(args.path)
    
    if not path.exists():
        logger.error(f"Path does not exist: {path}")
        return
    
    if path.is_file():
        if path.suffix.lower() != '.pdf':
            logger.error(f"Not a PDF file: {path}")
            return
        process_pdf(path)
    elif path.is_dir():
        process_directory(path)
    else:
        logger.error(f"Invalid path type: {path}")

if __name__ == "__main__":
    main()