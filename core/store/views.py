# Импорт для generic представлений Django
from django.views.generic import TemplateView

# Представление для домашней страницы магазина
class HomeView(TemplateView):
    # Шаблон для отображения
    template_name = 'store/home.html'

# Представление для страницы документации
class DocsView(TemplateView):
    # Шаблон для отображения
    template_name = 'store/docs.html'
