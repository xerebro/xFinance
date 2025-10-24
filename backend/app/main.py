"""FastAPI application entrypoint for xFinance backend."""

from fastapi import FastAPI

from .config import Settings, get_settings
from .routers import (
    search,
    sources_edgar,
    sources_oge,
    sources_ptr_house,
    sources_ptr_senate,
)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application instance."""
    cfg = settings or get_settings()
    app = FastAPI(
        title="xFinance Sources API",
        version="0.1.0",
        default_response_class=cfg.default_response_class,
    )

    # include routers under a single versioned prefix
    app.include_router(sources_edgar.router, prefix=cfg.api_prefix)
    app.include_router(sources_ptr_house.router, prefix=cfg.api_prefix)
    app.include_router(sources_ptr_senate.router, prefix=cfg.api_prefix)
    app.include_router(sources_oge.router, prefix=cfg.api_prefix)
    app.include_router(search.router, prefix=cfg.api_prefix)

    return app


app = create_app()
