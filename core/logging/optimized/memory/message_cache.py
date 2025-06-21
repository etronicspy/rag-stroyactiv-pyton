"""
Message cache implementation.

This module provides a cache for log messages to avoid duplicating strings in memory.
"""

import threading
import time
from typing import Dict, Any, Optional, Tuple, List


class MessageCache:
    """
    Cache for log messages.
    
    This cache stores log messages to avoid duplicating strings in memory.
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        ttl: float = 300.0,
        cleanup_interval: float = 60.0,
    ):
        """
        Initialize a new message cache.
        
        Args:
            max_size: The maximum cache size
            ttl: The time-to-live for cache entries in seconds
            cleanup_interval: The interval for cache cleanup in seconds
        """
        self._cache: Dict[str, Tuple[str, float, int]] = {}
        self._max_size = max_size
        self._ttl = ttl
        self._cleanup_interval = cleanup_interval
        self._lock = threading.RLock()
        self._last_cleanup = time.time()
        self._hit_count = 0
        self._miss_count = 0
    
    def get(self, message: str) -> str:
        """
        Get a message from the cache.
        
        Args:
            message: The message to get
            
        Returns:
            The cached message or the original message
        """
        with self._lock:
            # Check if cleanup is needed
            current_time = time.time()
            if current_time - self._last_cleanup >= self._cleanup_interval:
                self._cleanup(current_time)
            
            # Check if the message exists in the cache
            if message in self._cache:
                # Update hit count
                self._hit_count += 1
                
                # Get the message and update access time and count
                cached_message, _, access_count = self._cache[message]
                self._cache[message] = (cached_message, current_time, access_count + 1)
                
                return cached_message
            
            # Update miss count
            self._miss_count += 1
            
            # Check if the cache is full
            if len(self._cache) >= self._max_size:
                # Remove the least recently used message
                self._remove_lru_message()
            
            # Add to the cache
            self._cache[message] = (message, current_time, 1)
            
            return message
    
    def clear(self) -> None:
        """Clear the cache."""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache.
        
        Returns:
            Statistics about the cache
        """
        with self._lock:
            hit_rate = 0.0
            if self._hit_count + self._miss_count > 0:
                hit_rate = self._hit_count / (self._hit_count + self._miss_count)
            
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hit_count": self._hit_count,
                "miss_count": self._miss_count,
                "hit_rate": hit_rate,
                "last_cleanup": self._last_cleanup,
            }
    
    def reset_stats(self) -> None:
        """Reset statistics."""
        with self._lock:
            self._hit_count = 0
            self._miss_count = 0
    
    def _cleanup(self, current_time: float) -> None:
        """
        Clean up expired cache entries.
        
        Args:
            current_time: The current time
        """
        # Find expired entries
        expired_keys = [
            key for key, (_, access_time, _) in self._cache.items()
            if current_time - access_time > self._ttl
        ]
        
        # Remove expired entries
        for key in expired_keys:
            del self._cache[key]
        
        # Update last cleanup time
        self._last_cleanup = current_time
    
    def _remove_lru_message(self) -> None:
        """Remove the least recently used message from the cache."""
        if not self._cache:
            return
        
        # Find the least recently used message
        lru_key = None
        lru_time = float('inf')
        
        for key, (_, access_time, _) in self._cache.items():
            if access_time < lru_time:
                lru_key = key
                lru_time = access_time
        
        # Remove the least recently used message
        if lru_key is not None:
            del self._cache[lru_key]


class StructuredLogCache:
    """
    Cache for structured log entries.
    
    This cache stores structured log entries to avoid duplicating data in memory.
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        ttl: float = 300.0,
        cleanup_interval: float = 60.0,
    ):
        """
        Initialize a new structured log cache.
        
        Args:
            max_size: The maximum cache size
            ttl: The time-to-live for cache entries in seconds
            cleanup_interval: The interval for cache cleanup in seconds
        """
        self._message_cache = MessageCache(max_size, ttl, cleanup_interval)
        self._cache: Dict[str, Tuple[Dict[str, Any], float, int]] = {}
        self._max_size = max_size
        self._ttl = ttl
        self._cleanup_interval = cleanup_interval
        self._lock = threading.RLock()
        self._last_cleanup = time.time()
        self._hit_count = 0
        self._miss_count = 0
    
    def get(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a log entry from the cache.
        
        Args:
            log_entry: The log entry to get
            
        Returns:
            The cached log entry or a new log entry with cached strings
        """
        # Create a cache key
        cache_key = self._create_cache_key(log_entry)
        
        with self._lock:
            # Check if cleanup is needed
            current_time = time.time()
            if current_time - self._last_cleanup >= self._cleanup_interval:
                self._cleanup(current_time)
            
            # Check if the log entry exists in the cache
            if cache_key in self._cache:
                # Update hit count
                self._hit_count += 1
                
                # Get the log entry and update access time and count
                cached_entry, _, access_count = self._cache[cache_key]
                self._cache[cache_key] = (cached_entry, current_time, access_count + 1)
                
                return cached_entry
            
            # Update miss count
            self._miss_count += 1
            
            # Check if the cache is full
            if len(self._cache) >= self._max_size:
                # Remove the least recently used log entry
                self._remove_lru_entry()
            
            # Create a new log entry with cached strings
            new_entry = self._create_cached_entry(log_entry)
            
            # Add to the cache
            self._cache[cache_key] = (new_entry, current_time, 1)
            
            return new_entry
    
    def clear(self) -> None:
        """Clear the cache."""
        with self._lock:
            self._cache.clear()
            self._message_cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache.
        
        Returns:
            Statistics about the cache
        """
        with self._lock:
            hit_rate = 0.0
            if self._hit_count + self._miss_count > 0:
                hit_rate = self._hit_count / (self._hit_count + self._miss_count)
            
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hit_count": self._hit_count,
                "miss_count": self._miss_count,
                "hit_rate": hit_rate,
                "last_cleanup": self._last_cleanup,
                "message_cache": self._message_cache.get_stats(),
            }
    
    def reset_stats(self) -> None:
        """Reset statistics."""
        with self._lock:
            self._hit_count = 0
            self._miss_count = 0
            self._message_cache.reset_stats()
    
    def _create_cache_key(self, log_entry: Dict[str, Any]) -> str:
        """
        Create a cache key for a log entry.
        
        Args:
            log_entry: The log entry
            
        Returns:
            A cache key
        """
        # Simple implementation: use the message as the key
        return str(log_entry.get("message", ""))
    
    def _create_cached_entry(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new log entry with cached strings.
        
        Args:
            log_entry: The log entry
            
        Returns:
            A new log entry with cached strings
        """
        # Create a new log entry
        new_entry = {}
        
        # Cache strings in the log entry
        for key, value in log_entry.items():
            if isinstance(value, str):
                new_entry[key] = self._message_cache.get(value)
            else:
                new_entry[key] = value
        
        return new_entry
    
    def _cleanup(self, current_time: float) -> None:
        """
        Clean up expired cache entries.
        
        Args:
            current_time: The current time
        """
        # Find expired entries
        expired_keys = [
            key for key, (_, access_time, _) in self._cache.items()
            if current_time - access_time > self._ttl
        ]
        
        # Remove expired entries
        for key in expired_keys:
            del self._cache[key]
        
        # Update last cleanup time
        self._last_cleanup = current_time
    
    def _remove_lru_entry(self) -> None:
        """Remove the least recently used log entry from the cache."""
        if not self._cache:
            return
        
        # Find the least recently used log entry
        lru_key = None
        lru_time = float('inf')
        
        for key, (_, access_time, _) in self._cache.items():
            if access_time < lru_time:
                lru_key = key
                lru_time = access_time
        
        # Remove the least recently used log entry
        if lru_key is not None:
            del self._cache[lru_key]


# Singleton instances
_default_message_cache: Optional[MessageCache] = None
_default_structured_log_cache: Optional[StructuredLogCache] = None
_cache_lock = threading.RLock()


def get_default_message_cache() -> MessageCache:
    """
    Get the default message cache.
    
    Returns:
        The default message cache
    """
    global _default_message_cache
    
    with _cache_lock:
        if _default_message_cache is None:
            _default_message_cache = MessageCache()
        
        return _default_message_cache


def get_default_structured_log_cache() -> StructuredLogCache:
    """
    Get the default structured log cache.
    
    Returns:
        The default structured log cache
    """
    global _default_structured_log_cache
    
    with _cache_lock:
        if _default_structured_log_cache is None:
            _default_structured_log_cache = StructuredLogCache()
        
        return _default_structured_log_cache 