# URL-шаблоны для API v1

# Импорты Django и DRF
from django.urls import path
from . import views
from drf_spectacular.views import (
    SpectacularAPIView,  # Схема API
    SpectacularRedocView,  # Документация ReDoc
    SpectacularSwaggerView,  # Документация Swagger
)

# Список URL-шаблонов
urlpatterns = [
    # Разработчики: список и детальная страница
    path("developers/", views.developer_list, name="developer-list"),
    path("developers/<int:pk>/", views.developer_detail, name="developer-detail"),
    # Игры: список, создание, детальная страница
    path("games/", views.GameListCreateView.as_view(), name="game-list"),
    path("games/<int:pk>/", views.GameDetailView.as_view(), name="game-detail"),
    # Жанры: список
    path("genres/", views.GenreView.as_view(), name="genre-list"),
    # Отзывы: список, детальная страница
    path("reviews/", views.ReviewList.as_view(), name="review-list"),
    path("reviews/<int:pk>/", views.ReviewDetail.as_view(), name="review-detail"),
    # Отзывы для конкретной игры
    path(
        "games/<int:game_id>/reviews/", views.ReviewList.as_view(), name="game-reviews"
    ),
    # Документация API
    path('docs/', SpectacularAPIView.as_view(), name='schema'),  # JSON схема
    path('docs/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),  # Swagger UI
    path('docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),  # ReDoc
]
