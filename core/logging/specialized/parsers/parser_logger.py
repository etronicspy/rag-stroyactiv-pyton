"""
Parser Logger Implementation

Specialized logger for parser operations with correlation tracking,
performance monitoring, and AI-specific logging capabilities.
"""

import time
import json
import uuid
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from functools import lru_cache

from core.logging.core.logger import Logger
from core.logging.context.correlation import CorrelationProvider
from core.logging.interfaces.core import ILogger
from core.logging.interfaces.context import ICorrelationProvider
from core.logging.interfaces.metrics import IMetricsCollector, IPerformanceTracker


class ParserLogger:
    """
    Specialized logger for parser operations.
    
    Integrates with the main logging system to provide structured logging
    for parser operations with correlation tracking and performance monitoring.
    """
    
    def __init__(self, logger_name: str = "parsers"):
        """
        Initialize parser logger.
        
        Args:
            logger_name: Name for the logger instance
        """
        self.logger = Logger(logger_name)
        self.correlation_provider = CorrelationProvider()
        self._start_times: Dict[str, float] = {}
        self._operation_counts: Dict[str, int] = {}
        
    def log_parse_start(
        self,
        operation_id: str,
        input_type: str,
        parser_type: str,
        input_size: Optional[int] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Log the start of a parsing operation.
        
        Args:
            operation_id: Unique identifier for the operation
            input_type: Type of input being parsed
            parser_type: Type of parser being used
            input_size: Size of input data (optional)
            correlation_id: Correlation ID for tracking (optional)
        """
        if correlation_id:
            self.correlation_provider.set_correlation_id(correlation_id)
        
        self._start_times[operation_id] = time.time()
        self._operation_counts[parser_type] = self._operation_counts.get(parser_type, 0) + 1
        
        context = {
            "operation_id": operation_id,
            "input_type": input_type,
            "parser_type": parser_type,
            "input_size": input_size,
            "correlation_id": correlation_id or self.correlation_provider.get_correlation_id(),
            "operation_number": self._operation_counts[parser_type],
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.info(
            f"🚀 Starting {parser_type} parsing operation",
            extra={"parse_context": context}
        )
    
    def log_parse_success(
        self,
        operation_id: str,
        result_data: Optional[Dict[str, Any]] = None,
        confidence: Optional[float] = None,
        output_size: Optional[int] = None
    ) -> None:
        """
        Log successful parsing operation.
        
        Args:
            operation_id: Unique identifier for the operation
            result_data: Summary of parsing results (optional)
            confidence: Confidence score of the result (optional)
            output_size: Size of output data (optional)
        """
        processing_time = self._get_processing_time(operation_id)
        
        context = {
            "operation_id": operation_id,
            "processing_time": processing_time,
            "confidence": confidence,
            "output_size": output_size,
            "result_summary": result_data,
            "correlation_id": self.correlation_provider.get_correlation_id(),
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.info(
            f"✅ Parsing operation completed successfully in {processing_time:.2f}s",
            extra={"parse_context": context}
        )
    
    def log_parse_failure(
        self,
        operation_id: str,
        error_message: str,
        error_type: str,
        retry_count: int = 0,
        stack_trace: Optional[str] = None
    ) -> None:
        """
        Log failed parsing operation.
        
        Args:
            operation_id: Unique identifier for the operation
            error_message: Error message
            error_type: Type of error
            retry_count: Number of retries attempted
            stack_trace: Full stack trace (optional)
        """
        processing_time = self._get_processing_time(operation_id)
        
        context = {
            "operation_id": operation_id,
            "processing_time": processing_time,
            "error_message": error_message,
            "error_type": error_type,
            "retry_count": retry_count,
            "stack_trace": stack_trace,
            "correlation_id": self.correlation_provider.get_correlation_id(),
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.error(
            f"❌ Parsing operation failed after {processing_time:.2f}s: {error_message}",
            extra={"parse_context": context}
        )
    
    def log_batch_operation(
        self,
        batch_id: str,
        batch_size: int,
        successful_count: int,
        failed_count: int,
        total_processing_time: float,
        parallel_processing: bool = False
    ) -> None:
        """
        Log batch parsing operation results.
        
        Args:
            batch_id: Unique identifier for the batch
            batch_size: Total number of items in batch
            successful_count: Number of successful operations
            failed_count: Number of failed operations
            total_processing_time: Total time for batch processing
            parallel_processing: Whether parallel processing was used
        """
        success_rate = (successful_count / batch_size) * 100 if batch_size > 0 else 0
        
        context = {
            "batch_id": batch_id,
            "batch_size": batch_size,
            "successful_count": successful_count,
            "failed_count": failed_count,
            "success_rate": success_rate,
            "total_processing_time": total_processing_time,
            "average_time_per_item": total_processing_time / batch_size if batch_size > 0 else 0,
            "parallel_processing": parallel_processing,
            "correlation_id": self.correlation_provider.get_correlation_id(),
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.info(
            f"📊 Batch operation completed: {successful_count}/{batch_size} successful "
            f"({success_rate:.1f}%) in {total_processing_time:.2f}s",
            extra={"batch_context": context}
        )
    
    def _get_processing_time(self, operation_id: str) -> float:
        """
        Get processing time for an operation.
        
        Args:
            operation_id: Unique identifier for the operation
            
        Returns:
            float: Processing time in seconds
        """
        start_time = self._start_times.get(operation_id)
        if start_time:
            processing_time = time.time() - start_time
            # Clean up to prevent memory leaks
            del self._start_times[operation_id]
            return processing_time
        return 0.0
    
    def get_operation_stats(self) -> Dict[str, Any]:
        """
        Get operation statistics.
        
        Returns:
            Dict[str, Any]: Operation statistics
        """
        return {
            "operation_counts": self._operation_counts.copy(),
            "active_operations": len(self._start_times),
            "total_operations": sum(self._operation_counts.values())
        }


class AIParserLogger(ParserLogger):
    """
    Specialized logger for AI parser operations.
    
    Extends ParserLogger with AI-specific logging capabilities including
    token usage, model information, and cost tracking.
    """
    
    def __init__(self, logger_name: str = "ai_parsers"):
        """
        Initialize AI parser logger.
        
        Args:
            logger_name: Name for the logger instance
        """
        super().__init__(logger_name)
        self._token_usage: Dict[str, int] = {}
        self._cost_tracking: Dict[str, float] = {}
    
    def log_ai_request(
        self,
        operation_id: str,
        model_name: str,
        prompt: str,
        temperature: float,
        max_tokens: int,
        request_id: Optional[str] = None
    ) -> None:
        """
        Log AI API request.
        
        Args:
            operation_id: Unique identifier for the operation
            model_name: Name of the AI model used
            prompt: Prompt sent to AI model
            temperature: Temperature setting
            max_tokens: Maximum tokens setting
            request_id: AI provider request ID (optional)
        """
        context = {
            "operation_id": operation_id,
            "model_name": model_name,
            "prompt_length": len(prompt),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "request_id": request_id,
            "correlation_id": self.correlation_provider.get_correlation_id(),
            "timestamp": datetime.now().isoformat()
        }
        
        # Log prompt only in debug mode for security
        if self.logger.logger.level <= 10:  # DEBUG level
            context["prompt"] = prompt
        
        self.logger.debug(
            f"🤖 AI request sent to {model_name}",
            extra={"ai_request_context": context}
        )
    
    def log_ai_response(
        self,
        operation_id: str,
        response_data: Dict[str, Any],
        tokens_used: int,
        cost_estimate: Optional[float] = None,
        response_time: Optional[float] = None
    ) -> None:
        """
        Log AI API response.
        
        Args:
            operation_id: Unique identifier for the operation
            response_data: AI response data
            tokens_used: Number of tokens used
            cost_estimate: Estimated cost (optional)
            response_time: API response time (optional)
        """
        self._token_usage[operation_id] = tokens_used
        if cost_estimate:
            self._cost_tracking[operation_id] = cost_estimate
        
        context = {
            "operation_id": operation_id,
            "tokens_used": tokens_used,
            "cost_estimate": cost_estimate,
            "response_time": response_time,
            "response_length": len(str(response_data)),
            "correlation_id": self.correlation_provider.get_correlation_id(),
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.debug(
            f"🤖 AI response received: {tokens_used} tokens used",
            extra={"ai_response_context": context}
        )
    
    def log_embedding_generation(
        self,
        operation_id: str,
        text_length: int,
        embedding_dimensions: int,
        embedding_model: str,
        processing_time: float
    ) -> None:
        """
        Log embedding generation.
        
        Args:
            operation_id: Unique identifier for the operation
            text_length: Length of input text
            embedding_dimensions: Dimensions of generated embedding
            embedding_model: Model used for embedding generation
            processing_time: Time taken for embedding generation
        """
        context = {
            "operation_id": operation_id,
            "text_length": text_length,
            "embedding_dimensions": embedding_dimensions,
            "embedding_model": embedding_model,
            "processing_time": processing_time,
            "correlation_id": self.correlation_provider.get_correlation_id(),
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.info(
            f"🔢 Embedding generated: {embedding_dimensions}D from {text_length} chars in {processing_time:.2f}s",
            extra={"embedding_context": context}
        )
    
    def log_confidence_validation(
        self,
        operation_id: str,
        confidence_score: float,
        threshold: float,
        validation_result: bool,
        retry_triggered: bool = False
    ) -> None:
        """
        Log confidence validation.
        
        Args:
            operation_id: Unique identifier for the operation
            confidence_score: Actual confidence score
            threshold: Required threshold
            validation_result: Whether validation passed
            retry_triggered: Whether retry was triggered
        """
        context = {
            "operation_id": operation_id,
            "confidence_score": confidence_score,
            "threshold": threshold,
            "validation_result": validation_result,
            "retry_triggered": retry_triggered,
            "correlation_id": self.correlation_provider.get_correlation_id(),
            "timestamp": datetime.now().isoformat()
        }
        
        status = "✅ passed" if validation_result else "❌ failed"
        self.logger.info(
            f"🎯 Confidence validation {status}: {confidence_score:.2f} vs {threshold:.2f}",
            extra={"confidence_context": context}
        )
    
    def get_ai_stats(self) -> Dict[str, Any]:
        """
        Get AI-specific statistics.
        
        Returns:
            Dict[str, Any]: AI statistics
        """
        total_tokens = sum(self._token_usage.values())
        total_cost = sum(self._cost_tracking.values())
        
        return {
            **self.get_operation_stats(),
            "total_tokens_used": total_tokens,
            "total_estimated_cost": total_cost,
            "operations_with_tokens": len(self._token_usage),
            "operations_with_cost": len(self._cost_tracking)
        }


class MaterialParserLogger(AIParserLogger):
    """
    Specialized logger for material parser operations.
    
    Extends AIParserLogger with material-specific logging capabilities.
    """
    
    def __init__(self, logger_name: str = "material_parsers"):
        """
        Initialize material parser logger.
        
        Args:
            logger_name: Name for the logger instance
        """
        super().__init__(logger_name)
        self._material_stats: Dict[str, Any] = {
            "units_extracted": 0,
            "colors_extracted": 0,
            "coefficients_calculated": 0,
            "categories_identified": 0
        }
    
    def log_material_parsing(
        self,
        operation_id: str,
        material_name: str,
        extracted_unit: Optional[str] = None,
        extracted_color: Optional[str] = None,
        extracted_price: Optional[float] = None,
        confidence: Optional[float] = None
    ) -> None:
        """
        Log material parsing results.
        
        Args:
            operation_id: Unique identifier for the operation
            material_name: Name of the material
            extracted_unit: Extracted unit (optional)
            extracted_color: Extracted color (optional)
            extracted_price: Extracted price (optional)
            confidence: Confidence score (optional)
        """
        # Update statistics
        if extracted_unit:
            self._material_stats["units_extracted"] += 1
        if extracted_color:
            self._material_stats["colors_extracted"] += 1
        
        context = {
            "operation_id": operation_id,
            "material_name": material_name,
            "extracted_unit": extracted_unit,
            "extracted_color": extracted_color,
            "extracted_price": extracted_price,
            "confidence": confidence,
            "correlation_id": self.correlation_provider.get_correlation_id(),
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.info(
            f"🏗️ Material parsed: {material_name} -> {extracted_unit or 'N/A'} "
            f"({extracted_color or 'no color'})",
            extra={"material_context": context}
        )
    
    def log_unit_conversion(
        self,
        operation_id: str,
        from_unit: str,
        to_unit: str,
        coefficient: float,
        calculation_method: str
    ) -> None:
        """
        Log unit conversion calculation.
        
        Args:
            operation_id: Unique identifier for the operation
            from_unit: Source unit
            to_unit: Target unit
            coefficient: Conversion coefficient
            calculation_method: Method used for calculation
        """
        self._material_stats["coefficients_calculated"] += 1
        
        context = {
            "operation_id": operation_id,
            "from_unit": from_unit,
            "to_unit": to_unit,
            "coefficient": coefficient,
            "calculation_method": calculation_method,
            "correlation_id": self.correlation_provider.get_correlation_id(),
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.info(
            f"🔄 Unit conversion: {from_unit} -> {to_unit} (coefficient: {coefficient})",
            extra={"conversion_context": context}
        )
    
    def get_material_stats(self) -> Dict[str, Any]:
        """
        Get material-specific statistics.
        
        Returns:
            Dict[str, Any]: Material statistics
        """
        return {
            **self.get_ai_stats(),
            "material_stats": self._material_stats.copy()
        }


class BatchParserLogger(AIParserLogger):
    """
    Specialized logger for batch parser operations.
    
    Extends AIParserLogger with batch-specific logging capabilities.
    """
    
    def __init__(self, logger_name: str = "batch_parsers"):
        """
        Initialize batch parser logger.
        
        Args:
            logger_name: Name for the logger instance
        """
        super().__init__(logger_name)
        self._batch_stats: Dict[str, Any] = {
            "total_batches": 0,
            "total_items_processed": 0,
            "parallel_batches": 0,
            "sequential_batches": 0
        }
    
    def log_batch_start(
        self,
        batch_id: str,
        batch_size: int,
        parallel_processing: bool,
        max_workers: int
    ) -> None:
        """
        Log batch operation start.
        
        Args:
            batch_id: Unique identifier for the batch
            batch_size: Number of items in batch
            parallel_processing: Whether parallel processing is used
            max_workers: Number of parallel workers
        """
        self.log_parse_start(
            operation_id=batch_id,
            input_type="batch",
            parser_type="batch_parser",
            input_size=batch_size
        )
        
        self._batch_stats["total_batches"] += 1
        self._batch_stats["total_items_processed"] += batch_size
        
        if parallel_processing:
            self._batch_stats["parallel_batches"] += 1
        else:
            self._batch_stats["sequential_batches"] += 1
        
        context = {
            "batch_id": batch_id,
            "batch_size": batch_size,
            "parallel_processing": parallel_processing,
            "max_workers": max_workers,
            "correlation_id": self.correlation_provider.get_correlation_id(),
            "timestamp": datetime.now().isoformat()
        }
        
        processing_mode = "parallel" if parallel_processing else "sequential"
        self.logger.info(
            f"🚀 Batch operation started: {batch_size} items ({processing_mode})",
            extra={"batch_start_context": context}
        )
    
    def get_batch_stats(self) -> Dict[str, Any]:
        """
        Get batch-specific statistics.
        
        Returns:
            Dict[str, Any]: Batch statistics
        """
        return {
            **self.get_ai_stats(),
            "batch_stats": self._batch_stats.copy()
        }


# Factory functions for easy access
@lru_cache(maxsize=10)
def get_parser_logger(logger_name: str = "parsers") -> ParserLogger:
    """
    Get cached parser logger instance.
    
    Args:
        logger_name: Name for the logger instance
        
    Returns:
        ParserLogger: Cached logger instance
    """
    return ParserLogger(logger_name)


@lru_cache(maxsize=10)
def get_ai_parser_logger(logger_name: str = "ai_parsers") -> AIParserLogger:
    """
    Get cached AI parser logger instance.
    
    Args:
        logger_name: Name for the logger instance
        
    Returns:
        AIParserLogger: Cached logger instance
    """
    return AIParserLogger(logger_name)


@lru_cache(maxsize=10)
def get_material_parser_logger(logger_name: str = "material_parsers") -> MaterialParserLogger:
    """
    Get cached material parser logger instance.
    
    Args:
        logger_name: Name for the logger instance
        
    Returns:
        MaterialParserLogger: Cached logger instance
    """
    return MaterialParserLogger(logger_name)


@lru_cache(maxsize=10)
def get_batch_parser_logger(logger_name: str = "batch_parsers") -> BatchParserLogger:
    """
    Get cached batch parser logger instance.
    
    Args:
        logger_name: Name for the logger instance
        
    Returns:
        BatchParserLogger: Cached logger instance
    """
    return BatchParserLogger(logger_name)


# Export all logger types
__all__ = [
    'ParserLogger',
    'AIParserLogger',
    'MaterialParserLogger',
    'BatchParserLogger',
    'get_parser_logger',
    'get_ai_parser_logger',
    'get_material_parser_logger',
    'get_batch_parser_logger'
] 