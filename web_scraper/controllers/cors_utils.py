ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "https://cs-react.redtechitsolutions.com"
]

def get_cors_headers(request):
    origin = request.httprequest.headers.get('Origin')
    if origin in ALLOWED_ORIGINS:
        return [
            ('Access-Control-Allow-Origin', origin),
            ('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS'),
            ('Access-Control-Allow-Headers', 'Origin, Content-Type, Accept, Authorization'),
            ('Access-Control-Allow-Credentials', 'true'),
        ]
    else:
        return [] 