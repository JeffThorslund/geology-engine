"""
Run uvicorn with PORT from environment (Railway sets PORT; default 8000 locally).
Usage: python -m scripts.start
"""
import os
import uvicorn

port = int(os.environ.get("PORT", "8000"))
uvicorn.run(
    "app.main:app",
    host="0.0.0.0",
    port=port,
    reload=False,
)
