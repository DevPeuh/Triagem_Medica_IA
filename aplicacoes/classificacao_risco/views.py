from rest_framework import viewsets

from aplicacoes.permissoes import IsAdministradorOuProfissional
from .models import ClassificacaoRisco
from .serializers import ClassificacaoRiscoSerializer


class ClassificacaoRiscoViewSet(viewsets.ModelViewSet):
    queryset = ClassificacaoRisco.objects.select_related('triagem').all()
    serializer_class = ClassificacaoRiscoSerializer
    permission_classes = [IsAdministradorOuProfissional]