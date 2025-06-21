"""
Batch processor implementation.

This module provides a processor for batched log processing.
"""

import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Union

from core.logging.interfaces import IHandler
from core.logging.optimized.async_logging.logging_queue import LoggingQueue


class BatchProcessor:
    """
    Processor for batched log processing.
    
    This processor processes logs in batches for improved performance.
    """
    
    def __init__(
        self,
        queue: Optional[LoggingQueue] = None,
        batch_size: int = 100,
        flush_interval: float = 0.5,
        worker_count: int = 1,
        handlers: Optional[List[IHandler]] = None,
        error_logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize a new batch processor.
        
        Args:
            queue: The logging queue to use
            batch_size: The batch size for processing logs
            flush_interval: The flush interval in seconds
            worker_count: The number of worker tasks
            handlers: The handlers for processing logs
            error_logger: The logger for error reporting
        """
        self._queue = queue or LoggingQueue()
        self._batch_size = batch_size
        self._flush_interval = flush_interval
        self._worker_count = worker_count
        self._handlers = handlers or []
        self._error_logger = error_logger or logging.getLogger("batch_processor")
        
        self._workers: List[asyncio.Task] = []
        self._running = False
        self._last_flush_time = 0.0
        self._processed_count = 0
        self._error_count = 0
    
    async def start(self) -> None:
        """Start the batch processor."""
        if self._running:
            return
        
        self._running = True
        self._last_flush_time = time.time()
        
        # Start worker tasks
        for _ in range(self._worker_count):
            worker = asyncio.create_task(self._worker_task())
            self._workers.append(worker)
    
    async def stop(self) -> None:
        """Stop the batch processor."""
        if not self._running:
            return
        
        self._running = False
        
        # Wait for all workers to complete
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)
            self._workers = []
        
        # Process any remaining logs
        await self._process_batch(self._queue.get_all())
    
    async def process(self, log_entry: Dict[str, Any]) -> None:
        """
        Process a log entry.
        
        Args:
            log_entry: The log entry to process
        """
        await self._queue.put(log_entry)
    
    def process_sync(self, log_entry: Dict[str, Any]) -> None:
        """
        Process a log entry synchronously.
        
        Args:
            log_entry: The log entry to process
        """
        self._queue.put_nowait(log_entry)
    
    async def flush(self) -> None:
        """Flush all pending logs."""
        await self._process_batch(self._queue.get_all())
        self._last_flush_time = time.time()
    
    async def _worker_task(self) -> None:
        """Worker task for processing logs from the queue."""
        while self._running:
            try:
                # Check if it's time to flush
                current_time = time.time()
                if current_time - self._last_flush_time >= self._flush_interval:
                    # Get all logs and process them
                    batch = self._queue.get_all()
                    if batch:
                        await self._process_batch(batch)
                    self._last_flush_time = current_time
                else:
                    # Get a batch of logs from the queue
                    batch = await self._queue.get_batch(
                        self._batch_size,
                        timeout=min(self._flush_interval, 0.1)
                    )
                    
                    if batch:
                        # Process the batch
                        await self._process_batch(batch)
            except Exception as e:
                # Log the error
                self._error_count += 1
                self._error_logger.error(f"Error in batch processor: {e}", exc_info=True)
            
            # Small sleep to avoid tight loop
            await asyncio.sleep(0.001)
    
    async def _process_batch(self, batch: List[Dict[str, Any]]) -> None:
        """
        Process a batch of logs.
        
        Args:
            batch: The batch of logs to process
        """
        if not batch:
            return
        
        try:
            # Process each log entry with all handlers
            for handler in self._handlers:
                for log_entry in batch:
                    try:
                        # Extract log information
                        record = self._create_log_record(log_entry)
                        
                        # Process with handler
                        if handler.level <= record.levelno:
                            handler.handle(record)
                    except Exception as e:
                        # Log the error
                        self._error_count += 1
                        self._error_logger.error(
                            f"Error processing log entry with handler {handler}: {e}",
                            exc_info=True
                        )
            
            # Update processed count
            self._processed_count += len(batch)
        except Exception as e:
            # Log the error
            self._error_count += 1
            self._error_logger.error(f"Error processing batch: {e}", exc_info=True)
    
    def _create_log_record(self, log_entry: Dict[str, Any]) -> logging.LogRecord:
        """
        Create a log record from a log entry.
        
        Args:
            log_entry: The log entry
            
        Returns:
            A log record
        """
        # Extract log information
        level = log_entry["level"]
        message = log_entry["message"]
        args = log_entry.get("args", ())
        kwargs = log_entry.get("kwargs", {})
        extra = kwargs.get("extra", {})
        
        # Create a log record
        record = logging.LogRecord(
            name=kwargs.get("name", ""),
            level=level,
            pathname=extra.get("pathname", ""),
            lineno=extra.get("lineno", 0),
            msg=message,
            args=args,
            exc_info=kwargs.get("exc_info"),
            func=extra.get("funcName", ""),
            sinfo=extra.get("stack_info")
        )
        
        # Add extra attributes
        for key, value in extra.items():
            setattr(record, key, value)
        
        return record
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the batch processor.
        
        Returns:
            Statistics about the batch processor
        """
        return {
            "processed_count": self._processed_count,
            "error_count": self._error_count,
            "queue_size": self._queue.size(),
            "queue_overflow_count": self._queue.get_overflow_count(),
            "running": self._running,
            "worker_count": len(self._workers),
        }
    
    def reset_stats(self) -> None:
        """Reset statistics."""
        self._processed_count = 0
        self._error_count = 0
        self._queue.reset_overflow_count()
    
    def add_handler(self, handler: IHandler) -> None:
        """
        Add a handler to the batch processor.
        
        Args:
            handler: The handler to add
        """
        if handler not in self._handlers:
            self._handlers.append(handler)
    
    def remove_handler(self, handler: IHandler) -> None:
        """
        Remove a handler from the batch processor.
        
        Args:
            handler: The handler to remove
        """
        if handler in self._handlers:
            self._handlers.remove(handler) 