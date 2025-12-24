"""
Конфигурация URL для проекта core.

Список `urlpatterns` маршрутизирует URL к представлениям. Для дополнительной информации смотрите:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Примеры:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

# Импорты Django
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Импорты представлений из приложений
from store.views import HomeView, DocsView
from web.views import (
    game_list, add_game, add_developer, buy_games, sell_games, catalog, about,
    account, register, logout_view, support_chat, cart, rate_game, get_user_rating,
    delete_game, checkout, payment_success, order_cancelled, select_game_chat,
    seller_chat, leave_review, withdraw_money, order_history
)

# Список URL-шаблонов
urlpatterns = [
    # Главная страница
    path('', game_list, name='home'),
    # О нас
    path('about/', about, name='about'),
    # Каталог игр
    path('catalog/', catalog, name='catalog'),
    # Регистрация
    path('register/', register, name='register'),
    # Получение рейтинга пользователя
    path('get-user-rating/', get_user_rating, name='get_user_rating'),
    # Корзина
    path('cart/', cart, name='cart'),
    # Аккаунт
    path('account/', account, name='account'),
    # Выход
    path('logout/', logout_view, name='logout'),
    # Чат с поддержкой
    path('support/', support_chat, name='support_chat'),
    # Оценка игры
    path('rate-game/', rate_game, name='rate_game'),
    # Покупка игр
    path('buy-games/', buy_games, name='buy_games'),
    # Продажа игр
    path('sell-games/', sell_games, name='sell_games'),
    # Добавление игры
    path('add-game/', add_game, name='add_game'),
    # Добавление разработчика
    path('add-developer/', add_developer, name='add_developer'),
    # Удаление игры
    path('delete-game/<int:game_id>/', delete_game, name='delete_game'),
    # Оформление заказа
    path('checkout/', checkout, name='checkout'),
    # Успешная оплата
    path('payment-success/', payment_success, name='payment_success'),
    path('order-cancelled/', order_cancelled, name='order_cancelled'),
    # Выбор игры для чата
    path('select-game-chat/', select_game_chat, name='select_game_chat'),
    # Чат с продавцом
    path('seller-chat/<int:game_id>/', seller_chat, name='seller_chat'),
    # Вывод денег
    path('withdraw/', withdraw_money, name='withdraw_money'),
    # История заказов
    path('orders/', order_history, name='order_history'),
    # Оставить отзыв
    path('leave-review/<int:game_id>/', leave_review, name='leave_review'),
    # Приветственная страница
    path('welcome/', HomeView.as_view(), name='welcome'),
    # Документация
    path('docs/', DocsView.as_view(), name='docs'),
    # Админка
    path('admin/', admin.site.urls),
    # API v1
    path('api/v1/', include('api_v1.urls')),
]

# В режиме отладки добавляем обслуживание медиа файлов
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
