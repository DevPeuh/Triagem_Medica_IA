from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PacienteViewSet

router = DefaultRouter()
router.register('', PacienteViewSet, basename='pacientes')

urlpatterns = [
    path('', include(router.urls)),
]
