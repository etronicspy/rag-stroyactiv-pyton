"""
Logging queue implementation.

This module provides a queue for asynchronous logging.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional


class LoggingQueue:
    """
    Queue for asynchronous logging.
    
    This queue is used to store log entries for asynchronous processing.
    """
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize a new logging queue.
        
        Args:
            max_size: The maximum queue size
        """
        self._queue: List[Dict[str, Any]] = []
        self._max_size = max_size
        self._lock = asyncio.Lock()
        self._not_empty = asyncio.Condition(self._lock)
        self._overflow_count = 0
    
    async def put(self, item: Dict[str, Any]) -> None:
        """
        Add an item to the queue.
        
        Args:
            item: The item to add
        """
        async with self._lock:
            # Check if the queue is full
            if len(self._queue) >= self._max_size:
                # Increment the overflow count
                self._overflow_count += 1
                return
            
            # Add the item to the queue
            self._queue.append(item)
            
            # Notify waiters
            self._not_empty.notify()
    
    def put_nowait(self, item: Dict[str, Any]) -> None:
        """
        Add an item to the queue without waiting.
        
        Args:
            item: The item to add
        """
        # Check if the queue is full
        if len(self._queue) >= self._max_size:
            # Increment the overflow count
            self._overflow_count += 1
            return
        
        # Add the item to the queue
        self._queue.append(item)
    
    async def get(self) -> Optional[Dict[str, Any]]:
        """
        Get an item from the queue.
        
        Returns:
            An item from the queue, or None if the queue is empty
        """
        async with self._lock:
            # Wait for an item
            await self._not_empty.wait_for(lambda: len(self._queue) > 0)
            
            # Get the item
            return self._queue.pop(0) if self._queue else None
    
    def get_nowait(self) -> Optional[Dict[str, Any]]:
        """
        Get an item from the queue without waiting.
        
        Returns:
            An item from the queue, or None if the queue is empty
        """
        if not self._queue:
            return None
        
        return self._queue.pop(0)
    
    async def get_batch(self, batch_size: int, timeout: float = 0.1) -> List[Dict[str, Any]]:
        """
        Get a batch of items from the queue.
        
        Args:
            batch_size: The maximum batch size
            timeout: The timeout in seconds
            
        Returns:
            A batch of items from the queue
        """
        batch = []
        start_time = time.time()
        
        async with self._lock:
            # Wait for at least one item or timeout
            try:
                await asyncio.wait_for(
                    self._not_empty.wait_for(lambda: len(self._queue) > 0),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                # Timeout occurred, return an empty batch
                return []
            
            # Get items up to the batch size
            while self._queue and len(batch) < batch_size:
                batch.append(self._queue.pop(0))
        
        return batch
    
    def get_all(self) -> List[Dict[str, Any]]:
        """
        Get all items from the queue.
        
        Returns:
            All items from the queue
        """
        items = self._queue
        self._queue = []
        return items
    
    def size(self) -> int:
        """
        Get the current queue size.
        
        Returns:
            The current queue size
        """
        return len(self._queue)
    
    def get_overflow_count(self) -> int:
        """
        Get the overflow count.
        
        Returns:
            The number of items that were dropped due to queue overflow
        """
        return self._overflow_count
    
    def reset_overflow_count(self) -> None:
        """Reset the overflow count."""
        self._overflow_count = 0
    
    def clear(self) -> None:
        """Clear the queue."""
        self._queue = [] 