# handlers/__init__.py
# Этот файл делает папку handlers настоящим Python-пакетом
# и экспортирует роутеры для main.py

from . import keyboards
from . import psycho
from . import challenges
from . import family

# Экспортируем роутеры для удобного импорта в main.py
__all__ = ['keyboards', 'psycho', 'challenges', 'family']