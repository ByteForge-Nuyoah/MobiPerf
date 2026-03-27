import sys
import os
from loguru import logger
from datetime import datetime

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{extra[request_id]}</cyan> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

LOG_FORMAT_SIMPLE = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
    "{level: <8} | "
    "{extra[request_id]} | "
    "{name}:{function}:{line} | "
    "{message}"
)

def setup_logging(log_level: str = "INFO", enable_file_log: bool = True):
    logger.remove()
    
    logger.add(
        sys.stdout,
        format=LOG_FORMAT,
        level=log_level,
        colorize=True,
        filter=lambda record: record["extra"].setdefault("request_id", "-") or True
    )
    
    if enable_file_log:
        today = datetime.now().strftime("%Y-%m-%d")
        
        logger.add(
            f"{LOG_DIR}/mobiperf_{today}.log",
            format=LOG_FORMAT_SIMPLE,
            level=log_level,
            rotation="00:00",
            retention="30 days",
            compression="zip",
            encoding="utf-8",
            filter=lambda record: record["extra"].setdefault("request_id", "-") or True
        )
        
        logger.add(
            f"{LOG_DIR}/error_{today}.log",
            format=LOG_FORMAT_SIMPLE,
            level="ERROR",
            rotation="00:00",
            retention="30 days",
            compression="zip",
            encoding="utf-8",
            filter=lambda record: record["extra"].setdefault("request_id", "-") or True
        )
    
    logger.info(f"Logging configured: level={log_level}, file_logging={enable_file_log}")
    
    return logger

def get_logger_with_request_id(request_id: str):
    return logger.bind(request_id=request_id)

class RequestContext:
    _current_request_id: str = "-"
    
    @classmethod
    def set_request_id(cls, request_id: str):
        cls._current_request_id = request_id
    
    @classmethod
    def get_request_id(cls) -> str:
        return cls._current_request_id
    
    @classmethod
    def clear_request_id(cls):
        cls._current_request_id = "-"
