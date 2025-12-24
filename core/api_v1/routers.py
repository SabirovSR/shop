# Импорт для локального хранения данных в потоке
from threading import local

# Локальная переменная для хранения текущей базы данных в потоке
current_db = local()

# Маршрутизатор баз данных для разделения на buy и sell
class BuySellRouter:
    # Определяет базу для чтения
    def db_for_read(self, model, **hints):
        if hasattr(current_db, 'db'):
            return current_db.db  # Возвращает установленную базу ('buy' или 'sell')
        return 'default'  # По умолчанию

    # Определяет базу для записи
    def db_for_write(self, model, **hints):
        if hasattr(current_db, 'db'):
            return current_db.db
        return 'default'

    # Разрешает связи между объектами из разных баз
    def allow_relation(self, obj1, obj2, **hints):
        return True

    # Разрешает миграции для определенных баз
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'api_v1':  # Для нашего API приложения
            return db in ['buy', 'sell', 'default']  # Разрешить миграции в эти базы
        return True  # Для других приложений разрешить все