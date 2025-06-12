"""Database-specific exceptions for error handling."""


class DatabaseError(Exception):
    """Base exception for all database-related errors."""
    
    def __init__(self, message: str, details: str = None):
        """Initialize database error.
        
        Args:
            message: Error message
            details: Additional error details
        """
        self.message = message
        self.details = details
        super().__init__(self.message)


class ConnectionError(DatabaseError):
    """Exception raised when database connection fails."""
    
    def __init__(self, database_type: str, message: str = None, details: str = None):
        """Initialize connection error.
        
        Args:
            database_type: Type of database (PostgreSQL, Qdrant, Redis)
            message: Error message
            details: Additional error details
        """
        self.database_type = database_type
        default_message = f"Failed to connect to {database_type} database"
        super().__init__(message or default_message, details)


class QueryError(DatabaseError):
    """Exception raised when database query fails."""
    
    def __init__(self, query: str = None, message: str = None, details: str = None):
        """Initialize query error.
        
        Args:
            query: Failed query
            message: Error message  
            details: Additional error details
        """
        self.query = query
        default_message = "Database query failed"
        if query:
            default_message += f": {query[:100]}..."
        super().__init__(message or default_message, details)


class ConfigurationError(DatabaseError):
    """Exception raised when database configuration is invalid."""
    
    def __init__(self, config_key: str = None, message: str = None, details: str = None):
        """Initialize configuration error.
        
        Args:
            config_key: Configuration key that failed
            message: Error message
            details: Additional error details
        """
        self.config_key = config_key
        default_message = "Database configuration error"
        if config_key:
            default_message += f" for key: {config_key}"
        super().__init__(message or default_message, details)


class TransactionError(DatabaseError):
    """Exception raised when database transaction fails."""
    
    def __init__(self, operation: str = None, message: str = None, details: str = None):
        """Initialize transaction error.
        
        Args:
            operation: Transaction operation that failed
            message: Error message
            details: Additional error details
        """
        self.operation = operation
        default_message = "Database transaction failed"
        if operation:
            default_message += f" during {operation}"
        super().__init__(message or default_message, details)


class ValidationError(DatabaseError):
    """Exception raised when data validation fails."""
    
    def __init__(self, field: str = None, value: str = None, message: str = None, details: str = None):
        """Initialize validation error.
        
        Args:
            field: Field that failed validation
            value: Invalid value
            message: Error message
            details: Additional error details
        """
        self.field = field
        self.value = value
        default_message = "Data validation failed"
        if field:
            default_message += f" for field: {field}"
        super().__init__(message or default_message, details) 