from loguru import logger
import os
import sys

logger.remove()
logger.add(sys.stdout, level=os.environ.get("LOG_LEVEL", "INFO"))

__all__ = ["logger"]
