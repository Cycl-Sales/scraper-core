# Security Guide

## 🔒 Security Measures Implemented

### 1. **Authentication & Authorization**

#### API Key Authentication
```python
from fastapi import Depends
from app.core.security import verify_api_key

@app.get("/protected")
async def protected_route(api_key: str = Depends(verify_api_key)):
    # Only accessible with valid API key
    pass
```

#### Bearer Token Authentication
```python
from fastapi import Depends
from app.core.security import verify_bearer_token

@app.get("/protected")
async def protected_route(token: str = Depends(verify_bearer_token)):
    # Only accessible with valid bearer token
    pass
```

### 2. **Rate Limiting**

Prevents DoS attacks and API abuse:

```python
from fastapi import Depends
from app.core.rate_limit import check_rate_limit

@app.get("/limited", dependencies=[Depends(lambda r: check_rate_limit(r, max_requests=10, window_seconds=60))])
async def limited_route():
    # Max 10 requests per minute per IP
    pass
```

**Default limits:**
- API endpoints: 100 requests/minute per IP
- OAuth endpoints: 10 requests/minute per IP
- Webhook endpoints: 1000 requests/minute per IP

### 3. **Input Validation**

All inputs validated using Pydantic schemas:

```python
from pydantic import BaseModel, Field, validator

class ContactCreate(BaseModel):
    email: str = Field(..., max_length=255)
    name: str = Field(..., max_length=500)

    @validator('email')
    def validate_email(cls, v):
        # Email validation logic
        return v
```

**Protections:**
- Max string lengths enforced
- SQL injection prevention (SQLAlchemy ORM)
- XSS prevention (input sanitization)
- NoSQL injection prevention
- Path traversal prevention

### 4. **Security Headers**

Automatically added to all responses:

```
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'...
Strict-Transport-Security: max-age=31536000 (production only)
```

### 5. **CORS Configuration**

Restrictive CORS policy:

```python
# Only allow specific origins
allow_origins=settings.CORS_ORIGINS

# Explicit HTTP methods only
allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"]

# Credentials allowed (for cookies/auth)
allow_credentials=True
```

### 6. **Database Security**

- **Parameterized queries** (SQLAlchemy ORM)
- **Connection pooling** with limits
- **No raw SQL** (prevents injection)
- **Encrypted connections** to database
- **Automatic escaping** of inputs

### 7. **Secrets Management**

✅ **DO:**
- Store secrets in environment variables
- Use `.env` file (never commit to git)
- Rotate credentials regularly
- Use strong, random SECRET_KEY

❌ **DON'T:**
- Hardcode credentials in code
- Commit `.env` to version control
- Share secrets in plain text
- Use default/weak passwords

### 8. **Webhook Signature Verification**

Verify webhooks from GHL:

```python
from app.core.security import verify_webhook_signature

# In webhook handler
payload = await request.body()
signature = request.headers.get("X-Signature")
secret = settings.GHL_WEBHOOK_SECRET

if not verify_webhook_signature(payload, signature, secret):
    raise HTTPException(status_code=401, detail="Invalid signature")
```

## 🚨 Security Best Practices

### Production Checklist

- [ ] Set `DEBUG=False` in production
- [ ] Use HTTPS only (enforced by Railway)
- [ ] Configure `CORS_ORIGINS` to your actual domains only
- [ ] Set strong `SECRET_KEY` (32+ characters, random)
- [ ] Enable database SSL connection
- [ ] Set up monitoring (Sentry)
- [ ] Regular dependency updates
- [ ] API docs disabled in production (`/docs`, `/redoc`)
- [ ] Rate limiting enabled
- [ ] Security headers configured

### Environment Variables Security

**Required for Production:**
```bash
DEBUG=False
ENVIRONMENT=production
SECRET_KEY=<generate-strong-random-key>
DATABASE_URL=postgresql://...?sslmode=require
CORS_ORIGINS=["https://yourdomain.com"]
```

**Generate Strong SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Common Vulnerabilities & Mitigations

| Vulnerability | Mitigation | Status |
|--------------|------------|--------|
| **SQL Injection** | SQLAlchemy ORM, parameterized queries | ✅ Protected |
| **XSS** | Input sanitization, CSP headers | ✅ Protected |
| **CSRF** | SameSite cookies, CORS policy | ✅ Protected |
| **Clickjacking** | X-Frame-Options header | ✅ Protected |
| **Open Redirect** | URL validation | ✅ Protected |
| **DoS** | Rate limiting | ✅ Protected |
| **MIME Sniffing** | X-Content-Type-Options | ✅ Protected |
| **Host Header Injection** | TrustedHostMiddleware | ✅ Protected |
| **Sensitive Data Exposure** | HTTPS only, secure headers | ✅ Protected |

## 🔍 Security Monitoring

### Recommended Tools

1. **Sentry** - Error tracking and monitoring
   ```python
   import sentry_sdk
   sentry_sdk.init(dsn=settings.SENTRY_DSN)
   ```

2. **GitHub Dependabot** - Automatic dependency updates
   - Already enabled for this repo
   - Scans for vulnerabilities daily

3. **OWASP ZAP** - Security testing
   ```bash
   docker run -t owasp/zap2docker-stable zap-baseline.py -t https://your-api.railway.app
   ```

### Logging Security Events

All security events are logged:

```python
import logging
logger = logging.getLogger(__name__)

# Failed authentication attempts
logger.warning(f"Failed auth attempt from {client_ip}")

# Rate limit exceeded
logger.warning(f"Rate limit exceeded: {client_ip}")

# Invalid signatures
logger.error(f"Invalid webhook signature from {source}")
```

## 🛡️ Additional Security Measures

### TODO: Implement for Production

1. **API Key Management**
   - Generate unique API keys per client
   - Store hashed keys in database
   - Support key rotation

2. **JWT Tokens**
   - Implement JWT-based authentication
   - Short-lived access tokens (15 min)
   - Long-lived refresh tokens (7 days)
   - Token blacklist on logout

3. **IP Whitelisting**
   - Allow only specific IPs for admin endpoints
   - Configurable per environment

4. **Audit Logging**
   - Log all data modifications
   - Track who/when/what changed
   - Immutable audit trail

5. **2FA/MFA**
   - Two-factor authentication for admin users
   - TOTP or SMS-based

6. **Data Encryption**
   - Encrypt sensitive fields at rest
   - Use database-level encryption
   - Encrypt backups

## 📞 Security Incident Response

### If You Detect a Security Issue:

1. **Immediately:**
   - Rotate all credentials (API keys, database passwords)
   - Block suspicious IP addresses
   - Review audit logs

2. **Investigate:**
   - Check logs for unauthorized access
   - Identify affected data
   - Determine attack vector

3. **Notify:**
   - Inform affected users
   - Report to relevant authorities (if required)
   - Document incident

4. **Remediate:**
   - Fix vulnerability
   - Deploy security patch
   - Monitor for recurrence

### Reporting Security Vulnerabilities

**DO NOT** open public GitHub issues for security vulnerabilities.

Instead:
- Email: security@cyclsales.com (if available)
- Or create a **private** security advisory on GitHub

## 🔐 Compliance

### GDPR Compliance

- **Data minimization**: Only collect necessary data
- **Right to deletion**: Implement data deletion endpoints
- **Data portability**: Allow users to export their data
- **Consent tracking**: Log user consents

### SOC 2 / ISO 27001

- **Access controls**: Role-based access
- **Encryption**: In transit (HTTPS) and at rest
- **Logging**: Comprehensive audit trails
- **Monitoring**: Real-time security monitoring

## 🔄 Regular Security Tasks

### Weekly
- [ ] Review access logs for anomalies
- [ ] Check rate limiting effectiveness
- [ ] Monitor error rates

### Monthly
- [ ] Update dependencies
- [ ] Review and rotate API keys
- [ ] Security audit of new features

### Quarterly
- [ ] Penetration testing
- [ ] Security training for team
- [ ] Review and update security policies

---

**Last Updated:** 2025-01-07
**Security Contact:** security@cyclsales.com (update with actual email)
