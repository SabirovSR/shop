"""
Конфигурация WSGI для проекта core.

Экспортирует WSGI callable как переменную модуля с именем ``application``.

Для дополнительной информации смотрите
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

# Импорт os для работы с переменными окружения
import os

# Импорт функции для получения WSGI приложения Django
from django.core.wsgi import get_wsgi_application

# Установка переменной окружения DJANGO_SETTINGS_MODULE, если она не установлена
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Создание WSGI приложения
application = get_wsgi_application()
