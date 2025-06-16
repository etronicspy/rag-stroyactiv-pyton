"""
Compression middleware for optimized response delivery.
Supports multiple compression algorithms with intelligent selection.
"""

import gzip
import zlib
import time
import logging
from typing import Optional, List, Dict, Any, Callable
from io import BytesIO

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class CompressionMiddleware(BaseHTTPMiddleware):
    """
    Advanced compression middleware with multiple algorithms and intelligent selection.
    
    Features:
    - Multiple compression algorithms (gzip, deflate, brotli)
    - Intelligent algorithm selection based on content type and size
    - Streaming compression for large responses
    - Configurable compression thresholds
    - Performance monitoring
    """
    
    def __init__(
        self,
        app: ASGIApp,
        minimum_size: int = 1024,  # Don't compress responses smaller than 1KB
        maximum_size: int = 10 * 1024 * 1024,  # Don't compress responses larger than 10MB
        compression_level: int = 6,  # Balanced compression level
        enable_brotli: bool = True,
        enable_streaming: bool = True,
        exclude_content_types: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None,
        enable_performance_logging: bool = False,
    ):
        """
        Initialize compression middleware.
        
        Args:
            app: ASGI application
            minimum_size: Minimum response size to compress (bytes)
            maximum_size: Maximum response size to compress (bytes)
            compression_level: Compression level (1-9, higher = better compression)
            enable_brotli: Enable Brotli compression (requires brotli package)
            enable_streaming: Enable streaming compression for large responses
            exclude_content_types: List of content types to exclude from compression
            exclude_paths: List of paths to exclude from compression
            enable_performance_logging: Log compression performance metrics
        """
        super().__init__(app)
        
        self.minimum_size = minimum_size
        self.maximum_size = maximum_size
        self.compression_level = compression_level
        self.enable_brotli = enable_brotli
        self.enable_streaming = enable_streaming
        self.enable_performance_logging = enable_performance_logging
        
        # Default excluded content types (already compressed)
        self.exclude_content_types = set(exclude_content_types or [
            "image/jpeg", "image/png", "image/gif", "image/webp",
            "video/mp4", "video/mpeg", "video/webm",
            "audio/mpeg", "audio/wav", "audio/ogg",
            "application/zip", "application/gzip",
            "application/x-rar-compressed", "application/x-7z-compressed",
        ])
        
        self.exclude_paths = set(exclude_paths or [])
        
        # Performance tracking
        self.total_responses = 0
        self.compressed_responses = 0
        self.total_bytes_original = 0
        self.total_bytes_compressed = 0
        self.total_compression_time = 0
        
        # Check for Brotli availability
        self.brotli_available = False
        if self.enable_brotli:
            try:
                import brotli
                self.brotli_available = True
                logger.info("✅ Brotli compression available")
            except ImportError:
                logger.warning("⚠️ Brotli not available, using gzip/deflate only")
        
        logger.info(
            f"✅ CompressionMiddleware initialized: "
            f"min_size={minimum_size}B, max_size={maximum_size}B, "
            f"level={compression_level}, brotli={self.brotli_available}"
        )

    def _should_compress(self, request: Request, response: Response, content_length: int) -> bool:
        """Determine if response should be compressed."""
        # Check path exclusions
        if request.url.path in self.exclude_paths:
            return False
        
        # Check size thresholds
        if content_length < self.minimum_size or content_length > self.maximum_size:
            return False
        
        # Check if already compressed
        if response.headers.get("content-encoding"):
            return False
        
        # Check content type
        content_type = response.headers.get("content-type", "").split(";")[0].strip()
        if content_type in self.exclude_content_types:
            return False
        
        # Check if client accepts compression
        accept_encoding = request.headers.get("accept-encoding", "").lower()
        if not any(encoding in accept_encoding for encoding in ["gzip", "deflate", "br"]):
            return False
        
        return True

    def _select_compression_algorithm(self, accept_encoding: str) -> Optional[str]:
        """Select the best compression algorithm based on client support and preference."""
        accept_encoding = accept_encoding.lower()
        
        # Priority order: brotli > gzip > deflate
        if self.brotli_available and "br" in accept_encoding:
            return "br"
        elif "gzip" in accept_encoding:
            return "gzip"
        elif "deflate" in accept_encoding:
            return "deflate"
        
        return None

    def _compress_content(self, content: bytes, algorithm: str) -> bytes:
        """Compress content using specified algorithm."""
        # Safety check - ensure content is valid
        if content is None:
            raise ValueError("Content cannot be None for compression")
        
        if not isinstance(content, (bytes, str)):
            raise ValueError(f"Content must be bytes or str, got {type(content)}")
        
        if isinstance(content, str):
            content = content.encode('utf-8')
        
        if len(content) == 0:
            logger.debug("⚠️  Empty content provided for compression, returning as-is")
            return content
        
        if algorithm == "gzip":
            return gzip.compress(content, compresslevel=self.compression_level)
        elif algorithm == "deflate":
            return zlib.compress(content, level=self.compression_level)
        elif algorithm == "br" and self.brotli_available:
            import brotli
            return brotli.compress(content, quality=self.compression_level)
        else:
            raise ValueError(f"Unsupported compression algorithm: {algorithm}")

    async def _compress_streaming_response(
        self, 
        response: StreamingResponse, 
        algorithm: str
    ) -> StreamingResponse:
        """Compress streaming response content."""
        if algorithm == "gzip":
            compressor = gzip.GzipFile(fileobj=None, mode='wb', compresslevel=self.compression_level)
        elif algorithm == "deflate":
            compressor = zlib.compressobj(level=self.compression_level)
        elif algorithm == "br" and self.brotli_available:
            import brotli
            compressor = brotli.Compressor(quality=self.compression_level)
        else:
            raise ValueError(f"Unsupported compression algorithm: {algorithm}")

        async def compressed_generator():
            try:
                if algorithm == "gzip":
                    # For gzip, we need to handle the file-like object differently
                    buffer = BytesIO()
                    with gzip.GzipFile(fileobj=buffer, mode='wb', compresslevel=self.compression_level) as gz:
                        async for chunk in response.body_iterator:
                            if chunk is None:  # Skip None chunks
                                continue
                            if isinstance(chunk, str):
                                chunk = chunk.encode('utf-8')
                            elif not isinstance(chunk, bytes):
                                chunk = str(chunk).encode('utf-8')
                            
                            if chunk:  # Only write non-empty chunks
                                gz.write(chunk)
                    
                    buffer.seek(0)
                    while True:
                        chunk = buffer.read(8192)
                        if not chunk:
                            break
                        yield chunk
                else:
                    # For deflate and brotli
                    async for chunk in response.body_iterator:
                        if chunk is None:  # Skip None chunks
                            continue
                        if isinstance(chunk, str):
                            chunk = chunk.encode('utf-8')
                        elif not isinstance(chunk, bytes):
                            chunk = str(chunk).encode('utf-8')
                        
                        if not chunk:  # Skip empty chunks
                            continue
                        
                        if algorithm == "deflate":
                            compressed_chunk = compressor.compress(chunk)
                        else:  # brotli
                            compressed_chunk = compressor.process(chunk)
                        
                        if compressed_chunk:
                            yield compressed_chunk
                    
                    # Flush remaining data
                    if algorithm == "deflate":
                        final_chunk = compressor.flush()
                    else:  # brotli
                        final_chunk = compressor.finish()
                    
                    if final_chunk:
                        yield final_chunk
                        
            except Exception as e:
                logger.error(f"Streaming compression error: {e}")
                # Fallback to original content
                async for chunk in response.body_iterator:
                    if chunk is not None:  # Only yield non-None chunks
                        yield chunk

        return StreamingResponse(
            compressed_generator(),
            status_code=response.status_code,
            headers=response.headers,
            media_type=response.media_type,
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Main dispatch method with compression logic."""
        start_time = time.time() if self.enable_performance_logging else 0
        self.total_responses += 1
        
        # Process request
        response = await call_next(request)
        
        # Check if we should compress
        if hasattr(response, 'body') and response.body is not None:
            content_length = len(response.body)
        else:
            # For streaming responses or empty responses, we'll compress anyway if conditions are met
            content_length = self.minimum_size + 1
        
        if not self._should_compress(request, response, content_length):
            return response
        
        # Select compression algorithm
        accept_encoding = request.headers.get("accept-encoding", "")
        algorithm = self._select_compression_algorithm(accept_encoding)
        
        if not algorithm:
            return response
        
        try:
            compression_start = time.time()
            
            if isinstance(response, StreamingResponse) and self.enable_streaming:
                # Handle streaming response
                compressed_response = await self._compress_streaming_response(response, algorithm)
                compressed_response.headers["content-encoding"] = algorithm
                compressed_response.headers["vary"] = "Accept-Encoding"
                
                # Remove content-length for streaming responses
                if "content-length" in compressed_response.headers:
                    del compressed_response.headers["content-length"]
                
                self.compressed_responses += 1
                
            else:
                # Handle regular response - IMPROVED NULL CHECK
                if not hasattr(response, 'body'):
                    logger.debug(f"⚠️  Skipping compression: response has no body attribute for {request.method} {request.url.path}")
                    return response
                
                try:
                    original_content = getattr(response, 'body', None)
                except Exception as e:
                    logger.warning(f"⚠️  Cannot access response.body for {request.method} {request.url.path}: {e}")
                    return response
                
                # Additional safety check - ensure content is not None or empty
                if original_content is None:
                    logger.debug(f"⚠️  Skipping compression: response.body is None for {request.method} {request.url.path}")
                    return response
                
                # Convert string to bytes if needed
                if isinstance(original_content, str):
                    if not original_content.strip():  # Skip empty strings
                        logger.debug(f"⚠️  Skipping compression: empty content for {request.method} {request.url.path}")
                        return response
                    original_content = original_content.encode('utf-8')
                elif isinstance(original_content, bytes):
                    if len(original_content) == 0:  # Skip empty bytes
                        logger.debug(f"⚠️  Skipping compression: empty bytes for {request.method} {request.url.path}")
                        return response
                else:
                    # Handle other types - convert to string first
                    try:
                        content_str = str(original_content)
                        if not content_str.strip():
                            logger.debug(f"⚠️  Skipping compression: empty converted content for {request.method} {request.url.path}")
                            return response
                        original_content = content_str.encode('utf-8')
                    except Exception as e:
                        logger.warning(f"⚠️  Cannot convert response.body to bytes for compression: {e}")
                        return response
                
                # Final safety check before compression
                if not original_content:
                    logger.debug(f"⚠️  Skipping compression: final content check failed for {request.method} {request.url.path}")
                    return response
                
                # DEBUG: Add detailed logging before compression
                logger.debug(f"🔍 DEBUG: About to compress content for {request.method} {request.url.path}")
                logger.debug(f"🔍 DEBUG: original_content type: {type(original_content)}")
                logger.debug(f"🔍 DEBUG: original_content is None: {original_content is None}")
                logger.debug(f"🔍 DEBUG: original_content length: {len(original_content) if original_content else 'N/A'}")
                logger.debug(f"🔍 DEBUG: algorithm: {algorithm}")
                
                try:
                    compressed_content = self._compress_content(original_content, algorithm)
                except Exception as compression_error:
                    logger.error(f"❌ _compress_content failed for {request.method} {request.url.path}: {compression_error}")
                    logger.error(f"❌ Content type was: {type(original_content)}, Content is None: {original_content is None}")
                    return response
                
                # Update response
                response.body = compressed_content
                response.headers["content-encoding"] = algorithm
                response.headers["content-length"] = str(len(compressed_content))
                response.headers["vary"] = "Accept-Encoding"
                
                # Update statistics
                self.compressed_responses += 1
                self.total_bytes_original += len(original_content)
                self.total_bytes_compressed += len(compressed_content)
                
                if self.enable_performance_logging:
                    compression_time = time.time() - compression_start
                    self.total_compression_time += compression_time
                    compression_ratio = len(compressed_content) / len(original_content)
                    
                    logger.debug(
                        f"✅ Compressed {request.method} {request.url.path}: "
                        f"{len(original_content)}B -> {len(compressed_content)}B "
                        f"({compression_ratio:.2f} ratio, {algorithm}, {compression_time*1000:.2f}ms)"
                    )
            
            return response
            
        except Exception as e:
            logger.error(f"Compression error for {request.method} {request.url.path}: {e}")
            # Return original response if compression fails  
            return response

    def get_compression_stats(self) -> Dict[str, Any]:
        """Get compression performance statistics."""
        if self.total_responses == 0:
            return {
                "total_responses": 0,
                "compressed_responses": 0,
                "compression_rate": 0.0,
                "average_compression_ratio": 0.0,
                "average_compression_time": 0.0,
                "total_bytes_saved": 0,
            }
        
        compression_rate = self.compressed_responses / self.total_responses
        average_compression_ratio = (
            self.total_bytes_compressed / self.total_bytes_original
            if self.total_bytes_original > 0 else 0.0
        )
        average_compression_time = (
            self.total_compression_time / self.compressed_responses
            if self.compressed_responses > 0 else 0.0
        )
        total_bytes_saved = self.total_bytes_original - self.total_bytes_compressed
        
        return {
            "total_responses": self.total_responses,
            "compressed_responses": self.compressed_responses,
            "compression_rate": compression_rate,
            "average_compression_ratio": average_compression_ratio,
            "average_compression_time": average_compression_time,
            "total_bytes_original": self.total_bytes_original,
            "total_bytes_compressed": self.total_bytes_compressed,
            "total_bytes_saved": total_bytes_saved,
            "brotli_available": self.brotli_available,
        } 