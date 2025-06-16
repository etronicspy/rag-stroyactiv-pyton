"""
Advanced Search Service for Materials

Продвинутый сервис поиска материалов с расширенными возможностями:
- Многокритериальная фильтрация
- Fuzzy search с настраиваемой толерантностью  
- Мульти-поле поиск с весами
- Автодополнение и предложения
- Аналитика поиска
- Cursor-based пагинация
"""

import asyncio
import json
import re
import time
from base64 import b64encode, b64decode
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Set
from difflib import SequenceMatcher
import logging

from core.schemas.materials import (
    AdvancedSearchQuery, MaterialFilterOptions, SortOption, PaginationOptions,
    SearchResponse, MaterialSearchResult, SearchSuggestion, SearchHighlight,
    SearchAnalytics, Material
)
from core.repositories.cached_materials import CachedMaterialsRepository
from core.database.adapters.redis_adapter import RedisDatabase
from core.database.exceptions import DatabaseError, ValidationError

logger = logging.getLogger(__name__)


class AdvancedSearchService:
    """Advanced search service with comprehensive filtering and analytics.
    
    Продвинутый сервис поиска с комплексной фильтрацией и аналитикой.
    """
    
    def __init__(
        self,
        materials_repo: CachedMaterialsRepository,
        redis_db: RedisDatabase,
        analytics_enabled: bool = True
    ):
        self.materials_repo = materials_repo
        self.redis_db = redis_db
        self.analytics_enabled = analytics_enabled
        
        # Search configuration
        self.fuzzy_algorithms = {
            'levenshtein': self._levenshtein_similarity,
            'jaro_winkler': self._jaro_winkler_similarity,
            'sequence_matcher': self._sequence_matcher_similarity
        }
        
        # Field weights for multi-field search
        self.field_weights = {
            'name': 0.4,
            'description': 0.3,
            'use_category': 0.2,
            'sku': 0.1
        }
        
        # Cache keys
        self.suggestions_cache_key = "search_suggestions"
        self.analytics_cache_key = "search_analytics"
        self.popular_queries_key = "popular_queries"
        
    async def advanced_search(self, query: AdvancedSearchQuery) -> SearchResponse:
        """Perform advanced search with comprehensive filtering and sorting.
        
        Args:
            query: Advanced search query with filters and options
            
        Returns:
            Comprehensive search response with metadata
            
        Raises:
            DatabaseError: If search fails
            ValidationError: If query parameters are invalid
        """
        start_time = time.time()
        
        try:
            # Validate query
            await self._validate_search_query(query)
            
            # Track analytics
            if self.analytics_enabled and query.query:
                asyncio.create_task(self._track_search_analytics(query))
            
            # Perform search based on type
            if query.search_type == "vector":
                raw_results = await self._vector_search(query)
            elif query.search_type == "sql":
                raw_results = await self._sql_search(query)
            elif query.search_type == "fuzzy":
                raw_results = await self._fuzzy_search(query)
            else:  # hybrid
                raw_results = await self._hybrid_search(query)
            
            # Apply filters
            filtered_results = await self._apply_filters(raw_results, query.filters)
            
            # Apply sorting
            sorted_results = await self._apply_sorting(filtered_results, query.sort_by)
            
            # Apply pagination
            paginated_results, pagination_info = await self._apply_pagination(
                sorted_results, query.pagination
            )
            
            # Generate highlights if requested
            if query.highlight_matches and query.query:
                paginated_results = await self._add_highlights(
                    paginated_results, query.query
                )
            
            # Generate suggestions if requested
            suggestions = None
            if query.include_suggestions and query.query:
                suggestions = await self._generate_suggestions(query.query)
            
            # Calculate execution time
            search_time_ms = (time.time() - start_time) * 1000
            
            # Build response
            response = SearchResponse(
                results=paginated_results,
                total_count=len(filtered_results),
                page=query.pagination.page,
                page_size=query.pagination.page_size,
                total_pages=pagination_info['total_pages'],
                search_time_ms=search_time_ms,
                suggestions=suggestions,
                filters_applied=self._summarize_filters(query.filters),
                next_cursor=pagination_info.get('next_cursor')
            )
            
            logger.info(
                f"Advanced search completed: query='{query.query}', "
                f"results={len(paginated_results)}, time={search_time_ms:.2f}ms"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Advanced search failed: {e}")
            if isinstance(e, (DatabaseError, ValidationError)):
                raise
            raise DatabaseError(
                message="Advanced search failed",
                details=str(e)
            )
    
    async def _vector_search(self, query: AdvancedSearchQuery) -> List[Dict[str, Any]]:
        """Perform vector-based semantic search."""
        if not query.query:
            return []
        
        # Use cached repository for vector search
        materials = await self.materials_repo.vector_search(
            query=query.query,
            limit=query.pagination.page_size * 5,  # Get more for filtering
            threshold=query.fuzzy_threshold or 0.7
        )
        
        # Convert to standard format
        results = []
        for material in materials:
            results.append({
                'material': material,
                'score': getattr(material, 'score', 0.8),
                'search_type': 'vector'
            })
        
        return results
    
    async def _sql_search(self, query: AdvancedSearchQuery) -> List[Dict[str, Any]]:
        """Perform SQL-based text search."""
        if not query.query:
            return []
        
        # Use hybrid repository for SQL search
        materials = await self.materials_repo.hybrid_repo.search_materials(
            query=query.query,
            limit=query.pagination.page_size * 5
        )
        
        # Convert to standard format
        results = []
        for material in materials:
            results.append({
                'material': material,
                'score': 0.7,  # Default SQL score
                'search_type': 'sql'
            })
        
        return results
    
    async def _fuzzy_search(self, query: AdvancedSearchQuery) -> List[Dict[str, Any]]:
        """Perform fuzzy search with configurable algorithms."""
        if not query.query:
            return []
        
        # Get all materials for fuzzy matching
        all_materials = await self.materials_repo.get_all_materials(limit=1000)
        
        results = []
        threshold = query.fuzzy_threshold or 0.8
        
        for material in all_materials:
            # Calculate fuzzy similarity for each field
            similarities = {}
            
            # Name similarity
            if material.name:
                similarities['name'] = self._sequence_matcher_similarity(
                    query.query.lower(), material.name.lower()
                )
            
            # Description similarity
            if material.description:
                similarities['description'] = self._sequence_matcher_similarity(
                    query.query.lower(), material.description.lower()
                )
            
            # Category similarity
            if material.use_category:
                similarities['category'] = self._sequence_matcher_similarity(
                    query.query.lower(), material.use_category.lower()
                )
            
            # Calculate weighted score
            weighted_score = 0.0
            total_weight = 0.0
            
            for field, similarity in similarities.items():
                weight = self.field_weights.get(field, 0.1)
                weighted_score += similarity * weight
                total_weight += weight
            
            if total_weight > 0:
                final_score = weighted_score / total_weight
                
                if final_score >= threshold:
                    results.append({
                        'material': material,
                        'score': final_score,
                        'search_type': 'fuzzy',
                        'field_similarities': similarities
                    })
        
        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results
    
    async def _hybrid_search(self, query: AdvancedSearchQuery) -> List[Dict[str, Any]]:
        """Perform hybrid search combining multiple approaches."""
        if not query.query:
            return []
        
        # Run searches in parallel
        vector_task = asyncio.create_task(self._vector_search(query))
        sql_task = asyncio.create_task(self._sql_search(query))
        fuzzy_task = asyncio.create_task(self._fuzzy_search(query))
        
        vector_results, sql_results, fuzzy_results = await asyncio.gather(
            vector_task, sql_task, fuzzy_task, return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(vector_results, Exception):
            logger.warning(f"Vector search failed: {vector_results}")
            vector_results = []
        if isinstance(sql_results, Exception):
            logger.warning(f"SQL search failed: {sql_results}")
            sql_results = []
        if isinstance(fuzzy_results, Exception):
            logger.warning(f"Fuzzy search failed: {fuzzy_results}")
            fuzzy_results = []
        
        # Combine and deduplicate results
        combined_results = self._combine_search_results(
            vector_results, sql_results, fuzzy_results
        )
        
        return combined_results
    
    def _combine_search_results(
        self,
        vector_results: List[Dict[str, Any]],
        sql_results: List[Dict[str, Any]],
        fuzzy_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Combine results from different search methods."""
        # Weights for different search types
        weights = {'vector': 0.5, 'sql': 0.3, 'fuzzy': 0.2}
        
        # Collect all results by material ID
        results_by_id = {}
        
        for results, search_type in [
            (vector_results, 'vector'),
            (sql_results, 'sql'),
            (fuzzy_results, 'fuzzy')
        ]:
            for result in results:
                material = result['material']
                material_id = material.id
                
                if material_id not in results_by_id:
                    results_by_id[material_id] = {
                        'material': material,
                        'scores': {},
                        'search_types': set()
                    }
                
                results_by_id[material_id]['scores'][search_type] = result['score']
                results_by_id[material_id]['search_types'].add(search_type)
        
        # Calculate combined scores
        final_results = []
        for material_id, data in results_by_id.items():
            combined_score = 0.0
            total_weight = 0.0
            
            for search_type, score in data['scores'].items():
                weight = weights.get(search_type, 0.1)
                combined_score += score * weight
                total_weight += weight
            
            if total_weight > 0:
                final_score = combined_score / total_weight
                
                # Boost score if found by multiple methods
                if len(data['search_types']) > 1:
                    final_score *= 1.2  # 20% boost for multi-method matches
                
                final_results.append({
                    'material': data['material'],
                    'score': min(final_score, 1.0),  # Cap at 1.0
                    'search_type': 'hybrid',
                    'found_by': list(data['search_types'])
                })
        
        # Sort by combined score
        final_results.sort(key=lambda x: x['score'], reverse=True)
        
        return final_results
    
    async def _apply_filters(
        self,
        results: List[Dict[str, Any]],
        filters: Optional[MaterialFilterOptions]
    ) -> List[Dict[str, Any]]:
        """Apply advanced filters to search results."""
        if not filters:
            return results
        
        filtered_results = []
        
        for result in results:
            material = result['material']
            
            # Category filter
            if filters.categories:
                if material.use_category not in filters.categories:
                    continue
            
            # Unit filter
            if filters.units:
                if material.unit not in filters.units:
                    continue
            
            # SKU pattern filter
            if filters.sku_pattern and material.sku:
                if not self._match_pattern(material.sku, filters.sku_pattern):
                    continue
            
            # Date filters
            if filters.created_after:
                if material.created_at < filters.created_after:
                    continue
            
            if filters.created_before:
                if material.created_at > filters.created_before:
                    continue
            
            if filters.updated_after:
                if material.updated_at < filters.updated_after:
                    continue
            
            if filters.updated_before:
                if material.updated_at > filters.updated_before:
                    continue
            
            # Similarity threshold filter
            if filters.min_similarity:
                if result['score'] < filters.min_similarity:
                    continue
            
            filtered_results.append(result)
        
        return filtered_results
    
    async def _apply_sorting(
        self,
        results: List[Dict[str, Any]],
        sort_options: Optional[List[SortOption]]
    ) -> List[Dict[str, Any]]:
        """Apply multi-field sorting to results."""
        if not sort_options:
            return results
        
        def sort_key(result):
            material = result['material']
            keys = []
            
            for sort_option in sort_options:
                field = sort_option.field
                direction = sort_option.direction
                
                if field == "relevance":
                    value = result['score']
                elif field == "name":
                    value = material.name or ""
                elif field == "created_at":
                    value = material.created_at
                elif field == "updated_at":
                    value = material.updated_at
                elif field == "use_category":
                    value = material.use_category or ""
                elif field == "unit":
                    value = material.unit or ""
                elif field == "sku":
                    value = material.sku or ""
                else:
                    value = ""
                
                # Reverse for descending order
                if direction == "desc":
                    if isinstance(value, str):
                        value = value.lower()
                        keys.append((-ord(value[0]) if value else 0, value))
                    else:
                        keys.append(-value if value is not None else 0)
                else:
                    if isinstance(value, str):
                        value = value.lower()
                    keys.append(value if value is not None else "")
            
            return tuple(keys)
        
        try:
            sorted_results = sorted(results, key=sort_key)
            return sorted_results
        except Exception as e:
            logger.warning(f"Sorting failed, returning unsorted results: {e}")
            return results
    
    async def _apply_pagination(
        self,
        results: List[Dict[str, Any]],
        pagination: PaginationOptions
    ) -> Tuple[List[MaterialSearchResult], Dict[str, Any]]:
        """Apply pagination to results."""
        total_count = len(results)
        total_pages = (total_count + pagination.page_size - 1) // pagination.page_size
        
        # Calculate offset
        offset = (pagination.page - 1) * pagination.page_size
        
        # Get page results
        page_results = results[offset:offset + pagination.page_size]
        
        # Convert to MaterialSearchResult
        search_results = []
        for result in page_results:
            search_result = MaterialSearchResult(
                material=result['material'],
                score=result['score'],
                search_type=result['search_type'],
                highlights=result.get('highlights')
            )
            search_results.append(search_result)
        
        # Generate cursor for next page
        next_cursor = None
        if pagination.page < total_pages:
            cursor_data = {
                'page': pagination.page + 1,
                'total_count': total_count
            }
            next_cursor = b64encode(json.dumps(cursor_data).encode()).decode()
        
        pagination_info = {
            'total_pages': total_pages,
            'next_cursor': next_cursor
        }
        
        return search_results, pagination_info
    
    async def _add_highlights(
        self,
        results: List[MaterialSearchResult],
        query: str
    ) -> List[MaterialSearchResult]:
        """Add text highlights to search results."""
        query_terms = query.lower().split()
        
        for result in results:
            highlights = []
            material = result.material
            
            # Highlight in name
            if material.name:
                highlighted_name = self._highlight_text(material.name, query_terms)
                if highlighted_name != material.name:
                    highlights.append(SearchHighlight(
                        field="name",
                        original=material.name,
                        highlighted=highlighted_name
                    ))
            
            # Highlight in description
            if material.description:
                highlighted_desc = self._highlight_text(material.description, query_terms)
                if highlighted_desc != material.description:
                    highlights.append(SearchHighlight(
                        field="description",
                        original=material.description,
                        highlighted=highlighted_desc
                    ))
            
            # Highlight in category
            if material.use_category:
                highlighted_cat = self._highlight_text(material.use_category, query_terms)
                if highlighted_cat != material.use_category:
                    highlights.append(SearchHighlight(
                        field="use_category",
                        original=material.use_category,
                        highlighted=highlighted_cat
                    ))
            
            result.highlights = highlights if highlights else None
        
        return results
    
    def _highlight_text(self, text: str, query_terms: List[str]) -> str:
        """Add HTML highlights to text."""
        highlighted = text
        
        for term in query_terms:
            if len(term) >= 2:  # Only highlight terms with 2+ characters
                pattern = re.compile(re.escape(term), re.IGNORECASE)
                highlighted = pattern.sub(f'<mark>{term}</mark>', highlighted)
        
        return highlighted
    
    async def _generate_suggestions(self, query: str) -> List[SearchSuggestion]:
        """Generate search suggestions based on query."""
        suggestions = []
        
        try:
            # Get cached suggestions
            cached_suggestions = await self.redis_db.get(
                f"{self.suggestions_cache_key}:{query.lower()}"
            )
            
            if cached_suggestions:
                return [SearchSuggestion(**s) for s in cached_suggestions]
            
            # Generate new suggestions
            # 1. Popular queries that start with the query
            popular_queries = await self._get_popular_queries()
            for pop_query in popular_queries[:5]:
                if pop_query.query.lower().startswith(query.lower()) and pop_query.query.lower() != query.lower():
                    suggestions.append(SearchSuggestion(
                        text=pop_query.query,
                        type="query",
                        score=0.9
                    ))
            
            # 2. Material names that contain the query
            materials = await self.materials_repo.get_all_materials(limit=100)
            for material in materials:
                if query.lower() in material.name.lower():
                    suggestions.append(SearchSuggestion(
                        text=material.name,
                        type="material",
                        score=0.8
                    ))
                    
                    if len(suggestions) >= 10:
                        break
            
            # 3. Categories that contain the query
            categories = set()
            for material in materials:
                if query.lower() in material.use_category.lower():
                    categories.add(material.use_category)
            
            for category in list(categories)[:3]:
                suggestions.append(SearchSuggestion(
                    text=category,
                    type="category",
                    score=0.7
                ))
            
            # Sort by score and limit
            suggestions.sort(key=lambda x: x.score, reverse=True)
            suggestions = suggestions[:8]
            
            # Cache suggestions
            await self.redis_db.set(
                f"{self.suggestions_cache_key}:{query.lower()}",
                [s.dict() for s in suggestions],
                ttl=3600  # 1 hour
            )
            
            return suggestions
            
        except Exception as e:
            logger.warning(f"Failed to generate suggestions: {e}")
            return []
    
    async def _track_search_analytics(self, query: AdvancedSearchQuery):
        """Track search analytics asynchronously."""
        try:
            analytics = SearchAnalytics(
                query=query.query or "",
                results_count=0,  # Will be updated after search
                search_time_ms=0.0,  # Will be updated after search
                search_type=query.search_type
            )
            
            # Store in Redis
            analytics_key = f"{self.analytics_cache_key}:{datetime.utcnow().strftime('%Y-%m-%d')}"
            await self.redis_db.lpush(analytics_key, analytics.dict())
            

            
        except Exception as e:
            logger.warning(f"Failed to track analytics: {e}")
    

    
    async def get_search_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get search analytics for a date range."""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=7)
            if not end_date:
                end_date = datetime.utcnow()
            
            analytics_data = {
                'total_searches': 0,
                'avg_search_time': 0.0,
                'avg_results_count': 0.0,
                'search_types': defaultdict(int),
                'popular_queries': [],
                'daily_stats': {}
            }
            
            # Collect daily analytics
            current_date = start_date.date()
            end_date_only = end_date.date()
            
            while current_date <= end_date_only:
                date_str = current_date.strftime('%Y-%m-%d')
                analytics_key = f"{self.analytics_cache_key}:{date_str}"
                
                daily_searches = await self.redis_db.lrange(analytics_key, 0, -1)
                daily_stats = {
                    'searches': len(daily_searches),
                    'avg_time': 0.0,
                    'avg_results': 0.0,
                    'search_types': defaultdict(int)
                }
                
                if daily_searches:
                    total_time = 0.0
                    total_results = 0
                    
                    for search_data in daily_searches:
                        if isinstance(search_data, dict):
                            total_time += search_data.get('search_time_ms', 0)
                            total_results += search_data.get('results_count', 0)
                            search_type = search_data.get('search_type', 'unknown')
                            daily_stats['search_types'][search_type] += 1
                            analytics_data['search_types'][search_type] += 1
                    
                    daily_stats['avg_time'] = total_time / len(daily_searches)
                    daily_stats['avg_results'] = total_results / len(daily_searches)
                
                analytics_data['daily_stats'][date_str] = daily_stats
                analytics_data['total_searches'] += daily_stats['searches']
                
                current_date = current_date.replace(day=current_date.day + 1)
            
            # Calculate overall averages
            if analytics_data['total_searches'] > 0:
                total_time = sum(day['avg_time'] * day['searches'] 
                               for day in analytics_data['daily_stats'].values())
                total_results = sum(day['avg_results'] * day['searches'] 
                                  for day in analytics_data['daily_stats'].values())
                
                analytics_data['avg_search_time'] = total_time / analytics_data['total_searches']
                analytics_data['avg_results_count'] = total_results / analytics_data['total_searches']
            
            return analytics_data
            
        except Exception as e:
            logger.error(f"Failed to get search analytics: {e}")
            return {'error': str(e)}
    
    # Utility methods for fuzzy search
    def _levenshtein_similarity(self, s1: str, s2: str) -> float:
        """Calculate Levenshtein similarity."""
        if not s1 or not s2:
            return 0.0
        
        max_len = max(len(s1), len(s2))
        if max_len == 0:
            return 1.0
        
        distance = self._levenshtein_distance(s1, s2)
        return 1.0 - (distance / max_len)
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance."""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _jaro_winkler_similarity(self, s1: str, s2: str) -> float:
        """Calculate Jaro-Winkler similarity."""
        # Simplified implementation
        if not s1 or not s2:
            return 0.0
        
        if s1 == s2:
            return 1.0
        
        # Use SequenceMatcher as approximation
        return SequenceMatcher(None, s1, s2).ratio()
    
    def _sequence_matcher_similarity(self, s1: str, s2: str) -> float:
        """Calculate similarity using SequenceMatcher."""
        if not s1 or not s2:
            return 0.0
        
        return SequenceMatcher(None, s1, s2).ratio()
    
    def _match_pattern(self, text: str, pattern: str) -> bool:
        """Match text against pattern with wildcards."""
        # Convert shell-style wildcards to regex
        regex_pattern = pattern.replace('*', '.*').replace('?', '.')
        return bool(re.match(f"^{regex_pattern}$", text, re.IGNORECASE))
    
    async def _validate_search_query(self, query: AdvancedSearchQuery):
        """Validate search query parameters."""
        if query.pagination.page < 1:
            raise ValidationError("Page number must be >= 1")
        
        if query.pagination.page_size < 1 or query.pagination.page_size > 100:
            raise ValidationError("Page size must be between 1 and 100")
        
        if query.fuzzy_threshold and (query.fuzzy_threshold < 0 or query.fuzzy_threshold > 1):
            raise ValidationError("Fuzzy threshold must be between 0 and 1")
        
        if query.filters and query.filters.min_similarity:
            if query.filters.min_similarity < 0 or query.filters.min_similarity > 1:
                raise ValidationError("Minimum similarity must be between 0 and 1")
    
    def _summarize_filters(self, filters: Optional[MaterialFilterOptions]) -> Optional[Dict[str, Any]]:
        """Summarize applied filters for response."""
        if not filters:
            return None
        
        summary = {}
        
        if filters.categories:
            summary['categories'] = filters.categories
        
        if filters.units:
            summary['units'] = filters.units
        
        if filters.sku_pattern:
            summary['sku_pattern'] = filters.sku_pattern
        
        if filters.created_after or filters.created_before:
            date_range = {}
            if filters.created_after:
                date_range['from'] = filters.created_after.isoformat()
            if filters.created_before:
                date_range['to'] = filters.created_before.isoformat()
            summary['created_date_range'] = date_range
        
        if filters.updated_after or filters.updated_before:
            date_range = {}
            if filters.updated_after:
                date_range['from'] = filters.updated_after.isoformat()
            if filters.updated_before:
                date_range['to'] = filters.updated_before.isoformat()
            summary['updated_date_range'] = date_range
        
        if filters.search_fields:
            summary['search_fields'] = filters.search_fields
        
        if filters.min_similarity:
            summary['min_similarity'] = filters.min_similarity
        
        return summary if summary else None
