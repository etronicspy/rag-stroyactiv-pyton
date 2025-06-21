"""
Dependency injection for the logging system.

This module provides dependency injection utilities for the logging system.
"""

from .container import LoggingContainer, get_container

__all__ = [
    "LoggingContainer",
    "get_container"
] 