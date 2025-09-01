# -*- coding: utf-8 -*-

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://cs-react.redtechitsolutions.com",
    "https://866d-161-49-226-50.ngrok-free.app",
    "https://dashboard.cyclsales.com"
]

def get_cors_headers(request):
    """Get CORS headers for the request"""
    origin = request.httprequest.headers.get('Origin')
    if origin in ALLOWED_ORIGINS:
        return [
            ('Access-Control-Allow-Origin', origin),
            ('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS'),
            ('Access-Control-Allow-Headers', 'Origin, Content-Type, Accept, Authorization, X-Requested-With'),
            ('Access-Control-Allow-Credentials', 'true'),
        ]
    else:
        return [] 