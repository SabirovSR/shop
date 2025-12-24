# Представления для API v1

# Импорты Django и DRF
from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from .models import Developer, Genre, Game, Review
from .serializers import (
    DeveloperSerializer,
    GenreSerializer,
    GameSerializer,
    ReviewSerializer,
)

# Домашняя страница API (HTML страница с ссылками)
def home(request):
    html = """
    <html>
    <head>
        <title>Shop API</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                text-align: center;
            }
            h1 {
                font-size: 3em;
                margin-bottom: 20px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            }
            p {
                font-size: 1.2em;
                margin: 10px 0;
            }
            ul {
                list-style-type: none;
                padding: 0;
            }
            li {
                margin: 10px 0;
            }
            a {
                color: #ffd700;
                text-decoration: none;
                font-weight: bold;
                transition: color 0.3s;
            }
            a:hover {
                color: #ffed4e;
            }
            .container {
                max-width: 600px;
                padding: 20px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Welcome to Shop API</h1>
            <p>API endpoints:</p>
            <ul>
                <li><a href="/api/v1/authors/">Authors</a></li>
                <li><a href="/api/v1/books/">Books</a></li>
                <li><a href="/api/v1/categories/">Categories</a></li>
                <li><a href="/api/v1/reviews/">Reviews</a></li>
            </ul>
            <p><a href="/api/v1/docs/">API Documentation</a></p>
            <p><a href="/admin/">Admin</a></p>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html)


# Представления для Developer с использованием декораторов @api_view
@api_view(["GET", "POST"])
def developer_list(request):
    # Получение списка разработчиков
    if request.method == "GET":
        developers = Developer.objects.all()
        serializer = DeveloperSerializer(developers, many=True)
        return Response(serializer.data)

    # Создание нового разработчика
    elif request.method == "POST":
        serializer = DeveloperSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Детальная страница разработчика
@api_view(["GET", "DELETE"])
def developer_detail(request, pk):
    try:
        developer = Developer.objects.get(pk=pk)
    except Developer.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    # Получение данных разработчика
    if request.method == "GET":
        serializer = DeveloperSerializer(developer)
        return Response(serializer.data)

    # Удаление разработчика
    elif request.method == "DELETE":
        developer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# Представления для Game с использованием Generic Views
class GameListCreateView(ListCreateAPIView):
    # Queryset для всех игр
    queryset = Game.objects.all()
    # Сериализатор для игр
    serializer_class = GameSerializer

# Детальная страница игры
class GameDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Game.objects.all()
    serializer_class = GameSerializer

# Представления для Genre с использованием APIView
class GenreView(APIView):
    # Получение списка жанров
    def get(self, request):
        genres = Genre.objects.all()
        serializer = GenreSerializer(genres, many=True)
        return Response(serializer.data)

    # Создание нового жанра
    def post(self, request):
        serializer = GenreSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Представления для Review с использованием APIView
class ReviewList(APIView):
    # Получение списка отзывов (для всех или для конкретной игры)
    def get(self, request, game_id=None):
        if game_id:
            reviews = Review.objects.filter(game_id=game_id)
        else:
            reviews = Review.objects.all()

        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    # Создание нового отзыва
    def post(self, request):
        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Детальная страница отзыва
class ReviewDetail(APIView):
    # Удаление отзыва
    def delete(self, request, pk):
        try:
            review = Review.objects.get(pk=pk)
            review.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Review.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
