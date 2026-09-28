"""FastAPI entrypoint: CORS open for the Vite dev server (free-tier static)."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.audit import router as audit_router
from .api.documents import router as documents_router
from .api.legal_aid import router as legal_aid_router
from .api.review import router as review_router
from .api.voice import router as voice_router


def create_app() -> FastAPI:
    import os as _os

    if not _os.getenv("REVIEWER_API_KEY"):
        print("WARNING: REVIEWER AUTH DISABLED — set REVIEWER_API_KEY to protect /api/v1/review/*")
    app = FastAPI(title="Yojana Mitra — Notice Explainer", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(documents_router)
    app.include_router(legal_aid_router)
    app.include_router(audit_router)
    app.include_router(voice_router)
    app.include_router(review_router)

    @app.get("/health")
    def health() -> dict:
        from .api import deps as _deps

        return {"ok": True, "aiMode": _deps.AI_MODE}

    return app


app = create_app()
