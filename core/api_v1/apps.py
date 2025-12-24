# Импорт базового класса для конфигурации приложения Django
from django.apps import AppConfig

# Конфигурация приложения api_v1
class ApiV1Config(AppConfig):
    # Имя приложения (должно совпадать с папкой)
    name = 'api_v1'
