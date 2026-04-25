# handlers/__init__.py
"""
Пакет хендлеров бота.
Экспортирует роутеры для main.py
"""

# Импортируем роутеры из модулей
from .psycho import router as psycho_router
from .challenges import router as challenges_router
from .family import router as family_router

# keyboards — это просто функции, импортируем их отдельно в main.py

__all__ = [
    'psycho_router',
    'challenges_router', 
    'family_router'
]