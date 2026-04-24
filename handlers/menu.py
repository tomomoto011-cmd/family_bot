from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧠 Психо")],
            [KeyboardButton(text="🥊 Груша")],
            [KeyboardButton(text="📅 Напоминания")],
            [KeyboardButton(text="🛒 Список")],
        ],
        resize_keyboard=True
    )