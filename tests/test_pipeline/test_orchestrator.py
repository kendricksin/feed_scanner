# tests/test_pipeline/test_orchestrator.py

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import json

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.pipeline.orchestrator import PipelineOrchestrator
from src.db.session import init_db, get_db
from src.core.constants import Status, DEPARTMENTS
from src.core.logging import get_logger

logger = get_logger(__name__)

def save_test_results(results: dict, output_file: Path):
    """Save test results to a JSON file"""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Test results saved to {output_file}")

async def test_pipeline_orchestrator(
    test_departments: list[str] = None, 
    output_dir: Path = None
):
    """
    Comprehensive test of the pipeline orchestrator
    
    Args:
        test_departments: List of department IDs to test. 
                          If None, uses all configured departments.
        output_dir: Directory to save test results
    """
    # Initialize output directory
    if output_dir is None:
        output_dir = project_root / "data" / "test_results" / datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    # Determine departments to test
    if test_departments is None:
        test_departments = list(DEPARTMENTS.keys())
    
    logger.info(f"Testing departments: {test_departments}")
    
    try:
        # Create orchestrator
        orchestrator = PipelineOrchestrator()
        
        # Run pipeline
        start_time = datetime.now()
        results = await orchestrator.run(test_departments)
        
        # Validate results
        logger.info("Validating pipeline results...")
        
        # Comprehensive result validation
        validation_results = {
            "summary": results,
            "department_details": {}
        }
        
        # Check database for processed announcements
        with get_db() as conn:
            cursor = conn.cursor()
            
            for dept_id in test_departments:
                # Check announcements for each department
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_announcements,
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_announcements,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_announcements,
                        COUNT(CASE WHEN pdf_path IS NOT NULL THEN 1 END) as pdf_processed
                    FROM announcements
                    WHERE dept_id = ?
                """, (dept_id,))
                
                dept_stats = cursor.fetchone()
                
                validation_results["department_details"][dept_id] = {
                    "total_announcements": dept_stats['total_announcements'],
                    "completed_announcements": dept_stats['completed_announcements'],
                    "failed_announcements": dept_stats['failed_announcements'],
                    "pdf_processed": dept_stats['pdf_processed']
                }
        
        # Save results
        if output_dir:
            save_test_results(validation_results, output_dir / "orchestrator_test_results.json")
        
        # Logging and assertions
        logger.info("Pipeline Orchestrator Test Completed")
        logger.info(f"Total Departments Processed: {results['departments']}")
        logger.info(f"Pipeline Status: {results['status']}")
        logger.info(f"Total Execution Time: {results.get('execution_time', 'N/A')} seconds")
        
        # Basic validation assertions
        assert results['status'] == Status.COMPLETED, "Pipeline did not complete successfully"
        assert results['departments'] > 0, "No departments were processed"
        
        return validation_results
        
    except Exception as e:
        logger.error(f"Orchestrator test failed: {e}")
        raise

def main():
    """Run the orchestrator test"""
    # You can configure specific departments to test here
    test_departments = [
            "0703", # กรมชลประทาน
            "0708",  # กรมพัฒนาที่ดิน
            "1507", # กรมโยธาธิการและผังเมือง
            "1509", # กรุงเทพมหานคร
            # "0204", # กองทัพบก
            # "0205", # กองทัพเรือ
            # "0206", # กองทัพอากาศ
            # "0207", # กองทัพไทย
            # "S312", # การรถไฟแห่งประเทศไทย
            # "S504", # การไฟฟ้าฝ่ายผลิตแห่งปทท
            # "S505", # การไฟฟ้านครหลวง
            # "S506" # การไฟฟ้าส่วนภูมิภาค
            ]
    
    logger.info(f"Starting Orchestrator Test at {datetime.now()}")
    test_results = asyncio.run(test_pipeline_orchestrator(
        test_departments=test_departments
    ))
    
    # Print out department-wise details
    for dept, details in test_results['department_details'].items():
        print(f"\nDepartment {dept} Results:")
        print(f"Total Announcements: {details['total_announcements']}")
        print(f"Completed Announcements: {details['completed_announcements']}")
        print(f"Failed Announcements: {details['failed_announcements']}")
        print(f"PDFs Processed: {details['pdf_processed']}")

if __name__ == "__main__":
    main()