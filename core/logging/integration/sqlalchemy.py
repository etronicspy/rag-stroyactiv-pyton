"""
SQLAlchemy integration implementation.

This module provides integration with SQLAlchemy.
"""

import logging
import time
from typing import Any, Callable, Dict, List, Optional, Union, cast

from sqlalchemy.engine import Engine
from sqlalchemy.event import listen
from sqlalchemy.orm import Session

from core.logging.config import get_configuration
from core.logging.interfaces import ILogger
from core.logging.specialized.database import SqlLogger


class SQLAlchemyEventListener:
    """
    Event listener for SQLAlchemy.
    
    This listener logs SQLAlchemy events.
    """
    
    def __init__(
        self,
        logger: Optional[ILogger] = None,
        sql_logger: Optional[SqlLogger] = None,
    ):
        """
        Initialize a new SQLAlchemy event listener.
        
        Args:
            logger: The logger to use
            sql_logger: The SQL logger to use
        """
        # Get configuration
        config = get_configuration()
        database_settings = config.get_database_settings()
        
        # Create logger if not provided
        self._logger = logger or logging.getLogger("sqlalchemy")
        
        # Create SQL logger if not provided
        self._sql_logger = sql_logger or SqlLogger(
            logger=self._logger,
            log_queries=database_settings["log_sql_queries"],
            log_parameters=database_settings["log_sql_parameters"],
            slow_query_threshold_ms=database_settings["slow_query_threshold_ms"],
        )
        
        # Set enabled flag
        self._enabled = database_settings["enable_database_logging"]
    
    def register(self, engine: Engine) -> None:
        """
        Register the event listener with an engine.
        
        Args:
            engine: The SQLAlchemy engine
        """
        # Skip registration if disabled
        if not self._enabled:
            return
        
        # Register before_cursor_execute event
        listen(engine, "before_cursor_execute", self._before_cursor_execute)
        
        # Register after_cursor_execute event
        listen(engine, "after_cursor_execute", self._after_cursor_execute)
    
    def _before_cursor_execute(
        self,
        conn: Any,
        cursor: Any,
        statement: str,
        parameters: Dict[str, Any],
        context: Any,
        executemany: bool,
    ) -> None:
        """
        Handle before_cursor_execute event.
        
        Args:
            conn: The connection
            cursor: The cursor
            statement: The SQL statement
            parameters: The parameters
            context: The context
            executemany: Whether to execute many
        """
        # Store start time in context
        context._logging_start_time = time.time()
    
    def _after_cursor_execute(
        self,
        conn: Any,
        cursor: Any,
        statement: str,
        parameters: Dict[str, Any],
        context: Any,
        executemany: bool,
    ) -> None:
        """
        Handle after_cursor_execute event.
        
        Args:
            conn: The connection
            cursor: The cursor
            statement: The SQL statement
            parameters: The parameters
            context: The context
            executemany: Whether to execute many
        """
        # Calculate duration
        duration_ms = (time.time() - getattr(context, "_logging_start_time", time.time())) * 1000
        
        # Log query
        self._sql_logger.log_query(statement, parameters, duration_ms, executemany)


class SessionExtension:
    """
    Extension for SQLAlchemy Session.
    
    This extension logs Session operations.
    """
    
    def __init__(
        self,
        session: Session,
        logger: Optional[ILogger] = None,
        sql_logger: Optional[SqlLogger] = None,
    ):
        """
        Initialize a new Session extension.
        
        Args:
            session: The SQLAlchemy Session
            logger: The logger to use
            sql_logger: The SQL logger to use
        """
        # Store session
        self._session = session
        
        # Get configuration
        config = get_configuration()
        database_settings = config.get_database_settings()
        
        # Create logger if not provided
        self._logger = logger or logging.getLogger("sqlalchemy")
        
        # Create SQL logger if not provided
        self._sql_logger = sql_logger or SqlLogger(
            logger=self._logger,
            log_queries=database_settings["log_sql_queries"],
            log_parameters=database_settings["log_sql_parameters"],
            slow_query_threshold_ms=database_settings["slow_query_threshold_ms"],
        )
        
        # Set enabled flag
        self._enabled = database_settings["enable_database_logging"]
        
        # Patch session methods
        self._patch_session()
    
    def _patch_session(self) -> None:
        """Patch session methods."""
        # Skip patching if disabled
        if not self._enabled:
            return
        
        # Patch commit method
        original_commit = self._session.commit
        
        def commit_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Start timer
            start_time = time.time()
            
            try:
                # Call original method
                result = original_commit(*args, **kwargs)
                
                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000
                
                # Log commit
                self._sql_logger.log_operation("commit", None, duration_ms)
                
                return result
            except Exception as e:
                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000
                
                # Log exception
                self._sql_logger.log_exception("commit", None, e, duration_ms)
                
                # Re-raise exception
                raise
        
        # Replace method
        self._session.commit = commit_wrapper  # type: ignore
        
        # Patch rollback method
        original_rollback = self._session.rollback
        
        def rollback_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Start timer
            start_time = time.time()
            
            try:
                # Call original method
                result = original_rollback(*args, **kwargs)
                
                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000
                
                # Log rollback
                self._sql_logger.log_operation("rollback", None, duration_ms)
                
                return result
            except Exception as e:
                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000
                
                # Log exception
                self._sql_logger.log_exception("rollback", None, e, duration_ms)
                
                # Re-raise exception
                raise
        
        # Replace method
        self._session.rollback = rollback_wrapper  # type: ignore
        
        # Patch flush method
        original_flush = self._session.flush
        
        def flush_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Start timer
            start_time = time.time()
            
            try:
                # Call original method
                result = original_flush(*args, **kwargs)
                
                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000
                
                # Log flush
                self._sql_logger.log_operation("flush", None, duration_ms)
                
                return result
            except Exception as e:
                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000
                
                # Log exception
                self._sql_logger.log_exception("flush", None, e, duration_ms)
                
                # Re-raise exception
                raise
        
        # Replace method
        self._session.flush = flush_wrapper  # type: ignore


def setup_logging(engine: Engine) -> None:
    """
    Set up logging for a SQLAlchemy engine.
    
    Args:
        engine: The SQLAlchemy engine
    """
    # Create event listener
    listener = SQLAlchemyEventListener()
    
    # Register event listener
    listener.register(engine)


def session_logging(session: Session) -> SessionExtension:
    """
    Set up logging for a SQLAlchemy Session.
    
    Args:
        session: The SQLAlchemy Session
        
    Returns:
        SessionExtension: The session extension
    """
    # Create session extension
    return SessionExtension(session) 