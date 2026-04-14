# Routes package init
from .jobs import router as jobs_router
from .health import router as health_router
from .candidates import router as candidates_router

__all__ = ["jobs_router", "health_router", "candidates_router"]