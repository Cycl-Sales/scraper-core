"""
Security utilities and middleware
"""
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import secrets
import hashlib
import hmac

from app.core.config import settings


# API Key Authentication (for webhook verification)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Bearer token authentication (for OAuth tokens)
bearer_scheme = HTTPBearer(auto_error=False)


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify webhook signature from GHL

    Args:
        payload: Raw request body
        signature: Signature from X-Signature header
        secret: Webhook secret from GHL

    Returns:
        True if signature is valid
    """
    if not signature or not secret:
        return False

    # Compute expected signature
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(signature, expected_signature)


def generate_api_key() -> str:
    """Generate a secure API key"""
    return secrets.token_urlsafe(32)


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """
    Verify API key from request header

    Usage:
        @app.get("/protected")
        async def protected_route(api_key: str = Depends(verify_api_key)):
            ...
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )

    # TODO: Implement actual API key validation against database
    # For now, just check it exists
    if len(api_key) < 32:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    return api_key


async def verify_bearer_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme)
) -> str:
    """
    Verify Bearer token from Authorization header

    Usage:
        @app.get("/protected")
        async def protected_route(token: str = Depends(verify_bearer_token)):
            ...
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # TODO: Implement token validation (JWT or database lookup)
    return credentials.credentials


def sanitize_input(value: str, max_length: int = 500) -> str:
    """
    Sanitize user input to prevent injection attacks

    Args:
        value: Input string
        max_length: Maximum allowed length

    Returns:
        Sanitized string
    """
    if not value:
        return ""

    # Truncate to max length
    sanitized = value[:max_length]

    # Remove null bytes
    sanitized = sanitized.replace('\x00', '')

    # Strip leading/trailing whitespace
    sanitized = sanitized.strip()

    return sanitized


def is_safe_redirect_url(url: str) -> bool:
    """
    Check if a redirect URL is safe (prevents open redirect vulnerabilities)

    Args:
        url: URL to validate

    Returns:
        True if URL is safe
    """
    if not url:
        return False

    # Only allow relative URLs or URLs matching FRONTEND_URL
    if url.startswith('/'):
        return True

    # Check if URL starts with allowed frontend URL
    allowed_origins = settings.CORS_ORIGINS + [settings.FRONTEND_URL]
    return any(url.startswith(origin) for origin in allowed_origins)


class SecurityHeaders:
    """Security headers middleware"""

    @staticmethod
    def get_headers() -> dict:
        """Get recommended security headers"""
        return {
            # Prevent clickjacking
            "X-Frame-Options": "DENY",

            # Prevent MIME sniffing
            "X-Content-Type-Options": "nosniff",

            # Enable XSS protection
            "X-XSS-Protection": "1; mode=block",

            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",

            # Content Security Policy
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:;"
            ),

            # HSTS (only in production with HTTPS)
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains" if not settings.DEBUG else "",
        }
