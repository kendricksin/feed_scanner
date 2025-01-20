import uvicorn
from src.db.session import init_db
from src.core.config import config
from src.core.logging import logger

if __name__ == "__main__":
    try:
        # Initialize database
        init_db()
        logger.info("Database initialized")
        
        # Start API server
        uvicorn.run(
            "src.api.app:app",
            host=config.api_host,
            port=config.api_port,
            reload=True
        )
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise