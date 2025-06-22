"""
SQL logger implementation.

This module provides a logger for SQL operations.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Union

from core.logging.specialized.database.database_logger import DatabaseLogger, AsyncDatabaseLogger


class SqlLogger(DatabaseLogger):
    """Logger for SQL operations."""
    
    def __init__(
        self,
        name: str,
        db_type: str = "postgresql",
        level: Union[int, str] = logging.INFO,
        mask_sensitive_data: bool = True,
        log_parameters: bool = True,
        max_query_length: int = 1000
    ):
        """
        Initialize a new SQL logger.
        
        Args:
            name: The logger name
            db_type: The database type (e.g., 'postgresql', 'mysql')
            level: The log level
            mask_sensitive_data: Whether to mask sensitive data in queries
            log_parameters: Whether to log query parameters
            max_query_length: The maximum query length to log
        """
        super().__init__(name, db_type, level)
        self._mask_sensitive_data = mask_sensitive_data
        self._log_parameters = log_parameters
        self._max_query_length = max_query_length
    
    def log_query(
        self,
        query: str,
        duration_ms: float,
        parameters: Optional[Union[Dict[str, Any], List[Any], tuple]] = None,
        record_count: Optional[int] = None,
        affected_rows: Optional[int] = None,
        success: bool = True,
        error: Optional[Exception] = None,
        **kwargs
    ) -> None:
        """
        Log a SQL query.
        
        Args:
            query: The SQL query
            duration_ms: The duration in milliseconds
            parameters: The query parameters
            record_count: The number of records returned
            affected_rows: The number of rows affected
            success: Whether the query was successful
            error: The error, if any
            **kwargs: Additional context for the log message
        """
        # Process the query
        processed_query = self._process_query(query)
        
        # Build the context
        context = {
            "query": processed_query,
            "duration_ms": duration_ms,
        }
        
        # Add parameters if enabled
        if self._log_parameters and parameters:
            context["parameters"] = self._process_parameters(parameters)
        
        # Add record count if available
        if record_count is not None:
            context["record_count"] = record_count
        
        # Add affected rows if available
        if affected_rows is not None:
            context["affected_rows"] = affected_rows
        
        # Add additional context
        context.update(kwargs)
        
        # Determine the operation type
        operation = self._get_operation_type(query)
        
        # Log the operation
        self.log_operation(
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            error=error,
            **context
        )
    
    def _process_query(self, query: str) -> str:
        """
        Process a SQL query for logging.
        
        Args:
            query: The SQL query
            
        Returns:
            The processed query
        """
        # Truncate the query if it's too long
        if len(query) > self._max_query_length:
            query = f"{query[:self._max_query_length]}... [truncated]"
        
        # Mask sensitive data if enabled
        if self._mask_sensitive_data:
            query = self._mask_sensitive_data_in_query(query)
        
        return query
    
    def _process_parameters(self, parameters: Union[Dict[str, Any], List[Any], tuple]) -> Any:
        """
        Process query parameters for logging.
        
        Args:
            parameters: The query parameters
            
        Returns:
            The processed parameters
        """
        # For dictionaries, mask sensitive keys
        if isinstance(parameters, dict):
            return {
                k: self._mask_value(k, v) for k, v in parameters.items()
            }
        
        # For lists and tuples, return as is
        return parameters
    
    def _mask_value(self, key: str, value: Any) -> Any:
        """
        Mask a sensitive value.
        
        Args:
            key: The parameter key
            value: The parameter value
            
        Returns:
            The masked value
        """
        # List of sensitive key patterns
        sensitive_keys = [
            "password", "secret", "token", "key", "auth", "credential"
        ]
        
        # Check if the key is sensitive
        for pattern in sensitive_keys:
            if pattern.lower() in key.lower():
                return "********"
        
        return value
    
    def _mask_sensitive_data_in_query(self, query: str) -> str:
        """
        Mask sensitive data in a SQL query.
        
        Args:
            query: The SQL query
            
        Returns:
            The query with sensitive data masked
        """
        # Mask passwords in connection strings
        query = re.sub(
            r"password=([^;'\s]+)",
            r"password=********",
            query,
            flags=re.IGNORECASE
        )
        
        # Mask passwords in SQL statements
        query = re.sub(
            r"password\s*=\s*'([^']*)'",
            r"password='********'",
            query,
            flags=re.IGNORECASE
        )
        
        return query
    
    def _get_operation_type(self, query: str) -> str:
        """
        Get the operation type from a SQL query.
        
        Args:
            query: The SQL query
            
        Returns:
            The operation type
        """
        # Normalize the query
        normalized_query = query.strip().upper()
        
        # Determine the operation type
        if normalized_query.startswith("SELECT"):
            return "SELECT"
        elif normalized_query.startswith("INSERT"):
            return "INSERT"
        elif normalized_query.startswith("UPDATE"):
            return "UPDATE"
        elif normalized_query.startswith("DELETE"):
            return "DELETE"
        elif normalized_query.startswith("CREATE"):
            return "CREATE"
        elif normalized_query.startswith("ALTER"):
            return "ALTER"
        elif normalized_query.startswith("DROP"):
            return "DROP"
        elif normalized_query.startswith("TRUNCATE"):
            return "TRUNCATE"
        else:
            return "SQL"

    def log_connection(
        self,
        duration_ms: float = 0.0,
        success: bool = True,
        error: Optional[Exception] = None,
        **kwargs
    ) -> None:
        """Log the establishment of a database connection.

        Args:
            duration_ms: The duration in milliseconds it took to establish the connection.
            success: Whether the connection was successful.
            error: The error, if any.
            **kwargs: Additional context for the log message.
        """
        self.log_operation(
            operation="connect",
            duration_ms=duration_ms,
            success=success,
            error=error,
            **kwargs,
        )


class AsyncSqlLogger(AsyncDatabaseLogger, SqlLogger):
    """Asynchronous logger for SQL operations."""
    
    async def alog_query(
        self,
        query: str,
        duration_ms: float,
        parameters: Optional[Union[Dict[str, Any], List[Any], tuple]] = None,
        record_count: Optional[int] = None,
        affected_rows: Optional[int] = None,
        success: bool = True,
        error: Optional[Exception] = None,
        **kwargs
    ) -> None:
        """
        Log a SQL query asynchronously.
        
        Args:
            query: The SQL query
            duration_ms: The duration in milliseconds
            parameters: The query parameters
            record_count: The number of records returned
            affected_rows: The number of rows affected
            success: Whether the query was successful
            error: The error, if any
            **kwargs: Additional context for the log message
        """
        # Process the query
        processed_query = self._process_query(query)
        
        # Build the context
        context = {
            "query": processed_query,
            "duration_ms": duration_ms,
        }
        
        # Add parameters if enabled
        if self._log_parameters and parameters:
            context["parameters"] = self._process_parameters(parameters)
        
        # Add record count if available
        if record_count is not None:
            context["record_count"] = record_count
        
        # Add affected rows if available
        if affected_rows is not None:
            context["affected_rows"] = affected_rows
        
        # Add additional context
        context.update(kwargs)
        
        # Determine the operation type
        operation = self._get_operation_type(query)
        
        # Log the operation
        await self.alog_operation(
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            error=error,
            **context
        ) 