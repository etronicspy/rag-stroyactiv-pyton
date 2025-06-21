"""
Async logger implementation.

This module provides an asynchronous logger implementation that offloads logging to a background task.
"""

import asyncio
import logging
import threading
from typing import Any, Dict, Optional, Union

from core.logging.interfaces import ILogger, IHandler
from core.logging.core import Logger
from core.logging.optimized.async_logging.logging_queue import LoggingQueue


class AsyncLogger(Logger):
    """
    Asynchronous logger implementation.
    
    This logger offloads logging operations to a background task to avoid blocking the main thread.
    """
    
    def __init__(
        self,
        name: str,
        level: Union[int, str] = logging.INFO,
        handlers: Optional[list[IHandler]] = None,
        queue: Optional[LoggingQueue] = None,
        max_queue_size: int = 1000,
        worker_count: int = 1,
        flush_interval: float = 0.1,
        batch_size: int = 100,
    ):
        """
        Initialize a new asynchronous logger.
        
        Args:
            name: The logger name
            level: The log level
            handlers: The handlers for the logger
            queue: The logging queue to use
            max_queue_size: The maximum queue size
            worker_count: The number of worker tasks
            flush_interval: The flush interval in seconds
            batch_size: The batch size for processing logs
        """
        super().__init__(name, level, handlers)
        
        self._queue = queue or LoggingQueue(max_size=max_queue_size)
        self._worker_count = worker_count
        self._flush_interval = flush_interval
        self._batch_size = batch_size
        self._workers: list[asyncio.Task] = []
        self._running = False
        self._loop = None
        
        # For synchronous usage
        self._thread = None
        self._sync_loop = None
    
    async def start(self) -> None:
        """Start the asynchronous logger."""
        if self._running:
            return
        
        self._running = True
        self._loop = asyncio.get_running_loop()
        
        # Start worker tasks
        for _ in range(self._worker_count):
            worker = self._loop.create_task(self._worker_task())
            self._workers.append(worker)
    
    async def stop(self) -> None:
        """Stop the asynchronous logger."""
        if not self._running:
            return
        
        self._running = False
        
        # Wait for all workers to complete
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)
            self._workers = []
        
        # Flush remaining logs
        await self._process_batch(self._queue.get_all())
    
    def start_sync(self) -> None:
        """Start the asynchronous logger in synchronous mode."""
        if self._running:
            return
        
        self._running = True
        self._sync_loop = asyncio.new_event_loop()
        
        # Start a background thread for the event loop
        self._thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._thread.start()
    
    def stop_sync(self) -> None:
        """Stop the asynchronous logger in synchronous mode."""
        if not self._running or not self._sync_loop:
            return
        
        # Schedule the stop task
        asyncio.run_coroutine_threadsafe(self.stop(), self._sync_loop)
        
        # Wait for the thread to complete
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None
        
        # Close the event loop
        if self._sync_loop:
            self._sync_loop.close()
            self._sync_loop = None
        
        self._running = False
    
    def _run_event_loop(self) -> None:
        """Run the event loop in a background thread."""
        asyncio.set_event_loop(self._sync_loop)
        
        # Start worker tasks
        for _ in range(self._worker_count):
            worker = self._sync_loop.create_task(self._worker_task())
            self._workers.append(worker)
        
        # Run the event loop
        self._sync_loop.run_forever()
    
    async def _worker_task(self) -> None:
        """Worker task for processing logs from the queue."""
        while self._running:
            # Get a batch of logs from the queue
            batch = await self._queue.get_batch(self._batch_size, self._flush_interval)
            
            if batch:
                # Process the batch
                await self._process_batch(batch)
            
            # Small sleep to avoid tight loop
            await asyncio.sleep(0.001)
    
    async def _process_batch(self, batch: list[Dict[str, Any]]) -> None:
        """
        Process a batch of logs.
        
        Args:
            batch: The batch of logs to process
        """
        for log_entry in batch:
            # Extract log information
            level = log_entry["level"]
            message = log_entry["message"]
            args = log_entry.get("args", ())
            kwargs = log_entry.get("kwargs", {})
            
            # Call the parent log method directly
            super().log(level, message, *args, **kwargs)
    
    def log(self, level: int, message: str, *args: Any, **kwargs: Any) -> None:
        """
        Log a message.
        
        Args:
            level: The log level
            message: The log message
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        # Skip if the level is too low
        if level < self.level:
            return
        
        # Create a log entry
        log_entry = {
            "level": level,
            "message": message,
            "args": args,
            "kwargs": kwargs,
        }
        
        # Add to the queue
        self._queue.put(log_entry)
    
    def __del__(self) -> None:
        """Clean up resources."""
        if self._running:
            if self._sync_loop:
                self.stop_sync()
            elif self._loop:
                # This is not ideal, but we need to ensure resources are cleaned up
                try:
                    asyncio.run_coroutine_threadsafe(self.stop(), self._loop)
                except:
                    pass 