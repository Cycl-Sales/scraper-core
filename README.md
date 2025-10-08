# CyclSales Dashboard API

Modern FastAPI-based backend for the CyclSales Dashboard, providing GHL (GoHighLevel) integration, contact management, and analytics.

## Architecture

Clean, modern Python API built with:
- **FastAPI** - High-performance async web framework
- **SQLAlchemy** - ORM for PostgreSQL
- **Alembic** - Database migrations
- **Celery** - Background job processing
- **Redis** - Caching and job queue

## Project Structure

```
.
├── app/
│   ├── api/              # API endpoints
│   │   ├── v1/
│   │   │   ├── oauth.py      # GHL OAuth flow
│   │   │   ├── webhooks.py   # GHL webhook handlers
│   │   │   ├── locations.py  # Location management
│   │   │   └── contacts.py   # Contact management
│   ├── core/             # Core functionality
│   │   ├── config.py         # Configuration
│   │   ├── security.py       # Auth & security
│   │   └── database.py       # DB connection
│   ├── models/           # SQLAlchemy models
│   │   ├── location.py
│   │   ├── contact.py
│   │   └── oauth_token.py
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   │   ├── ghl_client.py    # GHL API client
│   │   └── analytics.py     # Analytics service
│   └── workers/          # Background jobs
│       └── sync_jobs.py
├── alembic/              # Database migrations
├── tests/                # Test suite
├── .env.example          # Example environment variables
├── requirements.txt      # Python dependencies
└── main.py              # Application entry point
```

## Setup

1. **Install dependencies:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. **Run database migrations:**
```bash
alembic upgrade head
```

4. **Start the server:**
```bash
uvicorn main:app --reload
```

5. **Start background workers:**
```bash
celery -A app.workers worker --loglevel=info
```

## API Documentation

Once running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Key Features

- **GHL OAuth Integration** - Secure OAuth flow for GHL marketplace apps
- **Webhook Processing** - Handle GHL events (install, uninstall, etc.)
- **Contact Sync** - Efficient batch syncing with pagination
- **Analytics** - Real-time dashboard metrics
- **Background Jobs** - Async processing for heavy operations

## Development

```bash
# Run tests
pytest

# Format code
black .

# Lint
flake8 .

# Type checking
mypy .
```

## Deployment

Optimized for deployment on:
- **Railway** (Recommended)
- **Heroku**
- **Docker/Kubernetes**
- **AWS ECS**

See `deploy/` folder for deployment configurations.
