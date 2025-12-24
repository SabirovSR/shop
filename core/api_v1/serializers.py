# Импорт сериализаторов Django REST Framework
from rest_framework import serializers
from .models import Developer, Genre, Game, Review

# Сериализатор для разработчиков (автоматический на основе модели)
class DeveloperSerializer(serializers.ModelSerializer):
    class Meta:
        model = Developer
        fields = '__all__'  # Все поля модели

# Сериализатор для жанров (ручной, с методами create/update)
class GenreSerializer(serializers.Serializer):
    # Поле ID (только для чтения)
    id = serializers.IntegerField(read_only=True)
    # Название жанра
    name = serializers.CharField(max_length=50)
    # Описание (необязательно)
    description = serializers.CharField(required=False)

    # Метод создания нового жанра
    def create(self, validated_data):
        return Genre.objects.create(**validated_data)

    # Метод обновления существующего жанра
    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.save()
        return instance

# Сериализатор для игр (автоматический)
class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = '__all__'

# Сериализатор для отзывов (автоматический)
class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'