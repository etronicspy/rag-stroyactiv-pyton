"""
Log formatters for different output formats.

Provides structured JSON formatting and colored console output.
Extracted and refactored from core/monitoring/logger.py.
"""

import logging
import json
from datetime import datetime
from typing import List

from .interfaces import FormatterInterface


class StructuredFormatter(FormatterInterface, logging.Formatter):
    """JSON structured log formatter for production environments."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON structure."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # 🔧 OPTIMIZED: Use list comprehension for performance
        extra_fields = [
            'correlation_id', 'database_type', 'operation', 'duration_ms',
            'record_count', 'error_details', 'user_id', 'request_id'
        ]
        
        for field in extra_fields:
            if hasattr(record, field):
                log_data[field] = getattr(record, field)
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_data, ensure_ascii=False)


class BaseColorFormatter(logging.Formatter):
    """Base formatter with color support functionality."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green  
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def colorize_level(self, record: logging.LogRecord) -> str:
        """Colorize log level name."""
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        return f"{color}{record.levelname:<8s}{reset}"


class ColoredFormatter(BaseColorFormatter, FormatterInterface):
    """Colored formatter for beautiful terminal output."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format record with colors."""
        # Create a copy to avoid modifying the original record
        colored_record = logging.makeLogRecord(record.__dict__)
        colored_record.levelname = self.colorize_level(record)
        return super().format(colored_record) 