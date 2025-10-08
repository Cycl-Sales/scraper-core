"""
Rate Limiting
Prevents abuse and DoS attacks
"""
from fastapi import HTTPException, Request
from typing import Dict, Optional
import time
from collections import defaultdict, deque


class RateLimiter:
    """
    Simple in-memory rate limiter
    For production, use Redis-based rate limiting
    """

    def __init__(self):
        # Store request timestamps per IP
        self.requests: Dict[str, deque] = defaultdict(deque)

    def check_rate_limit(
        self,
        request: Request,
        max_requests: int = 100,
        window_seconds: int = 60
    ) -> bool:
        """
        Check if request is within rate limit

        Args:
            request: FastAPI request object
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            True if within limit

        Raises:
            HTTPException: If rate limit exceeded
        """
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Get current timestamp
        now = time.time()
        window_start = now - window_seconds

        # Clean old requests
        request_queue = self.requests[client_ip]
        while request_queue and request_queue[0] < window_start:
            request_queue.popleft()

        # Check if limit exceeded
        if len(request_queue) >= max_requests:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Max {max_requests} requests per {window_seconds} seconds.",
                headers={
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(request_queue[0] + window_seconds)),
                }
            )

        # Add current request
        request_queue.append(now)

        return True

    def get_rate_limit_headers(
        self,
        request: Request,
        max_requests: int = 100,
        window_seconds: int = 60
    ) -> Dict[str, str]:
        """Get rate limit headers for response"""
        client_ip = request.client.host if request.client else "unknown"
        request_queue = self.requests[client_ip]

        now = time.time()
        window_start = now - window_seconds

        # Count requests in current window
        valid_requests = sum(1 for ts in request_queue if ts >= window_start)
        remaining = max(0, max_requests - valid_requests)

        # Calculate reset time
        reset_time = int(now + window_seconds) if request_queue else int(now)

        return {
            "X-RateLimit-Limit": str(max_requests),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time),
        }


# Global rate limiter instance
rate_limiter = RateLimiter()


def check_rate_limit(request: Request, max_requests: int = 100, window_seconds: int = 60):
    """
    Dependency function for route rate limiting

    Usage:
        @app.get("/endpoint", dependencies=[Depends(check_rate_limit)])
        async def endpoint():
            ...
    """
    return rate_limiter.check_rate_limit(request, max_requests, window_seconds)
