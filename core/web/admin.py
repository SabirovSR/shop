# Импорт для работы с админкой Django
from django.contrib import admin
from .models import (
    Cart, CartItem, Order, OrderItem, OrderStatus,
    Payment, PaymentMethod, SellerPayout, SupportMessage, GameRating
)


# ==============================================================================
# КОРЗИНА
# ==============================================================================

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('added_at',)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'user_type', 'is_active', 'total_items', 'created_at')
    list_filter = ('is_active', 'user_type', 'created_at')
    search_fields = ('user_id',)
    inlines = [CartItemInline]
    readonly_fields = ('created_at', 'updated_at', 'total_items', 'total_price')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'game_id', 'quantity', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('game_id',)


# ==============================================================================
# СТАТУСЫ И СПОСОБЫ ОПЛАТЫ (Справочники)
# ==============================================================================

@admin.register(OrderStatus)
class OrderStatusAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'sort_order')
    list_editable = ('sort_order',)
    ordering = ('sort_order',)


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active')
    list_filter = ('is_active',)
    list_editable = ('is_active',)


# ==============================================================================
# ЗАКАЗЫ
# ==============================================================================

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('total_price',)


class PaymentInline(admin.StackedInline):
    model = Payment
    extra = 0
    readonly_fields = ('created_at', 'paid_at')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user_id', 'status', 'total_amount', 'items_count', 'created_at')
    list_filter = ('status', 'created_at', 'user_type')
    search_fields = ('order_number', 'user_id')
    inlines = [OrderItemInline, PaymentInline]
    readonly_fields = ('order_number', 'created_at', 'updated_at', 'total_amount', 'items_count')
    date_hierarchy = 'created_at'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'game_id', 'quantity', 'price_at_purchase', 'total_price', 'seller_id')
    list_filter = ('order__status',)
    search_fields = ('order__order_number', 'game_id')


# ==============================================================================
# ПЛАТЕЖИ И ВЫПЛАТЫ
# ==============================================================================

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'method', 'status', 'amount', 'paid_at')
    list_filter = ('status', 'method', 'created_at')
    search_fields = ('order__order_number', 'transaction_id')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'


@admin.register(SellerPayout)
class SellerPayoutAdmin(admin.ModelAdmin):
    list_display = ('id', 'seller_id', 'order_item', 'amount', 'status', 'created_at', 'paid_at')
    list_filter = ('status', 'created_at')
    search_fields = ('seller_id',)
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'


# ==============================================================================
# СООБЩЕНИЯ И РЕЙТИНГИ
# ==============================================================================

@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'display_name', 'is_support', 'short_message', 'timestamp')
    list_filter = ('is_support', 'timestamp')
    search_fields = ('user', 'display_name', 'message')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'

    def short_message(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    short_message.short_description = 'Сообщение'


@admin.register(GameRating)
class GameRatingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'user_type', 'game', 'rating', 'created_at')
    list_filter = ('rating', 'user_type', 'created_at')
    search_fields = ('user_id', 'game__title')
    readonly_fields = ('created_at',)
