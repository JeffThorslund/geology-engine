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

## API

| Endpoint      | Auth     | Description                                                |
| ------------- | -------- | ---------------------------------------------------------- |
| `GET /`       | Public   | Service info and link to docs                              |
| `GET /health` | Public   | Health check (`{"status": "ok"}`)                          |
| `GET /docs`   | Public   | Interactive Swagger UI (auto-generated)                    |
| `GET /me`     | Required | Returns the authenticated user's identity                  |

### Authentication

Protected endpoints require a valid **Supabase JWT** in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

The token is verified using the Supabase project's JWT secret (HS256). If the token is missing, expired, or invalid the API returns `401 Unauthorized`.

#### Calling from Next.js

```ts
const {
  data: { session },
} = await supabase.auth.getSession();

const res = await fetch("https://your-geology-engine.railway.app/me", {
  headers: {
    Authorization: `Bearer ${session?.access_token}`,
  },
});
```

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
