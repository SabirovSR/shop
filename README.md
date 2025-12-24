# 🎮 PlayTrade — Магазин игр на Django

Веб-приложение для покупки и продажи игр с REST API и нормализованной БД (3НФ).

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Django](https://img.shields.io/badge/Django-4.2+-green.svg)
![DRF](https://img.shields.io/badge/DRF-3.14+-orange.svg)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)

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

## 📁 Структура проекта

```
core/
├── api_v1/              # REST API
│   ├── models.py        # Модели данных (3НФ)
│   ├── views.py         # API endpoints
│   ├── serializers.py   # DRF сериализаторы
│   └── urls.py          # Маршрутизация API
├── web/                 # Веб-интерфейс
│   ├── views.py         # View-функции
│   ├── models.py        # Модели корзины/заказов
│   ├── templates/       # HTML шаблоны
│   │   ├── base.html    # Базовый шаблон
│   │   ├── catalog.html # Каталог игр
│   │   └── ...
│   └── static/web/css/  
│       └── main.css     # Единый CSS файл
├── core/                # Настройки Django
├── media/               # Загруженные файлы
├── API.md               # Документация API
├── db.sqlite3           # База данных
└── requirements.txt
```

---

## 🎨 Дизайн-система

### Цветовая палитра

| Цвет | Hex | Использование |
|------|-----|---------------|
| Primary Gradient | `#667eea` → `#764ba2` | Фон |
| Gold | `#ffd700` | Акцент, заголовки |
| CTA Orange | `#ff6b35` → `#f7931e` | Кнопки действия |
| Success Green | `#28a745` → `#20c997` | Успех, подтверждение |

### CSS Классы

```html
<!-- Карточки с эффектом стекла -->
<div class="glass-card p-6">...</div>
<div class="glass-card-dark p-4">...</div>

<!-- Кнопки -->
<button class="btn btn-primary">Купить</button>
<button class="btn btn-success">Подтвердить</button>
<button class="btn btn-outline-light">Отмена</button>

<!-- Типография -->
<h1 class="title-gold">Заголовок</h1>
<p class="text-gold">Акцентный текст</p>
```

---

## 📖 API

Полная документация: **[API.md](core/API.md)**

### Основные эндпоинты

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| GET | `/api/v1/games/` | Список игр |
| POST | `/api/v1/games/` | Создать игру |
| GET | `/api/v1/games/{id}/` | Детали игры |
| PUT | `/api/v1/games/{id}/` | Обновить игру |
| DELETE | `/api/v1/games/{id}/` | Удалить игру |
| GET | `/api/v1/genres/` | Список жанров |
| GET | `/api/v1/developers/` | Разработчики |
| GET | `/api/v1/reviews/` | Отзывы |
| GET | `/api/v1/games/{id}/reviews/` | Отзывы игры |

### Интерактивная документация

- 📚 Swagger: http://127.0.0.1:7070/api/v1/docs/swagger-ui/
- 📖 ReDoc: http://127.0.0.1:7070/api/v1/docs/redoc/

### Пример запроса

```bash
# Получить все игры
curl http://localhost:7070/api/v1/games/

# Создать отзыв
curl -X POST http://localhost:7070/api/v1/reviews/ \
  -H "Content-Type: application/json" \
  -d '{"game": 1, "reviewer_name": "User", "rating": 5, "comment": "Great!"}'
```

---

## 🗃️ База данных (3НФ)

### Основные модели

```
BuyUser          SellUser         Game
├── username     ├── username     ├── title
├── email        ├── email        ├── price
├── phone        ├── balance      ├── genre (FK)
└── avatar       └── avatar       └── developer (FK)

Order            OrderItem        Cart
├── user_id      ├── order (FK)   ├── user_id
├── status       ├── game_id      └── items[]
└── items[]      └── price_at_purchase
```

### Вычисляемые свойства (не хранятся)

```python
# Динамический расчёт вместо хранения
Order.total_amount  # SUM(items.price * quantity)
BuyUser.total_purchases  # SUM(all_orders)
SellUser.total_sales  # SUM(sold_items)
```

---

## 🛠️ Команды разработки

```bash
# Миграции
python core/manage.py makemigrations
python core/manage.py migrate

# Админ-пользователь
python core/manage.py createsuperuser

# Тесты
python core/manage.py test

# Сбор статики
python core/manage.py collectstatic
```

---

## ⚡ Оптимизации

### Frontend
- ✅ Единый CSS файл `main.css` (уменьшение HTTP запросов)
- ✅ Template inheritance с `base.html`
- ✅ Lazy loading для изображений
- ✅ CSS переменные для консистентности
- ✅ Glass morphism эффекты через backdrop-filter

### Backend
- ✅ Database normalized to 3NF
- ✅ `select_related()` для FK joins
- ✅ Computed properties вместо денормализации
- ✅ drf-spectacular для OpenAPI схемы

---

## 📝 Лицензия

MIT License

---

**GitHub:** [V1perBS](https://github.com/V1perBS)

*Последнее обновление: Декабрь 2024*
