# Импорты для моделей Django
from django.db import models
from django.utils import timezone
from decimal import Decimal


# ==============================================================================
# КОРЗИНА (Cart + CartItems) - Нормализованная структура 3НФ
# ==============================================================================

class Cart(models.Model):
    """
    Корзина покупок - шапка корзины (3НФ)
    Один пользователь = одна активная корзина
    """
    # ID пользователя (связь с BuyUser)
    user_id = models.IntegerField()
    # Тип пользователя (для совместимости)
    user_type = models.CharField(max_length=10, default='buy')
    # Дата создания корзины
    created_at = models.DateTimeField(auto_now_add=True)
    # Дата последнего обновления
    updated_at = models.DateTimeField(auto_now=True)
    # Активна ли корзина
    is_active = models.BooleanField(default=True)

    class Meta:
        # Уникальная активная корзина для пользователя
        constraints = [
            models.UniqueConstraint(
                fields=['user_id', 'user_type'],
                condition=models.Q(is_active=True),
                name='unique_active_cart_per_user'
            )
        ]

    def __str__(self):
        return f"Корзина #{self.id} для пользователя {self.user_id} ({self.user_type})"

    @property
    def total_items(self):
        """Общее количество товаров в корзине"""
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self):
        """Общая стоимость корзины"""
        return sum(item.subtotal for item in self.items.all())


class CartItem(models.Model):
    """
    Позиции корзины (3НФ)
    Связь многие-к-одному с Cart
    """
    # Связь с корзиной (FK)
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        null=True,  # Временно nullable для миграции
        blank=True
    )
    # ID пользователя (для обратной совместимости, будет удалено)
    user_id = models.IntegerField(null=True, blank=True)
    # Тип пользователя (для обратной совместимости, будет удалено)
    user_type = models.CharField(max_length=10, null=True, blank=True)
    # ID игры (FK на Game)
    game_id = models.IntegerField()
    # Количество в корзине
    quantity = models.PositiveIntegerField(default=1)
    # Дата добавления
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Уникальность: одна игра в одной корзине
        constraints = [
            models.UniqueConstraint(
                fields=['cart', 'game_id'],
                name='unique_game_in_cart'
            )
        ]

    def __str__(self):
        return f"CartItem #{self.id}: игра {self.game_id} x{self.quantity}"

    @property
    def subtotal(self):
        """Стоимость позиции (цена * количество)"""
        from api_v1.models import Game
        try:
            game = Game.objects.get(id=self.game_id)
            price = game.discount_price if game.discount_price else game.price
            return price * self.quantity
        except Game.DoesNotExist:
            return Decimal('0.00')


# ==============================================================================
# СТАТУСЫ ЗАКАЗОВ - Справочник (3НФ)
# ==============================================================================

class OrderStatus(models.Model):
    """
    Справочник статусов заказа (3НФ)
    """
    STATUS_CHOICES = [
        ('pending', 'Ожидает оплаты'),
        ('paid', 'Оплачен'),
        ('processing', 'В обработке'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('completed', 'Завершён'),
        ('cancelled', 'Отменён'),
        ('refunded', 'Возврат'),
    ]

    code = models.CharField(max_length=20, unique=True, choices=STATUS_CHOICES)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    # Порядок сортировки
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order']
        verbose_name = 'Статус заказа'
        verbose_name_plural = 'Статусы заказов'

    def __str__(self):
        return self.name


# ==============================================================================
# ЗАКАЗЫ (Orders + OrderItems) - Нормализованная структура 3НФ
# ==============================================================================

class Order(models.Model):
    """
    Заказ - шапка заказа (3НФ)
    Не хранит данные о товарах - они в OrderItem
    """
    # ID покупателя (связь с BuyUser)
    user_id = models.IntegerField()
    user_type = models.CharField(max_length=10, default='buy')

    # Статус заказа (FK на справочник)
    status = models.ForeignKey(
        OrderStatus,
        on_delete=models.PROTECT,
        related_name='orders',
        null=True,
        blank=True
    )

    # Даты
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Номер заказа (уникальный)
    order_number = models.CharField(max_length=50, unique=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Генерируем номер заказа
            import uuid
            self.order_number = f"ORD-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Заказ {self.order_number}"

    @property
    def total_amount(self):
        """
        Общая сумма заказа - вычисляется через SUM(order_items.price * quantity)
        НЕ хранится в базе (нормализация)
        """
        return sum(item.total_price for item in self.items.all())

    @property
    def items_count(self):
        """Количество позиций в заказе"""
        return self.items.count()


class OrderItem(models.Model):
    """
    Позиции заказа (3НФ)
    Хранит цену на момент покупки (price_at_purchase)
    """
    # Связь с заказом (FK)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )

    # ID игры (связь с Game)
    game_id = models.IntegerField()

    # Количество
    quantity = models.PositiveIntegerField(default=1)

    # Цена на момент покупки (важно для истории!)
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)

    # ID продавца для учёта выплат
    seller_id = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказов'

    def __str__(self):
        return f"OrderItem #{self.id}: игра {self.game_id} x{self.quantity}"

    @property
    def total_price(self):
        """Стоимость позиции = цена * количество"""
        return self.price_at_purchase * self.quantity


# ==============================================================================
# ПЛАТЕЖИ (Payments) - Отдельная таблица (3НФ)
# ==============================================================================

class PaymentMethod(models.Model):
    """
    Справочник способов оплаты (3НФ)
    """
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    icon = models.CharField(max_length=50, blank=True)  # CSS класс иконки

    class Meta:
        verbose_name = 'Способ оплаты'
        verbose_name_plural = 'Способы оплаты'

    def __str__(self):
        return self.name


class Payment(models.Model):
    """
    Платёж (3НФ)
    Отдельная таблица для платёжных данных
    """
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('processing', 'Обрабатывается'),
        ('completed', 'Завершён'),
        ('failed', 'Ошибка'),
        ('refunded', 'Возврат'),
        ('cancelled', 'Отменён'),
    ]

    # Связь с заказом (один заказ = один платёж)
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='payment'
    )

    # Способ оплаты (FK на справочник)
    method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    # Код метода оплаты (для обратной совместимости)
    method_code = models.CharField(max_length=20, blank=True)

    # Статус платежа
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )

    # Сумма платежа
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    # ID транзакции (от платёжной системы)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)

    # Даты
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    # Последние 4 цифры карты (для отображения)
    card_last_four = models.CharField(max_length=4, blank=True)

    class Meta:
        verbose_name = 'Платёж'
        verbose_name_plural = 'Платежи'

    def __str__(self):
        return f"Платёж #{self.id} для заказа {self.order.order_number}"


# ==============================================================================
# ВЫПЛАТЫ ПРОДАВЦАМ (SellerPayouts) - Для учёта выплат (3НФ)
# ==============================================================================

class SellerPayout(models.Model):
    """
    Выплаты продавцам (3НФ)
    Связывает заказы с выплатами продавцам
    """
    PAYOUT_STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('processing', 'Обрабатывается'),
        ('completed', 'Выплачено'),
        ('failed', 'Ошибка'),
    ]

    # ID продавца (связь с SellUser)
    seller_id = models.IntegerField()

    # Связь с позицией заказа
    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.CASCADE,
        related_name='seller_payouts'
    )

    # Сумма выплаты
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Статус выплаты
    status = models.CharField(
        max_length=20,
        choices=PAYOUT_STATUS_CHOICES,
        default='pending'
    )

    # Даты
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Выплата продавцу'
        verbose_name_plural = 'Выплаты продавцам'

    def __str__(self):
        return f"Выплата #{self.id} продавцу {self.seller_id}: {self.amount}"


# ==============================================================================
# СУЩЕСТВУЮЩИЕ МОДЕЛИ (Обновлённые)
# ==============================================================================

class SupportMessage(models.Model):
    """
    Модель для сообщений поддержки
    """
    # Идентификатор чата (например, 'buy_1' или 'sell_2')
    user = models.CharField(max_length=100)
    # Отображаемое имя отправителя
    display_name = models.CharField(max_length=100, default='Гость')
    # Текст сообщения
    message = models.TextField()
    # Флаг: сообщение от поддержки или от пользователя
    is_support = models.BooleanField(default=False)
    # Время отправки
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name = 'Сообщение поддержки'
        verbose_name_plural = 'Сообщения поддержки'

    def __str__(self):
        return f"{'Support' if self.is_support else self.display_name}: {self.message[:50]}"


class GameRating(models.Model):
    """
    Модель для рейтингов игр от пользователей
    """
    # ID пользователя
    user_id = models.IntegerField()
    # Тип пользователя
    user_type = models.CharField(max_length=10, default='buy')
    # Связь с игрой
    game = models.ForeignKey(
        'api_v1.Game',
        on_delete=models.CASCADE,
        related_name='user_ratings'
    )
    # Рейтинг (1-5)
    rating = models.IntegerField(default=5)
    # Дата создания
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Уникальность: один пользователь - один рейтинг на игру
        unique_together = ('user_id', 'user_type', 'game')
        verbose_name = 'Рейтинг игры'
        verbose_name_plural = 'Рейтинги игр'

    def __str__(self):
        return f"Рейтинг {self.rating} для игры {self.game.title} от пользователя {self.user_id}"


class ChatReadStatus(models.Model):
    """
    Модель для отслеживания прочитанных сообщений в чатах
    Хранится в БД вместо сессии для постоянства данных
    """
    user_id = models.IntegerField()
    user_type = models.CharField(max_length=10)  # 'buy' или 'sell'
    chat_key = models.CharField(max_length=255)  # Идентификатор чата
    last_read_at = models.DateTimeField()

    class Meta:
        unique_together = ('user_id', 'user_type', 'chat_key')
        verbose_name = 'Статус прочтения чата'
        verbose_name_plural = 'Статусы прочтения чатов'

    def __str__(self):
        return f"{self.user_type}_{self.user_id}: {self.chat_key} - {self.last_read_at}"
