from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def main_menu():
    """Главное меню"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🧠 Психолог"),
                KeyboardButton(text="🎯 Челлендж")
            ],
            [
                KeyboardButton(text="👨‍👩‍👧 Семья"),
                KeyboardButton(text="💰 Баланс")
            ],
            [
                KeyboardButton(text="🐶 Питомцы"),
                KeyboardButton(text="📊 Статистика")
            ],
            [
                KeyboardButton(text=" Высказаться"),
                KeyboardButton(text="🔄 Меню")
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )


def role_keyboard():
    """Выбор роли"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Родитель")],
            [KeyboardButton(text="Ребёнок")],
            [KeyboardButton(text="Друг семьи")],
            [KeyboardButton(text="🔄 Назад")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def psycho_keyboard():
    """Клавиатура для психо-режима"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔚 Выйти из режима", callback_data="psycho_exit")]
        ]
    )


def challenge_keyboard(challenge_id):
    """Кнопки для челленджа"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Выполнено", callback_data=f"challenge_done:{challenge_id}")],
            [InlineKeyboardButton(text="❌ Пропустить", callback_data=f"challenge_skip:{challenge_id}")]
        ]
    )