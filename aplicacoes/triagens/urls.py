from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import RespostaTriagemViewSet, TriagemViewSet

router = DefaultRouter()
router.register('respostas', RespostaTriagemViewSet, basename='respostas-triagem')
router.register('', TriagemViewSet, basename='triagens')

urlpatterns = [
    path('', include(router.urls)),
]
