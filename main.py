"""
CyclSales Dashboard API - Main Application Entry Point
"""
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.core.security import SecurityHeaders
from app.api.v1 import oauth, webhooks, locations, contacts, auth

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version="2.0.0",
    description="Modern API for CyclSales Dashboard - GHL Integration & Analytics",
    # Docs URLs - will add authentication below
    docs_url=None,  # Disable default docs
    redoc_url=None,  # Disable default redoc
    openapi_url=None,  # Disable default OpenAPI
)


# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Add security headers
        for header, value in SecurityHeaders.get_headers().items():
            if value:  # Only add non-empty headers
                response.headers[header] = value
        return response


app.add_middleware(SecurityHeadersMiddleware)

# CORS Middleware (configured restrictively)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # Only allow specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],  # Explicit methods only
    allow_headers=["*"],
    max_age=3600,  # Cache preflight for 1 hour
)

# Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Trusted Host Middleware (prevents host header attacks)
if not settings.DEBUG:
    # In production, only allow requests to your actual domain
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.railway.app", "*.cyclsales.com", "localhost"]
    )

# Include API routers
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication"])
app.include_router(oauth.router, prefix=f"{settings.API_V1_PREFIX}/oauth", tags=["OAuth"])
app.include_router(webhooks.router, prefix=f"{settings.API_V1_PREFIX}/webhooks", tags=["Webhooks"])
app.include_router(locations.router, prefix=f"{settings.API_V1_PREFIX}/locations", tags=["Locations"])
app.include_router(contacts.router, prefix=f"{settings.API_V1_PREFIX}/contacts", tags=["Contacts"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": "2.0.0",
        "environment": settings.ENVIRONMENT
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",  # TODO: Add actual DB check
        "redis": "connected",  # TODO: Add actual Redis check
    }


# Secure API Documentation
# Only accessible with admin credentials
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import JSONResponse
from app.core.ip_filter import check_admin_ip


@app.get("/openapi.json", include_in_schema=False)
async def get_openapi(admin_ip: str = Depends(check_admin_ip)):
    """Protected OpenAPI schema"""
    return JSONResponse(app.openapi())


@app.get("/docs", include_in_schema=False)
async def get_documentation(admin_ip: str = Depends(check_admin_ip)):
    """Protected Swagger UI documentation"""
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{settings.APP_NAME} - Documentation"
    )


@app.get("/redoc", include_in_schema=False)
async def get_redoc(admin_ip: str = Depends(check_admin_ip)):
    """Protected ReDoc documentation"""
    return get_redoc_html(
        openapi_url="/openapi.json",
        title=f"{settings.APP_NAME} - Documentation"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
