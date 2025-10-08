# Railway Deployment Guide

## Why Railway?

✅ **Cheapest managed option**: $10-20/month typical
✅ **Auto-scaling**: Handles growth automatically
✅ **Zero-downtime deploys**: No service interruptions
✅ **Easy management**: Web dashboard, no CLI needed
✅ **Built-in database**: PostgreSQL included
✅ **Free SSL**: Automatic HTTPS
✅ **Git integration**: Deploy on push

## Cost Breakdown

### Starter Phase (1-100 clients)
- **Web Service**: ~$5/month
- **PostgreSQL**: ~$5/month
- **Total**: **~$10/month**

### Growth Phase (100-1000 clients)
- **Web Service**: ~$10/month (auto-scales)
- **PostgreSQL**: ~$10/month
- **Redis** (optional): ~$5/month
- **Total**: **~$20-25/month**

### Scale Phase (1000+ clients)
- **Web Service**: ~$20-30/month
- **PostgreSQL**: ~$15-20/month
- **Redis**: ~$5/month
- **Workers**: ~$10/month
- **Total**: **~$50-65/month**

Compare to Odoo: $150-300/month for same scale! 💰

## Step-by-Step Deployment

### 1. Create Railway Account

1. Go to https://railway.app
2. Click "Start a New Project"
3. Sign up with GitHub (recommended)
4. Verify your email

### 2. Create New Project

1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose `cs-dashboard-2.0` repository
4. Railway will auto-detect it's a Python app

### 3. Add PostgreSQL Database

1. In your project, click "New"
2. Select "Database"
3. Choose "PostgreSQL"
4. Railway automatically creates and links it
5. Database URL is auto-added to environment variables

### 4. Configure Environment Variables

In Railway dashboard, add these variables:

```bash
# Application
APP_NAME=CyclSales Dashboard API
DEBUG=False
ENVIRONMENT=production
SECRET_KEY=<generate-with-command-below>

# Database (auto-populated by Railway)
DATABASE_URL=${DATABASE_URL}

# GHL OAuth (YOUR CREDENTIALS)
GHL_CLIENT_ID=your-actual-client-id
GHL_CLIENT_SECRET=your-actual-client-secret
GHL_APP_ID=your-actual-app-id
GHL_REDIRECT_URI=https://your-app.railway.app/api/v1/oauth/callback

# Frontend (your React app URL)
FRONTEND_URL=https://your-frontend.com

# OpenAI (optional)
OPENAI_API_KEY=your-openai-key

# CORS (your frontend domains)
CORS_ORIGINS=["https://your-frontend.com","https://www.your-frontend.com"]
```

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 5. Deploy!

Railway automatically deploys when you:
1. Push to GitHub, OR
2. Click "Deploy" in Railway dashboard

First deployment takes ~2-3 minutes.

### 6. Run Database Migrations

After first deployment:

1. Go to Railway dashboard
2. Click on your service
3. Go to "Settings" tab
4. Under "Deploy", add this:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port $PORT`

This runs migrations automatically on each deploy.

### 7. Get Your URL

Railway gives you a URL like:
```
https://cs-dashboard-20-production.up.railway.app
```

You can add a custom domain later:
```
https://api.cyclsales.com
```

## Continuous Deployment

Once set up, your workflow is:

```bash
# Make changes locally
git add .
git commit -m "Add new feature"
git push

# Railway automatically:
# ✅ Detects push
# ✅ Builds new version
# ✅ Runs migrations
# ✅ Deploys with zero downtime
# ✅ Sends you notification
```

## Monitoring & Logs

### View Logs
1. Go to Railway dashboard
2. Click your service
3. Click "Deployments"
4. Click latest deployment
5. See real-time logs

### Metrics
Railway shows:
- CPU usage
- Memory usage
- Request count
- Response times
- Error rates

### Alerts
Set up notifications for:
- Deployment failures
- High error rates
- Resource limits

## Scaling

### Automatic Scaling
Railway auto-scales based on:
- CPU usage
- Memory usage
- Request volume

You don't do anything - it just works! 🚀

### Manual Scaling
If needed, you can:
1. Go to service settings
2. Increase resources:
   - More RAM
   - More CPU cores
   - More replicas

### Database Scaling
1. Click PostgreSQL service
2. Upgrade plan:
   - Starter: 1GB RAM ($5/mo)
   - Developer: 2GB RAM ($10/mo)
   - Pro: 4GB+ RAM ($20+/mo)

## Adding Services (As You Grow)

### Add Redis (for background jobs)
1. Click "New" in project
2. Select "Redis"
3. Auto-connects, adds REDIS_URL

### Add Worker Service (for heavy tasks)
1. Click "New Service"
2. Same repo, different start command:
   ```
   celery -A app.workers worker --loglevel=info
   ```

### Add Monitoring (Sentry)
1. Sign up at sentry.io (free tier)
2. Add to requirements.txt:
   ```
   sentry-sdk[fastapi]==1.40.0
   ```
3. Add to main.py:
   ```python
   import sentry_sdk
   sentry_sdk.init(dsn=settings.SENTRY_DSN)
   ```

## Custom Domain Setup

1. Buy domain (namecheap.com, ~$10/year)
2. In Railway:
   - Go to Settings
   - Click "Domains"
   - Add "api.yourdomain.com"
3. Add CNAME record in your DNS:
   ```
   api.yourdomain.com → your-app.railway.app
   ```
4. SSL auto-configured! ✅

## Backup Strategy

### Database Backups
Railway automatically backs up PostgreSQL:
- Daily backups (kept 7 days)
- Point-in-time recovery available

### Manual Backup
```bash
# From Railway dashboard, get DATABASE_URL
# Then run locally:
pg_dump $DATABASE_URL > backup.sql

# Restore:
psql $DATABASE_URL < backup.sql
```

## Troubleshooting

### Deployment Failed
1. Check logs in Railway dashboard
2. Common issues:
   - Missing environment variable
   - Database migration error
   - Python version mismatch

### App Not Starting
1. Check start command is correct:
   ```
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
2. Verify all dependencies in requirements.txt
3. Check environment variables

### Database Connection Error
1. Verify DATABASE_URL is set
2. Check database service is running
3. Ensure migrations ran successfully

### Slow Responses
1. Check metrics in Railway
2. Consider:
   - Adding database indexes
   - Increasing database plan
   - Adding Redis cache
   - Enabling CDN

## Cost Optimization Tips

1. **Use connection pooling** (already configured in code)
2. **Add Redis caching** (reduces DB queries)
3. **Optimize database queries** (use indexes)
4. **Clean up old data** (archive old webhooks)
5. **Monitor usage** (Railway shows breakdown)

## Comparison: Railway vs Others

| Feature | Railway | Heroku | AWS | DigitalOcean |
|---------|---------|--------|-----|--------------|
| **Monthly Cost** | $10-20 | $10-15 | $25-50 | $20-40 |
| **Setup Time** | 5 min | 10 min | 1-2 hrs | 30 min |
| **Auto-scaling** | ✅ Yes | ✅ Yes | ⚠️ Manual | ⚠️ Manual |
| **Zero-downtime** | ✅ Yes | ✅ Yes | ⚠️ DIY | ⚠️ DIY |
| **Database included** | ✅ Yes | ✅ Yes | ❌ No | ✅ Yes |
| **Monitoring** | ✅ Built-in | ✅ Built-in | ⚠️ Extra | ⚠️ Extra |
| **Ease of use** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |

## Support

### Railway Support
- Docs: https://docs.railway.app
- Discord: https://discord.gg/railway
- Status: https://status.railway.app

### Application Support
- API Docs: https://your-app.railway.app/docs
- Logs: Railway dashboard
- Metrics: Railway dashboard

## Next Steps After Deployment

1. ✅ Test all API endpoints
2. ✅ Set up custom domain
3. ✅ Connect frontend application
4. ✅ Enable monitoring (Sentry)
5. ✅ Set up automated backups
6. ✅ Create staging environment
7. ✅ Add CI/CD tests
8. ✅ Document API for clients

---

**Ready to deploy?** Follow the steps above, and you'll be live in 10 minutes! 🚀
