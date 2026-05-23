from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import SintomaViewSet

router = DefaultRouter()
router.register('', SintomaViewSet, basename='sintomas')

urlpatterns = [
    path('', include(router.urls)),
]
