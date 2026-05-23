from rest_framework import viewsets 

from aplicacoes.permissoes import IsAdministradorOuProfissional
from .models import Paciente
from .serializers import PacienteSerializer


class PacienteViewSet(viewsets.ModelViewSet):
    queryset = Paciente.objects.all()
    serializer_class = PacienteSerializer
    permission_classes = [IsAdministradorOuProfissional]