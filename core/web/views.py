import requests
import logging
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Avg
from api_v1.models import BuyUser, SellUser, Game, Review
from web.models import (
    SupportMessage, Cart, CartItem, GameRating, ChatReadStatus,
    Order, OrderItem, OrderStatus, Payment, PaymentMethod, SellerPayout
)
# Router больше не нужен - используем единую БД
from decimal import Decimal
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# ==============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==============================================================================

def get_or_create_cart(user_id, user_type='buy'):
    """
    Получает или создаёт активную корзину для пользователя (3НФ)
    """
    cart, created = Cart.objects.get_or_create(
        user_id=user_id,
        user_type=user_type,
        is_active=True
    )
    return cart


def get_or_create_order_statuses():
    """
    Создаёт справочник статусов заказа, если не существует
    """
    statuses = [
        ('pending', 'Ожидает оплаты', 1),
        ('paid', 'Оплачен', 2),
        ('processing', 'В обработке', 3),
        ('shipped', 'Отправлен', 4),
        ('delivered', 'Доставлен', 5),
        ('completed', 'Завершён', 6),
        ('cancelled', 'Отменён', 7),
        ('refunded', 'Возврат', 8),
    ]
    for code, name, order in statuses:
        OrderStatus.objects.get_or_create(
            code=code,
            defaults={'name': name, 'sort_order': order}
        )


def get_or_create_payment_methods():
    """
    Создаёт справочник способов оплаты, если не существует
    """
    methods = [
        ('tinkoff', 'Тинькофф', 'tinkoff-icon'),
        ('sber', 'Сбербанк', 'sber-icon'),
        ('alfa', 'Альфа-Банк', 'alfa-icon'),
        ('ozon', 'Ozon Bank', 'ozon-icon'),
        ('vtb', 'ВТБ', 'vtb-icon'),
        ('sbp', 'СБП', 'sbp-icon'),
    ]
    for code, name, icon in methods:
        PaymentMethod.objects.get_or_create(
            code=code,
            defaults={'name': name, 'icon': icon}
        )

# Функция для генерации автоматических ответов поддержки
def generate_support_response(message):
    # Словарь с ключевыми словами и ответами
    responses = {
        'привет': 'Привет! Чем могу помочь?',
        'здравствуйте': 'Здравствуйте! Чем можем вам помочь?',
        'проблема': 'Расскажите подробнее о вашей проблеме, и мы постараемся помочь.',
        'ошибка': 'Опишите ошибку, которую вы встретили, и мы разберемся.',
        'спасибо': 'Пожалуйста! Если у вас есть еще вопросы, спрашивайте.',
        'помощь': 'Я здесь, чтобы помочь. Что вас интересует?',
        'купить': 'Для покупки игр перейдите в каталог и выберите интересующую вас игру.',
        'продать': 'Для продажи игр зарегистрируйтесь как продавец и добавьте свои игры.',
        'регистрация': 'Чтобы зарегистрироваться, нажмите на "Купить игры" или "Выложить игры" и заполните форму.',
        'вход': 'Для входа используйте свои учетные данные на странице регистрации.',
    }
    # Поиск совпадения ключевого слова в сообщении
    for key, response in responses.items():
        if key in message.lower():  # Приводим к нижнему регистру
            return response
    # Ответ по умолчанию
    return 'Спасибо за ваше сообщение! Мы ответим вам в ближайшее время.'

# Константы для URL API (для получения данных из API)
GAMES_API_URL = 'http://localhost:7070/api/v1/games/'
DEVELOPERS_API_URL = 'http://localhost:7070/api/v1/developers/'
GENRES_API_URL = 'http://localhost:7070/api/v1/genres/'


def game_list(request):
    template_name = 'home.html'

    # Получаем список игр из API
    response = requests.get(GAMES_API_URL)
    games = response.json() if response.status_code == 200 else []

    # Получаем список разработчиков из API
    response_developers = requests.get(DEVELOPERS_API_URL)
    developers = response_developers.json() if response_developers.status_code == 200 else []

    # Создаем словарь разработчиков для быстрого доступа
    developers_dict = {developer['id']: developer for developer in developers}

    # Добавляем информацию о разработчиках к играм
    for game in games:
        developer_id = game.get('developer')
        if developer_id and developer_id in developers_dict:
            game['developer_info'] = developers_dict[developer_id]
            game['developer_name'] = developers_dict[developer_id]['name']

    return render(request, template_name, {'games': games})


def catalog(request):
    from django.db.models import Q, Case, When, DecimalField, Avg
    from django.core.paginator import Paginator
    from django.http import JsonResponse
    from django.views.decorators.csrf import csrf_exempt
    from api_v1.models import Game, Genre, Developer, Review
    from web.models import CartItem, GameRating

    is_logged_in = 'user_id' in request.session
    user_type = request.session.get('user_type')

    # Обработка добавления в корзину (3НФ - через Cart)
    if request.method == 'POST' and is_logged_in and user_type == 'buy':
        game_id = request.POST.get('game_id')
        if game_id:
            try:
                game_id = int(game_id)
                # Получаем или создаём корзину пользователя
                cart = get_or_create_cart(request.session['user_id'], 'buy')
                # Проверяем, есть ли уже в корзине
                cart_item, created = CartItem.objects.get_or_create(
                    cart=cart,
                    game_id=game_id,
                    defaults={'quantity': 1}
                )
                if not created:
                    cart_item.quantity += 1
                    cart_item.save()
                messages.success(request, 'Игра добавлена в корзину!')
                request.session.save()
            except (ValueError, Game.DoesNotExist):
                messages.error(request, 'Ошибка при добавлении в корзину.')
    
        return redirect('catalog')
    # Обработка регистрации и входа
    if request.method == 'POST':
        if 'username' in request.POST and 'password' in request.POST:  # Регистрация
            username = request.POST.get('username')
            password = request.POST.get('password').strip()
            email = request.POST.get('email')
            phone = request.POST.get('phone')

            if BuyUser.objects.filter(username=username).exists() or SellUser.objects.filter(username=username).exists():
                messages.error(request, 'Такой пользователь уже есть!')
            elif BuyUser.objects.filter(email=email).exists() or SellUser.objects.filter(email=email).exists():
                messages.error(request, 'Такой пользователь уже есть!')
            else:
                user = BuyUser.objects.create(
                    username=username,
                    password=make_password(password),
                    email=email,
                    phone=phone
                )
                messages.success(request, 'Вы успешно зарегистрировались!')
                request.session['user_id'] = user.id
                request.session['user_type'] = 'buy'
                request.session.save()
                return redirect('catalog')
        elif 'login_username' in request.POST:  # Вход
            username = request.POST.get('login_username')
            password = request.POST.get('login_password').strip()
            try:
                user = BuyUser.objects.get(username=username)
                if check_password(password, user.password):
                    messages.success(request, 'Вы вошли в систему!')
                    request.session['user_id'] = user.id
                    request.session['user_type'] = 'buy'
                    request.session.save()
                    return redirect('catalog')
                else:
                    messages.error(request, 'Неверный пароль!')
            except BuyUser.DoesNotExist:
                try:
                    user = SellUser.objects.get(username=username)
                    if check_password(password, user.password):
                        messages.success(request, 'Вы вошли в систему!')
                        request.session['user_id'] = user.id
                        request.session['user_type'] = 'sell'
                        request.session.save()
                        return redirect('catalog')
                    else:
                        messages.error(request, 'Неверный пароль!')
                except SellUser.DoesNotExist:
                    messages.error(request, 'Такого пользователя не существует!')

    # Всегда показываем каталог

    # Получаем все игры с фильтрами
    games = Game.objects.select_related('developer', 'genre').all()

    # Аннотируем эффективную цену для фильтрации и сортировки
    games = games.annotate(
        effective_price=Case(
            When(discount_price__isnull=False, then='discount_price'),
            default='price',
            output_field=DecimalField()
        )
    )

    # Фильтры
    search = request.GET.get('search', '')
    genre_names = request.GET.getlist('genre')
    price_range = request.GET.get('price_range', '')
    if price_range:
        if '-' in price_range:
            min_p, max_p = price_range.split('-')
            min_price = int(min_p)
            max_price = int(max_p)
        else:
            min_price = ''
            max_price = ''
    else:
        min_price = ''
        max_price = ''
    # min_rating removed
    in_stock = request.GET.get('in_stock', '')

    if search:
        games = games.filter(Q(title__icontains=search) | Q(developer__name__icontains=search))

    if genre_names:
        games = games.filter(genre__name__in=genre_names)

    if min_price:
        games = games.filter(effective_price__gte=float(min_price))

    if max_price:
        games = games.filter(effective_price__lte=float(max_price))

    # min_rating filter removed

    if in_stock == 'true':
        games = games.filter(in_stock=True)

    # Сортировка
    sort_by = request.GET.get('sort', 'popularity')
    if sort_by == 'price_asc':
        games = games.order_by('effective_price')
    elif sort_by == 'price_desc':
        games = games.order_by('-effective_price')
    else:  # popularity
        games = games.order_by('-sold_count', '-rating')

    # Пагинация
    per_page = 100  # Фиксированное значение
    paginator = Paginator(games, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Статистика жанров
    genre_counts = {}
    genre_names = ['Экшен', 'Приключения', 'RPG', 'Стратегия', 'Симулятор', 'Спорт', 'Гонки', 'Головоломки']
    for genre_name in genre_names:
        try:
            genre = Genre.objects.get(name=genre_name)
            count = Game.objects.filter(genre=genre, in_stock=True).count()
        except Genre.DoesNotExist:
            count = 0
        genre_counts[genre_name] = count

    # Получаем объект пользователя для аватара
    user = None
    if user_type == 'buy':
        user = BuyUser.objects.get(id=request.session['user_id'])
    elif user_type == 'sell':
        user = SellUser.objects.get(id=request.session['user_id'])

    context = {
        'games': page_obj,
        'genre_counts': genre_counts,
        'search': search,
        'genre_names': genre_names,
        'price_range': price_range,
        'in_stock': in_stock,
        'sort': sort_by,
        'is_logged_in': True,
        'user_type': user_type,
        'page_obj': page_obj,
        'user': user,
        'username': request.session.get('username', ''),
    }

    return render(request, 'catalog.html', context)


def about(request):
    return render(request, 'about.html')


def register(request):
    if request.method == 'POST':
        if 'username' in request.POST:  # Регистрация
            user_type = request.POST.get('user_type')
            username = request.POST.get('username')
            password = request.POST.get('password')
            email = request.POST.get('email')
            phone = request.POST.get('phone')

            if not all([user_type, username, password, email, phone]):
                messages.error(request, 'Все поля обязательны!')
                return render(request, 'register.html')

            password = password.strip()
            if len(password) < 6:
                messages.error(request, 'Пароль должен быть не менее 6 символов!')
                return render(request, 'register.html')

            # Проверка уникальности
            if BuyUser.objects.filter(username=username).exists() or SellUser.objects.filter(username=username).exists():
                messages.error(request, 'Такой пользователь уже есть!')
                return render(request, 'register.html')
            if BuyUser.objects.filter(email=email).exists() or SellUser.objects.filter(email=email).exists():
                messages.error(request, 'Такой пользователь уже есть!')
                return render(request, 'register.html')

            # Создание пользователя
            if user_type == 'buy':
                user = BuyUser.objects.create(
                    username=username,
                    password=make_password(password),
                    email=email,
                    phone=phone
                )
                messages.success(request, 'Вы успешно зарегистрировались для покупки игр!')
                request.session['user_id'] = user.id
                request.session['user_type'] = 'buy'
                request.session['username'] = user.username
                request.session.set_expiry(86400 * 7)  # 7 дней
                request.session.save()
                return redirect('catalog')
            elif user_type == 'sell':
                user = SellUser.objects.create(
                    username=username,
                    password=make_password(password),
                    email=email,
                    phone=phone
                )
                messages.success(request, 'Вы успешно зарегистрировались для продажи игр!')
                request.session['user_id'] = user.id
                request.session['user_type'] = 'sell'
                request.session['username'] = user.username
                request.session.set_expiry(86400 * 7)  # 7 дней
                request.session.save()
                return redirect('catalog')
        elif 'login_username' in request.POST:  # Вход
            username = request.POST.get('login_username')
            password = request.POST.get('login_password')

            if not username or not password:
                messages.error(request, 'Введите имя пользователя и пароль!')
                return render(request, 'register.html')

            # Проверка в обеих базах
            user = None
            db = None
            try:
                user = BuyUser.objects.get(username=username)
                db = 'buy'
            except BuyUser.DoesNotExist:
                try:
                    user = SellUser.objects.get(username=username)
                    db = 'sell'
                except SellUser.DoesNotExist:
                    pass

            if user and check_password(password, user.password):
                messages.success(request, 'Вы вошли в систему!')
                request.session['user_id'] = user.id
                request.session['user_type'] = db
                request.session['username'] = user.username
                request.session.save()
                return redirect('catalog')
            else:
                messages.error(request, 'Неверное имя пользователя или пароль!')
                return render(request, 'register.html')

        elif 'login_username' in request.POST:  # Вход
            username = request.POST.get('login_username')
            password = request.POST.get('login_password')

            if not username or not password:
                messages.error(request, 'Введите имя пользователя и пароль!')
                return render(request, 'register.html')

            # Проверка в обеих базах
            user = None
            db = None
            try:
                user = BuyUser.objects.get(username=username)
                db = 'buy'
            except BuyUser.DoesNotExist:
                try:
                    user = SellUser.objects.get(username=username)
                    db = 'sell'
                except SellUser.DoesNotExist:
                    pass

            if user and check_password(password, user.password):
                messages.success(request, 'Вы вошли в систему!')
                request.session['user_id'] = user.id
                request.session['user_type'] = db
                request.session['username'] = user.username
                request.session.set_expiry(86400 * 7)  # 7 дней
                request.session.save()
                return redirect('catalog')
            else:
                messages.error(request, 'Неверное имя пользователя или пароль!')
                return render(request, 'register.html', {'show_login': True})

    return render(request, 'register.html')


# Функция для добавления новой игры (только для продавцов)
def add_game(request):
    # Получаем ID и тип пользователя из сессии
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')

    # Проверяем, что пользователь - продавец
    if not user_id or user_type != 'sell':
        messages.error(request, 'Только продавцы могут добавлять игры. Войдите как продавец.')
        return redirect('catalog')

    from api_v1.models import Game, Genre, Developer, SellUser

    # Получаем username продавца
    try:
        seller = SellUser.objects.get(id=user_id)
        seller_username = seller.username
    except SellUser.DoesNotExist:
        messages.error(request, 'Пользователь не найден.')
        return redirect('catalog')

    # Обработка POST запроса (добавление игры)
    if request.method == 'POST':
        from django.core.files.images import get_image_dimensions
        try:
            # Получаем данные из формы
            title = request.POST.get('title')
            genre_id = request.POST.get('genre')
            release_date = request.POST.get('release_date')
            price_str = request.POST.get('price')

            if not title:
                messages.error(request, 'Пожалуйста, введите название игры.')
                return redirect('add_game')
            if not genre_id:
                messages.error(request, 'Пожалуйста, выберите жанр.')
                return redirect('add_game')
            try:
                genre_id = int(genre_id)
            except ValueError:
                messages.error(request, 'Неверный жанр.')
                return redirect('add_game')
            if not release_date:
                messages.error(request, 'Пожалуйста, введите дату релиза.')
                return redirect('add_game')
            try:
                from datetime import date
                date.fromisoformat(release_date)
                year = int(release_date.split('-')[0])
                if year < 1900 or year > 2100:
                    raise ValueError('Год должен быть между 1900 и 2100.')
            except ValueError as e:
                messages.error(request, f'Неверная дата релиза: {str(e)}')
                return redirect('add_game')
            if not price_str:
                messages.error(request, 'Пожалуйста, введите цену.')
                return redirect('add_game')

            try:
                price = Decimal(price_str)
                if price < 0:
                    raise ValueError
            except ValueError:
                messages.error(request, 'Цена должна быть положительным числом.')
                return redirect('add_game')

            image = request.FILES.get('image')
            if image:
                # Валидация размера файла
                if image.size > 10 * 1024 * 1024:  # 10MB
                    messages.error(request, 'Максимальный размер файла 10MB.')
                    return redirect('add_game')
                # Валидация типа файла
                if image.content_type not in ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']:
                    messages.error(request, 'Разрешены только файлы JPG, PNG, GIF.')
                    return redirect('add_game')
                # Валидация размеров изображения, если PIL доступен
                if PIL_AVAILABLE:
                    try:
                        from django.core.files.images import get_image_dimensions
                        width, height = get_image_dimensions(image)
                        if width > 2000 or height > 2000:
                            messages.error(request, 'Максимальный размер изображения 2000x2000 пикселей.')
                            return redirect('add_game')
                    except Exception as e:
                        messages.error(request, f'Ошибка при обработке изображения: {str(e)}')
                        return redirect('add_game')
                else:
                    # Если PIL не установлен, пропускаем валидацию размеров
                    pass

            genre = Genre.objects.get(id=genre_id)

            # Создаем новую игру в базе данных
            # Примечание: seller FK не работает между разными БД,
            # поэтому используем seller_id напрямую
            game = Game.objects.create(
                title=title,
                developer=None,  # Разработчик не указывается при добавлении
                genre=genre,
                release_date=release_date,
                price=price,
                in_stock=request.POST.get('in_stock') == 'on',  # Преобразуем чекбокс в boolean
                image=image,
                seller_id=seller.id,  # ID продавца (работает между БД)
                seller_username=seller_username  # Для обратной совместимости
            )
            messages.success(request, 'Игра добавлена успешно!')
            request.session.save()  # Сохраняем сессию
            return redirect('catalog')
        except Genre.DoesNotExist:
            messages.error(request, 'Выбранный жанр не существует.')
        except Exception as e:
            logging.error(f'Error adding game: {str(e)}')
            messages.error(request, f'Ошибка при добавлении игры: {str(e)}')

    # Получаем жанры и разработчиков для формы
    from api_v1.models import Genre, Developer
    genres = list(Genre.objects.values('id', 'name'))
    developers = list(Developer.objects.values('id', 'name'))

    # Создаем базовые жанры и разработчиков, если их нет
    default_genres = [
        {'name': 'Экшен', 'description': 'Игры с динамичным геймплеем'},
        {'name': 'Приключения', 'description': 'Истории и исследования'},
        {'name': 'RPG', 'description': 'Ролевые игры'},
        {'name': 'Стратегия', 'description': 'Стратегические игры'},
        {'name': 'Симулятор', 'description': 'Симуляторы'},
        {'name': 'Спорт', 'description': 'Спортивные игры'},
        {'name': 'Гонки', 'description': 'Гоночные игры'},
        {'name': 'Головоломки', 'description': 'Логические игры'},
    ]
    default_developers = [
        {'name': 'Valve', 'email': 'info@valve.com', 'bio': 'Известный разработчик игр', 'founded_date': '1996-11-19'},
        {'name': 'Ubisoft', 'email': 'info@ubisoft.com', 'bio': 'Французская компания', 'founded_date': '1986-03-12'},
        {'name': 'EA', 'email': 'info@ea.com', 'bio': 'Electronic Arts', 'founded_date': '1982-05-27'},
        {'name': 'Rockstar', 'email': 'info@rockstar.com', 'bio': 'Разработчик GTA', 'founded_date': '1998-12-01'},
        {'name': 'Mojang', 'email': 'info@mojang.com', 'bio': 'Разработчик Minecraft', 'founded_date': '2009-05-17'},
    ]
    # Создаем записи, используя get_or_create
    for genre_data in default_genres:
        Genre.objects.get_or_create(**genre_data)
    for dev_data in default_developers:
        Developer.objects.get_or_create(**dev_data)
    genres = list(Genre.objects.values('id', 'name'))
    developers = list(Developer.objects.values('id', 'name'))

    # Статистика жанров
    genre_counts = {}
    for genre in genres:
        count = 0
        genre_counts[genre['id']] = count

    return render(request, 'add_game.html', {'genres': genres, 'developers': developers, 'genre_counts': genre_counts})


def add_developer(request):
    if request.method == 'POST':
        data = {
            'name': request.POST.get('name'),
            'email': request.POST.get('email'),
            'bio': request.POST.get('bio'),
            'founded_date': request.POST.get('founded_date')
        }
        response = requests.post(DEVELOPERS_API_URL, json=data)
        if response.status_code == 201:
            messages.success(request, 'Разработчик добавлен успешно!')
            return redirect('home')
        else:
            messages.error(request, 'Ошибка при добавлении разработчика.')

    return render(request, 'add_developer.html')


def buy_games(request):
    if request.method == 'POST':
        if 'username' in request.POST:  # Регистрация
            username = request.POST.get('username')
            password = request.POST.get('password').strip()
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            if BuyUser.objects.filter(username=username).exists() or SellUser.objects.filter(username=username).exists():
                messages.error(request, 'Такой пользователь уже есть!')
            elif BuyUser.objects.filter(email=email).exists() or SellUser.objects.filter(email=email).exists():
                messages.error(request, 'Такой пользователь уже есть!')
            else:
                user = BuyUser.objects.create(
                    username=username,
                    password=make_password(password),
                    email=email,
                    phone=phone
                )
                messages.success(request, 'Вы успешно зарегистрировались!')
                request.session['user_id'] = user.id
                request.session['user_type'] = 'buy'
                return redirect('catalog')
        elif 'login_username' in request.POST:  # Вход
            username = request.POST.get('login_username')
            password = request.POST.get('login_password').strip()
            try:
                user = BuyUser.objects.get(username=username)
                if check_password(password, user.password):
                    messages.success(request, 'Вы вошли в систему!')
                    request.session['user_id'] = user.id
                    request.session['user_type'] = 'buy'
                    request.session['username'] = user.username
                    request.session.set_expiry(86400 * 7)  # 7 дней
                    request.session.save()
                    return redirect('catalog')
                else:
                    messages.error(request, 'Неверный пароль!')
            except BuyUser.DoesNotExist:
                try:
                    user = SellUser.objects.get(username=username)
                    if check_password(password, user.password):
                        messages.success(request, 'Вы вошли в систему!')
                        request.session['user_id'] = user.id
                        request.session['user_type'] = 'sell'
                        request.session['username'] = user.username
                        request.session.set_expiry(86400 * 7)  # 7 дней
                        request.session.save()
                        return redirect('catalog')
                    else:
                        messages.error(request, 'Неверный пароль!')
                except SellUser.DoesNotExist:
                    messages.error(request, 'Такого пользователя не существует!')
    return render(request, 'buy_games.html', {'user_type': request.GET.get('type', 'buy')})


def sell_games(request):
    if request.method == 'POST':
        if 'username' in request.POST:  # Регистрация
            username = request.POST.get('username')
            password = request.POST.get('password').strip()
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            audience = request.POST.get('audience')
            if BuyUser.objects.filter(username=username).exists() or SellUser.objects.filter(username=username).exists():
                messages.error(request, 'Такой пользователь уже есть!')
            elif BuyUser.objects.filter(email=email).exists() or SellUser.objects.filter(email=email).exists():
                messages.error(request, 'Такой пользователь уже есть!')
            else:
                user = SellUser.objects.create(
                    username=username,
                    password=make_password(password),
                    email=email,
                    phone=phone,
                    audience=audience
                )
                messages.success(request, 'Вы успешно зарегистрировались!')
                request.session['user_id'] = user.id
                request.session['user_type'] = 'sell'
                return redirect('catalog')
        elif 'login_username' in request.POST:  # Вход
            username = request.POST.get('login_username')
            password = request.POST.get('login_password').strip()
            try:
                user = SellUser.objects.get(username=username)
                if check_password(password, user.password):
                    messages.success(request, 'Вы вошли в систему!')
                    request.session['user_id'] = user.id
                    request.session['user_type'] = 'sell'
                    request.session['username'] = user.username
                    request.session.save()
                    return redirect('catalog')
                else:
                    messages.error(request, 'Неверный пароль!')
            except SellUser.DoesNotExist:
                messages.error(request, 'Такого пользователя не существует!')
    return render(request, 'sell_games.html')


def logout_view(request):
    request.session.flush()
    return redirect('catalog')


def account(request):
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')

    if not user_id or not user_type:
        return render(request, 'account.html', {
            'error': 'Сначала необходимо пройти регистрацию',
            'is_logged_in': False
        })

    try:
        if user_type == 'buy':
            user = BuyUser.objects.get(id=user_id)
            if request.method == 'POST':
                user.first_name = request.POST.get('first_name', '')
                user.last_name = request.POST.get('last_name', '')
                user.country = request.POST.get('country', '')
                user.city = request.POST.get('city', '')
                birth_date = request.POST.get('birth_date')
                user.birth_date = birth_date if birth_date else None

                # Обработка аватара
                avatar = request.FILES.get('avatar')
                if avatar:
                    # Валидация
                    if avatar.size > 5 * 1024 * 1024:  # 5MB
                        messages.error(request, 'Максимальный размер файла 5MB.')
                        return redirect('account')
                    if avatar.content_type not in ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']:
                        messages.error(request, 'Разрешены только файлы JPG, PNG, GIF.')
                        return redirect('account')
                    user.avatar = avatar

                user.save()
                messages.success(request, 'Профиль обновлен!')
                return redirect('account')

            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'phone': user.phone,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'country': user.country,
                'city': user.city,
                'birth_date': user.birth_date,
                'registration_date': user.registration_date.strftime('%d.%m.%Y %H:%M'),
                'user_type': 'Покупатель',
                'avatar': user.avatar  # Добавляем аватар
            }

        elif user_type == 'sell':
            user = SellUser.objects.get(id=user_id)
            if request.method == 'POST':
                user.first_name = request.POST.get('first_name', '')
                user.last_name = request.POST.get('last_name', '')
                user.country = request.POST.get('country', '')
                user.city = request.POST.get('city', '')
                birth_date = request.POST.get('birth_date')
                user.birth_date = birth_date if birth_date else None

                # Обработка аватара
                avatar = request.FILES.get('avatar')
                if avatar:
                    # Валидация
                    if avatar.size > 5 * 1024 * 1024:  # 5MB
                        messages.error(request, 'Максимальный размер файла 5MB.')
                        return redirect('account')
                    if avatar.content_type not in ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']:
                        messages.error(request, 'Разрешены только файлы JPG, PNG, GIF.')
                        return redirect('account')
                    user.avatar = avatar

                user.save()
                messages.success(request, 'Профиль обновлен!')
                return redirect('account')

            # Получаем игры продавца по seller_id
            seller_games = Game.objects.filter(seller_id=user.id).select_related('genre')

            # Получаем отзывы на игры продавца
            from api_v1.models import Review
            reviews = Review.objects.filter(game__seller_id=user.id).select_related('game').order_by('-created_at')

            # Получаем чаты продавца
            seller_chats = []
            for game in seller_games:
                # Ищем чаты по паттерну buyer_*_seller_{user.id}_game_{game.id}
                chat_pattern = f'seller_{user.id}_game_{game.id}'
                chat_messages = SupportMessage.objects.filter(user__contains=chat_pattern).order_by('-timestamp')
                if chat_messages.exists():
                    # Получаем последнее сообщение
                    last_message = chat_messages.first()
                    # Извлекаем buyer_id из user поля
                    user_parts = last_message.user.split('_')
                    buyer_id = user_parts[1] if len(user_parts) > 1 and user_parts[0] == 'buyer' else None
                    buyer_name = f"Покупатель {buyer_id}" if buyer_id else "Покупатель"
                    chat_key = f'seller_{user.id}_game_{game.id}'
                    
                    # Получаем статус прочтения из БД
                    read_status = ChatReadStatus.objects.filter(
                        user_id=user.id,
                        user_type='sell',
                        chat_key=chat_key
                    ).first()
                    
                    if read_status:
                        unread_count = chat_messages.filter(is_support=False, timestamp__gt=read_status.last_read_at).count()
                    else:
                        unread_count = chat_messages.filter(is_support=False).count()
                    
                    seller_chats.append({
                        'game': game,
                        'last_message': last_message.message,
                        'last_sender': last_message.display_name,
                        'timestamp': last_message.timestamp,
                        'chat_id': last_message.user,
                        'unread_count': unread_count  # Непрочитанные от покупателя
                    })

            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'phone': user.phone,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'country': user.country,
                'city': user.city,
                'birth_date': user.birth_date,
                'registration_date': user.registration_date.strftime('%d.%m.%Y %H:%M'),
                'user_type': 'Продавец',
                'balance': user.balance,
                'games': seller_games,
                'games_count': seller_games.count(),
                'reviews': reviews,
                'reviews_count': reviews.count(),
                'chats': seller_chats,
                'avatar': user.avatar,  # Добавляем аватар
                # Статистика через агрегацию (3НФ)
                'total_sales': user.total_sales,
                'total_games_sold': user.total_games_sold
            }
        else:
            return render(request, 'account.html', {'error': 'Неизвестный тип пользователя!'})

        return render(request, 'account.html', {
            'user': user_data,
            'is_logged_in': True,
            'user_type': user_type
        })

    except (BuyUser.DoesNotExist, SellUser.DoesNotExist):
        # Удаляем невалидную сессию
        request.session.flush()
        return render(request, 'account.html', {
            'error': 'Сессия истекла. Пожалуйста, войдите снова.',
            'is_logged_in': False
        })


def cart(request):
    """
    Просмотр и управление корзиной (3НФ)
    Использует модели Cart и CartItem
    """
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')

    if not user_id or user_type != 'buy':
        messages.error(request, 'Только покупатели могут просматривать корзину.')
        return redirect('catalog')

    # Получаем или создаём корзину (3НФ)
    cart_obj = get_or_create_cart(user_id, user_type)
    cart_items = cart_obj.items.all()
    
    games = []
    total = Decimal('0.00')

    for item in cart_items:
        try:
            game = Game.objects.get(id=item.game_id)
            price = game.discount_price if game.discount_price else game.price
            subtotal = price * item.quantity
            games.append({
                'id': game.id,
                'title': game.title,
                'price': price,
                'original_price': game.price,
                'has_discount': bool(game.discount_price),
                'quantity': item.quantity,
                'subtotal': subtotal,
                'image': game.image.url if game.image else None,
                'seller_id': game.seller_id,
                'seller_name': game.seller_name
            })
            total += subtotal
        except Game.DoesNotExist:
            # Игру удалили, удаляем из корзины
            item.delete()

    if request.method == 'POST':
        if 'remove' in request.POST:
            game_id = request.POST.get('game_id')
            CartItem.objects.filter(cart=cart_obj, game_id=game_id).delete()
            messages.success(request, 'Игра удалена из корзины.')
            return redirect('cart')
        elif 'update_quantity' in request.POST:
            game_id = request.POST.get('game_id')
            quantity = int(request.POST.get('quantity', 1))
            if quantity > 0:
                CartItem.objects.filter(cart=cart_obj, game_id=game_id).update(quantity=quantity)
            else:
                CartItem.objects.filter(cart=cart_obj, game_id=game_id).delete()
            return redirect('cart')
        elif 'checkout' in request.POST:
            return redirect('checkout')

    return render(request, 'cart.html', {
        'games': games,
        'total': total,
        'cart': cart_obj,
        'items_count': cart_obj.total_items,
        'is_logged_in': True,
        'user_type': user_type
    })


def checkout(request):
    """
    Оформление заказа (3НФ)
    Создаёт Order, OrderItem и Payment в нормализованной структуре
    """
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')

    if not user_id or user_type != 'buy':
        messages.error(request, 'Только покупатели могут оформлять заказы.')
        return redirect('catalog')

    # Инициализируем справочники
    get_or_create_order_statuses()
    get_or_create_payment_methods()

    # Получаем корзину пользователя (3НФ)
    cart_obj = get_or_create_cart(user_id, user_type)
    cart_items = cart_obj.items.all()
    
    games = []
    total = Decimal('0.00')

    for item in cart_items:
        try:
            game = Game.objects.get(id=item.game_id)
            price = game.discount_price if game.discount_price else game.price
            subtotal = price * item.quantity
            games.append({
                'id': game.id,
                'title': game.title,
                'price': price,
                'quantity': item.quantity,
                'subtotal': subtotal,
                'image': game.image.url if game.image else None,
                'seller_id': game.seller_id,
                'seller_name': game.seller_name
            })
            total += subtotal
        except Game.DoesNotExist:
            item.delete()

    if not games:
        messages.error(request, 'Ваша корзина пуста.')
        return redirect('cart')

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        valid_methods = ['tinkoff', 'sber', 'alfa', 'ozon', 'vtb', 'sbp']
        
        if payment_method in valid_methods:
            card_number = request.POST.get('card_number', '')
            expiry_date = request.POST.get('expiry_date', '')
            cvv = request.POST.get('cvv', '')
            cardholder_name = request.POST.get('cardholder_name', '')
            phone = request.POST.get('phone', '') if payment_method == 'sbp' else None

            # Валидация
            if not all([card_number, expiry_date, cvv, cardholder_name]):
                messages.error(request, 'Заполните все поля карты.')
                return render(request, 'checkout.html', {
                    'games': games, 'total': total,
                    'is_logged_in': True, 'user_type': user_type
                })
            
            if payment_method == 'sbp' and not phone:
                messages.error(request, 'Введите номер телефона для СБП.')
                return render(request, 'checkout.html', {
                    'games': games, 'total': total,
                    'is_logged_in': True, 'user_type': user_type
                })

            try:
                # 1. Создаём заказ (3НФ - шапка)
                pending_status = OrderStatus.objects.get(code='pending')
                order = Order.objects.create(
                    user_id=user_id,
                    user_type=user_type,
                    status=pending_status
                )

                # 2. Создаём позиции заказа (3НФ - OrderItems)
                for item in cart_items:
                    try:
                        game = Game.objects.get(id=item.game_id)
                        price = game.discount_price if game.discount_price else game.price
                        seller_id = game.seller_id  # Используем seller_id напрямую
                        
                        order_item = OrderItem.objects.create(
                            order=order,
                            game_id=game.id,
                            quantity=item.quantity,
                            price_at_purchase=price,
                            seller_id=seller_id
                        )

                        # Обновляем счётчик продаж
                        game.sold_count += item.quantity
                        game.save()

                        # Создаём запись о выплате продавцу
                        if seller_id:
                            SellerPayout.objects.create(
                                seller_id=seller_id,
                                order_item=order_item,
                                amount=price * item.quantity,
                                status='pending'
                            )
                    except Game.DoesNotExist:
                        continue

                # 3. Создаём платёж (3НФ - Payment)
                import uuid
                payment_method_obj = PaymentMethod.objects.filter(code=payment_method).first()
                payment = Payment.objects.create(
                    order=order,
                    method=payment_method_obj,
                    method_code=payment_method,
                    status='completed',
                    amount=total,
                    transaction_id=f"TXN-{uuid.uuid4().hex[:12].upper()}",
                    paid_at=timezone.now(),
                    card_last_four=card_number[-4:] if len(card_number) >= 4 else ''
                )

                # 4. Обновляем статус заказа
                paid_status = OrderStatus.objects.get(code='paid')
                order.status = paid_status
                order.save()

                # 5. Начисляем деньги продавцам
                for item in cart_items:
                    try:
                        game = Game.objects.get(id=item.game_id)
                        if game.seller_id:
                            # Получаем продавца
                            seller = SellUser.objects.get(id=game.seller_id)
                            price = game.discount_price if game.discount_price else game.price
                            seller.balance += price * item.quantity
                            seller.save()
                            
                            # Обновляем статус выплаты
                            SellerPayout.objects.filter(
                                seller_id=seller.id,
                                order_item__order=order
                            ).update(status='completed', paid_at=timezone.now())
                    except (Game.DoesNotExist, SellUser.DoesNotExist):
                        pass

                # 6. Деактивируем корзину и удаляем элементы
                cart_items.delete()
                cart_obj.is_active = False
                cart_obj.save()

                # Сохраняем номер заказа в сессию для страницы успеха
                request.session['last_order_number'] = order.order_number
                request.session.save()

                return redirect('payment_success')

            except Exception as e:
                logging.error(f'Checkout error: {str(e)}')
                messages.error(request, f'Ошибка при оформлении заказа: {str(e)}')
        else:
            messages.error(request, 'Выберите способ оплаты.')

    return render(request, 'checkout.html', {
        'games': games,
        'total': total,
        'is_logged_in': True,
        'user_type': user_type
    })


def payment_success(request):
    """
    Страница успешной оплаты
    """
    order_number = request.session.get('last_order_number', '')
    return render(request, 'payment_success.html', {
        'order_number': order_number
    })


def order_cancelled(request):
    return render(request, 'order_cancelled.html')


def select_game_chat(request):
    """
    Выбор игры для чата с продавцом (3НФ)
    """
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')

    if not user_id or user_type != 'buy':
        messages.error(request, 'Только покупатели могут общаться с продавцами.')
        return redirect('catalog')

    # Получаем корзину через Cart модель (3НФ)
    cart_obj = get_or_create_cart(user_id, user_type)
    cart_items = cart_obj.items.all()
    
    games = []

    for item in cart_items:
        try:
            game = Game.objects.get(id=item.game_id)
            games.append({
                'id': game.id,
                'title': game.title,
                'price': game.current_price,
                'seller_name': game.seller_name,
                'seller_id': game.seller_id
            })
        except Game.DoesNotExist:
            pass

    if not games:
        messages.error(request, 'В вашей корзине нет игр.')
        return redirect('checkout')

    return render(request, 'select_game_chat.html', {'games': games})


def seller_chat(request, game_id):
    """
    Чат между покупателем и продавцом (3НФ)
    Использует seller как FK на SellUser
    """
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')

    if not user_id:
        messages.error(request, 'Войдите в систему.')
        return redirect('catalog')

    if user_type not in ['buy', 'sell']:
        messages.error(request, 'Недостаточно прав.')
        return redirect('catalog')

    # Для продавцов: отметить чат как прочитанный (сохраняем в БД)
    if user_type == 'sell':
        chat_key = f'seller_{user_id}_game_{game_id}'
        ChatReadStatus.objects.update_or_create(
            user_id=user_id,
            user_type='sell',
            chat_key=chat_key,
            defaults={'last_read_at': timezone.now()}
        )

    try:
        game = Game.objects.select_related('genre').get(id=game_id)

        if user_type == 'buy':
            # Покупатель пишет продавцу
            buyer = BuyUser.objects.get(id=user_id)
            buyer_name = buyer.username
            
            # Получаем продавца по seller_id
            if game.seller_id:
                seller = SellUser.objects.get(id=game.seller_id)
                seller_name = seller.username
            else:
                messages.error(request, 'У этой игры нет продавца.')
                return redirect('catalog')
            
            chat_identifier = f'buyer_{user_id}_seller_{seller.id}_game_{game_id}'
            
        elif user_type == 'sell':
            # Продавец отвечает покупателю
            seller = SellUser.objects.get(id=user_id)
            seller_name = seller.username
            
            # Ищем существующий чат
            chat_pattern = f'seller_{user_id}_game_{game_id}'
            existing_chat = SupportMessage.objects.filter(user__contains=chat_pattern).first()
            
            if existing_chat:
                chat_identifier = existing_chat.user
                user_parts = chat_identifier.split('_')
                buyer_id = int(user_parts[1]) if len(user_parts) > 1 and user_parts[0] == 'buyer' else None
                if buyer_id:
                    try:
                        buyer = BuyUser.objects.get(id=buyer_id)
                        buyer_name = buyer.username
                    except BuyUser.DoesNotExist:
                        messages.error(request, 'Покупатель не найден.')
                        return redirect('account')
                else:
                    buyer_name = 'Покупатель'
            else:
                messages.error(request, 'Чат не найден.')
                return redirect('account')
        else:
            messages.error(request, 'Недостаточно прав.')
            return redirect('catalog')

        messages_list = SupportMessage.objects.filter(user=chat_identifier).order_by('timestamp')

        if request.method == 'POST':
            message_text = request.POST.get('message')
            if message_text:
                if user_type == 'buy':
                    SupportMessage.objects.create(
                        user=chat_identifier,
                        display_name=buyer_name,
                        message=message_text,
                        is_support=False
                    )
                    response = f'Здравствуйте, {buyer_name}! Спасибо за ваш вопрос по игре "{game.title}". Мы свяжемся с вами в ближайшее время.'
                    SupportMessage.objects.create(
                        user=chat_identifier,
                        display_name=seller_name,
                        message=response,
                        is_support=True
                    )
                elif user_type == 'sell':
                    SupportMessage.objects.create(
                        user=chat_identifier,
                        display_name=seller_name,
                        message=message_text,
                        is_support=True
                    )
                return redirect('seller_chat', game_id=game_id)

        # Welcome message if empty (только для покупателей)
        if not messages_list.exists() and user_type == 'buy':
            welcome = f'Здравствуйте! Вы пишете по поводу игры "{game.title}". Чем можем помочь?'
            SupportMessage.objects.create(
                user=chat_identifier,
                display_name=seller_name,
                message=welcome,
                is_support=True
            )
            messages_list = SupportMessage.objects.filter(user=chat_identifier).order_by('timestamp')

        return render(request, 'seller_chat.html', {
            'messages': messages_list,
            'game': game,
            'seller_name': seller_name,
            'buyer_name': buyer_name,
            'user_type': user_type
        })

    except Game.DoesNotExist:
        messages.error(request, 'Игра не найдена.')
        return redirect('checkout')
    except BuyUser.DoesNotExist:
        messages.error(request, 'Пользователь не найден.')
        return redirect('catalog')
    except SellUser.DoesNotExist:
        messages.error(request, 'Продавец не найден.')
        return redirect('catalog')


def support_chat(request):
    # Получаем информацию о пользователе из сессии
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')

    # Если пользователь не вошел, перенаправляем
    if not user_id or not user_type:
        messages.error(request, 'Войдите в систему, чтобы использовать чат с поддержкой.')
        return redirect('catalog')

    # Получаем реальное имя пользователя
    username = "Гость"  # Значение по умолчанию

    try:
        if user_type == 'buy':
            user = BuyUser.objects.get(id=user_id)
            username = user.username
        elif user_type == 'sell':
            user = SellUser.objects.get(id=user_id)
            username = user.username
    except (BuyUser.DoesNotExist, SellUser.DoesNotExist):
        # Если пользователь не найден, используем сессионный ключ
        username = f"Гость_{request.session.session_key[:8]}"

    # Получаем или создаем уникальный идентификатор для чата
    # Используем комбинацию user_id и user_type
    chat_identifier = f"{user_type}_{user_id}"

    # Проверяем, запрошен ли новый чат
    new_chat = request.GET.get('new_chat', False)
    if new_chat:
        # Удаляем все старые сообщения пользователя
        SupportMessage.objects.filter(user=chat_identifier).delete()

        # Создаем новое приветственное сообщение
        welcome_message = f'Здравствуйте, {username}! Чем можем вам помочь? 😊'
        SupportMessage.objects.create(
            user=chat_identifier,
            display_name='Поддержка',
            message=welcome_message,
            is_support=True
        )

        # Редирект на ту же страницу без параметра new_chat
        return redirect('support_chat')

    # Получаем все сообщения для этого пользователя
    messages_list = SupportMessage.objects.filter(user=chat_identifier).order_by('timestamp')

    if request.method == 'POST':
        message_text = request.POST.get('message')
        if message_text:
            # Сохраняем сообщение от пользователя с его реальным именем
            SupportMessage.objects.create(
                user=chat_identifier,
                display_name=username,
                message=message_text,
                is_support=False
            )

            # Генерируем ответ поддержки
            response = generate_support_response(message_text.lower())
            SupportMessage.objects.create(
                user=chat_identifier,
                display_name='Поддержка',
                message=response,
                is_support=True
            )

            return redirect('support_chat')

    # Добавляем приветственное сообщение, если чат пустой
    if not messages_list.exists():
        welcome_message = f'Здравствуйте, {username}! Чем можем вам помочь? 😊'
        SupportMessage.objects.create(
            user=chat_identifier,
            display_name='Поддержка',
            message=welcome_message,
            is_support=True
        )
        messages_list = SupportMessage.objects.filter(user=chat_identifier).order_by('timestamp')

    return render(request, 'support_chat.html', {
        'messages': messages_list,
        'username': username,
        'user_display_name': username  # Передаем имя пользователя в шаблон
    })


def rate_game(request):
    """
    Оценка игры покупателем
    """
    if request.method == 'POST' and request.session.get('user_id') and request.session.get('user_type') == 'buy':
        import json
        try:
            data = json.loads(request.body)
            game_id = data.get('game_id')
            rating_value = data.get('rating', 0)

            game = Game.objects.get(id=int(game_id))
            user_id = request.session.get('user_id')

            # Создаем или обновляем рейтинг пользователя
            # GameRating хранится в default БД, но ссылается на game_id
            user_rating, created = GameRating.objects.get_or_create(
                user_id=int(user_id),
                user_type='buy',
                game_id=int(game_id),  # Используем game_id вместо game объекта
                defaults={'rating': int(rating_value)}
            )
            if not created:
                user_rating.rating = int(rating_value)
                user_rating.save()

            # Пересчитываем средний рейтинг игры на основе всех рейтингов
            ratings = GameRating.objects.filter(game_id=int(game_id))
            if ratings.exists():
                avg_rating = ratings.aggregate(avg_rating=Avg('rating'))['avg_rating']
                game.rating = round(avg_rating, 1)
                game.save()

            return JsonResponse({
                'success': True,
                'new_rating': float(game.rating),
                'total_ratings': ratings.count()
            })
        except Game.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Game not found'})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Not authenticated or invalid request'})


def get_user_rating(request):
    """
    Получение рейтинга пользователя для игры
    """
    if request.method == 'GET':
        game_id = request.GET.get('game_id')
        user_id = request.session.get('user_id')
        user_type = request.session.get('user_type')

        if not user_id or user_type != 'buy':
            return JsonResponse({'success': False, 'user_rating': 0})

        try:
            # Используем game_id напрямую
            user_rating = GameRating.objects.filter(
                user_id=int(user_id),
                user_type='buy',
                game_id=int(game_id)
            ).first()

            if user_rating:
                return JsonResponse({
                    'success': True,
                    'user_rating': user_rating.rating
                })
            else:
                return JsonResponse({'success': True, 'user_rating': 0})

        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'user_rating': 0})

    return JsonResponse({'success': False, 'user_rating': 0})


def leave_review(request, game_id):
    """
    Страница оставления отзыва и рейтинга
    """
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')

    if not user_id or user_type != 'buy':
        messages.error(request, 'Только покупатели могут оставлять отзывы.')
        return redirect('catalog')

    try:
        game = Game.objects.select_related('genre').get(id=game_id)
    except Game.DoesNotExist:
        messages.error(request, 'Игра не найдена.')
        return redirect('catalog')

    # Получаем существующий рейтинг пользователя
    existing_rating = GameRating.objects.filter(
        user_id=user_id,
        user_type='buy',
        game_id=game_id
    ).first()
    
    # Получаем существующий отзыв пользователя
    existing_review = Review.objects.filter(
        game=game,
        reviewer_name=request.session.get('username', 'Гость')
    ).first()

    if request.method == 'POST':
        rating_value = request.POST.get('rating')
        comment = request.POST.get('comment', '').strip()

        # Сохраняем рейтинг
        if rating_value:
            rating_value = int(rating_value)
            user_rating, created = GameRating.objects.get_or_create(
                user_id=user_id,
                user_type='buy',
                game_id=game_id,
                defaults={'rating': rating_value}
            )
            if not created:
                user_rating.rating = rating_value
                user_rating.save()

            # Пересчитываем средний рейтинг игры
            ratings = GameRating.objects.filter(game_id=game_id)
            if ratings.exists():
                avg_rating = ratings.aggregate(avg_rating=Avg('rating'))['avg_rating']
                game.rating = round(avg_rating, 1)
                game.save()

        # Сохраняем отзыв (если есть текст)
        if comment:
            review, created = Review.objects.get_or_create(
                game=game,
                reviewer_name=request.session.get('username', 'Гость'),
                defaults={'rating': rating_value or 0, 'comment': comment}
            )
            if not created:
                review.comment = comment
                if rating_value:
                    review.rating = rating_value
                review.save()

        if rating_value or comment:
            messages.success(request, 'Спасибо за отзыв! 😊')
            return redirect('catalog')
        else:
            messages.warning(request, 'Выберите оценку или напишите отзыв.')
            return redirect('leave_review', game_id=game_id)

    return render(request, 'leave_review.html', {
        'game': game,
        'user_rating': existing_rating.rating if existing_rating else None,
        'existing_comment': existing_review.comment if existing_review else ''
    })


def delete_game(request, game_id):
    """
    Удаление игры продавцом (3НФ)
    Использует seller как FK
    """
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')

    if not user_id or user_type != 'sell':
        messages.error(request, 'Только продавцы могут удалять игры.')
        return redirect('account')

    try:
        # Получаем продавца
        seller = SellUser.objects.get(id=user_id)
        # Получаем игру и проверяем, что она принадлежит этому продавцу (по seller_id)
        game = Game.objects.get(id=game_id, seller_id=seller.id)
        game_title = game.title
        game.delete()
        messages.success(request, f'Игра "{game_title}" удалена успешно!')
    except SellUser.DoesNotExist:
        messages.error(request, 'Пользователь не найден.')
    except Game.DoesNotExist:
        messages.error(request, 'Игра не найдена или не принадлежит вам.')

    return redirect('account')


def order_history(request):
    """
    История заказов пользователя (3НФ)
    """
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')

    if not user_id or user_type != 'buy':
        messages.error(request, 'Войдите как покупатель для просмотра заказов.')
        return redirect('catalog')

    # Получаем заказы пользователя с позициями и платежами
    orders = Order.objects.filter(
        user_id=user_id,
        user_type=user_type
    ).select_related('status').prefetch_related('items').order_by('-created_at')

    orders_data = []
    for order in orders:
        items_data = []
        for item in order.items.all():
            try:
                game = Game.objects.get(id=item.game_id)
                items_data.append({
                    'game_id': item.game_id,
                    'game_title': game.title,
                    'game_image': game.image.url if game.image else None,
                    'quantity': item.quantity,
                    'price': item.price_at_purchase,
                    'total': item.total_price
                })
            except Game.DoesNotExist:
                items_data.append({
                    'game_id': item.game_id,
                    'game_title': f'Игра #{item.game_id} (удалена)',
                    'game_image': None,
                    'quantity': item.quantity,
                    'price': item.price_at_purchase,
                    'total': item.total_price
                })

        # Получаем платёж
        try:
            payment = order.payment
            payment_info = {
                'method': payment.method.name if payment.method else payment.method_code,
                'status': payment.get_status_display(),
                'paid_at': payment.paid_at,
                'card_last_four': payment.card_last_four
            }
        except Payment.DoesNotExist:
            payment_info = None

        orders_data.append({
            'order_number': order.order_number,
            'status': order.status.name if order.status else 'Неизвестно',
            'status_code': order.status.code if order.status else 'unknown',
            'created_at': order.created_at,
            'total': order.total_amount,
            'items_count': order.items_count,
            'items': items_data,
            'payment': payment_info
        })

    return render(request, 'order_history.html', {
        'orders': orders_data,
        'is_logged_in': True,
        'user_type': user_type
    })


def withdraw_money(request):
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')

    if not user_id or user_type != 'sell':
        messages.error(request, 'Только продавцы могут выводить деньги.')
        return redirect('account')

    from api_v1.models import SellUser

    try:
        seller = SellUser.objects.get(id=user_id)
    except SellUser.DoesNotExist:
        messages.error(request, 'Пользователь не найден.')
        return redirect('account')

    if request.method == 'POST':
        bank = request.POST.get('bank')
        card_number = request.POST.get('card_number')
        amount_str = request.POST.get('amount')

        if not bank or not card_number or not amount_str:
            messages.error(request, 'Заполните все поля.')
            return redirect('account')

        try:
            amount = Decimal(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messages.error(request, 'Неверная сумма.')
            return redirect('account')

        if amount > seller.balance:
            messages.error(request, 'Недостаточно средств на балансе.')
            return redirect('account')

        # Вычесть сумму
        seller.balance -= amount
        seller.save()

        messages.success(request, 'Деньги скоро придут к вам на карту.')

        return redirect('account')

    return redirect('account')
