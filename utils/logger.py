import sys
from loguru import logger
from config import settings

LOG_FILE_PATH = "mcp.log" 

def setup_logger():
    logger.remove()

    if settings.APP_ENV == "production":
        logger.add(
            sys.stdout,
            level=settings.LOG_LEVEL.upper(),
            format="{message}",
            serialize=True,
            colorize=False
        )
    else:
        logger.add(
            sys.stderr,
            level=settings.LOG_LEVEL.upper(),
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
            colorize=True
        )
        logger.add(
            LOG_FILE_PATH,
            level="DEBUG",
            format="{message}",
            serialize=True,
            rotation="10 MB",
            retention="7 days"
        )
        logger.info(f"Dev logger initialized. JSON output is in '{LOG_FILE_PATH}'")


    return logger

log = setup_logger()