"""FastAPI entrypoint: CORS open for the Vite dev server (free-tier static)."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.documents import router as documents_router
from .api.review import router as review_router


def create_app() -> FastAPI:
    app = FastAPI(title="Yojana Mitra — Notice Explainer", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(documents_router)
    app.include_router(review_router)

    @app.get("/health")
    def health() -> dict:
        return {"ok": True}

    return app


app = create_app()
