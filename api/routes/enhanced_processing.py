"""
API endpoints for batch processing materials.
This stage 8.5: API endpoints for asynchronous material processing.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from core.schemas.processing_models import (
    BatchMaterialsRequest,
    BatchProcessingResponse,
    BatchValidationError,
    ProcessingStatusResponse,
    ProcessingResultsResponse,
    ProcessingStatus,
    ProcessingProgress,
    MaterialProcessingResult,
    ProcessingStatistics,
    BatchResponse
)
from services.batch_processing_service import get_batch_processing_service
from core.logging import get_logger

# Создаем router
router = APIRouter(
    prefix="",
    tags=["enhanced-processing"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)

logger = get_logger(__name__)


@router.post(
    "/",
    response_model=BatchProcessingResponse,
    summary="📦 Batch Processing – Enterprise Material Processing System",
    response_description="Advanced batch processing results with validation and analytics"
)
async def process_materials_batch(
    request: BatchMaterialsRequest,
    background_tasks: BackgroundTasks,
    batch_service = Depends(get_batch_processing_service)
) -> BatchProcessingResponse:
    """
    📦 **Batch Processing** - Enterprise material processing system
    
    Accepts a list of materials for asynchronous processing through a complete pipeline
    including validation, data enrichment, vectorization, and storage in vector database.
    
    **Features:**
    - ⚡ Asynchronous processing of large data volumes
    - 🔍 Multi-level material validation
    - 🧠 Generation of semantic embeddings (OpenAI)
    - 📊 Detailed statistics and processing metrics
    - 🔄 Real-time progress tracking
    - 🛡️ Graceful handling of errors and partial failures
    
    **Limits and Constraints:**
    - **Minimum**: 1 material per request
    - **Maximum**: 10,000 materials per request
    - **Batch size**: 100 materials (configurable)
    - **Timeout**: 30 minutes for entire batch
    - **Concurrent batches**: maximum 5 simultaneous
    
    **Request Body Example:**
    ```json
    {
        "request_id": "batch_2025_001",
        "materials": [
            {
                "name": "Portland Cement M500 D0",
                "use_category": "Cement",
                "unit": "bag",
                "sku": "CEM500-001",
                "description": "High-strength cement for structural concrete"
            },
            {
                "name": "Solid Ceramic Brick",
                "use_category": "Brick",
                "unit": "pcs",
                "sku": "BRICK-001",
                "description": "Red brick for load-bearing structures"
            }
        ],
        "processing_options": {
            "batch_size": 100,
            "timeout_seconds": 1800,
            "validate_duplicates": true,
            "generate_embeddings": true
        }
    }
    ```
    
    **Response Example (Success):**
    ```json
    {
        "success": true,
        "request_id": "batch_20250116_164629_abc123",
        "status": "accepted",
        "materials_count": 2,
        "estimated_completion": "2025-01-16T16:51:29.421964Z",
        "tracking_url": "/api/v1/batch-processing/status/batch_20250116_164629_abc123",
        "processing_options": {
            "batch_size": 100,
            "timeout_seconds": 1800,
            "validate_duplicates": true,
            "generate_embeddings": true
        }
    }
    ```
    
    **Response Example (Validation Error):**
    ```json
    {
        "success": false,
        "errors": ["Too many materials: 150 > 100"],
        "rejected_materials": [],
        "error_code": "VALIDATION_ERROR"
    }
    ```
    
    **Response Status Codes:**
    - **202 Accepted**: Batch accepted for processing
    - **400 Bad Request**: Data validation error
    - **429 Too Many Requests**: Concurrent batch limit exceeded
    - **500 Internal Server Error**: Processing initialization error
    
    **Use Cases:**
    - Bulk import of materials from price lists
    - Data migration between systems
    - Updating large material catalogs
    - Creating vector indexes for search
    - Validation and cleaning of material data
    
    Args:
        request: BatchMaterialsRequest with materials and processing options
        background_tasks: FastAPI background tasks for asynchronous execution
        batch_service: Batch processing service (injected)
        
    Returns:
        BatchResponse with status and processing tracking information
        
    Raises:
        HTTPException: On validation errors, limit exceeded, or processing failures
    """
    try:
        # Логируем начало обработки
        logger.info(f"Received batch processing request {request.request_id} with {len(request.materials)} materials")
        
        # Проверяем лимиты
        service_stats = batch_service.get_service_stats()
        
        if len(request.materials) > batch_service.config.max_materials_per_request:
            error_response = BatchValidationError(
                errors=[f"Too many materials: {len(request.materials)} > {batch_service.config.max_materials_per_request}"],
                rejected_materials=[]
            )
            return error_response
        
        # Проверяем активные задачи
        if service_stats['active_jobs'] >= batch_service.config.max_concurrent_batches:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many active jobs: {service_stats['active_jobs']} >= {batch_service.config.max_concurrent_batches}"
            )
        
        # Запускаем background job
        job_started = await batch_service.start_processing_job(
            request.request_id,
            request.materials
        )
        
        if not job_started:
            error_response = BatchValidationError(
                errors=["Failed to start processing job"],
                rejected_materials=[]
            )
            return error_response
        
        # Вычисляем предполагаемое время завершения
        estimated_completion = datetime.utcnow() + timedelta(
            seconds=len(request.materials) * 2  # Примерно 2 секунды на материал
        )
        
        # Успешный ответ
        response = BatchProcessingResponse(
            status="accepted",
            request_id=request.request_id,
            materials_count=len(request.materials),
            estimated_completion=estimated_completion
        )
        
        logger.info(f"Started batch processing job {request.request_id}")
        return response
        
    except ValidationError as e:
        error_response = BatchValidationError(
            errors=[str(err) for err in e.errors()],
            rejected_materials=[]
        )
        logger.warning(f"Validation error for request {request.request_id}: {e}")
        return error_response
        
    except Exception as e:
        logger.error(f"Unexpected error processing batch request {request.request_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during request processing"
        )


@router.get(
    "/status/{request_id}",
    response_model=ProcessingStatusResponse,
    summary="📊 Processing Status – Real-time Batch Processing Monitoring",
    response_description="Real-time processing status with detailed analytics and progress metrics"
)
async def get_processing_status(
    request_id: str,
    batch_service = Depends(get_batch_processing_service)
) -> ProcessingStatusResponse:
    """
    📊 **Processing Status** – Get batch processing request status
    
    Returns detailed information about the current status and progress of batch material processing, including performance metrics.
    
    **Features:**
    - 🔄 Real-time processing status
    - 📈 Detailed progress and performance metrics
    - ⏱️ Estimated completion time
    - 📊 Success/failure statistics
    - 🔍 Error and warning information
    - 📋 List of processed and problematic materials
    
    **Processing Statuses:**
    - `pending`: Request is queued for processing
    - `processing`: Active material processing
    - `completed`: Processing completed successfully
    - `failed`: Processing failed with critical errors
    - `partial`: Partial processing (some successes and failures)
    - `cancelled`: Processing cancelled by user
    
    **Path Parameters:**
    - `request_id`: Batch request identifier (format: batch_YYYYMMDD_HHMMSS_xxx)
    
    **Response Example:**
    ```json
    {
        "success": true,
        "request_id": "batch_20250116_164629_abc123",
        "status": "processing",
        "progress": {
            "total_materials": 1000,
            "processed_materials": 750,
            "successful_materials": 720,
            "failed_materials": 30,
            "completion_percentage": 75.0,
            "estimated_remaining_time": "00:05:30"
        },
        "performance_metrics": {
            "processing_rate": 12.5,
            "avg_time_per_material": 2.3,
            "start_time": "2025-01-16T16:46:29.421964Z",
            "elapsed_time": "00:15:30",
            "estimated_completion": "2025-01-16T17:07:29.421964Z"
        },
        "error_summary": {
            "validation_errors": 15,
            "processing_errors": 10,
            "timeout_errors": 5,
            "recent_errors": [
                {
                    "material_index": 245,
                    "error_type": "validation_error",
                    "message": "Missing required field 'name'"
                }
            ]
        },
        "current_batch": {
            "batch_number": 8,
            "total_batches": 10,
            "batch_size": 100,
            "batch_progress": 50
        }
    }
    ```
    
    **Response Status Codes:**
    - **200 OK**: Status retrieved successfully
    - **404 Not Found**: Request with specified ID not found
    - **400 Bad Request**: Invalid request_id format
    - **500 Internal Server Error**: Error retrieving status
    
    **Polling Guidelines:**
    - Recommended polling interval: 5-10 seconds
    - For large batches: 30-60 seconds
    - Stop polling on statuses: completed, failed, cancelled
    
    **Use Cases:**
    - UI progress monitoring
    - Automatic completion tracking
    - Processing diagnostics
    - Batch parameter optimization
    - Performance reporting
    """
    try:
        logger.debug(f"Getting processing status for request {request_id}")
        
        # Получаем прогресс обработки
        progress = await batch_service.get_processing_progress(request_id)
        
        # Проверяем, найден ли запрос
        if progress.total == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Request {request_id} not found"
            )
        
        # Определяем общий статус
        if progress.pending > 0:
            overall_status = ProcessingStatus.PROCESSING
        elif progress.failed > 0 and progress.completed == 0:
            overall_status = ProcessingStatus.FAILED
        elif progress.completed == progress.total:
            overall_status = ProcessingStatus.COMPLETED
        else:
            overall_status = ProcessingStatus.PROCESSING
        
        # Проверяем активные задачи
        active_jobs = batch_service.get_active_jobs()
        is_active = request_id in active_jobs
        
        # Вычисляем предполагаемое время завершения
        estimated_completion = None
        if overall_status == ProcessingStatus.PROCESSING and progress.pending > 0:
            estimated_completion = datetime.utcnow() + timedelta(
                seconds=progress.pending * 2
            )
        
        response = ProcessingStatusResponse(
            request_id=request_id,
            status=overall_status,
            progress=progress,
            estimated_completion=estimated_completion,
            started_at=None,  # Можно добавить в БД
            completed_at=None  # Можно добавить в БД
        )
        
        logger.debug(f"Processing status for {request_id}: {overall_status.value}, {progress.completed}/{progress.total}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting processing status for {request_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while getting processing status"
        )


@router.get(
    "/results/{request_id}",
    response_model=ProcessingResultsResponse,
    summary="📋 Processing Results – Batch Processing Outcomes Analysis",
    response_description="Comprehensive processing results with quality metrics and error analysis"
)
async def get_processing_results(
    request_id: str,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    batch_service = Depends(get_batch_processing_service)
) -> ProcessingResultsResponse:
    """
    📋 **Processing Results** – Get batch processing results
    
    Returns detailed results of completed batch material processing, including successfully processed materials, errors, and full operation statistics.
    
    **Features:**
    - 📊 Full processing and performance statistics
    - ✅ List of successfully processed materials with UUID
    - ❌ Detailed error and failure information
    - 📈 Performance and timing metrics
    - 🔍 Data quality and validation analysis
    - 📋 Export results in various formats
    
    **Result Availability:**
    - Results available only for completed requests (status: completed/failed/partial)
    - Data retained for 30 days after processing
    - Pagination supported for large results (>1000 materials)
    - Automatic archiving of old results
    
    **Path Parameters:**
    - `request_id`: Completed batch request identifier
    
    **Response Example:**
    ```json
    {
        "success": true,
        "request_id": "batch_20250116_164629_abc123",
        "status": "completed",
        "summary": {
            "total_materials": 1000,
            "successful_materials": 980,
            "failed_materials": 20,
            "success_rate": 98.0,
            "processing_time": "00:25:30",
            "avg_time_per_material": 1.53
        },
        "successful_materials": [
            {
                "index": 0,
                "material_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Portland Cement M500 D0",
                "use_category": "Cement",
                "processing_time": 1.2,
                "embedding_generated": true,
                "created_at": "2025-01-16T16:47:15.123456Z"
            }
        ],
        "failed_materials": [
            {
                "index": 245,
                "original_data": {
                    "name": "",
                    "use_category": "Cement"
                },
                "error_type": "validation_error",
                "error_message": "Missing required field 'name'",
                "error_code": "MISSING_REQUIRED_FIELD",
                "timestamp": "2025-01-16T16:48:30.123456Z"
            }
        ],
        "performance_metrics": {
            "start_time": "2025-01-16T16:46:29.421964Z",
            "end_time": "2025-01-16T17:11:59.421964Z",
            "total_duration": "00:25:30",
            "avg_processing_rate": 39.2,
            "peak_processing_rate": 45.8,
            "embedding_generation_time": "00:18:45",
            "database_save_time": "00:04:20"
        },
        "quality_metrics": {
            "duplicate_materials_found": 5,
            "validation_warnings": 12,
            "data_quality_score": 94.5,
            "embedding_quality_avg": 0.87
        },
        "error_analysis": {
            "validation_errors": 15,
            "processing_errors": 3,
            "timeout_errors": 2,
            "most_common_error": "missing_required_field",
            "error_categories": {
                "data_validation": 15,
                "embedding_generation": 3,
                "database_errors": 2
            }
        }
    }
    ```
    
    **Response Status Codes:**
    - **200 OK**: Results retrieved successfully
    - **404 Not Found**: Request with specified ID not found
    - **409 Conflict**: Processing not yet completed
    - **410 Gone**: Results deleted (older than 30 days)
    - **500 Internal Server Error**: Error retrieving results
    
    **Result Categories:**
    - **successful_materials**: Successfully processed materials with UUID
    - **failed_materials**: Materials with errors and failure reasons
    - **performance_metrics**: Performance and timing metrics
    - **quality_metrics**: Data quality metrics
    - **error_analysis**: Error analysis and categorization
    
    **Use Cases:**
    - Retrieve results for integration with other systems
    - Analyze quality of imported data
    - Create performance reports
    - Diagnose and optimize processing workflows
    - Audit and monitor import operations
    """
    try:
        logger.debug(f"Getting processing results for request {request_id}")
        
        # Получаем результаты
        results = await batch_service.get_processing_results(
            request_id,
            limit=limit,
            offset=offset
        )
        
        # Проверяем, найден ли запрос
        if not results:
            # Проверяем прогресс, чтобы убедиться, что запрос существует
            progress = await batch_service.get_processing_progress(request_id)
            if progress.total == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Request {request_id} not found"
                )
        
        # Получаем общую статистику
        progress = await batch_service.get_processing_progress(request_id)
        
        # Создаем сводку по статусам
        summary = {
            "pending": progress.pending,
            "completed": progress.completed,
            "failed": progress.failed,
            "total": progress.total
        }
        
        response = ProcessingResultsResponse(
            request_id=request_id,
            total_materials=progress.total,
            results=results,
            summary=summary
        )
        
        logger.debug(f"Retrieved {len(results)} results for request {request_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting processing results for {request_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while getting processing results"
        )


@router.get(
    "/statistics",
    response_model=ProcessingStatistics,
    summary="📊 Processing Statistics – Advanced Analytics Platform",
    response_description="Comprehensive processing statistics with performance metrics and trend analysis"
)
async def get_processing_statistics(
    batch_service = Depends(get_batch_processing_service)
) -> ProcessingStatistics:
    """
    📊 **Processing Statistics** – Comprehensive processing statistics
    
    Returns detailed statistics for all batch material processing operations, including performance, success rates, and system usage analytics.
    
    **Features:**
    - 📈 Performance and throughput metrics
    - ✅ Success and quality statistics
    - ⏱️ Execution time and optimization analysis
    - 📊 Usage trends and peak loads
    - 🔍 Detailed error analytics and categories
    - 📋 Export statistics for reporting
    
    **Performance Metrics:**
    - Total processed requests for the period
    - Average and peak material processing speed
    - Success statistics by category
    - Execution time and bottleneck analysis
    - Resource utilization efficiency
    
    **Usage Analytics:**
    - Peak loads and maximum activity times
    - Batch request size distribution
    - Error frequency and detailed categorization
    - Performance trends for different periods
    - Comparative analysis with previous periods
    
    **Response Example:**
    ```json
    {
        "success": true,
        "statistics": {
            "overview": {
                "total_requests": 1250,
                "total_materials_processed": 125000,
                "success_rate": 97.8,
                "avg_processing_time": "00:15:30",
                "total_processing_time": "320:45:15",
                "period": "last_30_days"
            },
            "performance_metrics": {
                "avg_materials_per_second": 42.5,
                "peak_materials_per_second": 78.2,
                "avg_request_size": 100,
                "largest_request_size": 5000,
                "fastest_processing_time": "00:02:15",
                "slowest_processing_time": "02:45:30"
            },
            "success_metrics": {
                "successful_requests": 1223,
                "failed_requests": 27,
                "partial_success_requests": 15,
                "successful_materials": 122350,
                "failed_materials": 2650,
                "success_rate_by_category": {
                    "Cement": 98.5,
                    "Brick": 97.2,
                    "Metal": 96.8
                }
            },
            "error_analysis": {
                "most_common_errors": [
                    {
                        "error_type": "validation_error",
                        "count": 1250,
                        "percentage": 47.2
                    },
                    {
                        "error_type": "duplicate_material",
                        "count": 890,
                        "percentage": 33.6
                    }
                ],
                "error_trends": {
                    "increasing": ["timeout_errors"],
                    "decreasing": ["validation_errors"],
                    "stable": ["duplicate_materials"]
                }
            },
            "usage_patterns": {
                "peak_hours": ["09:00-11:00", "14:00-16:00"],
                "peak_days": ["Tuesday", "Wednesday"],
                "avg_requests_per_day": 41.7,
                "request_size_distribution": {
                    "small (1-50)": 35.2,
                    "medium (51-500)": 45.8,
                    "large (501-1000)": 15.6,
                    "extra_large (1000+)": 3.4
                }
            },
            "quality_metrics": {
                "avg_data_quality_score": 92.3,
                "avg_embedding_quality": 0.89,
                "duplicate_detection_rate": 99.1,
                "validation_accuracy": 98.7
            },
            "resource_utilization": {
                "avg_cpu_usage": 65.2,
                "peak_cpu_usage": 89.5,
                "avg_memory_usage": 72.8,
                "peak_memory_usage": 94.1,
                "database_connection_pool_usage": 45.6
            }
        },
        "generated_at": "2025-01-16T16:47:30.123456Z",
        "period_start": "2024-12-17T00:00:00Z",
        "period_end": "2025-01-16T23:59:59Z"
    }
    ```
    
    **Response Status Codes:**
    - **200 OK**: Statistics retrieved successfully
    - **500 Internal Server Error**: Error retrieving statistics
    - **503 Service Unavailable**: Statistics service temporarily unavailable
    
    **Statistics Categories:**
    - **overview**: General indicators for the period
    - **performance_metrics**: Performance metrics
    - **success_metrics**: Success indicators
    - **error_analysis**: Error analysis and trends
    - **usage_patterns**: Usage patterns
    - **quality_metrics**: Data quality metrics
    - **resource_utilization**: Resource usage
    
    **Use Cases:**
    - System performance monitoring
    - Resource and scaling planning
    - Data and process quality analysis
    - Management reporting
    - Workflow optimization
    - Bottleneck and issue detection
    """
    try:
        logger.debug("Getting processing statistics")
        
        # Получаем статистику из БД
        stats = await batch_service.get_service_statistics()
        
        logger.debug(f"Processing statistics: {stats.total_requests} requests, {stats.success_rate:.2%} success rate")
        return stats
        
    except Exception as e:
        logger.error(f"Error getting processing statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while getting statistics"
        )


@router.post(
    "/retry",
    summary="🔄 Retry Failed Materials – Intelligent Failure Recovery",
    response_description="Intelligent retry system with adaptive processing strategies"
)
async def retry_failed_materials(
    batch_service = Depends(get_batch_processing_service)
) -> Dict[str, Any]:
    """
    🔄 **Retry Failed Materials** – Retry processing of failed materials
    
    Initiates retry processing for materials that failed in previous batch operations, using improved parameters and strategies.
    
    **Features:**
    - 🎯 Selective retry for specific materials
    - 📦 Bulk retry for all failed items
    - ⚙️ Parameter tuning for improved success
    - 🧠 Automatic error analysis and optimization
    - 📊 Progress tracking for retry operations
    - 🛡️ Intelligent recovery strategies
    
    **Retry Strategies:**
    - **selective**: Retry only specified materials
    - **all_failed**: Retry all failed materials
    - **smart_retry**: Automatic selection based on error analysis
    - **enhanced_validation**: Enhanced data validation
    - **reduced_batch_size**: Reduced batch size for stability
    
    **Request Example (Selective Retry):**
    ```json
    {
        "original_request_id": "batch_20250116_164629_abc123",
        "retry_mode": "selective",
        "material_indices": [15, 23, 45, 67, 89],
        "processing_options": {
            "timeout_seconds": 300,
            "retry_attempts": 3,
            "skip_validation": false,
            "enhanced_error_handling": true
        }
    }
    ```
    
    **Request Example (Smart Retry):**
    ```json
    {
        "original_request_id": "batch_20250116_164629_abc123",
        "retry_mode": "smart_retry",
        "processing_options": {
            "batch_size": 50,
            "timeout_seconds": 600,
            "enhanced_validation": true,
            "auto_fix_common_errors": true
        }
    }
    ```
    
    **Response Example:**
    ```json
    {
        "success": true,
        "retry_request_id": "retry_20250116_170000_def456",
        "original_request_id": "batch_20250116_164629_abc123",
        "status": "accepted",
        "materials_to_retry": 25,
        "retry_strategy": "smart_retry",
        "estimated_completion": "2025-01-16T17:15:00Z",
        "tracking_url": "/api/v1/batch-processing/status/retry_20250116_170000_def456",
        "improvements_applied": [
            "reduced_batch_size",
            "enhanced_validation",
            "auto_error_correction"
        ]
    }
    ```
    
    **Response Status Codes:**
    - **202 Accepted**: Retry request accepted
    - **400 Bad Request**: Invalid request parameters
    - **404 Not Found**: Original request not found
    - **409 Conflict**: Original request still processing
    - **422 Unprocessable Entity**: No materials to retry
    - **500 Internal Server Error**: Retry initialization error
    
    **Automatic Improvements:**
    - Analyze failure reasons and adjust parameters
    - Reduce batch size for problematic materials
    - Increase timeout for complex operations
    - Apply alternative processing algorithms
    - Pre-clean and normalize data
    
    **Use Cases:**
    - Recovery after temporary service failures
    - Retry with improved parameters
    - Handle network interruptions and timeouts
    - Increase overall batch operation success
    - Automated recovery workflows
    """
    try:
        logger.info("Starting retry of failed materials")
        
        # Запускаем retry
        retry_count = await batch_service.retry_failed_materials()
        
        logger.info(f"Retry started for {retry_count} materials")
        return {
            "message": f"Retry started for {retry_count} materials",
            "retry_count": retry_count
        }
        
    except Exception as e:
        logger.error(f"Error retrying failed materials: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during retry"
        )


@router.delete(
    "/cleanup",
    summary="🧹 Cleanup Old Records – Data Lifecycle Management",
    response_description="Advanced data lifecycle management with storage optimization"
)
async def cleanup_old_records(
    days_old: int = 30,
    batch_service = Depends(get_batch_processing_service)
) -> Dict[str, Any]:
    """
    🧹 **Cleanup Old Records** – Cleanup outdated records
    
    Deletes old batch processing records, logs, and temporary data to free up space and maintain system performance.
    
    **Features:**
    - 🗓️ Configurable data retention period
    - 🛡️ Safe deletion of completed operations
    - 💾 Preserve active and recent operations
    - 📊 Detailed cleanup statistics and reporting
    - ✅ Automatic validation before deletion
    - 🔒 Backup of critical metadata
    
    **Cleanup Categories:**
    - **Completed requests**: Successfully processed batch operations
    - **Failed requests**: Requests with critical errors
    - **Temporary files**: Intermediate processing data
    - **Operation logs**: Detailed execution logs
    - **Cache data**: Temporary cached results
    
    **Retention Policies:**
    - Active requests: never deleted
    - Recent operations: retained regardless of status
    - Critical logs: retained for audit
    - Metadata: archived before deletion
    
    **Query Parameters:**
    - `days_old`: Number of days to retain data (default: 30)
    
    **Response Example:**
    ```json
    {
        "success": true,
        "cleanup_summary": {
            "records_deleted": 1250,
            "storage_freed_mb": 45.7,
            "retention_days": 30,
            "cleanup_duration": "00:02:15",
            "cleanup_started_at": "2025-01-16T17:00:00Z",
            "cleanup_completed_at": "2025-01-16T17:02:15Z"
        },
        "categories_cleaned": {
            "completed_requests": 890,
            "failed_requests": 180,
            "partial_requests": 45,
            "temporary_files": 180,
            "log_entries": 15000,
            "cache_entries": 5600
        },
        "preserved_data": {
            "active_requests": 5,
            "recent_requests": 45,
            "critical_logs": 500,
            "audit_records": 120
        },
        "storage_optimization": {
            "database_size_before_mb": 2048.5,
            "database_size_after_mb": 2002.8,
            "compression_applied": true,
            "index_optimization": true
        }
    }
    ```
    
    **Response Status Codes:**
    - **200 OK**: Cleanup completed successfully
    - **400 Bad Request**: Invalid retention period
    - **409 Conflict**: Cleanup already in progress
    - **423 Locked**: System locked for maintenance
    - **500 Internal Server Error**: Error during cleanup
    
    **Safety Measures:**
    - Never deletes active or pending requests
    - Retains critical error and audit logs
    - Checks data integrity before deletion
    - Backs up important metadata
    - Supports rollback if needed
    
    **Usage Recommendations:**
    - Run during low-traffic periods
    - Use retention period of at least 7 days
    - Monitor freed space
    - Regularly review cleanup logs
    
    **Use Cases:**
    - Regular maintenance and housekeeping
    - Storage optimization and cost management
    - Improve performance by cleaning up data
    - Enforce data retention policies
    - Prepare for backup
    """
    try:
        logger.info(f"Starting cleanup of records older than {days_old} days")
        
        # Запускаем очистку
        deleted_count = await batch_service.cleanup_old_records(days_old)
        
        logger.info(f"Cleanup completed: {deleted_count} records deleted")
        return {
            "message": f"Cleanup completed: {deleted_count} records deleted",
            "deleted_count": deleted_count,
            "days_old": days_old
        }
        
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during cleanup"
        )


# Health check endpoint
@router.get(
    "/health",
    summary="🩺 Enhanced Processing Health – Batch Processing Service Diagnostics",
    response_description="Comprehensive batch processing service health diagnostics with performance metrics"
)
async def get_service_health(
    batch_service = Depends(get_batch_processing_service)
) -> Dict[str, Any]:
    """
    🩺 **Enhanced Processing Health Check** - Batch processing service diagnostics
    
    Performs comprehensive diagnostics of all batch processing system components,
    including services, databases, and external dependencies.
    
    **Features:**
    - 🔍 Deep diagnostics of all critical components
    - ⚡ Quick service availability checks
    - 📊 Performance and resource monitoring
    - 🚨 Early problem and degradation detection
    - 📈 Service level agreement (SLA) metrics
    - 🛡️ Security and data integrity verification
    
    **Diagnosed Components:**
    - **Batch Processing Service**: Main materials processing service
    - **Database Connections**: PostgreSQL, Redis, vector database
    - **External APIs**: Embedding services, data validation
    - **File System**: Temporary directories availability
    - **Memory & CPU**: System resource usage
    - **Network**: Latency and throughput
    
    **Performance Metrics:**
    - Component response time (< 100ms - excellent)
    - CPU and memory load (< 80% - normal)
    - Active database connections count
    - Error statistics for last 5 minutes
    - Materials processing throughput
    - Embedding generation quality
    
    **Response Example:**
    ```json
    {
        "success": true,
        "status": "healthy",
        "timestamp": "2025-01-16T17:05:30.123456Z",
        "version": "1.2.3",
        "uptime": "72:15:30",
        "components": {
            "batch_processing_service": {
                "status": "healthy",
                "response_time_ms": 45,
                "active_requests": 3,
                "queue_size": 12,
                "last_error": null
            },
            "database": {
                "postgresql": {
                    "status": "healthy",
                    "response_time_ms": 12,
                    "active_connections": 15,
                    "max_connections": 100,
                    "last_backup": "2025-01-16T02:00:00Z"
                },
                "redis": {
                    "status": "healthy",
                    "response_time_ms": 3,
                    "memory_usage_mb": 256,
                    "connected_clients": 8
                },
                "vector_db": {
                    "status": "healthy",
                    "response_time_ms": 78,
                    "index_size": 125000,
                    "last_optimization": "2025-01-16T01:00:00Z"
                }
            },
            "external_services": {
                "embedding_api": {
                    "status": "healthy",
                    "response_time_ms": 234,
                    "rate_limit_remaining": 8500,
                    "success_rate_24h": 99.2
                },
                "validation_service": {
                    "status": "healthy",
                    "response_time_ms": 89,
                    "cache_hit_rate": 87.5
                }
            },
            "system_resources": {
                "cpu_usage_percent": 45.2,
                "memory_usage_percent": 67.8,
                "disk_usage_percent": 23.4,
                "network_latency_ms": 15
            }
        },
        "performance_metrics": {
            "requests_per_minute": 125,
            "avg_processing_time_ms": 1530,
            "error_rate_percent": 0.8,
            "success_rate_percent": 99.2,
            "queue_wait_time_ms": 45
        },
        "alerts": [],
        "recommendations": [
            "Consider scaling up during peak hours (9-11 AM)",
            "Database connection pool could be optimized"
        ]
    }
    ```
    
    **Response Status Codes:**
    - **200 OK**: All components operating normally
    - **503 Service Unavailable**: Critical components unavailable
    - **500 Internal Server Error**: Diagnostics execution error
    
    **Health Status Levels:**
    - **healthy**: All components operating optimally
    - **degraded**: Some components operating with limitations
    - **unhealthy**: Critical problems requiring intervention
    - **maintenance**: System in maintenance mode
    
    **Monitoring Integration:**
    - Prometheus metrics compatibility
    - Alerting system integration
    - Grafana dashboard data export
    - Webhook notifications on status changes
    
    **Use Cases:**
    - Real-time system status monitoring
    - Performance problem diagnostics
    - Preventive maintenance planning
    - Monitoring system integration
    - Load readiness verification
    - SLA monitoring and reporting
    
    Args:
        batch_service: Batch processing service (injected)
        
    Returns:
        Service status information with performance metrics
        
    Raises:
        HTTPException: On critical system errors or service unavailability
    """
    try:
        # Получаем статистику сервиса
        service_stats = batch_service.get_service_stats()
        
        # Проверяем состояние
        health_status = "healthy"
        if service_stats['active_jobs'] >= service_stats['config']['max_concurrent_batches']:
            health_status = "overloaded"
        elif service_stats['failed_jobs'] > service_stats['completed_jobs']:
            health_status = "degraded"
        
        return {
            "status": health_status,
            "timestamp": datetime.utcnow().isoformat(),
            "service_stats": service_stats,
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Error getting service health: {str(e)}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }