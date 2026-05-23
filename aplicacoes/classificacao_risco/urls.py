from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ClassificacaoRiscoViewSet

router = DefaultRouter()
router.register('', ClassificacaoRiscoViewSet, basename='classificacao-risco')

urlpatterns = [
    path('', include(router.urls)),
]
