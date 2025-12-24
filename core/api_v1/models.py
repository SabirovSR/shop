# Импорты Django для работы с моделями базы данных
from django.db import models  # Основной класс для моделей
from django.contrib.auth.hashers import make_password  # Функция хэширования паролей
from django.utils import timezone  # Работа с датами и временем


# ==============================================================================
# ПОЛЬЗОВАТЕЛИ
# ==============================================================================

class BuyUser(models.Model):
    """
    Модель для покупателей игр
    """
    # Уникальное имя пользователя
    username = models.CharField(max_length=100, unique=True)
    # Хэшированный пароль
    password = models.CharField(max_length=255)
    # Уникальный email
    email = models.EmailField(unique=True)
    # Номер телефона
    phone = models.CharField(max_length=20)
    # Имя (необязательно)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    # Фамилия (необязательно)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    # Страна (необязательно)
    country = models.CharField(max_length=100, blank=True, null=True)
    # Город (необязательно)
    city = models.CharField(max_length=100, blank=True, null=True)
    # Дата рождения (необязательно)
    birth_date = models.DateField(blank=True, null=True)
    # Аватар пользователя (необязательно)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    # Дата регистрации (автоматически)
    registration_date = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Покупатель'
        verbose_name_plural = 'Покупатели'

    def __str__(self):
        return self.username

    # Свойство для получения total_purchases через агрегацию (3НФ)
    @property
    def total_purchases(self):
        """
        Общая сумма покупок - вычисляется динамически через SUM()
        НЕ хранится в базе данных (соответствует 3НФ)
        """
        from web.models import OrderItem, Order
        from django.db.models import Sum, F
        
        total = OrderItem.objects.filter(
            order__user_id=self.id,
            order__user_type='buy'
        ).aggregate(
            total=Sum(F('price_at_purchase') * F('quantity'))
        )['total']
        
        return total or 0


class SellUser(models.Model):
    """
    Модель для продавцов игр
    
    Примечание: поле balance хранит текущий баланс, который обновляется
    при поступлении средств. Альтернативно можно вычислять через
    SUM(seller_payouts.amount), но для производительности храним.
    """
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    # Баланс продавца (обновляется при продажах)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    registration_date = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Продавец'
        verbose_name_plural = 'Продавцы'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username

    # Свойство для получения total_sales через агрегацию (3НФ)
    @property
    def total_sales(self):
        """
        Общая сумма продаж - вычисляется динамически через SUM()
        SUM(order_items.price_at_purchase * quantity) для товаров этого продавца
        НЕ хранится в базе данных (соответствует 3НФ)
        """
        from web.models import OrderItem
        from django.db.models import Sum, F
        
        total = OrderItem.objects.filter(
            seller_id=self.id
        ).aggregate(
            total=Sum(F('price_at_purchase') * F('quantity'))
        )['total']
        
        return total or 0

    @property
    def total_games_sold(self):
        """Количество проданных игр"""
        from web.models import OrderItem
        from django.db.models import Sum
        
        count = OrderItem.objects.filter(
            seller_id=self.id
        ).aggregate(
            total=Sum('quantity')
        )['total']
        
        return count or 0


# ==============================================================================
# РАЗРАБОТЧИКИ И ЖАНРЫ
# ==============================================================================

class Developer(models.Model):
    """
    Модель для разработчиков игр
    """
    # Название разработчика
    name = models.CharField(max_length=100)
    # Email разработчика
    email = models.EmailField(unique=True)
    # Биография
    bio = models.TextField()
    # Дата основания
    founded_date = models.DateField()

    class Meta:
        verbose_name = 'Разработчик'
        verbose_name_plural = 'Разработчики'

    def __str__(self):
        return self.name


class Genre(models.Model):
    """
    Модель для жанров игр (справочник)
    """
    # Название жанра (уникальное)
    name = models.CharField(max_length=50, unique=True)
    # Описание жанра
    description = models.TextField()
    # Иконка или код для фронтенда (опционально)
    icon = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'

    def __str__(self):
        return self.name


# ==============================================================================
# ИГРЫ
# ==============================================================================

class Game(models.Model):
    """
    Модель для игр (3НФ)
    
    Изменения для соответствия 3НФ:
    - Убран game_type (дублировал genre)
    - seller теперь FK на SellUser вместо CharField
    - genre остаётся как FK (правильно)
    """
    PLATFORM_CHOICES = [
        ('PC', 'PC'),
        ('PS', 'PlayStation'),
        ('XBOX', 'Xbox'),
        ('NINTENDO', 'Nintendo'),
    ]

    # Название игры
    title = models.CharField(max_length=200)
    
    # Связь с разработчиком (может быть null)
    developer = models.ForeignKey(
        Developer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='games'
    )
    
    # Связь с жанром (может быть null) - единственный источник информации о жанре
    genre = models.ForeignKey(
        Genre,
        on_delete=models.SET_NULL,
        null=True,
        related_name='games'
    )
    
    # Дата релиза
    release_date = models.DateField()
    
    # Цена игры
    price = models.DecimalField(max_digits=8, decimal_places=2)
    
    # Скидочная цена (необязательно)
    discount_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    # В наличии ли игра
    in_stock = models.BooleanField(default=True)
    
    # Изображение игры (необязательно)
    image = models.ImageField(upload_to='games/', null=True, blank=True)
    
    # Рейтинг игры (вычисляется как среднее из GameRating)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    
    # Платформа
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES, default='PC')
    
    # Флаги для фильтрации
    is_bestseller = models.BooleanField(default=False)
    is_new = models.BooleanField(default=False)
    is_discount = models.BooleanField(default=False)
    
    # Количество проданных копий (можно вычислять через OrderItem, но храним для производительности)
    sold_count = models.IntegerField(default=0)
    
    # Продавец - FK на SellUser (вместо CharField)
    # Используем seller_id для прямой связи
    seller = models.ForeignKey(
        SellUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='games'
    )
    
    # Для обратной совместимости - старое поле seller как строка
    # Будет удалено после миграции
    seller_username = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = 'Игра'
        verbose_name_plural = 'Игры'

    def __str__(self):
        return self.title

    @property
    def current_price(self):
        """Свойство для получения текущей цены (с учетом скидки)"""
        return self.discount_price if self.discount_price else self.price

    @property
    def discount_percent(self):
        """Процент скидки"""
        if self.discount_price and self.price:
            return int((1 - self.discount_price / self.price) * 100)
        return 0

    @property
    def seller_name(self):
        """Имя продавца для отображения"""
        if self.seller:
            return self.seller.username
        return self.seller_username or 'Неизвестный продавец'


# ==============================================================================
# ОТЗЫВЫ
# ==============================================================================

class Review(models.Model):
    """
    Модель для отзывов на игры
    """
    # Связь с игрой
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    # Имя рецензента
    reviewer_name = models.CharField(max_length=100)
    # Рейтинг (число)
    rating = models.IntegerField()
    # Текст отзыва
    comment = models.TextField()
    # Дата создания отзыва
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']

    def __str__(self):
        return f"Отзыв для {self.game.title} от {self.reviewer_name}"
