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

## Deploying to Railway

Deploy from your machine using the Railway CLI.

1. **Install the Railway CLI**  
   See [Railway CLI docs](https://docs.railway.com/guides/cli) (e.g. `brew install railway`).

2. **Log in and link the project**
   ```bash
   railway login
   railway link
   ```
   When prompted, select the **geology-engine** project and the **production** environment.

3. **Deploy**
   ```bash
   railway up --service geology-engine
   ```
   Use `--service geology-engine` because the project has more than one service. The CLI will upload the repo, Railway will build and deploy. For detached deploy (no log streaming): `railway up --service geology-engine -d`.

4. **Public URL**  
   Generate a domain in the dashboard: open the service → **Settings** → **Networking** → **Generate domain**. Or from the repo: `railway domain --service geology-engine`.

5. **Environment variables**  
   Set in the dashboard under the service’s **Variables**, or with `railway variables --service geology-engine`. The app uses `PORT` automatically (Railway sets it).

## Repository

```bash
# Create a new repo on GitHub, then:
git remote add origin git@github.com:<user>/geology-engine.git
git push -u origin main
```
