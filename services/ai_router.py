# services/ai_router.py
"""
AI Router: умный диспетчер для разных моделей
Gemini → Fallback при ошибке
"""

import logging
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)

# === GEMINI PROVIDER ===
try:
    import google.generativeai as genai
    from config import GEMINI_API_KEY
    
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        _gemini_model = genai.GenerativeModel("gemini-1.5-flash")
        GEMINI_AVAILABLE = True
    else:
        GEMINI_AVAILABLE = False
        logger.warning("⚠️ GEMINI_API_KEY not set, using fallback only")
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("⚠️ google-generativeai not installed, using fallback only")

# === FALLBACK PROVIDER ===
import random

FALLBACK_RESPONSES = {
    "psycho": [
        "Понимаю тебя. Иногда просто нужно выговориться. Я рядом. 💙",
        "Это сложная ситуация. Давай разберём: что случилось, что ты чувствуешь, что хочешь изменить?",
        "Твои чувства важны. Что бы ты хотел сделать прямо сейчас?",
        "Иногда лучший шаг — пауза. Подыши глубоко. Я здесь, когда будешь готов."
    ],
    "challenge": [
        "Отлично! Маленький шаг — это уже победа. 🎯",
        "Горжусь тобой! Продолжай в том же духе. 💪",
        "Каждый день — новая возможность. Ты справишься! ✨"
    ],
    "default": [
        "Спасибо, что поделился. Я здесь, чтобы помочь. 🤝",
        "Понял. Давай подумаем, как можно решить это вместе.",
        "Хороший вопрос. Давай разберёмся."
    ]
}

async def fallback_generate(prompt: str, system: str = "", task_type: str = "default", **kwargs) -> str:
    """Генерация ответа через шаблоны (когда AI недоступен)"""
    templates = FALLBACK_RESPONSES.get(task_type, FALLBACK_RESPONSES["default"])
    base = random.choice(templates)
    
    # Добавляем имя пользователя, если есть
    if kwargs.get("user_name"):
        base = f"{kwargs['user_name']}, {base}"
    
    return base + "\n\n⚠️ *AI временно недоступен, но я всё ещё здесь.*"

async def gemini_generate(prompt: str, system: str = "", **kwargs) -> str:
    """Генерация через Gemini"""
    if not GEMINI_AVAILABLE:
        raise RuntimeError("Gemini not available")
    
    full_prompt = f"{system}\n\nUSER: {prompt}\nASSISTANT:" if system else prompt
    
    try:
        # Запускаем в отдельном потоке, чтобы не блокировать event loop
        response = await asyncio.to_thread(
            _gemini_model.generate_content,
            full_prompt,
            safety_settings={
                "HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE",
                "SEXUAL": "BLOCK_MEDIUM_AND_ABOVE",
                "HATE_SPEECH": "BLOCK_MEDIUM_AND_ABOVE"
            }
        )
        return response.text.strip()
    except Exception as e:
        raise RuntimeError(f"Gemini error: {e}")

async def generate(prompt: str, system: str = "", task_type: str = "default", **kwargs) -> str:
    """
    Умный роутер: пробует Gemini, при ошибке — fallback.
    
    Args:
        prompt: Текст пользователя
        system: Системный промпт (инструкция для AI)
        task_type: Тип задачи (psycho/challenge/default) для выбора шаблонов
        **kwargs: Доп. параметры (user_name, context, etc.)
    """
    # Сначала пробуем Gemini
    if GEMINI_AVAILABLE:
        try:
            return await gemini_generate(prompt, system, **kwargs)
        except Exception as e:
            logger.warning(f"⚠️ Gemini failed: {e}. Switching to fallback.")
    
    # Fallback
    return await fallback_generate(prompt, system, task_type, **kwargs)