# geology-engine

FastAPI service with a health check endpoint, deployed on Railway. Pushes to `main` trigger a deploy.

## Local setup

Requires Python 3.11+.

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Run the server locally
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

## API

| Endpoint  | Description                              |
| --------- | ---------------------------------------- |
| `GET /`   | Service info and link to docs            |
| `GET /health` | Health check (`{"status": "ok"}`)   |
| `GET /docs`   | Interactive Swagger UI (auto-generated) |

## Deployment (Railway)

### Deploy on push to main (recommended)

1. **Give Railway access to GitHub**  
   Install the [Railway GitHub app](https://github.com/apps/railway-app/installations/new) for your user or org so Railway can see your repos.

2. **Connect this repo to your service**  
   In the [Railway dashboard](https://railway.com): open project **geology-engine** → click the service → **Settings** → find **Service source** → **Connect Repo** → choose `JeffThorslund/geology-engine` and branch **main**. Save.

   After this, every push to `main` will trigger a new build and deploy.

3. **Public domain**  
   In the service: **Settings** → **Networking** → generate a domain, or run `railway domain` from the repo (with `railway link` already set).

4. **Environment variables**  
   Use **Variables** in the dashboard or `railway variables`. The app uses `PORT` automatically (Railway sets it).

### Manual deploy (CLI)

From the repo root, with the project linked (`railway link`):

```bash
railway up            # streams build + deploy logs
railway up -d         # detached
```

## Repository

```bash
# Create a new repo on GitHub, then:
git remote add origin git@github.com:<user>/geology-engine.git
git push -u origin main
```
