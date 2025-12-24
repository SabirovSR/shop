#!/usr/bin/env python
"""Утилита командной строки Django для административных задач."""
# Импорт необходимых модулей
import os
import sys

def main():
    """Запуск административных задач."""
    # Установка переменной окружения для модуля настроек Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    try:
        # Импорт функции для выполнения команд из командной строки
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # Обработка ошибки импорта Django
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    # Выполнение команды из командной строки
    execute_from_command_line(sys.argv)

# Точка входа в скрипт
if __name__ == '__main__':
    main()
