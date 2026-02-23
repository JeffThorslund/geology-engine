#!/usr/bin/env bash
# Run the app locally. Uses .env if present; otherwise requires SUPABASE_JWT_SECRET in env.
set -e
cd "$(dirname "$0")/.."
if [ ! -f .env ]; then
  echo "No .env found. Copy .env.example to .env and set SUPABASE_JWT_SECRET, or export it."
  if [ -z "$SUPABASE_JWT_SECRET" ]; then
    export SUPABASE_JWT_SECRET=dev-secret-change-me
    echo "Using SUPABASE_JWT_SECRET=dev-secret-change-me for this run only."
  fi
fi
python -m scripts.start
