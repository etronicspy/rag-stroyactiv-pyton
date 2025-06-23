"""
Async worker implementation.

This module provides a worker for asynchronous log processing.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from core.logging.interfaces import IHandler
from core.logging.optimized.async_logging.batch_processor import BatchProcessor


class AsyncWorker:
    """
    Worker for asynchronous log processing.
    
    This worker manages the lifecycle of batch processors and provides a high-level interface
    for asynchronous logging.
    """
    
    def __init__(
        self,
        handlers: Optional[List[IHandler]] = None,
        batch_size: int = 100,
        flush_interval: float = 0.5,
        worker_count: int = 1,
        error_logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize a new asynchronous worker.
        
        Args:
            handlers: The handlers for processing logs
            batch_size: The batch size for processing logs
            flush_interval: The flush interval in seconds
            worker_count: The number of worker tasks
            error_logger: The logger for error reporting
        """
        self._handlers = handlers or []
        self._batch_size = batch_size
        self._flush_interval = flush_interval
        self._worker_count = worker_count
        self._error_logger = error_logger or logging.getLogger("async_worker")
        
        # Create a batch processor
        self._processor = BatchProcessor(
            batch_size=batch_size,
            flush_interval=flush_interval,
            worker_count=worker_count,
            handlers=handlers,
            error_logger=error_logger,
        )
        
        self._running = False
        self._background_task = None
        self._stats_task = None
        self._stats_interval = 60.0  # 1 minute
        self._stats: Dict[str, Any] = {}
    
    async def start(self) -> None:
        """Start the asynchronous worker."""
        if self._running:
            return
        
        self._running = True
        
        # Start the batch processor
        await self._processor.start()
        
        # Start the statistics task
        self._stats_task = asyncio.create_task(self._collect_stats())
    
    async def stop(self) -> None:
        """Stop the asynchronous worker."""
        if not self._running:
            return
        
        self._running = False
        
        # Stop the statistics task
        if self._stats_task:
            self._stats_task.cancel()
            try:
                await self._stats_task
            except asyncio.CancelledError:
                pass
            self._stats_task = None
        
        # Stop the batch processor
        await self._processor.stop()
    
    async def process(self, log_entry: Dict[str, Any]) -> None:
        """
        Process a log entry.
        
        Args:
            log_entry: The log entry to process
        """
        await self._processor.process(log_entry)
    
    def process_sync(self, log_entry: Dict[str, Any]) -> None:
        """
        Process a log entry synchronously.
        
        Args:
            log_entry: The log entry to process
        """
        self._processor.process_sync(log_entry)
    
    async def flush(self) -> None:
        """Flush all pending logs."""
        await self._processor.flush()
    
    def add_handler(self, handler: IHandler) -> None:
        """
        Add a handler to the worker.
        
        Args:
            handler: The handler to add
        """
        if handler not in self._handlers:
            self._handlers.append(handler)
            self._processor.add_handler(handler)
    
    def remove_handler(self, handler: IHandler) -> None:
        """
        Remove a handler from the worker.
        
        Args:
            handler: The handler to remove
        """
        if handler in self._handlers:
            self._handlers.remove(handler)
            self._processor.remove_handler(handler)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the worker.
        
        Returns:
            Statistics about the worker
        """
        return {
            **self._stats,
            **self._processor.get_stats(),
        }
    
    def reset_stats(self) -> None:
        """Reset statistics."""
        self._stats = {}
        self._processor.reset_stats()
    
    async def _collect_stats(self) -> None:
        """Collect statistics periodically."""
        while self._running:
            try:
                # Get processor stats
                processor_stats = self._processor.get_stats()
                
                # Calculate derived metrics
                current_time = time.time()
                
                # Update stats
                self._stats = {
                    "timestamp": current_time,
                    "uptime": time.time() - current_time,
                    **processor_stats,
                }
                
                # Log stats if there's activity
                if processor_stats["processed_count"] > 0 or processor_stats["error_count"] > 0:
                    self._error_logger.debug(f"AsyncWorker stats: {self._stats}")
            except Exception as e:
                self._error_logger.error(f"Error collecting stats: {e}", exc_info=True)
            
            # Sleep until the next collection
            await asyncio.sleep(self._stats_interval)
    
    @staticmethod
    def create_background_worker(
        handlers: Optional[List[IHandler]] = None,
        batch_size: int = 100,
        flush_interval: float = 0.5,
        worker_count: int = 1,
        error_logger: Optional[logging.Logger] = None,
    ) -> 'AsyncWorker':
        """
        Create and start a worker in a background thread.
        
        Args:
            handlers: The handlers for processing logs
            batch_size: The batch size for processing logs
            flush_interval: The flush interval in seconds
            worker_count: The number of worker tasks
            error_logger: The logger for error reporting
            
        Returns:
            The created worker
        """
        worker = AsyncWorker(
            handlers=handlers,
            batch_size=batch_size,
            flush_interval=flush_interval,
            worker_count=worker_count,
            error_logger=error_logger,
        )
        
        # Create a new event loop in a background thread
        thread = threading.Thread(target=AsyncWorker._run_worker, args=(worker,), daemon=True)
        thread.start()
        
        return worker
    
    @staticmethod
    def _run_worker(worker: 'AsyncWorker') -> None:
        """
        Run a worker in a background thread.
        
        Args:
            worker: The worker to run
        """
        # Create a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Start the worker
            loop.run_until_complete(worker.start())
            
            # Run the event loop
            loop.run_forever()
        except Exception as e:
            if worker._error_logger:
                worker._error_logger.error(f"Error in worker thread: {e}", exc_info=True)
        finally:
            # Stop the worker
            if worker._running:
                loop.run_until_complete(worker.stop())
            
            # Close the event loop
            loop.close()


# Import at the end to avoid circular imports
import threading 