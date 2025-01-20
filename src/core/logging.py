import logging
import sys
from pathlib import Path

def setup_logging():
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "egp_pipeline.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

logger = logging.getLogger("egp_pipeline")
