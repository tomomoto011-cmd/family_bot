# handlers/__init__.py
from .psycho import router as psycho_router
from .challenges import router as challenges_router
from .family import router as family_router

__all__ = ['psycho_router', 'challenges_router', 'family_router']