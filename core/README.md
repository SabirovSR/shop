# 🎮 PlayTrade — Магазин игр на Django

Веб-приложение для покупки и продажи игр с REST API и нормализованной БД (3НФ).

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Django](https://img.shields.io/badge/Django-4.2+-green.svg)

---

## ✨ Возможности

| Покупатели | Продавцы |
|------------|----------|
| 🛒 Каталог с фильтрами | ➕ Добавление игр |
| 🔍 Поиск игр | 💰 Баланс и вывод |
| 🛍️ Корзина и заказы | 📊 Статистика продаж |
| ⭐ Рейтинги и отзывы | 💬 Чат с покупателями |
| 💬 Чат с продавцами | |

---

## 🚀 Быстрый старт

```bash
# 1. Клонирование
git clone https://github.com/V1perBS/django-shop.git
cd django-shop

# 2. Виртуальное окружение
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/macOS

# 3. Зависимости
pip install -r core/requirements.txt

# 4. Миграции
python core/manage.py migrate

# 5. Запуск
python core/manage.py runserver 7070
```

🎉 Приложение: http://127.0.0.1:7070

---

## 📁 Структура

```
core/
├── api_v1/          # REST API (модели, views, serializers)
├── web/             # Веб-интерфейс (views, templates)
├── core/            # Настройки Django
├── media/           # Загруженные файлы
├── db.sqlite3       # База данных
└── requirements.txt
```

---

## 📖 API

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| GET | `/api/v1/games/` | Список игр |
| POST | `/api/v1/games/` | Создать игру |
| GET | `/api/v1/genres/` | Список жанров |

📚 Swagger: http://127.0.0.1:7070/api/v1/docs/swagger-ui/

---

## 🛠️ Команды

```bash
python core/manage.py makemigrations  # Создать миграции
python core/manage.py migrate         # Применить миграции
python core/manage.py createsuperuser # Создать админа
python core/manage.py test            # Запуск тестов
```

---

## 📝 Лицензия

MIT License

---

**GitHub:** [V1perBS](https://github.com/V1perBS)
