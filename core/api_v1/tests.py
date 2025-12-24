# Импорты для тестирования Django
from django.test import TestCase, Client
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from api_v1.models import Game, Genre, Developer, BuyUser, SellUser
from web.models import CartItem
from api_v1.routers import current_db


# Тесты для добавления игры в корзину
class AddToCartTest(TestCase):
    databases = ['default', 'buy', 'sell']

    def setUp(self):
        # Создаем тестового клиента
        self.client = Client()
        # Создаем пользователя-покупателя
        self.user = BuyUser.objects.create(
            username='testuser',
            password=make_password('testpass'),
            email='test@example.com',
            phone='+1234567890'
        )
        # Создаем жанр
        self.genre = Genre.objects.create(
            name='Экшен',
            description='Экшн игры'
        )
        # Создаем игру
        self.game = Game.objects.create(
            title='Test Game',
            genre=self.genre,
            release_date='2023-01-01',
            price=100.00,
            in_stock=True,
            seller='testuser'
        )

    # Тест успешного добавления игры в корзину
    def test_add_to_cart_success(self):
        # Логинимся
        self.client.post('/register/', {
            'user_type': 'buy',
            'username': 'testuser',
            'password': 'testpass'
        })
        # Добавляем в корзину
        response = self.client.post('/catalog/', {
            'game_id': self.game.id
        })
        # Проверяем редирект
        self.assertEqual(response.status_code, 302)
        # Проверяем, что игра добавлена в корзину
        cart_item = CartItem.objects.filter(
            user_id=self.user.id,
            user_type='buy',
            game_id=self.game.id
        ).first()
        self.assertIsNotNone(cart_item)
        self.assertEqual(cart_item.quantity, 1)

    # Тест добавления уже существующей игры (увеличение количества)
    def test_add_to_cart_increase_quantity(self):
        # Создаем элемент корзины
        CartItem.objects.create(
            user_id=self.user.id,
            user_type='buy',
            game_id=self.game.id,
            quantity=1
        )
        # Логинимся
        self.client.post('/register/', {
            'user_type': 'buy',
            'username': 'testuser',
            'password': 'testpass'
        })
        # Добавляем еще раз
        self.client.post('/catalog/', {
            'game_id': self.game.id
        })
        # Проверяем количество
        cart_item = CartItem.objects.get(
            user_id=self.user.id,
            user_type='buy',
            game_id=self.game.id
        )
        self.assertEqual(cart_item.quantity, 2)

    # Тест добавления в корзину без авторизации
    def test_add_to_cart_unauthorized(self):
        response = self.client.post('/catalog/', {
            'game_id': self.game.id
        })
        # Должен быть 200 (страница перезагрузится без добавления)
        self.assertEqual(response.status_code, 200)
        # Корзина должна быть пустой
        cart_count = CartItem.objects.filter(
            user_id=self.user.id,
            user_type='buy'
        ).count()
        self.assertEqual(cart_count, 0)


# Тесты для регистрации пользователей
class UserRegistrationTest(TestCase):
    databases = ['default', 'buy', 'sell']

    def setUp(self):
        self.client = Client()

    # Тест успешной регистрации покупателя
    def test_register_buy_user_success(self):
        response = self.client.post('/register/', {
            'user_type': 'buy',
            'username': 'newbuyer',
            'password': 'password123',
            'email': 'buyer@example.com',
            'phone': '+1234567890'
        })
        self.assertEqual(response.status_code, 302)  # Редирект на каталог
        # Проверяем создание пользователя
        user = BuyUser.objects.filter(username='newbuyer').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'buyer@example.com')

    # Тест успешной регистрации продавца
    def test_register_sell_user_success(self):
        response = self.client.post('/register/', {
            'user_type': 'sell',
            'username': 'newseller',
            'password': 'password123',
            'email': 'seller@example.com',
            'phone': '+1234567890'
        })
        self.assertEqual(response.status_code, 302)
        user = SellUser.objects.filter(username='newseller').first()
        self.assertIsNotNone(user)

    # Тест регистрации с существующим username
    def test_register_duplicate_username(self):
        # Создаем первого пользователя
        BuyUser.objects.create(
            username='existinguser',
            password=make_password('pass'),
            email='first@example.com',
            phone='+1111111111'
        )
        # Пытаемся создать второго с тем же username
        response = self.client.post('/register/', {
            'user_type': 'buy',
            'username': 'existinguser',
            'password': 'password123',
            'email': 'second@example.com',
            'phone': '+2222222222'
        })
        self.assertEqual(response.status_code, 200)  # Остаемся на странице
        # Проверяем сообщение об ошибке в контенте
        self.assertContains(response, 'Такой пользователь уже есть!')


# Тесты для API игр
class GameAPITest(APITestCase):
    databases = ['default', 'buy', 'sell']

    def setUp(self):
        current_db.db = 'buy'
        self.genre = Genre.objects.create(
            name='RPG',
            description='Ролевые игры'
        )
        self.developer = Developer.objects.create(
            name='Test Dev',
            email='dev@example.com',
            bio='Test developer',
            founded_date='2000-01-01'
        )
        self.game = Game.objects.create(
            title='API Test Game',
            genre=self.genre,
            developer=self.developer,
            release_date='2023-01-01',
            price=50.00,
            in_stock=True,
            seller='testuser'
        )

    # Тест получения списка игр
    def test_get_games_list(self):
        url = reverse('game-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    # Тест получения деталей игры
    def test_get_game_detail(self):
        url = reverse('game-detail', kwargs={'pk': self.game.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'API Test Game')

    # Тест создания игры
    def test_create_game(self):
        url = reverse('game-list')
        game_data = {
            'title': 'New Game',
            'genre': self.genre.id,
            'release_date': '2024-01-01',
            'price': '75.00',
            'in_stock': True
        }
        response = self.client.post(url, game_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Game.objects.filter(title='New Game').count(), 1)


# Тесты для жанров
class GenreAPITest(APITestCase):
    databases = ['default', 'buy', 'sell']

    def setUp(self):
        current_db.db = 'buy'
        self.genre = Genre.objects.create(
            name='Strategy',
            description='Стратегические игры'
        )

    # Тест получения списка жанров
    def test_get_genres_list(self):
        url = reverse('genre-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    # Тест создания жанра
    def test_create_genre(self):
        url = reverse('genre-list')
        genre_data = {
            'name': 'Puzzle',
            'description': 'Головоломки'
        }
        response = self.client.post(url, genre_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Genre.objects.filter(name='Puzzle').count(), 1)
