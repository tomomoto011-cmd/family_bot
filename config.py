import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

# Валидация
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в .env!")
if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL не найден в .env!")

# Логирование
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)