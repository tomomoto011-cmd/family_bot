import asyncio
import random
import logging
from config import GEMINI_API_KEY, logger

# === GEMINI SETUP ===
try:
    import google.generativeai as genai
    
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        _gemini_model = genai.GenerativeModel("gemini-1.5-flash")
        GEMINI_AVAILABLE = True
        logger.info("✅ Gemini AI подключён")
    else:
        GEMINI_AVAILABLE = False
        logger.warning("⚠️ GEMINI_API_KEY не задан, использую fallback")
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("⚠️ google-generativeai не установлен, использую fallback")

# === FALLBACK RESPONSES ===
FALLBACK_RESPONSES = {
    "psycho": [
        "Понимаю тебя. Иногда просто нужно выговориться. Я рядом. 💙",
        "Это сложная ситуация. Давай разберём: что случилось, что ты чувствуешь, что хочешь изменить?",
        "Твои чувства важны. Что бы ты хотел сделать прямо сейчас?",
        "Иногда лучший шаг — пауза. Подыши глубоко. Я здесь, когда будешь готов.",
        "Спасибо, что поделился. Ты не один. Я поддерживаю тебя. 🤝"
    ],
    "challenge": [
        "Отлично! Маленький шаг — это уже победа. 🎯",
        "Горжусь тобой! Продолжай в том же духе. 💪",
        "Каждый день — новая возможность. Ты справишься! ✨",
        "Молодец! Так держать! 🔥"
    ],
    "default": [
        "Спасибо, что поделился. Я здесь, чтобы помочь. 🤝",
        "Понял. Давай подумаем, как можно решить это вместе.",
        "Хороший вопрос. Давай разберёмся."
    ]
}

async def fallback_generate(prompt: str, system: str = "", task_type: str = "default", **kwargs) -> str:
    """Генерация через шаблоны (когда AI недоступен)"""
    templates = FALLBACK_RESPONSES.get(task_type, FALLBACK_RESPONSES["default"])
    base = random.choice(templates)
    
    if kwargs.get("user_name"):
        base = f"{kwargs['user_name']}, {base}"
    
    return base + "\n\n_⚠️ AI временно недоступен, но я всё ещё здесь._"

async def gemini_generate(prompt: str, system: str = "", **kwargs) -> str:
    """Генерация через Gemini"""
    if not GEMINI_AVAILABLE:
        raise RuntimeError("Gemini not available")
    
    full_prompt = f"{system}\n\nUSER: {prompt}\nASSISTANT:" if system else prompt
    
    try:
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
    """
    if GEMINI_AVAILABLE:
        try:
            return await gemini_generate(prompt, system, **kwargs)
        except Exception as e:
            logger.warning(f"⚠️ Gemini failed: {e}. Using fallback.")
    
    return await fallback_generate(prompt, system, task_type, **kwargs)