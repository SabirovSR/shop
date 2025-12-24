# Импорт для создания кастомных фильтров Django
from django import template

# Регистратор для фильтров
register = template.Library()

# Кастомный фильтр для получения значения из словаря по ключу
@register.filter
def get_item(dictionary, key):
    # Возвращает значение по ключу или 0, если ключ не найден
    return dictionary.get(key, 0)