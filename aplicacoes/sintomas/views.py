from rest_framework import viewsets

from aplicacoes.permissoes import IsAdministradorOuProfissional
from .models import Sintoma
from .serializers import SintomaSerializer


class SintomaViewSet(viewsets.ModelViewSet):
    queryset = Sintoma.objects.all()
    serializer_class = SintomaSerializer
    permission_classes = [IsAdministradorOuProfissional]