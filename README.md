# geology-engine

FastAPI service with a health check endpoint, deployed on Railway.

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

1. Install the [Railway CLI](https://docs.railway.com/guides/cli) and log in:

   ```bash
   railway login
   ```

2. Initialize or link a Railway project from the repo root:

   ```bash
   railway init          # new project
   # or
   railway link          # existing project
   ```

3. Deploy:

   ```bash
   railway up            # streams build + deploy logs
   railway up -d         # detached (returns immediately)
   ```

4. Generate a public domain in the Railway dashboard under **Settings > Networking**, or run `railway domain`.

5. Environment variables (if any) are managed via `railway variables` or the dashboard. The app reads `PORT` at runtime (Railway injects it automatically).

## Repository

```bash
# Create a new repo on GitHub, then:
git remote add origin git@github.com:<user>/geology-engine.git
git push -u origin main
```
