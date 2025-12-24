# Импорт для работы с админкой Django
from django.contrib import admin
from .models import Developer, Genre, Game, Review, BuyUser, SellUser


# ==============================================================================
# ПОЛЬЗОВАТЕЛИ
# ==============================================================================

@admin.register(BuyUser)
class BuyUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone', 'first_name', 'last_name', 'registration_date')
    list_filter = ('registration_date', 'country')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    readonly_fields = ('registration_date', 'total_purchases')
    date_hierarchy = 'registration_date'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('username', 'email', 'phone', 'password')
        }),
        ('Личные данные', {
            'fields': ('first_name', 'last_name', 'birth_date', 'avatar')
        }),
        ('Местоположение', {
            'fields': ('country', 'city'),
            'classes': ('collapse',)
        }),
        ('Статистика', {
            'fields': ('registration_date', 'total_purchases'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SellUser)
class SellUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone', 'balance', 'registration_date')
    list_filter = ('registration_date', 'country')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    readonly_fields = ('registration_date', 'total_sales', 'total_games_sold')
    date_hierarchy = 'registration_date'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('username', 'email', 'phone', 'password')
        }),
        ('Личные данные', {
            'fields': ('first_name', 'last_name', 'birth_date', 'avatar')
        }),
        ('Местоположение', {
            'fields': ('country', 'city'),
            'classes': ('collapse',)
        }),
        ('Финансы', {
            'fields': ('balance',)
        }),
        ('Статистика (вычисляется через SUM)', {
            'fields': ('registration_date', 'total_sales', 'total_games_sold'),
            'classes': ('collapse',),
            'description': 'Статистика рассчитывается динамически на основе заказов (3НФ)'
        }),
    )


# ==============================================================================
# РАЗРАБОТЧИКИ И ЖАНРЫ
# ==============================================================================

@admin.register(Developer)
class DeveloperAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'founded_date')
    search_fields = ('name', 'email')


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')
    search_fields = ('name',)


# ==============================================================================
# ИГРЫ
# ==============================================================================

class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'developer',
        'genre',
        'price',
        'discount_price',
        'platform',
        'seller_name',
        'in_stock',
        'sold_count'
    )
    list_filter = ('genre', 'platform', 'in_stock', 'is_bestseller', 'is_new', 'is_discount')
    search_fields = ('title', 'developer__name', 'seller__username')
    readonly_fields = ('current_price', 'discount_percent', 'seller_name')
    inlines = [ReviewInline]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'developer', 'genre', 'release_date', 'platform')
        }),
        ('Ценообразование', {
            'fields': ('price', 'discount_price', 'current_price', 'discount_percent')
        }),
        ('Продавец (3НФ - FK)', {
            'fields': ('seller', 'seller_username'),
            'description': 'seller - FK на SellUser (3НФ), seller_username - для обратной совместимости'
        }),
        ('Флаги', {
            'fields': ('in_stock', 'is_bestseller', 'is_new', 'is_discount'),
            'classes': ('collapse',)
        }),
        ('Статистика', {
            'fields': ('rating', 'sold_count')
        }),
        ('Медиа', {
            'fields': ('image',)
        }),
    )


# ==============================================================================
# ОТЗЫВЫ
# ==============================================================================

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('game', 'reviewer_name', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('reviewer_name', 'game__title', 'comment')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
