"""
Body Cache Middleware для единого чтения request body.

Решает проблему зависаний при попытке нескольких middleware читать один request body.
Использует правильный паттерн из документации Starlette.
"""

import json
from core.monitoring.logger import get_logger
from typing import Optional

from starlette.types import ASGIApp, Receive, Scope, Send, Message

logger = get_logger(__name__)


class BodyCacheMiddleware:
    """
    🔥 ПРАВИЛЬНЫЙ ASGI middleware для кеширования request body.
    
    Реализован согласно паттернам из официальной документации Starlette:
    https://www.starlette.io/middleware/#inspecting-or-modifying-the-request
    """
    
    def __init__(
        self, 
        app: ASGIApp,
        max_body_size: int = 10 * 1024 * 1024,  # 10MB по умолчанию
        methods_to_cache: list[str] = None
    ):
        self.app = app
        self.max_body_size = max_body_size
        self.methods_to_cache = methods_to_cache or ["POST", "PUT", "PATCH"]
        
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        🔥 ПРАВИЛЬНАЯ реализация ASGI middleware entry point.
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
            
        method = scope.get("method", "GET")
        
        # Кешируем body только для методов с телом запроса
        if method in self.methods_to_cache:
            # 🔥 ПРАВИЛЬНЫЙ паттерн: wrapping receive callable
            body_size = 0
            cached_body = b""
            
            async def receive_wrapper() -> Message:
                nonlocal body_size, cached_body
                
                message = await receive()
                
                if message["type"] == "http.request":
                    body_part = message.get("body", b"")
                    body_size += len(body_part)
                    
                    # Проверяем размер
                    if body_size <= self.max_body_size:
                        cached_body += body_part
                        
                        # Если это последний chunk, сохраняем в scope
                        if not message.get("more_body", False):
                            scope["_cached_body"] = {
                                "available": True,
                                "bytes": cached_body,
                                "str": cached_body.decode('utf-8', errors='ignore') if cached_body else ""
                            }
                            logger.debug(f"Body cached, size: {len(cached_body)} bytes")
                    else:
                        # Body слишком большой
                        if not hasattr(scope, "_cached_body"):
                            scope["_cached_body"] = {
                                "available": False,
                                "bytes": b"",
                                "str": "",
                                "error": "Body too large"
                            }
                            logger.warning(f"Request body too large: {body_size} bytes, limit: {self.max_body_size}")
                
                return message
            
            await self.app(scope, receive_wrapper, send)
        else:
            # Для GET и других методов без body
            scope["_cached_body"] = {"available": False, "bytes": b"", "str": ""}
            await self.app(scope, receive, send)


def get_cached_body_bytes(request) -> Optional[bytes]:
    """
    Получает кешированный body в виде bytes из scope.
    """
    if hasattr(request, "scope") and "_cached_body" in request.scope:
        cache = request.scope["_cached_body"]
        if cache.get("available", False):
            return cache.get("bytes", b"")
    return None


def get_cached_body_str(request) -> Optional[str]:
    """
    Получает кешированный body в виде строки из scope.
    """
    if hasattr(request, "scope") and "_cached_body" in request.scope:
        cache = request.scope["_cached_body"]
        if cache.get("available", False):
            return cache.get("str", "")
    return None


async def get_cached_body_json(request) -> Optional[dict]:
    """
    Получает кешированный body как JSON из scope.
    """
    try:
        body_str = get_cached_body_str(request)
        if body_str:
            return json.loads(body_str)
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse cached body as JSON: {e}")
        return None 