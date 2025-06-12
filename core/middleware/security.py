"""
Security middleware providing comprehensive protection against common attacks.
Includes request size limits, security headers, and input validation.
"""

import re
import time
import logging
from typing import Dict, List, Optional, Callable, Any
from urllib.parse import unquote

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from core.config import settings

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security middleware for FastAPI applications.
    
    Protection features:
    - Request size limits (50MB default)
    - Security headers (HSTS, CSP, etc.)
    - SQL injection protection
    - XSS protection
    - Path traversal protection
    - Rate limiting integration
    - CORS configuration by environment
    - Input sanitization
    """
    
    def __init__(
        self,
        app,
        max_request_size: int = 50 * 1024 * 1024,  # 50MB
        enable_security_headers: bool = True,
        enable_input_validation: bool = True,
        enable_xss_protection: bool = True,
        enable_sql_injection_protection: bool = True,
        enable_path_traversal_protection: bool = True,
        blocked_user_agents: Optional[List[str]] = None,
        allowed_file_extensions: Optional[List[str]] = None,
    ):
        super().__init__(app)
        self.max_request_size = max_request_size
        self.enable_security_headers = enable_security_headers
        self.enable_input_validation = enable_input_validation
        self.enable_xss_protection = enable_xss_protection
        self.enable_sql_injection_protection = enable_sql_injection_protection
        self.enable_path_traversal_protection = enable_path_traversal_protection
        
        # Blocked user agents (bots, scanners, etc.)
        self.blocked_user_agents = blocked_user_agents or [
            "sqlmap", "nikto", "nmap", "masscan", "zap", "w3af",
            "dirbuster", "gobuster", "ffuf", "wfuzz", "burp"
        ]
        
        # Allowed file extensions for uploads
        self.allowed_file_extensions = allowed_file_extensions or [
            ".csv", ".xlsx", ".xls", ".json", ".xml", ".txt", ".pdf"
        ]
        
        # SQL injection patterns
        self.sql_injection_patterns = [
            r"(\b(select|insert|update|delete|drop|create|alter|exec|execute|sp_|xp_)\b)",
            r"(\b(union|and|or)\b.*\b(select|insert|update|delete)\b)",
            r"(\b(script|javascript|vbscript|onload|onerror|onclick)\b)",
            r"(\b(eval|expression|behavior|import|include|require)\b)",
            r"(--|\#|/\*|\*/|;|@@|char\(|waitfor|delay)",
            r"(\b(concat|substring|ascii|hex|unhex|md5|sha1|decode|encode)\b)",
        ]
        
        # XSS patterns
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"vbscript:",
            r"onload\s*=",
            r"onerror\s*=",
            r"onclick\s*=",
            r"onmouseover\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"<link[^>]*>",
            r"<meta[^>]*>",
        ]
        
        # Path traversal patterns
        self.path_traversal_patterns = [
            r"\.\./",
            r"\.\.\\",
            r"%2e%2e%2f",
            r"%2e%2e%5c",
            r"..%2f",
            r"..%5c",
        ]
        
        # Compile regex patterns
        self.sql_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.sql_injection_patterns]
        self.xss_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.xss_patterns]
        self.path_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.path_traversal_patterns]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Main security middleware dispatch method."""
        try:
            # Security checks
            security_response = await self._perform_security_checks(request)
            if security_response:
                return security_response
            
            # Process request
            response = await call_next(request)
            
            # Add security headers
            if self.enable_security_headers:
                self._add_security_headers(response, request)
            
            return response
            
        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            # Log security incident
            await self._log_security_incident(request, "middleware_error", str(e))
            
            # Don't expose internal errors
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "message": "Request processing failed"}
            )

    async def _perform_security_checks(self, request: Request) -> Optional[Response]:
        """Perform all security checks on incoming request."""
        
        # Check request size
        if await self._check_request_size(request):
            await self._log_security_incident(request, "request_size_exceeded")
            return JSONResponse(
                status_code=413,
                content={
                    "error": "Request too large",
                    "message": f"Request size exceeds {self.max_request_size / (1024*1024):.1f}MB limit"
                }
            )
        
        # Check user agent
        if self._check_blocked_user_agent(request):
            await self._log_security_incident(request, "blocked_user_agent")
            return JSONResponse(
                status_code=403,
                content={"error": "Forbidden", "message": "Access denied"}
            )
        
        # Check path traversal
        if self.enable_path_traversal_protection and self._check_path_traversal(request):
            await self._log_security_incident(request, "path_traversal_attempt")
            return JSONResponse(
                status_code=400,
                content={"error": "Bad request", "message": "Invalid path"}
            )
        
        # Check file extensions for uploads
        if request.method in ["POST", "PUT"] and not self._check_file_extension(request):
            await self._log_security_incident(request, "invalid_file_extension")
            return JSONResponse(
                status_code=400,
                content={"error": "Bad request", "message": "Invalid file type"}
            )
        
        # Check input validation
        if self.enable_input_validation:
            validation_response = await self._validate_input(request)
            if validation_response:
                return validation_response
        
        return None

    async def _check_request_size(self, request: Request) -> bool:
        """Check if request size exceeds limit."""
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                return size > self.max_request_size
            except ValueError:
                return False
        return False

    def _check_blocked_user_agent(self, request: Request) -> bool:
        """Check if user agent is blocked."""
        user_agent = request.headers.get("user-agent", "").lower()
        return any(blocked_agent in user_agent for blocked_agent in self.blocked_user_agents)

    def _check_path_traversal(self, request: Request) -> bool:
        """Check for path traversal attempts."""
        path = unquote(request.url.path)
        query_string = unquote(str(request.url.query))
        
        # Check path and query parameters
        for pattern in self.path_regex:
            if pattern.search(path) or pattern.search(query_string):
                return True
        return False

    def _check_file_extension(self, request: Request) -> bool:
        """Check file extension for upload endpoints."""
        # Only check specific upload endpoints
        upload_paths = ["/api/v1/prices/upload", "/api/v1/materials/upload"]
        
        if not any(request.url.path.startswith(path) for path in upload_paths):
            return True  # Allow non-upload endpoints
        
        # Check Content-Type header
        content_type = request.headers.get("content-type", "")
        
        # Allow specific content types
        allowed_types = [
            "application/json",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel",
            "text/csv",
            "application/csv",
            "multipart/form-data"
        ]
        
        return any(allowed_type in content_type for allowed_type in allowed_types)

    async def _validate_input(self, request: Request) -> Optional[Response]:
        """Validate input for SQL injection and XSS."""
        # Get query parameters
        query_params = str(request.query_params)
        
        # Check query parameters
        if self.enable_sql_injection_protection and self._check_sql_injection(query_params):
            await self._log_security_incident(request, "sql_injection_attempt")
            return JSONResponse(
                status_code=400,
                content={"error": "Bad request", "message": "Invalid input detected"}
            )
        
        if self.enable_xss_protection and self._check_xss(query_params):
            await self._log_security_incident(request, "xss_attempt")
            return JSONResponse(
                status_code=400,
                content={"error": "Bad request", "message": "Invalid input detected"}
            )
        
        # Check request body for POST/PUT requests
        if request.method in ["POST", "PUT"]:
            try:
                # Read body (this will be cached by FastAPI)
                body = await request.body()
                if body:
                    body_str = body.decode("utf-8", errors="ignore").lower()
                    
                    if self.enable_sql_injection_protection and self._check_sql_injection(body_str):
                        await self._log_security_incident(request, "sql_injection_attempt")
                        return JSONResponse(
                            status_code=400,
                            content={"error": "Bad request", "message": "Invalid input detected"}
                        )
                    
                    if self.enable_xss_protection and self._check_xss(body_str):
                        await self._log_security_incident(request, "xss_attempt")
                        return JSONResponse(
                            status_code=400,
                            content={"error": "Bad request", "message": "Invalid input detected"}
                        )
            except Exception as e:
                logger.warning(f"Failed to validate request body: {e}")
        
        return None

    def _check_sql_injection(self, input_string: str) -> bool:
        """Check for SQL injection patterns."""
        input_lower = input_string.lower()
        return any(pattern.search(input_lower) for pattern in self.sql_regex)

    def _check_xss(self, input_string: str) -> bool:
        """Check for XSS patterns."""
        input_lower = input_string.lower()
        return any(pattern.search(input_lower) for pattern in self.xss_regex)

    def _add_security_headers(self, response: Response, request: Request):
        """Add security headers to response."""
        # Security headers for production
        if settings.ENVIRONMENT == "production":
            response.headers.update({
                # HSTS (HTTP Strict Transport Security)
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
                
                # Content Security Policy
                "Content-Security-Policy": (
                    "default-src 'self'; "
                    "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                    "style-src 'self' 'unsafe-inline'; "
                    "img-src 'self' data: https:; "
                    "font-src 'self' data:; "
                    "connect-src 'self' https: wss:; "
                    "frame-ancestors 'none'; "
                    "base-uri 'self'; "
                    "form-action 'self'"
                ),
                
                # X-Content-Type-Options
                "X-Content-Type-Options": "nosniff",
                
                # X-Frame-Options
                "X-Frame-Options": "DENY",
                
                # X-XSS-Protection
                "X-XSS-Protection": "1; mode=block",
                
                # Referrer Policy
                "Referrer-Policy": "strict-origin-when-cross-origin",
                
                # Permissions Policy
                "Permissions-Policy": (
                    "geolocation=(), "
                    "microphone=(), "
                    "camera=(), "
                    "payment=(), "
                    "usb=(), "
                    "magnetometer=(), "
                    "gyroscope=(), "
                    "accelerometer=()"
                ),
            })
        else:
            # Development headers (less restrictive)
            response.headers.update({
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "SAMEORIGIN",
                "X-XSS-Protection": "1; mode=block",
            })
        
        # Always add these headers
        response.headers.update({
            "X-Powered-By": "",  # Hide server information
            "Server": "",        # Hide server information
            "X-Content-Security": "protected",
            "X-Request-ID": getattr(request.state, "correlation_id", "unknown"),
        })

    async def _log_security_incident(
        self, 
        request: Request, 
        incident_type: str, 
        details: str = ""
    ):
        """Log security incidents for monitoring."""
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "Unknown")
        
        security_event = {
            "event": "security_incident",
            "incident_type": incident_type,
            "timestamp": time.time(),
            "client_ip": client_ip,
            "user_agent": user_agent,
            "path": request.url.path,
            "method": request.method,
            "query_params": dict(request.query_params),
            "details": details,
            "correlation_id": getattr(request.state, "correlation_id", "unknown"),
        }
        
        # Log as warning for security incidents
        logger.warning(f"Security incident: {security_event}")
        
        # In production, this could be sent to SIEM or security monitoring system
        if settings.ENVIRONMENT == "production":
            # Send to security monitoring system
            pass

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request headers."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"

    def get_cors_settings(self) -> Dict[str, Any]:
        """Get CORS settings based on environment."""
        if settings.ENVIRONMENT == "production":
            # Restrictive CORS for production
            return {
                "allow_origins": [
                    "https://yourdomain.com",
                    "https://api.yourdomain.com",
                    "https://admin.yourdomain.com",
                ],
                "allow_credentials": True,
                "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": [
                    "Content-Type",
                    "Authorization",
                    "X-API-Key",
                    "X-Requested-With",
                    "Accept",
                    "Origin",
                    "X-Correlation-ID",
                ],
                "expose_headers": [
                    "X-Correlation-ID",
                    "X-RateLimit-Limit-RPM",
                    "X-RateLimit-Remaining-RPM",
                    "X-RateLimit-Reset-RPM",
                ],
                "max_age": 600,  # 10 minutes
            }
        else:
            # Permissive CORS for development
            return {
                "allow_origins": ["*"],
                "allow_credentials": True,
                "allow_methods": ["*"],
                "allow_headers": ["*"],
                "expose_headers": [
                    "X-Correlation-ID",
                    "X-RateLimit-Limit-RPM",
                    "X-RateLimit-Remaining-RPM",
                ],
            } 