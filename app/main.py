from fastapi import FastAPI

app = FastAPI(title="geology-engine")


@app.get("/")
async def root():
    return {"service": "geology-engine", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "geology-engine"}
