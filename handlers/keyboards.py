from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🧠 Психолог"),
                KeyboardButton(text="🗣 Высказаться")
            ],
            [
                KeyboardButton(text="👨‍👩‍👧 Семья"),
                KeyboardButton(text="🎯 Челлендж")
            ],
            [
                KeyboardButton(text="💰 Баланс"),
                KeyboardButton(text="🎁 Дать очки")
            ],
            [
                KeyboardButton(text="🐶 Питомцы"),
                KeyboardButton(text="🎮 Игра")
            ],
        ],
        resize_keyboard=True
    )


def role_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Родитель")],
            [KeyboardButton(text="Ребёнок")],
            [KeyboardButton(text="Друг семьи")]
        ],
        resize_keyboard=True
    )