import asyncio, random, logging
from config import GEMINI_API_KEY, logger

try:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    AI_OK = True
except:
    AI_OK = False
    logger.warning("⚠️ Gemini не подключён, использую fallback")

FALLBACK = {
    "psycho": ["Понимаю. Иногда просто нужно выговориться. Я рядом. 💙", "Это непросто. Давай разберём по шагам?", "Твои чувства важны. Что хочешь сделать сейчас?"],
    "default": ["Спасибо, что поделился. Я здесь. 🤝", "Понял. Давай подумаем вместе.", "Хороший вопрос."]
}

async def generate(prompt, system="", task_type="default", **kw):
    if AI_OK:
        try:
            full = f"{system}\n\nUSER: {prompt}\nASSISTANT:" if system else prompt
            resp = await asyncio.to_thread(model.generate_content, full, safety_settings={"HARASSMENT":"BLOCK_NONE","SEXUAL":"BLOCK_NONE"})
            return resp.text.strip()
        except Exception as e:
            logger.warning(f"⚠️ AI fallback: {e}")
    return random.choice(FALLBACK.get(task_type, FALLBACK["default"])) + "\n\n_⚠️ AI временно недоступен_"