from rest_framework import mixins, viewsets

from aplicacoes.permissoes import IsAdministradorOuProfissional
from .models import AgendaProfissional, Encaminhamento, PreAgendamento
from .serializers import AgendaProfissionalSerializer, EncaminhamentoSerializer, PreAgendamentoSerializer


class EncaminhamentoViewSet(viewsets.ModelViewSet):
    queryset = Encaminhamento.objects.select_related('triagem').all()
    serializer_class = EncaminhamentoSerializer
    permission_classes = [IsAdministradorOuProfissional]


class AgendaProfissionalViewSet(viewsets.ModelViewSet):
    queryset = AgendaProfissional.objects.select_related('profissional').all()
    serializer_class = AgendaProfissionalSerializer
    permission_classes = [IsAdministradorOuProfissional]


class PreAgendamentoViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = PreAgendamento.objects.select_related('triagem', 'encaminhamento', 'profissional').all()
    serializer_class = PreAgendamentoSerializer
    permission_classes = [IsAdministradorOuProfissional]
