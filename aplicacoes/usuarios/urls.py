from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import UsuarioViewSet

router = DefaultRouter()
router.register('', UsuarioViewSet, basename='usuarios')

urlpatterns = [
    path('', include(router.urls)),
]
