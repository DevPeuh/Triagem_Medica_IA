from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AgendaProfissionalViewSet, EncaminhamentoViewSet, PreAgendamentoViewSet

encaminhamento_list = EncaminhamentoViewSet.as_view({'get': 'list', 'post': 'create'})
encaminhamento_detail = EncaminhamentoViewSet.as_view(
    {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}
)

router = DefaultRouter()
router.register('agenda-profissionais', AgendaProfissionalViewSet, basename='agenda-profissionais')
router.register('pre-agendamentos', PreAgendamentoViewSet, basename='pre-agendamentos')

urlpatterns = [
    path('', encaminhamento_list, name='encaminhamento-list'),
    path('<int:pk>/', encaminhamento_detail, name='encaminhamento-detail'),
    path('', include(router.urls)),
]
