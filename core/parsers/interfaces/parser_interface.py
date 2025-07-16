"""
Base Parser Interface

Abstract base class defining the contract for all parser implementations.
Provides type-safe, generic interface for parsing operations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Generic, TypeVar, Protocol
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

# Generic types for parser operations
InputType = TypeVar('InputType')
OutputType = TypeVar('OutputType')
ConfigType = TypeVar('ConfigType')


class ParseStatus(Enum):
    """Status of parsing operation."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    SUCCESS = "success"
    PARTIAL = "partial"
    ERROR = "error"
    TIMEOUT = "timeout"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ParseResult(BaseModel, Generic[OutputType]):
    """
    Generic result structure for parsing operations.
    
    Args:
        OutputType: Type of parsed output data
    """
    
    success: bool = Field(
        description="Whether parsing was successful"
    )
    
    data: Optional[OutputType] = Field(
        default=None,
        description="Parsed data if successful"
    )
    
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if parsing failed"
    )
    
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score of parsing result"
    )
    
    processing_time: Optional[float] = Field(
        default=None,
        description="Time taken for parsing operation in seconds"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about parsing operation"
    )
    
    status: ParseStatus = Field(
        default=ParseStatus.COMPLETED,
        description="Current status of parsing operation"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp of parsing operation"
    )
    
    request_id: Optional[str] = Field(
        default=None,
        description="Request ID for tracking"
    )


class ParseRequest(BaseModel, Generic[InputType]):
    """
    Generic request structure for parsing operations.
    
    Args:
        InputType: Type of input data to parse
    """
    
    input_data: InputType = Field(
        description="Input data to parse"
    )
    
    options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional parsing options"
    )
    
    correlation_id: Optional[str] = Field(
        default=None,
        description="Correlation ID for tracking requests"
    )
    
    timeout: Optional[int] = Field(
        default=None,
        ge=1,
        description="Timeout for parsing operation in seconds"
    )
    
    priority: int = Field(
        default=0,
        ge=0,
        le=10,
        description="Priority level for parsing operation"
    )


class BatchParseRequest(BaseModel, Generic[InputType]):
    """
    Generic batch parsing request structure.
    
    Args:
        InputType: Type of input data to parse
    """
    
    requests: List[ParseRequest[InputType]] = Field(
        min_length=1,
        description="List of parsing requests"
    )
    
    batch_id: Optional[str] = Field(
        default=None,
        description="Unique identifier for batch operation"
    )
    
    parallel_processing: bool = Field(
        default=True,
        description="Whether to process requests in parallel"
    )
    
    max_workers: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of parallel workers"
    )
    
    fail_fast: bool = Field(
        default=False,
        description="Stop batch processing on first failure"
    )


class BatchParseResult(BaseModel, Generic[OutputType]):
    """
    Generic batch parsing result structure.
    
    Args:
        OutputType: Type of parsed output data
    """
    
    results: List[ParseResult[OutputType]] = Field(
        description="List of parsing results"
    )
    
    batch_id: Optional[str] = Field(
        default=None,
        description="Unique identifier for batch operation"
    )
    
    total_processed: int = Field(
        description="Total number of items processed"
    )
    
    successful_count: int = Field(
        description="Number of successful parsing operations"
    )
    
    failed_count: int = Field(
        description="Number of failed parsing operations"
    )
    
    success_rate: float = Field(
        ge=0.0,
        le=100.0,
        description="Success rate as percentage"
    )
    
    total_processing_time: float = Field(
        description="Total time for batch processing in seconds"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about batch operation"
    )


class IParserHealthCheck(Protocol):
    """Protocol for parser health check operations."""
    
    def is_healthy(self) -> bool:
        """Check if parser is healthy and ready to process requests."""
        ...
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get detailed health status information."""
        ...


class IParserConfig(Protocol):
    """Protocol for parser configuration operations."""
    
    def get_config(self) -> Dict[str, Any]:
        """Get current parser configuration."""
        ...
    
    def update_config(self, config: Dict[str, Any]) -> bool:
        """Update parser configuration."""
        ...


class IParserMetrics(Protocol):
    """Protocol for parser metrics operations."""
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get parser performance metrics."""
        ...
    
    def reset_metrics(self) -> bool:
        """Reset parser metrics."""
        ...


class IBaseParser(ABC, Generic[InputType, OutputType, ConfigType]):
    """
    Abstract base class for all parser implementations.
    
    This interface defines the contract that all parsers must implement,
    providing type-safe operations for parsing various input types.
    
    Args:
        InputType: Type of input data to parse
        OutputType: Type of parsed output data
        ConfigType: Type of parser configuration
    """
    
    @abstractmethod
    async def parse(
        self,
        request: ParseRequest[InputType]
    ) -> ParseResult[OutputType]:
        """
        Parse a single input item.
        
        Args:
            request: Parsing request containing input data and options
            
        Returns:
            ParseResult: Result of parsing operation
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement parse method")
    
    @abstractmethod
    async def parse_batch(
        self,
        request: BatchParseRequest[InputType]
    ) -> BatchParseResult[OutputType]:
        """
        Parse multiple input items in batch.
        
        Args:
            request: Batch parsing request containing multiple items
            
        Returns:
            BatchParseResult: Result of batch parsing operation
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement parse_batch method")
    
    @abstractmethod
    def get_supported_input_types(self) -> List[str]:
        """
        Get list of supported input types.
        
        Returns:
            List[str]: List of supported input type names
        """
        raise NotImplementedError("Subclasses must implement get_supported_input_types method")
    
    @abstractmethod
    def get_parser_info(self) -> Dict[str, Any]:
        """
        Get parser information and capabilities.
        
        Returns:
            Dict[str, Any]: Parser information including name, version, capabilities
        """
        raise NotImplementedError("Subclasses must implement get_parser_info method")
    
    @abstractmethod
    async def validate_input(self, input_data: InputType) -> bool:
        """
        Validate input data before parsing.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            bool: True if input is valid, False otherwise
        """
        raise NotImplementedError("Subclasses must implement validate_input method")
    
    @abstractmethod
    async def cleanup(self) -> bool:
        """
        Cleanup parser resources.
        
        Returns:
            bool: True if cleanup was successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement cleanup method")
    
    # Optional methods with default implementations
    
    async def configure(self, config: ConfigType) -> bool:
        """
        Configure parser with new settings.
        
        Args:
            config: New configuration settings
            
        Returns:
            bool: True if configuration was successful, False otherwise
        """
        return True
    
    async def pre_parse_hook(self, request: ParseRequest[InputType]) -> ParseRequest[InputType]:
        """
        Pre-processing hook called before parsing.
        
        Args:
            request: Original parsing request
            
        Returns:
            ParseRequest: Modified parsing request
        """
        return request
    
    async def post_parse_hook(self, result: ParseResult[OutputType]) -> ParseResult[OutputType]:
        """
        Post-processing hook called after parsing.
        
        Args:
            result: Original parsing result
            
        Returns:
            ParseResult: Modified parsing result
        """
        return result
    
    def get_version(self) -> str:
        """
        Get parser version.
        
        Returns:
            str: Parser version string
        """
        return "1.0.0"
    
    def get_name(self) -> str:
        """
        Get parser name.
        
        Returns:
            str: Parser name
        """
        return self.__class__.__name__


# Export all interface types
__all__ = [
    'InputType',
    'OutputType', 
    'ConfigType',
    'ParseStatus',
    'ParseResult',
    'ParseRequest',
    'BatchParseRequest',
    'BatchParseResult',
    'IParserHealthCheck',
    'IParserConfig',
    'IParserMetrics',
    'IBaseParser'
] 