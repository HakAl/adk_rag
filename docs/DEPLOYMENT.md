# Deployment Guide - Security & Rate Limiting

## Overview

This application implements PostgreSQL-based rate limiting and session management for production deployments.

## Security Features

### 1. Rate Limiting (PostgreSQL-based)

**Unauthenticated Endpoints** (per IP address):
- General API requests: 10 requests/minute
- Registration: 3 attempts/hour
- Login: 5 attempts/15 minutes
- Email verification resend: 3 attempts/hour

**Authenticated Endpoints** (per user):
- Chat endpoints: 30 requests/minute
- General endpoints: 60 requests/minute

**CLI Tool**: No rate limits applied (for developer use)

### 2. Login Lockout Protection
- After 5 failed login attempts: 15-minute lockout
- Lockout applies per IP address
- Successful login clears failed attempts
- Email verification also clears failed attempts

### 3. Session Management
- Secure HttpOnly cookies (HTTPS-only in production)
- CSRF token protection for state-changing operations
- 24-hour session lifetime
- PostgreSQL-backed storage (survives container restarts)

### 4. CORS Configuration
- Environment-based allowed origins
- Development: localhost:3000, localhost:5173
- Production: Add your GitHub Pages and Render URLs

## Database Setup

### Required Tables

The application needs these new tables in PostgreSQL:

1. **sessions** - User session storage
2. **rate_limits** - Rate limiting counters
3. **login_attempts** - Failed login tracking

### Migration

Run the migration script to create tables:

```bash
python migrations/add_session_rate_limit_tables.py
```

Or let the application auto-create tables on startup (if using SQLAlchemy's `create_all`).

## Environment Configuration

### Development (.env)

```env
ENVIRONMENT=development
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/rag_agent
SESSION_COOKIE_SECURE=false
```

### Production (.env)

```env
ENVIRONMENT=production
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/database
SESSION_COOKIE_SECURE=true

# Add your production URLs to main.py CORS config:
# allowed_origins = ["https://yourusername.github.io", ...]
```

## Deployment Steps

### 1. Update CORS Origins

In `main.py`, add your production frontend URL:

```python
if settings.environment == "production":
    allowed_origins.append("https://yourusername.github.io")
    allowed_origins.append("https://your-app.onrender.com")
```

### 2. Configure Render PostgreSQL

1. Create PostgreSQL database on Render
2. Copy the internal database URL
3. Set `DATABASE_URL` environment variable in Render dashboard
4. Set `ENVIRONMENT=production`

### 3. Run Migration

Render will auto-run on deploy, or manually:

```bash
python migrations/add_session_rate_limit_tables.py
```

### 4. Deploy Backend

Push to GitHub and let Render auto-deploy, or:

```bash
git push render main
```

### 5. Deploy Frontend

Build and deploy to GitHub Pages:

```bash
cd frontend
npm run build
# Deploy dist/ to GitHub Pages
```

### 6. Update Frontend API URL

In your frontend config, set the production backend URL:

```typescript
const API_URL = import.meta.env.PROD 
  ? 'https://your-app.onrender.com'
  : 'http://localhost:8000';
```

## CLI Setup for Developers

### Generate API Token

Users need to register via the web interface, then:

1. Login to web interface
2. Navigate to settings/profile
3. Generate API token (starts with `vba_`)
4. Save to `~/.ragagent/config.json`:

```json
{
  "api_token": "vba_your_token_here"
}
```

### CLI Usage

```bash
python -m app.cli.chat
```

The CLI will:
- Load token from config file
- Bypass rate limits (development use only)
- Use standard authentication flow

## Monitoring & Maintenance

### Background Tasks

The application runs hourly cleanup tasks:
- Remove expired sessions
- Clean up old rate limit entries
- Remove resolved login lockouts

### Rate Limit Monitoring

Monitor rate limit hits in logs:

```bash
# Render logs
render logs

# Local logs
tail -f logs/app.log
```

### Adjusting Limits

Edit `app/api/rate_limiter.py`:

```python
RATE_LIMITS = {
    "unauth_general": {"requests": 10, "window": 60},
    # ... adjust as needed
}
```

## Security Best Practices

### ✅ Implemented
- Rate limiting on all endpoints
- Login lockout protection
- CSRF protection for web sessions
- Secure HttpOnly cookies
- Input validation and sanitization
- PostgreSQL-backed storage (no data loss)

### 🔄 Future Enhancements
- Redis for high-scale rate limiting
- IP-based geolocation blocking
- Rate limit headers (X-RateLimit-*)
- Suspicious activity alerts
- Advanced DDoS protection

## Troubleshooting

### Sessions Lost on Restart
- **Symptom**: Users logged out after container restart
- **Cause**: Using in-memory storage
- **Fix**: Ensure PostgreSQL session storage is working (check database connection)

### Rate Limits Not Working
- **Symptom**: Unlimited requests allowed
- **Cause**: Database tables not created
- **Fix**: Run migration script

### CLI Getting Rate Limited
- **Symptom**: CLI users hitting rate limits
- **Cause**: Authorization header not set
- **Fix**: Ensure API token is in `~/.ragagent/config.json`

### CORS Errors in Production
- **Symptom**: Frontend can't call backend
- **Cause**: Production URL not in allowed_origins
- **Fix**: Add frontend URL to CORS config in main.py

## Support

For issues or questions:
1. Check logs: `render logs` or `tail -f logs/app.log`
2. Verify environment variables are set correctly
3. Ensure database migrations have run
4. Check CORS configuration matches your URLs