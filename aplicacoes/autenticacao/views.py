from django.contrib.auth import authenticate, login, logout
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import CadastroPacienteSerializer


class CadastroPacienteAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = CadastroPacienteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        paciente = serializer.save()

        return Response(
            {
                'detalhe': 'Cadastro realizado com sucesso.',
                'paciente': {
                    'id': paciente.id,
                    'nome_completo': paciente.nome_completo,
                    'email': paciente.email,
                },
            },
            status=status.HTTP_201_CREATED,
        )


class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({'detalhe': 'Usuário e senha são obrigatórios.'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({'detalhe': 'Credenciais inválidas.'}, status=status.HTTP_401_UNAUTHORIZED)

        perfil_sistema = getattr(user, 'perfil_sistema', None)
        paciente_perfil = getattr(user, 'paciente_perfil', None)
        if perfil_sistema and not perfil_sistema.ativo:
            return Response(
                {'detalhe': 'Perfil de acesso inativo. Procure o administrador do sistema.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        login(request, user)
        return Response(
            {
                'detalhe': 'Login realizado com sucesso.',
                'usuario': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'perfil': getattr(perfil_sistema, 'perfil', None),
                    'paciente_id': getattr(paciente_perfil, 'id', None),
                },
            }
        )


class LogoutAPIView(APIView):
    def post(self, request):
        logout(request)
        return Response({'detalhe': 'Logout realizado com sucesso.'})


class SessaoAPIView(APIView):
    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({'autenticado': False}, status=status.HTTP_401_UNAUTHORIZED)

        perfil_sistema = getattr(user, 'perfil_sistema', None)
        paciente_perfil = getattr(user, 'paciente_perfil', None)
        return Response(
            {
                'autenticado': True,
                'usuario': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'perfil': getattr(perfil_sistema, 'perfil', None),
                    'paciente_id': getattr(paciente_perfil, 'id', None),
                },
            }
        )
