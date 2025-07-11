"""
Batch Parser Service

Specialized service for high-performance batch processing of construction materials
with parallel processing, progress tracking, and comprehensive result management.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Union, Callable, Awaitable
from pathlib import Path
from functools import lru_cache
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
import json

# Core infrastructure imports
from core.config.parsers import ParserConfig, get_parser_config
from core.logging.specialized.parsers import (
    get_batch_parser_logger,
    get_batch_parser_metrics
)

# Parser interface imports
from ..interfaces import (
    IBaseParser,
    MaterialParseData,
    AIParseRequest,
    AIParseResult,
    ParseStatus,
    BatchParseRequest,
    BatchParseResult,
    InputType,
    OutputType
)

# Service imports
from .material_parser_service import MaterialParserService, get_material_parser_service


@dataclass
class BatchProcessingContext:
    """Context for batch processing operations"""
    operation_id: str
    start_time: float
    total_items: int
    processed_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    skipped_items: int = 0
    current_batch: int = 0
    total_batches: int = 0
    
    # Progress tracking
    last_progress_update: float = field(default_factory=time.time)
    progress_callbacks: List[Callable[[float], None]] = field(default_factory=list)
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage"""
        if self.total_items == 0:
            return 100.0
        return (self.processed_items / self.total_items) * 100.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.processed_items == 0:
            return 0.0
        return self.successful_items / self.processed_items
    
    @property
    def elapsed_time(self) -> float:
        """Get elapsed time"""
        return time.time() - self.start_time
    
    @property
    def estimated_time_remaining(self) -> float:
        """Estimate remaining time"""
        if self.processed_items == 0:
            return 0.0
        
        time_per_item = self.elapsed_time / self.processed_items
        remaining_items = self.total_items - self.processed_items
        return time_per_item * remaining_items
    
    def update_progress(self) -> None:
        """Update progress and notify callbacks"""
        current_time = time.time()
        
        # Update progress every 1 second
        if current_time - self.last_progress_update >= 1.0:
            self.last_progress_update = current_time
            
            # Notify progress callbacks
            for callback in self.progress_callbacks:
                try:
                    callback(self.progress_percentage)
                except Exception:
                    pass  # Ignore callback errors


@dataclass
class BatchConfiguration:
    """Configuration for batch processing"""
    batch_size: int = 10
    max_workers: int = 5
    max_retries: int = 3
    retry_delay: float = 1.0
    enable_progress_tracking: bool = True
    enable_checkpointing: bool = False
    checkpoint_interval: int = 100
    fail_fast: bool = False
    parallel_processing: bool = True


class BatchParserService(IBaseParser[List[str], List[MaterialParseData]]):
    """
    Specialized service for high-performance batch processing.
    
    Provides advanced batch processing capabilities including parallel processing,
    progress tracking, checkpointing, and comprehensive result management.
    """
    
    def __init__(self, config: Optional[ParserConfig] = None):
        """
        Initialize Batch Parser Service.
        
        Args:
            config: Optional parser configuration. If None, uses default config.
        """
        self.config = config or get_parser_config()
        self.logger = get_batch_parser_logger()
        self.metrics = get_batch_parser_metrics()
        
        # Initialize material parser service
        self.material_parser_service = get_material_parser_service()
        
        # Service metadata
        self._service_name = "batch_parser_service"
        self._version = "2.0.0"
        self._initialized = True
        
        # Batch processing configuration
        self.batch_config = BatchConfiguration(
            batch_size=self.config.performance.batch_size,
            max_workers=self.config.performance.max_concurrent_requests,
            max_retries=self.config.performance.retry_attempts,
            parallel_processing=True
        )
        
        # Statistics
        self.stats = {
            "total_batch_operations": 0,
            "total_items_processed": 0,
            "successful_items": 0,
            "failed_items": 0,
            "average_batch_size": 0.0,
            "average_processing_time": 0.0,
            "peak_concurrency": 0
        }
        
        self.logger.info(f"Batch Parser Service v{self._version} initialized")
    
    @property
    def service_name(self) -> str:
        """Get service name"""
        return self._service_name
    
    @property
    def version(self) -> str:
        """Get service version"""
        return self._version
    
    def is_healthy(self) -> bool:
        """
        Check if service is healthy.
        
        Returns:
            bool: True if service is healthy, False otherwise
        """
        try:
            return (
                self._initialized and
                self.material_parser_service.is_healthy() and
                self.config is not None
            )
        except Exception:
            return False
    
    def get_health_details(self) -> Dict[str, Any]:
        """
        Get detailed health information.
        
        Returns:
            Dict[str, Any]: Health details
        """
        return {
            "service_name": self.service_name,
            "version": self.version,
            "initialized": self._initialized,
            "material_parser_healthy": self.material_parser_service.is_healthy(),
            "config_available": self.config is not None,
            "batch_config": {
                "batch_size": self.batch_config.batch_size,
                "max_workers": self.batch_config.max_workers,
                "parallel_processing": self.batch_config.parallel_processing
            },
            "statistics": self.stats,
            "material_parser_details": self.material_parser_service.get_health_details()
        }
    
    async def parse_batch(
        self, 
        materials: List[str], 
        batch_config: Optional[BatchConfiguration] = None,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> BatchParseResult[MaterialParseData]:
        """
        Parse materials in batch with advanced processing options.
        
        Args:
            materials: List of material description texts
            batch_config: Optional batch configuration
            progress_callback: Optional progress callback function
            
        Returns:
            BatchParseResult: Comprehensive batch parsing results
        """
        config = batch_config or self.batch_config
        
        self.logger.info(f"Starting batch processing of {len(materials)} materials")
        
        # Create processing context
        context = BatchProcessingContext(
            operation_id=f"batch_parse_{id(materials)}",
            start_time=time.time(),
            total_items=len(materials),
            total_batches=(len(materials) + config.batch_size - 1) // config.batch_size
        )
        
        # Add progress callback if provided
        if progress_callback:
            context.progress_callbacks.append(progress_callback)
        
        try:
            # Process materials
            if config.parallel_processing:
                results = await self._process_parallel(materials, config, context)
            else:
                results = await self._process_sequential(materials, config, context)
            
            # Update statistics
            self.stats["total_batch_operations"] += 1
            self.stats["total_items_processed"] += len(materials)
            self.stats["successful_items"] += context.successful_items
            self.stats["failed_items"] += context.failed_items
            self.stats["average_batch_size"] = (
                (self.stats["average_batch_size"] * (self.stats["total_batch_operations"] - 1) + len(materials)) /
                self.stats["total_batch_operations"]
            )
            self.stats["average_processing_time"] = (
                (self.stats["average_processing_time"] * (self.stats["total_batch_operations"] - 1) + context.elapsed_time) /
                self.stats["total_batch_operations"]
            )
            
            # Log batch metrics
            self.metrics.record_batch_operation(
                operation_type="parallel_batch" if config.parallel_processing else "sequential_batch",
                batch_size=len(materials),
                success_count=context.successful_items,
                failure_count=context.failed_items,
                processing_time=context.elapsed_time,
                concurrency_level=config.max_workers
            )
            
            # Create batch result
            batch_result = BatchParseResult(
                results=results,
                total_processed=context.processed_items,
                successful_count=context.successful_items,
                failed_count=context.failed_items,
                success_rate=context.success_rate,
                processing_time=context.elapsed_time
            )
            
            self.logger.info(
                f"Batch processing completed: {context.successful_items}/{context.total_items} successful "
                f"in {context.elapsed_time:.2f}s"
            )
            
            return batch_result
            
        except Exception as e:
            self.logger.error(f"Error in batch processing: {e}")
            self.stats["failed_items"] += len(materials)
            
            # Return error batch result
            error_results = [
                AIParseResult(
                    status=ParseStatus.ERROR,
                    data=MaterialParseData(
                        name=material,
                        original_unit="",
                        original_price=0.0
                    ),
                    confidence=0.0,
                    processing_time=0.0,
                    error_message=str(e),
                    request_id=f"batch_item_{i}"
                )
                for i, material in enumerate(materials)
            ]
            
            return BatchParseResult(
                results=error_results,
                total_processed=len(materials),
                successful_count=0,
                failed_count=len(materials),
                success_rate=0.0,
                processing_time=context.elapsed_time
            )
    
    async def _process_parallel(
        self, 
        materials: List[str], 
        config: BatchConfiguration, 
        context: BatchProcessingContext
    ) -> List[AIParseResult[MaterialParseData]]:
        """
        Process materials in parallel batches.
        
        Args:
            materials: List of materials
            config: Batch configuration
            context: Processing context
            
        Returns:
            List of parse results
        """
        all_results = []
        
        # Create batches
        batches = [
            materials[i:i + config.batch_size]
            for i in range(0, len(materials), config.batch_size)
        ]
        
        # Process batches with controlled concurrency
        semaphore = asyncio.Semaphore(config.max_workers)
        
        async def process_batch_with_semaphore(batch: List[str], batch_idx: int) -> List[AIParseResult[MaterialParseData]]:
            async with semaphore:
                context.current_batch = batch_idx + 1
                return await self._process_single_batch(batch, context)
        
        # Execute all batches concurrently
        batch_results = await asyncio.gather(
            *[process_batch_with_semaphore(batch, i) for i, batch in enumerate(batches)],
            return_exceptions=True
        )
        
        # Collect results
        for batch_result in batch_results:
            if isinstance(batch_result, Exception):
                # Handle batch error
                self.logger.error(f"Batch processing error: {batch_result}")
                context.failed_items += config.batch_size
            else:
                all_results.extend(batch_result)
        
        return all_results
    
    async def _process_sequential(
        self, 
        materials: List[str], 
        config: BatchConfiguration, 
        context: BatchProcessingContext
    ) -> List[AIParseResult[MaterialParseData]]:
        """
        Process materials sequentially.
        
        Args:
            materials: List of materials
            config: Batch configuration
            context: Processing context
            
        Returns:
            List of parse results
        """
        all_results = []
        
        # Create batches
        batches = [
            materials[i:i + config.batch_size]
            for i in range(0, len(materials), config.batch_size)
        ]
        
        # Process batches sequentially
        for batch_idx, batch in enumerate(batches):
            context.current_batch = batch_idx + 1
            
            try:
                batch_results = await self._process_single_batch(batch, context)
                all_results.extend(batch_results)
                
            except Exception as e:
                self.logger.error(f"Error processing batch {batch_idx + 1}: {e}")
                
                # Create error results for this batch
                error_results = [
                    AIParseResult(
                        status=ParseStatus.ERROR,
                        data=MaterialParseData(
                            name=material,
                            original_unit="",
                            original_price=0.0
                        ),
                        confidence=0.0,
                        processing_time=0.0,
                        error_message=str(e),
                        request_id=f"batch_{batch_idx}_item_{i}"
                    )
                    for i, material in enumerate(batch)
                ]
                
                all_results.extend(error_results)
                context.failed_items += len(batch)
        
        return all_results
    
    async def _process_single_batch(
        self, 
        batch: List[str], 
        context: BatchProcessingContext
    ) -> List[AIParseResult[MaterialParseData]]:
        """
        Process a single batch of materials.
        
        Args:
            batch: Batch of materials
            context: Processing context
            
        Returns:
            List of parse results
        """
        self.logger.debug(f"Processing batch {context.current_batch}/{context.total_batches} ({len(batch)} items)")
        
        # Parse batch using material parser service
        batch_result = await self.material_parser_service.parse_batch(batch)
        
        # Update context
        context.processed_items += len(batch)
        context.successful_items += batch_result.successful_count
        context.failed_items += batch_result.failed_count
        
        # Update progress
        context.update_progress()
        
        return batch_result.results
    
    async def parse_large_dataset(
        self, 
        materials: List[str], 
        chunk_size: int = 1000,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> BatchParseResult[MaterialParseData]:
        """
        Parse very large datasets with chunking and memory management.
        
        Args:
            materials: List of material descriptions
            chunk_size: Size of each chunk
            progress_callback: Optional progress callback
            
        Returns:
            BatchParseResult: Comprehensive results
        """
        self.logger.info(f"Processing large dataset: {len(materials)} materials in chunks of {chunk_size}")
        
        all_results = []
        total_successful = 0
        total_failed = 0
        start_time = time.time()
        
        # Process in chunks
        for i in range(0, len(materials), chunk_size):
            chunk = materials[i:i + chunk_size]
            chunk_progress = (i / len(materials)) * 100
            
            self.logger.info(f"Processing chunk {i//chunk_size + 1}/{(len(materials) + chunk_size - 1)//chunk_size}")
            
            # Process chunk
            chunk_result = await self.parse_batch(chunk)
            
            # Accumulate results
            all_results.extend(chunk_result.results)
            total_successful += chunk_result.successful_count
            total_failed += chunk_result.failed_count
            
            # Update progress
            if progress_callback:
                progress_callback(chunk_progress)
            
            # Optional: Force garbage collection for memory management
            import gc
            gc.collect()
        
        # Final progress update
        if progress_callback:
            progress_callback(100.0)
        
        processing_time = time.time() - start_time
        
        # Create final result
        return BatchParseResult(
            results=all_results,
            total_processed=len(materials),
            successful_count=total_successful,
            failed_count=total_failed,
            success_rate=total_successful / len(materials) if len(materials) > 0 else 0.0,
            processing_time=processing_time
        )
    
    async def parse_from_multiple_files(
        self, 
        file_paths: List[Union[str, Path]],
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> BatchParseResult[MaterialParseData]:
        """
        Parse materials from multiple files.
        
        Args:
            file_paths: List of file paths
            progress_callback: Optional progress callback
            
        Returns:
            BatchParseResult: Combined results from all files
        """
        self.logger.info(f"Processing {len(file_paths)} files")
        
        all_results = []
        total_successful = 0
        total_failed = 0
        start_time = time.time()
        
        for i, file_path in enumerate(file_paths):
            try:
                self.logger.info(f"Processing file {i+1}/{len(file_paths)}: {file_path}")
                
                # Parse file
                file_result = await self.material_parser_service.parse_from_file(file_path)
                
                # Accumulate results
                all_results.extend(file_result.results)
                total_successful += file_result.successful_count
                total_failed += file_result.failed_count
                
                # Update progress
                if progress_callback:
                    progress_callback(((i + 1) / len(file_paths)) * 100)
                
            except Exception as e:
                self.logger.error(f"Error processing file {file_path}: {e}")
                total_failed += 1
        
        processing_time = time.time() - start_time
        
        return BatchParseResult(
            results=all_results,
            total_processed=len(all_results),
            successful_count=total_successful,
            failed_count=total_failed,
            success_rate=total_successful / len(all_results) if len(all_results) > 0 else 0.0,
            processing_time=processing_time
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get batch processing statistics.
        
        Returns:
            Dict[str, Any]: Statistics dictionary
        """
        return {
            "service_name": self.service_name,
            "version": self.version,
            "batch_statistics": self.stats.copy(),
            "configuration": {
                "batch_size": self.batch_config.batch_size,
                "max_workers": self.batch_config.max_workers,
                "parallel_processing": self.batch_config.parallel_processing
            },
            "health_status": self.get_health_details()
        }
    
    def update_batch_config(self, **kwargs) -> None:
        """
        Update batch processing configuration.
        
        Args:
            **kwargs: Configuration parameters to update
        """
        for key, value in kwargs.items():
            if hasattr(self.batch_config, key):
                setattr(self.batch_config, key, value)
                self.logger.info(f"Updated batch config: {key} = {value}")
    
    def clear_statistics(self) -> None:
        """Clear all statistics"""
        self.stats = {
            "total_batch_operations": 0,
            "total_items_processed": 0,
            "successful_items": 0,
            "failed_items": 0,
            "average_batch_size": 0.0,
            "average_processing_time": 0.0,
            "peak_concurrency": 0
        }
        self.logger.info("Statistics cleared")


# Service factory
@lru_cache(maxsize=1)
def get_batch_parser_service() -> BatchParserService:
    """
    Get Batch Parser Service instance (singleton).
    
    Returns:
        BatchParserService: Service instance
    """
    return BatchParserService()


# Async context manager for service
@asynccontextmanager
async def batch_parser_service_context():
    """
    Async context manager for Batch Parser Service.
    
    Yields:
        BatchParserService: Service instance
    """
    service = get_batch_parser_service()
    try:
        yield service
    finally:
        # Cleanup if needed
        pass


# Convenience functions
async def parse_batch(
    materials: List[str], 
    batch_size: int = 10,
    max_workers: int = 5,
    progress_callback: Optional[Callable[[float], None]] = None
) -> BatchParseResult[MaterialParseData]:
    """
    Quick batch parse with custom settings.
    
    Args:
        materials: List of material descriptions
        batch_size: Size of each batch
        max_workers: Maximum concurrent workers
        progress_callback: Optional progress callback
        
    Returns:
        BatchParseResult: Batch parsing results
    """
    service = get_batch_parser_service()
    
    # Create custom batch config
    batch_config = BatchConfiguration(
        batch_size=batch_size,
        max_workers=max_workers,
        parallel_processing=True
    )
    
    return await service.parse_batch(materials, batch_config, progress_callback)


async def parse_large_dataset(
    materials: List[str], 
    chunk_size: int = 1000,
    progress_callback: Optional[Callable[[float], None]] = None
) -> BatchParseResult[MaterialParseData]:
    """
    Quick large dataset parse.
    
    Args:
        materials: List of material descriptions
        chunk_size: Size of each chunk
        progress_callback: Optional progress callback
        
    Returns:
        BatchParseResult: Batch parsing results
    """
    service = get_batch_parser_service()
    return await service.parse_large_dataset(materials, chunk_size, progress_callback) 