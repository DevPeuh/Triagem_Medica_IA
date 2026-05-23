from django.db import transaction
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from aplicacoes.permissoes import IsAdministradorOuProfissional, obter_perfil_usuario
from aplicacoes.usuarios.models import Usuario

from .models import RespostaTriagem, Triagem
from .serializers import (
    RespostaTriagemSerializer,
    TriagemRapidaSerializer,
    TriagemSerializer,
    criar_triagem_rapida,
)
from .servicos import classificar_e_gerar_resultado


class TriagemViewSet(viewsets.ModelViewSet):
    queryset = Triagem.objects.select_related('paciente', 'profissional_responsavel').all()
    serializer_class = TriagemSerializer

    def get_permissions(self):
        if self.action in {'triagem_rapida', 'minhas'}:
            return [permissions.IsAuthenticated()]
        return [IsAdministradorOuProfissional()]

    @action(detail=True, methods=['post'], url_path='classificar')
    @transaction.atomic
    def classificar(self, request, pk=None):
        triagem = self.get_object()
        resultado = classificar_e_gerar_resultado(triagem)
        return Response(resultado, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='triagem-rapida')
    @transaction.atomic
    def triagem_rapida(self, request):
        serializer = TriagemRapidaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        perfil = obter_perfil_usuario(request.user)
        if perfil is None:
            return Response(
                {'detalhe': 'Usuário sem perfil ativo para utilizar a triagem.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        profissional = None
        paciente = None

        if perfil in (Usuario.Perfil.ADMINISTRADOR, Usuario.Perfil.PROFISSIONAL):
            if 'paciente' not in serializer.validated_data:
                return Response(
                    {'paciente': ['Dados do paciente são obrigatórios para este perfil.']},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            profissional = getattr(request.user, 'perfil_sistema', None)
        elif perfil == Usuario.Perfil.PACIENTE:
            paciente = getattr(request.user, 'paciente_perfil', None)
            if paciente is None and 'paciente' not in serializer.validated_data:
                return Response(
                    {'paciente': ['Informe seus dados para iniciar a triagem.']},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response({'detalhe': 'Perfil sem permissão para triagem.'}, status=status.HTTP_403_FORBIDDEN)

        triagem = criar_triagem_rapida(
            serializer.validated_data,
            profissional_responsavel=profissional,
            paciente=paciente,
        )
        resultado = classificar_e_gerar_resultado(triagem)

        return Response(resultado, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='minhas')
    def minhas(self, request):
        paciente = getattr(request.user, 'paciente_perfil', None)
        if paciente is None:
            return Response({'detalhe': 'Paciente não vinculado ao usuário.'}, status=status.HTTP_403_FORBIDDEN)

        queryset = (
            Triagem.objects.select_related('paciente', 'profissional_responsavel')
            .prefetch_related('respostas')
            .filter(paciente=paciente)
            .order_by('-data_hora_inicio')
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RespostaTriagemViewSet(viewsets.ModelViewSet):
    queryset = RespostaTriagem.objects.select_related('triagem', 'sintoma').all()
    serializer_class = RespostaTriagemSerializer
    permission_classes = [IsAdministradorOuProfissional]