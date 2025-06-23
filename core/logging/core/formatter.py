"""
Formatter implementations.

This module provides implementations of the IFormatter interface.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict

from core.logging.interfaces import IFormatter


class BaseFormatter(IFormatter):
    """Base formatter implementation."""
    
    def __init__(self, timestamp_format: str = "%Y-%m-%d %H:%M:%S"):
        """
        Initialize a new formatter.
        
        Args:
            timestamp_format: The timestamp format
        """
        self._timestamp_format = timestamp_format
    
    def format(self, record: Dict[str, Any]) -> str:
        """
        Format a log record into a string.
        
        Args:
            record: The log record to format
            
        Returns:
            The formatted log record as a string
        """
        # Add timestamp if not present
        if "timestamp" not in record:
            record["timestamp"] = self._get_timestamp()
        
        return self._format_record(record)
    
    def _format_record(self, record: Dict[str, Any]) -> str:
        """
        Format a log record into a string.
        
        Args:
            record: The log record to format
            
        Returns:
            The formatted log record as a string
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def _get_timestamp(self) -> str:
        """
        Get the current timestamp.
        
        Returns:
            The current timestamp as a string
        """
        return datetime.now().strftime(self._timestamp_format)


class TextFormatter(BaseFormatter):
    """Text formatter implementation."""
    
    def __init__(
        self,
        timestamp_format: str = "%Y-%m-%d %H:%M:%S",
        template: str = "{timestamp} - {name} - {level_name} - {message}"
    ):
        """
        Initialize a new text formatter.
        
        Args:
            timestamp_format: The timestamp format
            template: The template string
        """
        super().__init__(timestamp_format)
        self._template = template
    
    def _format_record(self, record: Dict[str, Any]) -> str:
        """
        Format a log record into a string.
        
        Args:
            record: The log record to format
            
        Returns:
            The formatted log record as a string
        """
        # Format the basic message
        result = self._template.format(**record)
        
        # Add context if present
        if "context" in record and record["context"]:
            context_str = " ".join(f"{k}={v}" for k, v in record["context"].items())
            result = f"{result} - {context_str}"
        
        return result


class JsonFormatter(BaseFormatter):
    """JSON formatter implementation."""
    
    def _format_record(self, record: Dict[str, Any]) -> str:
        """
        Format a log record into a JSON string.
        
        Args:
            record: The log record to format
            
        Returns:
            The formatted log record as a JSON string
        """
        return json.dumps(record)


class ColoredFormatter(TextFormatter):
    """Colored text formatter implementation."""
    
    # ANSI color codes
    COLORS = {
        logging.DEBUG: "\033[36m",     # Cyan
        logging.INFO: "\033[32m",      # Green
        logging.WARNING: "\033[33m",   # Yellow
        logging.ERROR: "\033[31m",     # Red
        logging.CRITICAL: "\033[41m",  # Red background
    }
    RESET = "\033[0m"
    
    def __init__(
        self,
        timestamp_format: str = "%Y-%m-%d %H:%M:%S",
        template: str = "{timestamp} - {name} - {level_name} - {message}",
        use_colors: bool = True
    ):
        """
        Initialize a new colored formatter.
        
        Args:
            timestamp_format: The timestamp format
            template: The template string
            use_colors: Whether to use colors
        """
        super().__init__(timestamp_format, template)
        self._use_colors = use_colors
    
    def _format_record(self, record: Dict[str, Any]) -> str:
        """
        Format a log record into a colored string.
        
        Args:
            record: The log record to format
            
        Returns:
            The formatted log record as a colored string
        """
        # Get the basic formatted string
        result = super()._format_record(record)
        
        # Add colors if enabled
        if self._use_colors and "level" in record:
            level = record["level"]
            if level in self.COLORS:
                result = f"{self.COLORS[level]}{result}{self.RESET}"
        
        return result 