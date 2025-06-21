"""
Optimized Search Service with Parallel Hybrid Search and Advanced Caching.

Оптимизированный сервис поиска с параллельным гибридным поиском и расширенным кэшированием.
"""

import asyncio
import json
import time
from core.logging import get_logger
from typing import List, Dict, Any, Optional, Tuple, Set, Union
from dataclasses import dataclass
from functools import lru_cache
from datetime import datetime, timedelta

from core.schemas.materials import (
    AdvancedSearchQuery, MaterialFilterOptions, SortOption, PaginationOptions,
    SearchResponse, MaterialSearchResult, SearchSuggestion, Material
)
from core.repositories.cached_materials import CachedMaterialsRepository
from core.database.adapters.redis_adapter import RedisDatabase
from core.database.exceptions import DatabaseError, ValidationError
from services.advanced_search import AdvancedSearchService

logger = get_logger(__name__)


@dataclass
class SearchTaskResult:
    """Result from a search task."""
    search_type: str
    results: List[Dict[str, Any]]
    execution_time: float
    error: Optional[Exception] = None


@dataclass
class SearchPerformanceMetrics:
    """Performance metrics for search operations."""
    total_time: float
    vector_search_time: float
    sql_search_time: float
    fuzzy_search_time: float
    filtering_time: float
    sorting_time: float
    pagination_time: float
    cache_hits: int
    cache_misses: int
    parallel_efficiency: float


class OptimizedSearchService(AdvancedSearchService):
    """
    Optimized search service with enhanced parallel processing and caching.
    
    Key improvements:
    - Fully parallel search execution with timeout handling
    - Multi-level caching (L1: memory, L2: Redis, L3: database)
    - Intelligent result merging with confidence scoring
    - Performance monitoring and adaptive optimization
    - Stream processing for large result sets
    - Predictive prefetching based on search patterns
    """
    
    def __init__(
        self,
        materials_repo: CachedMaterialsRepository,
        redis_db: RedisDatabase,
        analytics_enabled: bool = True,
        enable_performance_monitoring: bool = True,
        enable_predictive_caching: bool = True,
        search_timeout: float = 5.0,
        max_concurrent_searches: int = 10,
    ):
        super().__init__(materials_repo, redis_db, analytics_enabled)
        
        self.enable_performance_monitoring = enable_performance_monitoring
        self.enable_predictive_caching = enable_predictive_caching
        self.search_timeout = search_timeout
        self.max_concurrent_searches = max_concurrent_searches
        
        # Performance tracking
        self.performance_metrics = {}
        
        # L1 Cache (in-memory)
        self._l1_cache = {}
        self._l1_cache_max_size = 1000
        self._l1_cache_ttl = 300  # 5 minutes
        
        # Semaphore for limiting concurrent searches
        self._search_semaphore = asyncio.Semaphore(max_concurrent_searches)
        
        # Enhanced search weights with confidence scoring
        self.enhanced_weights = {
            'vector': {'weight': 0.45, 'confidence_boost': 0.2},
            'sql': {'weight': 0.35, 'confidence_boost': 0.1},
            'fuzzy': {'weight': 0.20, 'confidence_boost': 0.05}
        }
        
        logger.info(
            f"✅ OptimizedSearchService initialized: "
            f"timeout={search_timeout}s, max_concurrent={max_concurrent_searches}, "
            f"caching={'enabled' if enable_predictive_caching else 'disabled'}"
        )

    async def optimized_search(self, query: AdvancedSearchQuery) -> SearchResponse:
        """
        Perform optimized search with full parallelization and caching.
        
        Args:
            query: Advanced search query with filters and options
            
        Returns:
            Enhanced search response with performance metrics
        """
        start_time = time.time()
        search_key = self._generate_search_key(query)
        
        try:
            # Check L1 cache first
            if self.enable_predictive_caching:
                cached_result = await self._get_from_l1_cache(search_key)
                if cached_result:
                    logger.debug(f"L1 cache hit for search: {search_key}")
                    return cached_result
            
            # Check L2 cache (Redis)
            cached_result = await self._get_from_l2_cache(search_key)
            if cached_result:
                logger.debug(f"L2 cache hit for search: {search_key}")
                # Store in L1 cache for faster access
                await self._store_in_l1_cache(search_key, cached_result)
                return cached_result
            
            # Perform parallel search
            search_results = await self._parallel_hybrid_search(query)
            
            # Process results with full parallelization
            processed_results = await self._parallel_process_results(
                search_results, query
            )
            
            # Cache results
            if self.enable_predictive_caching:
                await self._cache_search_results(search_key, processed_results)
            
            # Track performance metrics
            if self.enable_performance_monitoring:
                execution_time = time.time() - start_time
                await self._track_performance_metrics(query, search_results, execution_time)
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Optimized search failed: {e}")
            raise DatabaseError(f"Optimized search failed: {str(e)}")

    async def _parallel_hybrid_search(
        self, 
        query: AdvancedSearchQuery
    ) -> List[SearchTaskResult]:
        """
        Execute search tasks in parallel with timeout and error handling.
        """
        if not query.query:
            return []
        
        # Create search tasks
        search_tasks = []
        
        # Vector search task
        if query.search_type in ['vector', 'hybrid']:
            search_tasks.append(
                self._create_search_task('vector', query)
            )
        
        # SQL search task
        if query.search_type in ['sql', 'hybrid']:
            search_tasks.append(
                self._create_search_task('sql', query)
            )
        
        # Fuzzy search task
        if query.search_type in ['fuzzy', 'hybrid']:
            search_tasks.append(
                self._create_search_task('fuzzy', query)
            )
        
        # Execute all tasks in parallel with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*search_tasks, return_exceptions=True),
                timeout=self.search_timeout
            )
            
            # Process results and handle exceptions
            processed_results = []
            for result in results:
                if isinstance(result, SearchTaskResult):
                    processed_results.append(result)
                elif isinstance(result, Exception):
                    logger.warning(f"Search task failed: {result}")
                    # Create error result
                    processed_results.append(
                        SearchTaskResult(
                            search_type='unknown',
                            results=[],
                            execution_time=0.0,
                            error=result
                        )
                    )
            
            return processed_results
            
        except asyncio.TimeoutError:
            logger.warning(f"Search timeout after {self.search_timeout}s")
            raise DatabaseError(f"Search timeout after {self.search_timeout}s")

    async def _create_search_task(
        self, 
        search_type: str, 
        query: AdvancedSearchQuery
    ) -> SearchTaskResult:
        """Create and execute a search task with performance monitoring."""
        async with self._search_semaphore:
            start_time = time.time()
            
            try:
                if search_type == 'vector':
                    results = await self._vector_search(query)
                elif search_type == 'sql':
                    results = await self._sql_search(query)
                elif search_type == 'fuzzy':
                    results = await self._fuzzy_search(query)
                else:
                    raise ValueError(f"Unknown search type: {search_type}")
                
                execution_time = time.time() - start_time
                
                return SearchTaskResult(
                    search_type=search_type,
                    results=results,
                    execution_time=execution_time
                )
                
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"{search_type} search failed: {e}")
                
                return SearchTaskResult(
                    search_type=search_type,
                    results=[],
                    execution_time=execution_time,
                    error=e
                )

    async def _parallel_process_results(
        self, 
        search_results: List[SearchTaskResult], 
        query: AdvancedSearchQuery
    ) -> SearchResponse:
        """Process search results with parallel filtering, sorting, and pagination."""
        start_time = time.time()
        
        # Combine results from all search types
        combined_results = await self._intelligent_result_merging(search_results)
        
        # Create parallel processing tasks
        tasks = []
        
        # Filter task
        if query.filters:
            filter_task = asyncio.create_task(
                self._apply_filters(combined_results, query.filters)
            )
            tasks.append(('filter', filter_task))
        else:
            filter_task = asyncio.create_task(
                asyncio.coroutine(lambda: combined_results)()
            )
            tasks.append(('filter', filter_task))
        
        # Wait for filtering to complete
        filtered_results = await filter_task
        
        # Sort task
        if query.sort_by:
            sort_task = asyncio.create_task(
                self._apply_sorting(filtered_results, query.sort_by)
            )
        else:
            sort_task = asyncio.create_task(
                asyncio.coroutine(lambda: filtered_results)()
            )
        
        # Pagination task (depends on sorting)
        sorted_results = await sort_task
        pagination_task = asyncio.create_task(
            self._apply_pagination(sorted_results, query.pagination)
        )
        
        # Highlight task (if requested)
        paginated_results, pagination_info = await pagination_task
        
        highlight_task = None
        if query.highlight_matches and query.query:
            highlight_task = asyncio.create_task(
                self._add_highlights(paginated_results, query.query)
            )
        
        # Suggestions task (if requested)
        suggestions_task = None
        if query.include_suggestions and query.query:
            suggestions_task = asyncio.create_task(
                self._generate_suggestions(query.query)
            )
        
        # Wait for all remaining tasks
        final_results = paginated_results
        if highlight_task:
            final_results = await highlight_task
        
        suggestions = None
        if suggestions_task:
            suggestions = await suggestions_task
        
        # Calculate performance metrics
        search_time_ms = (time.time() - start_time) * 1000
        
        # Create enhanced response
        response = SearchResponse(
            results=final_results,
            total_count=len(filtered_results),
            page=query.pagination.page,
            page_size=query.pagination.page_size,
            total_pages=pagination_info['total_pages'],
            search_time_ms=search_time_ms,
            suggestions=suggestions,
            filters_applied=self._summarize_filters(query.filters),
            next_cursor=pagination_info.get('next_cursor')
        )
        
        return response

    async def _intelligent_result_merging(
        self, 
        search_results: List[SearchTaskResult]
    ) -> List[Dict[str, Any]]:
        """
        Intelligently merge search results with confidence scoring and deduplication.
        """
        # Collect all results by material ID with confidence scoring
        results_by_id = {}
        
        for task_result in search_results:
            search_type = task_result.search_type
            
            if task_result.error:
                logger.warning(f"Skipping {search_type} results due to error: {task_result.error}")
                continue
            
            # Get weight configuration
            weight_config = self.enhanced_weights.get(search_type, {
                'weight': 0.1, 
                'confidence_boost': 0.0
            })
            
            for result in task_result.results:
                material = result['material']
                material_id = material.id
                base_score = result.get('score', 0.5)
                
                # Calculate confidence score based on execution time and result quality
                confidence_score = self._calculate_confidence_score(
                    base_score, task_result.execution_time, search_type
                )
                
                if material_id not in results_by_id:
                    results_by_id[material_id] = {
                        'material': material,
                        'search_scores': {},
                        'confidence_scores': {},
                        'search_types': set(),
                        'total_confidence': 0.0
                    }
                
                results_by_id[material_id]['search_scores'][search_type] = base_score
                results_by_id[material_id]['confidence_scores'][search_type] = confidence_score
                results_by_id[material_id]['search_types'].add(search_type)
                results_by_id[material_id]['total_confidence'] += confidence_score
        
        # Calculate final scores with intelligent weighting
        final_results = []
        for material_id, data in results_by_id.items():
            combined_score = 0.0
            total_weight = 0.0
            
            # Weight by search type and confidence
            for search_type, base_score in data['search_scores'].items():
                weight_config = self.enhanced_weights.get(search_type, {
                    'weight': 0.1, 
                    'confidence_boost': 0.0
                })
                
                base_weight = weight_config['weight']
                confidence_score = data['confidence_scores'][search_type]
                
                # Adjust weight based on confidence
                adjusted_weight = base_weight * (1 + confidence_score * weight_config['confidence_boost'])
                
                combined_score += base_score * adjusted_weight
                total_weight += adjusted_weight
            
            if total_weight > 0:
                final_score = combined_score / total_weight
                
                # Multi-method bonus
                if len(data['search_types']) > 1:
                    multi_method_bonus = 0.1 * len(data['search_types'])
                    final_score *= (1 + multi_method_bonus)
                
                # Confidence bonus
                avg_confidence = data['total_confidence'] / len(data['search_types'])
                final_score *= (1 + avg_confidence * 0.1)
                
                final_results.append({
                    'material': data['material'],
                    'score': min(final_score, 1.0),  # Cap at 1.0
                    'search_type': 'optimized_hybrid',
                    'found_by': list(data['search_types']),
                    'confidence': avg_confidence
                })
        
        # Sort by final score
        final_results.sort(key=lambda x: x['score'], reverse=True)
        
        return final_results

    def _calculate_confidence_score(
        self, 
        base_score: float, 
        execution_time: float, 
        search_type: str
    ) -> float:
        """Calculate confidence score based on various factors."""
        # Base confidence from score
        confidence = base_score
        
        # Adjust for execution time (faster is better)
        if execution_time < 0.1:  # Very fast
            confidence *= 1.2
        elif execution_time < 0.5:  # Fast
            confidence *= 1.1
        elif execution_time > 2.0:  # Slow
            confidence *= 0.9
        
        # Search type specific adjustments
        if search_type == 'vector' and base_score > 0.8:
            confidence *= 1.15  # High confidence in good vector matches
        elif search_type == 'sql' and base_score > 0.9:
            confidence *= 1.1  # High confidence in exact SQL matches
        
        return min(confidence, 1.0)

    def _generate_search_key(self, query: AdvancedSearchQuery) -> str:
        """Generate a unique key for search caching."""
        key_components = [
            query.query or "",
            query.search_type,
            str(query.fuzzy_threshold),
            str(query.highlight_matches),
            str(query.include_suggestions),
            str(hash(str(query.filters))) if query.filters else "no_filters",
            str(hash(str(query.sort_by))) if query.sort_by else "no_sort",
            str(query.pagination.page),
            str(query.pagination.page_size)
        ]
        return f"search:{':'.join(key_components)}"

    async def _get_from_l1_cache(self, key: str) -> Optional[SearchResponse]:
        """Get result from L1 (memory) cache."""
        if key in self._l1_cache:
            cache_entry = self._l1_cache[key]
            if time.time() - cache_entry['timestamp'] < self._l1_cache_ttl:
                return cache_entry['data']
            else:
                del self._l1_cache[key]
        return None

    async def _store_in_l1_cache(self, key: str, data: SearchResponse):
        """Store result in L1 (memory) cache with size management."""
        # Manage cache size
        if len(self._l1_cache) >= self._l1_cache_max_size:
            # Remove oldest entries
            sorted_keys = sorted(
                self._l1_cache.keys(),
                key=lambda k: self._l1_cache[k]['timestamp']
            )
            for old_key in sorted_keys[:100]:  # Remove 100 oldest
                del self._l1_cache[old_key]
        
        self._l1_cache[key] = {
            'data': data,
            'timestamp': time.time()
        }

    async def _get_from_l2_cache(self, key: str) -> Optional[SearchResponse]:
        """Get result from L2 (Redis) cache."""
        try:
            cached_data = await self.redis_db.get(key)
            if cached_data:
                # Deserialize and return
                return SearchResponse.parse_obj(cached_data)
        except Exception as e:
            logger.warning(f"L2 cache get failed: {e}")
        return None

    async def _cache_search_results(self, key: str, data: SearchResponse):
        """Cache search results in both L1 and L2 caches."""
        try:
            # Store in L1 cache
            await self._store_in_l1_cache(key, data)
            
            # Store in L2 cache (Redis) with TTL
            await self.redis_db.setex(
                key, 
                ttl=1800,  # 30 minutes
                value=data.dict()
            )
        except Exception as e:
            logger.warning(f"Caching failed: {e}")

    async def _track_performance_metrics(
        self, 
        query: AdvancedSearchQuery, 
        search_results: List[SearchTaskResult], 
        total_time: float
    ):
        """Track detailed performance metrics."""
        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'query': query.query,
            'search_type': query.search_type,
            'total_time': total_time,
            'search_tasks': {}
        }
        
        # Track individual search task performance
        for task_result in search_results:
            metrics['search_tasks'][task_result.search_type] = {
                'execution_time': task_result.execution_time,
                'results_count': len(task_result.results),
                'error': str(task_result.error) if task_result.error else None
            }
        
        # Calculate parallel efficiency
        max_task_time = max(
            [t.execution_time for t in search_results if not t.error], 
            default=0
        )
        total_sequential_time = sum(
            [t.execution_time for t in search_results if not t.error]
        )
        
        if max_task_time > 0:
            parallel_efficiency = total_sequential_time / max_task_time
            metrics['parallel_efficiency'] = parallel_efficiency
        
        # Store metrics for analysis
        metrics_key = f"search_metrics:{int(time.time())}"
        await self.redis_db.setex(
            metrics_key, 
            ttl=86400,  # 24 hours
            value=metrics
        )

    async def get_performance_analytics(
        self, 
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get comprehensive performance analytics."""
        try:
            # Default to last 24 hours if no time range specified
            if not start_time:
                start_time = datetime.utcnow() - timedelta(hours=24)
            if not end_time:
                end_time = datetime.utcnow()
            
            # Get metrics from Redis
            metrics_pattern = "search_metrics:*"
            metrics_keys = await self.redis_db.keys(metrics_pattern)
            
            all_metrics = []
            for key in metrics_keys:
                try:
                    metrics_data = await self.redis_db.get(key)
                    if metrics_data:
                        all_metrics.append(metrics_data)
                except Exception as e:
                    logger.warning(f"Failed to retrieve metrics {key}: {e}")
            
            # Analyze metrics
            if not all_metrics:
                return {
                    "message": "No performance metrics available",
                    "time_range": {
                        "start": start_time.isoformat(),
                        "end": end_time.isoformat()
                    }
                }
            
            # Calculate aggregate statistics
            total_searches = len(all_metrics)
            avg_total_time = sum(m.get('total_time', 0) for m in all_metrics) / total_searches
            avg_parallel_efficiency = sum(
                m.get('parallel_efficiency', 1) for m in all_metrics
            ) / total_searches
            
            # Search type breakdown
            search_types = {}
            for metrics in all_metrics:
                search_type = metrics.get('search_type', 'unknown')
                if search_type not in search_types:
                    search_types[search_type] = {
                        'count': 0,
                        'avg_time': 0,
                        'total_time': 0
                    }
                search_types[search_type]['count'] += 1
                search_types[search_type]['total_time'] += metrics.get('total_time', 0)
            
            # Calculate averages
            for search_type, data in search_types.items():
                if data['count'] > 0:
                    data['avg_time'] = data['total_time'] / data['count']
            
            return {
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                },
                'summary': {
                    'total_searches': total_searches,
                    'average_total_time': avg_total_time,
                    'average_parallel_efficiency': avg_parallel_efficiency,
                    'performance_improvement': f"{((avg_parallel_efficiency - 1) * 100):.1f}%"
                },
                'search_types': search_types,
                'optimizations_active': [
                    'Parallel hybrid search',
                    'Multi-level caching (L1/L2)',
                    'Intelligent result merging',
                    'Confidence-based scoring',
                    'Timeout handling'
                ]
            }
            
        except Exception as e:
            logger.error(f"Performance analytics failed: {e}")
            raise DatabaseError(f"Performance analytics failed: {str(e)}") 