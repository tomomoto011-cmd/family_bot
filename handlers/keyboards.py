from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🧠 Психолог"), KeyboardButton(text="🎯 Челлендж")],
        [KeyboardButton(text="👨‍👩‍👧 Семья"), KeyboardButton(text="💰 Баланс")],
        [KeyboardButton(text="🐶 Питомцы"), KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="🗣 Высказаться"), KeyboardButton(text="🔄 Меню")]
    ], resize_keyboard=True)

def role_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Родитель")],
        [KeyboardButton(text="Ребёнок")],
        [KeyboardButton(text="Друг семьи")]
    ], resize_keyboard=True, one_time_keyboard=True)