from fastapi import Depends, FastAPI

from app.auth import SupabaseUser, get_supabase_user

app = FastAPI(title="geology-engine")


@app.get("/")
async def root():
    return {"service": "geology-engine", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "geology-engine"}


@app.get("/me")
async def me(user: SupabaseUser = Depends(get_supabase_user)):
    """Return the authenticated user's identity (requires valid Supabase JWT)."""
    return {"user_id": user.id, "email": user.email, "role": user.role}
