"""
Handler implementations.

This module provides implementations of the IHandler interface.
"""

import os
import sys
from typing import Any, Dict, Optional, TextIO

from core.logging.interfaces import IHandler, IFormatter
from core.logging.core.formatter import TextFormatter


class BaseHandler(IHandler):
    """Base handler implementation."""
    
    def __init__(self, formatter: Optional[IFormatter] = None):
        """
        Initialize a new handler.
        
        Args:
            formatter: The formatter to use
        """
        self._formatter = formatter or TextFormatter()
    
    def emit(self, record: Dict[str, Any]) -> None:
        """
        Emit a log record.
        
        Args:
            record: The log record to emit
        """
        # Format the record
        formatted_record = self._formatter.format(record)
        
        # Emit the formatted record
        self._emit_formatted_record(formatted_record, record)
    
    def set_formatter(self, formatter: IFormatter) -> None:
        """
        Set the formatter for this handler.
        
        Args:
            formatter: The formatter to use
        """
        self._formatter = formatter
    
    def close(self) -> None:
        """Close the handler and release any resources."""
    
    def _emit_formatted_record(self, formatted_record: str, original_record: Dict[str, Any]) -> None:
        """
        Emit a formatted record.
        
        Args:
            formatted_record: The formatted record
            original_record: The original record
        """
        raise NotImplementedError("Subclasses must implement this method")


class ConsoleHandler(BaseHandler):
    """Console handler implementation."""
    
    def __init__(
        self, 
        formatter: Optional[IFormatter] = None, 
        stream: TextIO = sys.stdout
    ):
        """
        Initialize a new console handler.
        
        Args:
            formatter: The formatter to use
            stream: The stream to write to
        """
        super().__init__(formatter)
        self._stream = stream
    
    def _emit_formatted_record(self, formatted_record: str, original_record: Dict[str, Any]) -> None:
        """
        Emit a formatted record to the console.
        
        Args:
            formatted_record: The formatted record
            original_record: The original record
        """
        print(formatted_record, file=self._stream)
    
    def close(self) -> None:
        """Close the handler and release any resources."""
        # Don't close stdout/stderr
        if self._stream not in (sys.stdout, sys.stderr):
            self._stream.close()


class FileHandler(BaseHandler):
    """File handler implementation."""
    
    def __init__(
        self, 
        filename: str, 
        formatter: Optional[IFormatter] = None, 
        mode: str = "a", 
        encoding: str = "utf-8"
    ):
        """
        Initialize a new file handler.
        
        Args:
            filename: The file to write to
            formatter: The formatter to use
            mode: The file mode
            encoding: The file encoding
        """
        super().__init__(formatter)
        self._filename = filename
        self._mode = mode
        self._encoding = encoding
        self._file = None
        self._open_file()
    
    def _open_file(self) -> None:
        """Open the log file."""
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(self._filename), exist_ok=True)
        
        # Open the file
        self._file = open(self._filename, self._mode, encoding=self._encoding)
    
    def _emit_formatted_record(self, formatted_record: str, original_record: Dict[str, Any]) -> None:
        """
        Emit a formatted record to the file.
        
        Args:
            formatted_record: The formatted record
            original_record: The original record
        """
        # Make sure the file is open
        if self._file is None or self._file.closed:
            self._open_file()
        
        # Write the record
        self._file.write(formatted_record + "\n")
        self._file.flush()
    
    def close(self) -> None:
        """Close the handler and release any resources."""
        if self._file is not None and not self._file.closed:
            self._file.close()
            self._file = None


class RotatingFileHandler(FileHandler):
    """Rotating file handler implementation."""
    
    def __init__(
        self, 
        filename: str, 
        formatter: Optional[IFormatter] = None, 
        mode: str = "a", 
        encoding: str = "utf-8", 
        max_bytes: int = 10 * 1024 * 1024,  # 10 MB
        backup_count: int = 5
    ):
        """
        Initialize a new rotating file handler.
        
        Args:
            filename: The file to write to
            formatter: The formatter to use
            mode: The file mode
            encoding: The file encoding
            max_bytes: The maximum file size in bytes
            backup_count: The number of backup files to keep
        """
        self._max_bytes = max_bytes
        self._backup_count = backup_count
        super().__init__(filename, formatter, mode, encoding)
    
    def _emit_formatted_record(self, formatted_record: str, original_record: Dict[str, Any]) -> None:
        """
        Emit a formatted record to the file, rotating if necessary.
        
        Args:
            formatted_record: The formatted record
            original_record: The original record
        """
        # Check if we need to rotate
        if self._should_rotate():
            self._rotate()
        
        # Write the record
        super()._emit_formatted_record(formatted_record, original_record)
    
    def _should_rotate(self) -> bool:
        """
        Check if the file should be rotated.
        
        Returns:
            True if the file should be rotated, False otherwise
        """
        if self._file is None or self._file.closed:
            return False
        
        # Get the file size
        try:
            file_size = os.path.getsize(self._filename)
            return file_size >= self._max_bytes
        except OSError:
            return False
    
    def _rotate(self) -> None:
        """Rotate the log files."""
        # Close the current file
        if self._file is not None and not self._file.closed:
            self._file.close()
            self._file = None
        
        # Rotate the backup files
        for i in range(self._backup_count - 1, 0, -1):
            src = f"{self._filename}.{i}"
            dst = f"{self._filename}.{i + 1}"
            
            if os.path.exists(src):
                if os.path.exists(dst):
                    os.remove(dst)
                os.rename(src, dst)
        
        # Rename the current file
        if os.path.exists(self._filename):
            dst = f"{self._filename}.1"
            if os.path.exists(dst):
                os.remove(dst)
            os.rename(self._filename, dst)
        
        # Open a new file
        self._open_file()


class NullHandler(BaseHandler):
    """Null handler implementation that discards all records."""
    
    def _emit_formatted_record(self, formatted_record: str, original_record: Dict[str, Any]) -> None:
        """
        Discard the formatted record.
        
        Args:
            formatted_record: The formatted record
            original_record: The original record
        """
