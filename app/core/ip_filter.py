"""
IP Filtering and Whitelisting
Restrict access based on IP addresses
"""
from fastapi import Request, HTTPException, status
from typing import List, Optional
import ipaddress
from sqlalchemy.orm import Session

from app.core.database import get_db


class IPFilter:
    """IP address filtering and whitelisting"""

    @staticmethod
    def get_client_ip(request: Request) -> str:
        """
        Get real client IP from request

        Handles proxies and load balancers (Railway, Cloudflare, etc.)
        """
        # Check X-Forwarded-For header (from proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take first IP (client IP before proxies)
            return forwarded_for.split(",")[0].strip()

        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct connection IP
        return request.client.host if request.client else "unknown"

    @staticmethod
    def is_ip_in_range(ip: str, ip_range: str) -> bool:
        """
        Check if IP is in CIDR range

        Args:
            ip: IP address to check
            ip_range: CIDR range (e.g., "192.168.1.0/24")

        Returns:
            True if IP is in range
        """
        try:
            return ipaddress.ip_address(ip) in ipaddress.ip_network(ip_range, strict=False)
        except ValueError:
            return False

    @staticmethod
    def is_ip_whitelisted(ip: str, whitelist: List[str]) -> bool:
        """
        Check if IP is in whitelist

        Args:
            ip: IP address to check
            whitelist: List of allowed IPs or CIDR ranges

        Returns:
            True if IP is whitelisted
        """
        for allowed in whitelist:
            # Check for exact match
            if ip == allowed:
                return True

            # Check for CIDR range
            if "/" in allowed:
                if IPFilter.is_ip_in_range(ip, allowed):
                    return True

        return False

    @staticmethod
    def check_ip_whitelist(request: Request, whitelist: List[str]):
        """
        Dependency to check IP against whitelist

        Usage:
            @app.get("/admin", dependencies=[Depends(lambda r: check_ip_whitelist(r, ADMIN_IPS))])
            async def admin_endpoint():
                pass

        Args:
            request: FastAPI request
            whitelist: List of allowed IPs/ranges

        Raises:
            HTTPException: If IP not whitelisted
        """
        client_ip = IPFilter.get_client_ip(request)

        if not IPFilter.is_ip_whitelisted(client_ip, whitelist):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied from IP: {client_ip}"
            )

        return client_ip

    @staticmethod
    def check_ip_blacklist(request: Request, blacklist: List[str]):
        """
        Check if IP is blacklisted

        Args:
            request: FastAPI request
            blacklist: List of blocked IPs/ranges

        Raises:
            HTTPException: If IP is blacklisted
        """
        client_ip = IPFilter.get_client_ip(request)

        if IPFilter.is_ip_whitelisted(client_ip, blacklist):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        return client_ip

    @staticmethod
    def is_local_ip(ip: str) -> bool:
        """Check if IP is from local/private network"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_private or ip_obj.is_loopback
        except ValueError:
            return False


# Common IP whitelists
LOCALHOST_IPS = ["127.0.0.1", "::1", "localhost"]
PRIVATE_NETWORKS = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]


def check_admin_ip(request: Request):
    """
    Check if request is from allowed admin IP

    Usage:
        @app.delete("/admin/users/{id}", dependencies=[Depends(check_admin_ip)])
        async def delete_user():
            pass
    """
    from app.core.config import settings

    # In development, allow all
    if settings.DEBUG:
        return IPFilter.get_client_ip(request)

    # In production, check whitelist
    admin_ips = getattr(settings, "ADMIN_IPS", LOCALHOST_IPS)
    return IPFilter.check_ip_whitelist(request, admin_ips)


def check_webhook_ip(request: Request):
    """
    Check if webhook request is from GHL

    GHL IP ranges (update these with actual GHL IPs)
    """
    # GHL webhook IPs (example - verify with GHL docs)
    ghl_ips = [
        "35.184.0.0/16",  # Example range
        "35.185.0.0/16",  # Example range
    ]

    client_ip = IPFilter.get_client_ip(request)

    # In development, allow all
    from app.core.config import settings
    if settings.DEBUG:
        return client_ip

    # In production, verify IP
    if not IPFilter.is_ip_whitelisted(client_ip, ghl_ips):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Webhook source not recognized"
        )

    return client_ip
