"""
Body Cache Middleware для единого чтения request body.

Решает проблему зависаний при попытке нескольких middleware читать один request body.
Читает body один раз и кеширует в request.state для использования другими middleware.
"""

import asyncio
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)


class BodyCacheMiddleware(BaseHTTPMiddleware):
    """
    Middleware для единого чтения и кеширования request body.
    
    Предотвращает зависания при попытке нескольких middleware читать body.
    Читает body один раз для методов POST/PUT/PATCH и кеширует в request.state.
    """
    
    def __init__(
        self, 
        app,
        max_body_size: int = 10 * 1024 * 1024,  # 10MB по умолчанию
        methods_to_cache: list[str] = None
    ):
        super().__init__(app)
        self.max_body_size = max_body_size
        self.methods_to_cache = methods_to_cache or ["POST", "PUT", "PATCH"]
        
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """
        Читает и кеширует request body для использования другими middleware.
        """
        # Кешируем body только для методов с телом запроса
        if request.method in self.methods_to_cache:
            try:
                # Читаем body один раз
                body_bytes = await self._read_body_safely(request)
                
                # Кешируем в request.state для использования другими middleware
                request.state.cached_body_bytes = body_bytes
                request.state.cached_body_str = body_bytes.decode('utf-8') if body_bytes else ""
                request.state.body_cache_available = True
                
                logger.debug(f"Body cached for {request.method} {request.url.path}, size: {len(body_bytes)} bytes")
                
            except Exception as e:
                logger.error(f"Failed to cache body for {request.method} {request.url.path}: {e}")
                request.state.cached_body_bytes = b""
                request.state.cached_body_str = ""
                request.state.body_cache_available = False
        else:
            # Для GET и других методов без body
            request.state.cached_body_bytes = b""
            request.state.cached_body_str = ""
            request.state.body_cache_available = False
            
        # Продолжаем обработку запроса
        response = await call_next(request)
        return response
    
    async def _read_body_safely(self, request: Request) -> bytes:
        """
        Безопасно читает request body с ограничением размера и таймаутом.
        """
        try:
            # Читаем body с таймаутом для предотвращения зависаний
            body_bytes = await asyncio.wait_for(
                request.body(), 
                timeout=30.0  # 30 секунд таймаут
            )
            
            # Проверяем размер
            if len(body_bytes) > self.max_body_size:
                logger.warning(f"Request body too large: {len(body_bytes)} bytes, limit: {self.max_body_size}")
                raise ValueError(f"Request body too large: {len(body_bytes)} bytes")
                
            return body_bytes
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout reading request body for {request.method} {request.url.path}")
            raise
        except Exception as e:
            logger.error(f"Error reading request body: {e}")
            raise


def get_cached_body_bytes(request: Request) -> Optional[bytes]:
    """
    Получает кешированный body в виде bytes.
    Используется другими middleware вместо request.body().
    """
    if hasattr(request.state, 'body_cache_available') and request.state.body_cache_available:
        return getattr(request.state, 'cached_body_bytes', b"")
    return None


def get_cached_body_str(request: Request) -> Optional[str]:
    """
    Получает кешированный body в виде строки.
    Используется другими middleware вместо чтения body.
    """
    if hasattr(request.state, 'body_cache_available') and request.state.body_cache_available:
        return getattr(request.state, 'cached_body_str', "")
    return None


async def get_cached_body_json(request: Request) -> Optional[dict]:
    """
    Получает кешированный body как JSON.
    Используется другими middleware вместо request.json().
    """
    try:
        body_str = get_cached_body_str(request)
        if body_str:
            import json
            return json.loads(body_str)
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse cached body as JSON: {e}")
        return None 