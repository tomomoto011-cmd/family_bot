# handlers/__init__.py
"""
Пакет хендлеров бота.
Экспортирует роутеры для подключения в main.py
"""

from . import keyboards
from .psycho import router as psycho_router
from .challenges import router as challenges_router
from .family import router as family_router

__all__ = [
    'keyboards',
    'psycho_router', 
    'challenges_router',
    'family_router'
]