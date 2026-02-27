# Railway Deployment Guide

This guide provides step-by-step instructions for deploying geology-engine to Railway.

## Prerequisites

1. **Railway CLI installed**
   ```bash
   # macOS
   brew install railway

   # Other platforms
   # See https://docs.railway.com/guides/cli
   ```

2. **Railway account and logged in**
   ```bash
   railway login
   ```

3. **Supabase JWT secret** (or test secret for development)

## Initial Setup (One-Time)

### 1. Link to Railway Project

If not already linked:

```bash
railway link
```

Select the **geology-engine** project and **production** environment when prompted.

Verify the link:

```bash
railway status
```

You should see:
```
Project: geology-engine
Environment: production
Service: geology-engine
```

### 2. Set Environment Variables

Set the required `GEOLOGY_ENGINE_API_KEY`:

```bash
# For production (use your real Supabase JWT secret)
railway variables set GEOLOGY_ENGINE_API_KEY="your-actual-supabase-jwt-secret" --service geology-engine

# For testing (use a test secret)
railway variables set GEOLOGY_ENGINE_API_KEY="test-jwt-secret-for-deployment-testing-only" --service geology-engine
```

Verify variables are set:

```bash
railway variables --service geology-engine
```

You should see `GEOLOGY_ENGINE_API_KEY` along with Railway's auto-injected variables.

### 3. Generate Public Domain

If not already done:

```bash
railway domain --service geology-engine
```

This will show your public URL (e.g., `https://geology-engine-production.up.railway.app`).

## Deployment Process

### Step 1: Pre-Deployment Checks

**a. Ensure virtual environment is activated:**

```bash
source .venv/bin/activate
```

**b. Run tests locally:**

```bash
pytest tests/ -v
```

All tests must pass before deploying.

**c. Verify railway.json is correct:**

```bash
cat railway.json
```

Should contain:
```json
{
  "$schema": "https://railway.com/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {}
}
```

The start command is defined in the Dockerfile's `CMD` directive rather than in `railway.json`
because the Dockerfile uses shell form to properly expand the `$PORT` environment variable.

> **Note:** The `dockerfilePath` is required because `ferreus_rbf` publishes Linux wheels
> tagged `manylinux_2_39`, which need glibc >= 2.39. The Dockerfile uses Ubuntu 24.04
> (glibc 2.39) to satisfy this. Without it, Railway defaults to Nixpacks, which has an
> older glibc and cannot install `ferreus_rbf`.

### Step 2: Deploy

Deploy to Railway:

```bash
railway up --service geology-engine
```

For detached deployment (non-blocking):

```bash
railway up --service geology-engine -d
```

### Step 3: Monitor Deployment

View logs in real-time:

```bash
railway logs --service geology-engine
```

Look for:
- `INFO:     Uvicorn running on http://0.0.0.0:XXXX`
- `INFO:     Application startup complete.`

### Step 4: Verify Deployment

**Test public endpoints:**

```bash
# Get your Railway domain
RAILWAY_DOMAIN=$(railway domain --service geology-engine 2>&1 | grep "https://" | awk '{print $NF}')

# Test root endpoint
curl $RAILWAY_DOMAIN/

# Expected output:
# {"service":"geology-engine","docs":"/docs"}

# Test health endpoint
curl $RAILWAY_DOMAIN/health

# Expected output:
# {"status":"ok","service":"geology-engine"}
```

### Step 5: Test Authentication

**a. Generate a test JWT:**

Create a Python script to generate a JWT with your Railway secret:

```python
# test_jwt.py
import jwt
import time

# Use the same secret you set in Railway
SECRET = "test-jwt-secret-for-deployment-testing-only"  # Replace with your actual secret

now = int(time.time())
payload = {
    "sub": "test-user-123",
    "email": "test@example.com",
    "role": "authenticated",
    "iat": now,
    "exp": now + 3600,  # Valid for 1 hour
}

token = jwt.encode(payload, SECRET, algorithm="HS256")
print(token)
```

Run it:

```bash
python test_jwt.py
```

**b. Test the protected `/me` endpoint:**

```bash
# Copy the token from above
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."

# Make authenticated request
curl -H "Authorization: Bearer $TOKEN" $RAILWAY_DOMAIN/me

# Expected output:
# {"user_id":"test-user-123","email":"test@example.com","role":"authenticated"}
```

## Troubleshooting

### Deployment fails

```bash
# Check logs for errors
railway logs --service geology-engine --follow

# Common issues:
# - Missing GEOLOGY_ENGINE_API_KEY: Set it with `railway variables set`
# - Build errors: Check requirements.txt and Python version
```

### Authentication fails (401)

```bash
# Verify JWT secret is set
railway variables --service geology-engine | grep SUPABASE

# Ensure your JWT is signed with the same secret
# Check token expiration
# Verify Authorization header format: "Bearer <token>"
```

### Service won't start

```bash
# Check if PORT is being read correctly
railway logs --service geology-engine | grep PORT

# Verify start command in railway.json
# Ensure all dependencies are in requirements.txt
```

## Quick Deploy Checklist

- [ ] Tests pass locally (`pytest tests/ -v`)
- [ ] `GEOLOGY_ENGINE_API_KEY` is set in Railway
- [ ] Deploy with `railway up --service geology-engine`
- [ ] Check logs for successful startup
- [ ] Test public endpoints (`/`, `/health`)
- [ ] Test authenticated endpoint (`/me`) with valid JWT
- [ ] Verify response times and errors

## Additional Commands

```bash
# Open Railway dashboard
railway open

# View service status
railway status

# Restart service
railway restart --service geology-engine

# View all environment variables
railway variables --service geology-engine

# Remove a variable
railway variables unset VARIABLE_NAME --service geology-engine
```

## Files Excluded from Deployment

The `.railwayignore` file ensures these are not deployed:

- `tests/` - Test files
- `.pytest_cache/` - Test cache
- `__pycache__/` - Python cache
- `.cursor/`, `.vscode/`, `.idea/` - IDE files
- `.env` - Local environment files
- Development scripts like `scripts/run-local.sh`

Only production-necessary files are deployed to Railway.
