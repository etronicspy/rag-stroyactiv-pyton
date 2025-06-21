"""
Dynamic Batch Processor for optimized data processing.

Динамический батч-процессор для оптимизированной обработки данных.
"""

import asyncio
import psutil
import time
from core.logging import get_logger
from typing import List, Dict, Any, Optional, Callable, TypeVar, Generic, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import math

logger = get_logger(__name__)

T = TypeVar('T')
R = TypeVar('R')


@dataclass
class BatchConfig:
    """Configuration for dynamic batch processing."""
    min_batch_size: int = 10
    max_batch_size: int = 1000
    target_memory_usage: float = 0.7  # 70% of available memory
    target_processing_time: float = 2.0  # 2 seconds per batch
    memory_safety_margin: float = 0.1  # 10% safety margin
    adaptive_sizing: bool = True
    enable_metrics: bool = True


@dataclass
class BatchMetrics:
    """Metrics for batch processing performance."""
    batch_size: int
    processing_time: float
    memory_used: int
    memory_available: int
    throughput: float  # items per second
    efficiency: float  # 0-1 scale
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ProcessingResult:
    """Result of batch processing operation."""
    processed_items: int
    failed_items: int
    total_time: float
    batches_processed: int
    average_batch_size: float
    total_memory_used: int
    throughput: float
    errors: List[str] = field(default_factory=list)


class DynamicBatchProcessor(Generic[T, R]):
    """
    Dynamic batch processor with intelligent sizing and resource management.
    
    Features:
    - Adaptive batch sizing based on memory and processing time
    - Resource monitoring and automatic adjustment
    - Parallel batch processing with concurrency control
    - Performance metrics and optimization
    - Error handling and retry logic
    - Memory-aware processing to prevent OOM
    """
    
    def __init__(
        self,
        processor_func: Callable[[List[T]], List[R]],
        config: Optional[BatchConfig] = None,
        max_concurrent_batches: int = 3,
        enable_parallel_processing: bool = True,
    ):
        """
        Initialize dynamic batch processor.
        
        Args:
            processor_func: Function to process each batch
            config: Batch processing configuration
            max_concurrent_batches: Maximum concurrent batch processing
            enable_parallel_processing: Enable parallel batch execution
        """
        self.processor_func = processor_func
        self.config = config or BatchConfig()
        self.max_concurrent_batches = max_concurrent_batches
        self.enable_parallel_processing = enable_parallel_processing
        
        # Performance tracking
        self.metrics_history: deque = deque(maxlen=100)
        self.current_batch_size = self.config.min_batch_size
        self.processing_semaphore = asyncio.Semaphore(max_concurrent_batches)
        
        # Adaptive parameters
        self.size_adjustment_factor = 1.2
        self.performance_threshold = 0.8
        self.consecutive_adjustments = 0
        self.last_adjustment_time = time.time()
        
        logger.info(
            f"✅ DynamicBatchProcessor initialized: "
            f"batch_size={self.current_batch_size}, "
            f"max_concurrent={max_concurrent_batches}, "
            f"parallel={'enabled' if enable_parallel_processing else 'disabled'}"
        )

    async def process_items(
        self, 
        items: List[T],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> ProcessingResult:
        """
        Process items using dynamic batching with optimization.
        
        Args:
            items: List of items to process
            progress_callback: Optional callback for progress updates
            
        Returns:
            ProcessingResult with detailed metrics
        """
        start_time = time.time()
        total_items = len(items)
        
        if not items:
            return ProcessingResult(
                processed_items=0,
                failed_items=0,
                total_time=0.0,
                batches_processed=0,
                average_batch_size=0.0,
                total_memory_used=0,
                throughput=0.0
            )
        
        logger.info(f"🚀 Starting dynamic batch processing: {total_items} items")
        
        try:
            # Analyze items for optimal initial batch size
            await self._analyze_and_adjust_initial_batch_size(items[:100])
            
            # Create batches
            batches = await self._create_dynamic_batches(items)
            
            # Process batches
            if self.enable_parallel_processing and len(batches) > 1:
                results = await self._process_batches_parallel(batches, progress_callback)
            else:
                results = await self._process_batches_sequential(batches, progress_callback)
            
            # Aggregate results
            processed_items = sum(r.processed_items for r in results)
            failed_items = sum(r.failed_items for r in results)
            total_memory_used = sum(r.total_memory_used for r in results)
            all_errors = []
            for r in results:
                all_errors.extend(r.errors)
            
            total_time = time.time() - start_time
            throughput = processed_items / total_time if total_time > 0 else 0
            
            result = ProcessingResult(
                processed_items=processed_items,
                failed_items=failed_items,
                total_time=total_time,
                batches_processed=len(batches),
                average_batch_size=total_items / len(batches) if batches else 0,
                total_memory_used=total_memory_used,
                throughput=throughput,
                errors=all_errors
            )
            
            logger.info(
                f"✅ Batch processing completed: "
                f"{processed_items}/{total_items} items processed "
                f"in {total_time:.2f}s ({throughput:.1f} items/s)"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Batch processing failed: {e}")
            return ProcessingResult(
                processed_items=0,
                failed_items=total_items,
                total_time=time.time() - start_time,
                batches_processed=0,
                average_batch_size=0.0,
                total_memory_used=0,
                throughput=0.0,
                errors=[str(e)]
            )

    async def _analyze_and_adjust_initial_batch_size(self, sample_items: List[T]):
        """Analyze sample items to determine optimal initial batch size."""
        if not sample_items:
            return
        
        try:
            # Estimate memory usage per item
            sample_size = min(len(sample_items), 10)
            sample_memory = self._estimate_memory_usage(sample_items[:sample_size])
            avg_memory_per_item = sample_memory / sample_size if sample_size > 0 else 1000
            
            # Get available memory
            memory_info = psutil.virtual_memory()
            available_memory = memory_info.available
            target_memory = available_memory * self.config.target_memory_usage
            
            # Calculate optimal batch size based on memory
            memory_based_batch_size = int(
                target_memory / avg_memory_per_item * (1 - self.config.memory_safety_margin)
            )
            
            # Clamp to configured limits
            optimal_size = max(
                self.config.min_batch_size,
                min(memory_based_batch_size, self.config.max_batch_size)
            )
            
            # Update current batch size
            old_size = self.current_batch_size
            self.current_batch_size = optimal_size
            
            logger.debug(
                f"📊 Batch size analysis: "
                f"memory_per_item={avg_memory_per_item}B, "
                f"available_memory={available_memory//1024//1024}MB, "
                f"batch_size: {old_size} → {optimal_size}"
            )
            
        except Exception as e:
            logger.warning(f"Failed to analyze batch size: {e}")

    async def _create_dynamic_batches(self, items: List[T]) -> List[List[T]]:
        """Create dynamic batches with adaptive sizing."""
        batches = []
        current_batch = []
        current_size = self.current_batch_size
        
        for i, item in enumerate(items):
            current_batch.append(item)
            
            # Check if batch is ready
            if len(current_batch) >= current_size:
                batches.append(current_batch)
                current_batch = []
                
                # Adaptive sizing: adjust based on system resources
                if self.config.adaptive_sizing and len(batches) % 5 == 0:
                    current_size = await self._calculate_adaptive_batch_size()
        
        # Add remaining items as final batch
        if current_batch:
            batches.append(current_batch)
        
        logger.debug(f"📦 Created {len(batches)} dynamic batches, sizes: {[len(b) for b in batches]}")
        return batches

    async def _calculate_adaptive_batch_size(self) -> int:
        """Calculate adaptive batch size based on current performance."""
        if not self.metrics_history:
            return self.current_batch_size
        
        try:
            # Analyze recent performance
            recent_metrics = list(self.metrics_history)[-10:]  # Last 10 batches
            
            if len(recent_metrics) < 3:
                return self.current_batch_size
            
            # Calculate average efficiency and processing time
            avg_efficiency = sum(m.efficiency for m in recent_metrics) / len(recent_metrics)
            avg_processing_time = sum(m.processing_time for m in recent_metrics) / len(recent_metrics)
            
            # Get current system resources
            memory_info = psutil.virtual_memory()
            memory_usage = 1 - (memory_info.available / memory_info.total)
            
            # Adjust batch size based on performance and resources
            adjustment_factor = 1.0
            
            # If efficiency is low or processing time is high, reduce batch size
            if avg_efficiency < self.performance_threshold:
                adjustment_factor *= 0.8
            elif avg_processing_time > self.config.target_processing_time:
                adjustment_factor *= 0.9
            
            # If memory usage is high, reduce batch size
            if memory_usage > self.config.target_memory_usage:
                adjustment_factor *= 0.7
            
            # If performance is good and resources available, increase batch size
            elif avg_efficiency > 0.9 and memory_usage < 0.5:
                adjustment_factor *= 1.2
            
            # Calculate new batch size
            new_batch_size = int(self.current_batch_size * adjustment_factor)
            new_batch_size = max(
                self.config.min_batch_size,
                min(new_batch_size, self.config.max_batch_size)
            )
            
            # Track consecutive adjustments to avoid oscillation
            if new_batch_size != self.current_batch_size:
                self.consecutive_adjustments += 1
                self.last_adjustment_time = time.time()
            else:
                self.consecutive_adjustments = 0
            
            # Limit rapid adjustments
            if self.consecutive_adjustments > 3:
                time_since_last = time.time() - self.last_adjustment_time
                if time_since_last < 10:  # Wait at least 10 seconds
                    return self.current_batch_size
            
            if new_batch_size != self.current_batch_size:
                logger.debug(
                    f"🔧 Adaptive batch sizing: {self.current_batch_size} → {new_batch_size} "
                    f"(efficiency={avg_efficiency:.2f}, memory={memory_usage:.2f})"
                )
            
            return new_batch_size
            
        except Exception as e:
            logger.warning(f"Failed to calculate adaptive batch size: {e}")
            return self.current_batch_size

    async def _process_batches_parallel(
        self, 
        batches: List[List[T]], 
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[ProcessingResult]:
        """Process batches in parallel with concurrency control."""
        results = []
        processed_items = 0
        total_items = sum(len(batch) for batch in batches)
        
        # Create semaphore for controlling concurrency
        async def process_single_batch(batch_idx: int, batch: List[T]) -> ProcessingResult:
            async with self.processing_semaphore:
                return await self._process_single_batch(batch_idx, batch)
        
        # Process batches in parallel
        tasks = [
            asyncio.create_task(process_single_batch(i, batch))
            for i, batch in enumerate(batches)
        ]
        
        # Wait for completion and track progress
        for i, task in enumerate(asyncio.as_completed(tasks)):
            try:
                result = await task
                results.append(result)
                processed_items += result.processed_items
                
                # Call progress callback
                if progress_callback:
                    progress_callback(processed_items, total_items)
                
                logger.debug(f"📋 Batch {i+1}/{len(batches)} completed")
                
            except Exception as e:
                logger.error(f"❌ Batch {i} failed: {e}")
                # Create error result
                batch_size = len(batches[i]) if i < len(batches) else 0
                results.append(ProcessingResult(
                    processed_items=0,
                    failed_items=batch_size,
                    total_time=0.0,
                    batches_processed=0,
                    average_batch_size=batch_size,
                    total_memory_used=0,
                    throughput=0.0,
                    errors=[str(e)]
                ))
        
        return results

    async def _process_batches_sequential(
        self, 
        batches: List[List[T]], 
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[ProcessingResult]:
        """Process batches sequentially."""
        results = []
        processed_items = 0
        total_items = sum(len(batch) for batch in batches)
        
        for i, batch in enumerate(batches):
            try:
                result = await self._process_single_batch(i, batch)
                results.append(result)
                processed_items += result.processed_items
                
                # Call progress callback
                if progress_callback:
                    progress_callback(processed_items, total_items)
                
                logger.debug(f"📋 Batch {i+1}/{len(batches)} completed")
                
            except Exception as e:
                logger.error(f"❌ Batch {i} failed: {e}")
                results.append(ProcessingResult(
                    processed_items=0,
                    failed_items=len(batch),
                    total_time=0.0,
                    batches_processed=0,
                    average_batch_size=len(batch),
                    total_memory_used=0,
                    throughput=0.0,
                    errors=[str(e)]
                ))
        
        return results

    async def _process_single_batch(self, batch_idx: int, batch: List[T]) -> ProcessingResult:
        """Process a single batch with metrics collection."""
        start_time = time.time()
        memory_before = self._get_memory_usage()
        
        try:
            # Process the batch
            if asyncio.iscoroutinefunction(self.processor_func):
                processed_results = await self.processor_func(batch)
            else:
                # Run in thread pool for CPU-bound tasks
                loop = asyncio.get_event_loop()
                processed_results = await loop.run_in_executor(
                    None, self.processor_func, batch
                )
            
            processing_time = time.time() - start_time
            memory_after = self._get_memory_usage()
            memory_used = max(0, memory_after - memory_before)
            
            # Calculate metrics
            batch_size = len(batch)
            throughput = batch_size / processing_time if processing_time > 0 else 0
            
            # Calculate efficiency (0-1 scale based on throughput and resource usage)
            target_throughput = batch_size / self.config.target_processing_time
            efficiency = min(1.0, throughput / target_throughput) if target_throughput > 0 else 0.5
            
            # Store metrics for adaptive sizing
            if self.config.enable_metrics:
                metrics = BatchMetrics(
                    batch_size=batch_size,
                    processing_time=processing_time,
                    memory_used=memory_used,
                    memory_available=psutil.virtual_memory().available,
                    throughput=throughput,
                    efficiency=efficiency
                )
                self.metrics_history.append(metrics)
            
            logger.debug(
                f"✅ Batch {batch_idx}: {batch_size} items in {processing_time:.2f}s "
                f"({throughput:.1f} items/s, efficiency={efficiency:.2f})"
            )
            
            return ProcessingResult(
                processed_items=len(processed_results) if processed_results else batch_size,
                failed_items=max(0, batch_size - (len(processed_results) if processed_results else batch_size)),
                total_time=processing_time,
                batches_processed=1,
                average_batch_size=batch_size,
                total_memory_used=memory_used,
                throughput=throughput
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ Batch {batch_idx} processing failed: {e}")
            
            return ProcessingResult(
                processed_items=0,
                failed_items=len(batch),
                total_time=processing_time,
                batches_processed=0,
                average_batch_size=len(batch),
                total_memory_used=0,
                throughput=0.0,
                errors=[str(e)]
            )

    def _estimate_memory_usage(self, items: List[T]) -> int:
        """Estimate memory usage for a list of items."""
        try:
            import sys
            return sum(sys.getsizeof(item) for item in items)
        except Exception:
            # Fallback estimation
            return len(items) * 1000  # 1KB per item estimate

    def _get_memory_usage(self) -> int:
        """Get current memory usage in bytes."""
        try:
            process = psutil.Process()
            return process.memory_info().rss
        except Exception:
            return 0

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        if not self.metrics_history:
            return {
                "total_batches": 0,
                "average_batch_size": 0.0,
                "average_processing_time": 0.0,
                "average_throughput": 0.0,
                "average_efficiency": 0.0,
                "current_batch_size": self.current_batch_size
            }
        
        metrics = list(self.metrics_history)
        
        return {
            "total_batches": len(metrics),
            "average_batch_size": sum(m.batch_size for m in metrics) / len(metrics),
            "average_processing_time": sum(m.processing_time for m in metrics) / len(metrics),
            "average_throughput": sum(m.throughput for m in metrics) / len(metrics),
            "average_efficiency": sum(m.efficiency for m in metrics) / len(metrics),
            "current_batch_size": self.current_batch_size,
            "memory_optimization": {
                "total_memory_used": sum(m.memory_used for m in metrics),
                "average_memory_per_batch": sum(m.memory_used for m in metrics) / len(metrics),
                "peak_memory_usage": max(m.memory_used for m in metrics) if metrics else 0
            },
            "adaptive_adjustments": self.consecutive_adjustments,
            "optimization_features": [
                "Dynamic batch sizing",
                "Memory-aware processing",
                "Parallel batch execution",
                "Performance metrics collection",
                "Adaptive resource management"
            ]
        } 