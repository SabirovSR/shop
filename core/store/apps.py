# Импорт базового класса для конфигурации приложения Django
from django.apps import AppConfig

# Конфигурация приложения store
class StoreConfig(AppConfig):
    # Тип поля автоинкремента по умолчанию
    default_auto_field = 'django.db.models.BigAutoField'
    # Имя приложения
    name = 'store'
