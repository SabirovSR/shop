"""
Конфигурация ASGI для проекта core.

Экспортирует ASGI callable как переменную модуля с именем ``application``.

Для дополнительной информации смотрите
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

# Импорт os для работы с переменными окружения
import os

# Импорт функции для получения ASGI приложения Django
from django.core.asgi import get_asgi_application

# Установка переменной окружения DJANGO_SETTINGS_MODULE, если она не установлена
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Создание ASGI приложения
application = get_asgi_application()
