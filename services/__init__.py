# services/__init__.py
"""
Пакет сервисов: AI, внешние API, утилиты.
НЕ импортирует ничего из handlers/ во избежание циклических импортов.
"""

# Экспортируем только AI-роутер
from .ai_router import generate

__all__ = ['generate']