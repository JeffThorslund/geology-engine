# geology-engine

FastAPI service with a health check endpoint, deployed on Railway.

## Local setup

Requires Python 3.11+.

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install Python dependencies (ferreus_rbf comes from PyPI; pip picks the right wheel)
pip install -r requirements.txt

# Run the server with auto-reload (development)
uvicorn app.main:app --reload

# Or run in production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

**Environment:** Config is loaded from the environment and automatically reads `.env` via python-dotenv. Copy `.env.example` to `.env` and set `SUPABASE_JWT_SECRET` for local development. Never commit `.env` (it is in `.gitignore`). The app will not start without a valid `SUPABASE_JWT_SECRET`.

### Testing

```bash
# With venv activated
pytest tests/ -v
```

## API Documentation

Interactive API documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs` (local) or `https://geology-engine-production.up.railway.app/docs` (production)
- **ReDoc**: `http://localhost:8000/redoc` (local) or `https://geology-engine-production.up.railway.app/redoc` (production)

The API includes:
- Public health check and service info endpoints
- Authenticated endpoints (require Supabase JWT): `/health/auth`, `/me`, `/rbf/coefficients`, `/rbf/evaluate`
- Public RBF interpolation endpoint: `/rbf/interpolate`

For detailed request/response schemas and examples, visit the `/docs` endpoint.

## Deploying to Railway

**See [DEPLOY.md](./DEPLOY.md) for comprehensive deployment guide.**

### Quick Deploy

```bash
# 1. Ensure tests pass
pytest tests/ -v

# 2. Deploy to Railway
railway up --service geology-engine

# 3. View deployment logs
railway logs --service geology-engine
```

### Requirements

- Railway CLI installed (`brew install railway`)
- Railway account and logged in (`railway login`)
- Project linked (`railway link` - select geology-engine project)
- `SUPABASE_JWT_SECRET` set in Railway variables

### Service Info

- **Domain**: `https://geology-engine-production.up.railway.app`
- **Start command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT` (defined in `railway.json`)
- **Environment variables**: Managed via `railway variables --service geology-engine`

Required variables:

| Variable              | Required | Description                                               |
| --------------------- | -------- | --------------------------------------------------------- |
| `PORT`                | Auto     | Injected by Railway automatically                         |
| `SUPABASE_JWT_SECRET` | Yes      | Supabase project JWT secret (Settings > API > JWT Secret) |

## Repository

```bash
# Create a new repo on GitHub, then:
git remote add origin git@github.com:<user>/geology-engine.git
git push -u origin main
```
