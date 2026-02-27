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

1. `app/config.py` - Settings loaded from environment using pydantic-settings. Requires `GEOLOGY_ENGINE_API_KEY` env var
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
- `app/rbf_models.py` - Pydantic models for RBF endpoints (SpatialInterval, request/response schemas)
- `app/rbf_service.py` - Business logic layer for RBF operations (fitting, evaluation, coefficient extraction)
- `tests/conftest.py` - Shared pytest fixtures (client, JWT tokens)
- `tests/test_auth.py` - Comprehensive auth test suite covering all JWT scenarios
- `tests/test_rbf.py` - RBF interpolation tests for both public and authenticated endpoints

### RBF Interpolation Endpoints

The service provides three RBF (Radial Basis Function) interpolation endpoints using the `ferreus_rbf` library:

#### 1. POST `/rbf/interpolate` (Public)
**No authentication required.** Legacy endpoint for simple RBF interpolation.

Request format:
```json
{
  "training_points": [[x1, y1], [x2, y2], ...],
  "training_values": [v1, v2, ...],
  "test_points": [[x_test1, y_test1], ...]
}
```

Response: `{"interpolated_values": [value1, value2, ...]}`

#### 2. POST `/rbf/coefficients` (Authenticated)
**Requires Supabase JWT.** Fits RBF model from 3D spatial intervals and returns model coefficients for client-side evaluation.

Request format (defined in `app/rbf_models.py:RBFCoefficientsRequest`):
```json
{
  "intervals": [
    {"x": 500000.0, "y": 4500000.0, "z": 100.0, "value": 0.0},
    {"x": 501000.0, "y": 4500000.0, "z": 100.0, "value": 1.0}
  ],
  "fitting_accuracy": 0.01
}
```

Response (defined in `app/rbf_models.py:RBFCoefficientsResponse`):
```json
{
  "source_points": [[x1, y1, z1], [x2, y2, z2], ...],
  "point_coefficients": [[c1], [c2], ...],
  "poly_coefficients": [[p1], ...] or null,
  "kernel_type": "linear",
  "polynomial_degree": 0,
  "nugget": 0.0,
  "translation_factor": [tx, ty, tz],
  "scale_factor": [sx, sy, sz],
  "extents": [min_x, min_y, min_z, max_x, max_y, max_z]
}
```

**Use case**: Client downloads coefficients once and evaluates the RBF function locally in the browser.

#### 3. POST `/rbf/evaluate` (Authenticated)
**Requires Supabase JWT.** Fits RBF model from 3D spatial intervals and evaluates at query points.

Request format (defined in `app/rbf_models.py:RBFEvaluateRequest`):
```json
{
  "intervals": [
    {"x": 500000.0, "y": 4500000.0, "z": 100.0, "value": 0.0},
    {"x": 501000.0, "y": 4500000.0, "z": 100.0, "value": 1.0}
  ],
  "query_points": [
    {"x": 500500.0, "y": 4500500.0, "z": 125.0}
  ],
  "fitting_accuracy": 0.01
}
```

Response (defined in `app/rbf_models.py:RBFEvaluateResponse`):
```json
{
  "values": [interpolated_value1, interpolated_value2, ...],
  "extents": [min_x, min_y, min_z, max_x, max_y, max_z]
}
```

**Use case**: Server-side RBF evaluation. Client sends training data and query points, receives interpolated values.

#### RBF Implementation Details

- **Data model**: `SpatialInterval` represents 3D points (x, y, z) with commodity values (signed distance)
- **Kernel**: Linear RBF kernel (`RBFKernelType.Linear`)
- **Fitting accuracy**: Configurable absolute accuracy (default: 0.01)
- **Service layer**: `app/rbf_service.py` handles RBF fitting, coefficient extraction, and evaluation
  - `fit_rbf_from_intervals()` - Converts SpatialIntervals to numpy arrays, fits RBF model
  - `extract_coefficients()` - Saves model to temp JSON, extracts coefficients, ensures proper cleanup
  - `evaluate_at_query_points()` - Fits RBF and evaluates at query points
- **File management**: Uses `tempfile.NamedTemporaryFile` with try/finally for guaranteed cleanup
- **Coefficient format**: Handles ferreus_rbf's JSON array format (dict with `nrows`, `ncols`, `data`)

### Environment Configuration

Required environment variable:
- `GEOLOGY_ENGINE_API_KEY` - JWT secret used to verify Bearer tokens

For local development:
1. Copy `.env.example` to `.env`
2. Set `GEOLOGY_ENGINE_API_KEY` in `.env`
3. The app automatically loads `.env` via python-dotenv
4. Never commit `.env` (already in `.gitignore`)

The app will fail to start if `GEOLOGY_ENGINE_API_KEY` is not set (fail-closed security).

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

- **Builder**: Dockerfile (Ubuntu 24.04, required for `ferreus_rbf` glibc 2.39 dependency)
- **Start command**: Defined in `Dockerfile` CMD as `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Port**: Railway automatically sets `PORT` environment variable (default 8080)
- **Domain**: `https://geology-engine-production.up.railway.app`
- **Excluded files**: See `.railwayignore` - tests, cache, and dev files are not deployed

### Environment Variables

Required Railway variables:
- `GEOLOGY_ENGINE_API_KEY` - Set via `railway variables set GEOLOGY_ENGINE_API_KEY="secret" --service geology-engine`

### Testing Deployed Authentication

Generate a test JWT using `scripts/generate_test_jwt.py`:

```bash
python scripts/generate_test_jwt.py
# Copy the token and test with:
curl -H "Authorization: Bearer <token>" https://geology-engine-production.up.railway.app/me
```

The JWT must be signed with the same `GEOLOGY_ENGINE_API_KEY` set in Railway variables.

## Testing Strategy

Tests use pytest with FastAPI's TestClient. The test suite in `tests/test_auth.py` covers:
- Public routes accessible without authentication
- Protected routes rejecting missing/malformed/expired/tampered tokens
- Valid tokens returning correct user claims
- Server error when JWT secret is misconfigured

Test fixtures create JWTs programmatically using the PyJWT library. The `GEOLOGY_ENGINE_API_KEY` is set in `tests/conftest.py` before importing the app to ensure consistent test behavior.
