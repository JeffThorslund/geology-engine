# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

geology-engine is a FastAPI service deployed on Railway. It provides health check endpoints and integrates with Supabase JWT authentication. The service depends on the `ferreus_rbf` package from PyPI.

## Development Commands

### Setup and Running

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server with auto-reload (development mode)
uvicorn app.main:app --reload

# Run server in production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run a single test file
pytest tests/test_auth.py -v

# Run a specific test
pytest tests/test_auth.py::TestPublicRoutes::test_root_returns_200_without_auth -v
```

**Important**: After making changes to `app/` or `tests/` code, always run `pytest tests/ -v` to verify nothing is broken before considering the change complete.

## Architecture

### Authentication Flow

The app uses Supabase JWT (HS256) for authentication:

1. `app/config.py` - Settings loaded from environment using pydantic-settings. Requires `SUPABASE_JWT_SECRET` to be set
2. `app/auth.py` - Provides `get_supabase_user` dependency that verifies Bearer tokens and extracts user claims (id, email, role)
3. Protected endpoints use `Depends(get_supabase_user)` to enforce authentication

Key implementation details:
- JWT verification happens in `app/auth.py:get_supabase_user` (line 21-59)
- Settings are cached globally and validated on first access via `app/config.py:get_settings`
- Test fixtures in `tests/conftest.py` create valid/expired/tampered JWTs for testing

### Application Structure

- `app/main.py` - FastAPI app with route definitions
- `app/auth.py` - Supabase JWT verification dependency
- `app/config.py` - Settings loaded from environment/`.env` file (uses python-dotenv)
- `tests/conftest.py` - Shared pytest fixtures (client, JWT tokens)
- `tests/test_auth.py` - Comprehensive auth test suite covering all JWT scenarios

### Environment Configuration

Required environment variable:
- `SUPABASE_JWT_SECRET` - Supabase project JWT secret (found in Supabase dashboard: Settings > API > JWT Secret)

For local development:
1. Copy `.env.example` to `.env`
2. Set `SUPABASE_JWT_SECRET` in `.env`
3. The app automatically loads `.env` via python-dotenv
4. Never commit `.env` (already in `.gitignore`)

The app will fail to start if `SUPABASE_JWT_SECRET` is not set (fail-closed security).

## Deployment

Deployed on Railway using CLI. **See DEPLOY.md for comprehensive deployment guide.**

### Quick Deploy Workflow

```bash
# 1. Ensure tests pass
pytest tests/ -v

# 2. Deploy to Railway
railway up --service geology-engine

# 3. Verify deployment
railway logs --service geology-engine

# 4. Test endpoints
curl https://geology-engine-production.up.railway.app/health
```

### Railway Configuration

- **Start command**: Defined in `railway.json` as `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Port**: Railway automatically sets `PORT` environment variable (default 8080)
- **Domain**: `https://geology-engine-production.up.railway.app`
- **Excluded files**: See `.railwayignore` - tests, cache, and dev files are not deployed

### Environment Variables

Required Railway variables:
- `SUPABASE_JWT_SECRET` - Set via `railway variables set SUPABASE_JWT_SECRET="secret" --service geology-engine`

### Testing Deployed Authentication

Generate a test JWT using `scripts/generate_test_jwt.py`:

```bash
python scripts/generate_test_jwt.py
# Copy the token and test with:
curl -H "Authorization: Bearer <token>" https://geology-engine-production.up.railway.app/me
```

The JWT must be signed with the same `SUPABASE_JWT_SECRET` set in Railway variables.

## Testing Strategy

Tests use pytest with FastAPI's TestClient. The test suite in `tests/test_auth.py` covers:
- Public routes accessible without authentication
- Protected routes rejecting missing/malformed/expired/tampered tokens
- Valid tokens returning correct user claims
- Server error when JWT secret is misconfigured

Test fixtures create JWTs programmatically using the PyJWT library. The `SUPABASE_JWT_SECRET` is set in `tests/conftest.py` before importing the app to ensure consistent test behavior.
