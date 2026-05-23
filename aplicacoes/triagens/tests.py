from django.contrib.auth.models import User
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from aplicacoes.pacientes.models import Paciente
from aplicacoes.triagens.models import Triagem
from aplicacoes.usuarios.models import Usuario


@override_settings(SECURE_SSL_REDIRECT=False)
class TriagemRapidaAPITests(APITestCase):
    def setUp(self):
        self.url_triagem_rapida = '/api/triagens/triagem-rapida/'
        self.url_minhas = '/api/triagens/minhas/'
        self.payload_sintomas = {
            'sintomas': [
                {
                    'descricao': 'dor de cabeça leve',
                    'intensidade': 2,
                    'duracao': '2 dias',
                    'possui_sinal_alerta': False,
                }
            ],
            'observacoes_gerais': 'Teste automatizado',
        }

    def test_nao_autenticado_nao_pode_usar_triagem_rapida(self):
        response = self.client.post(self.url_triagem_rapida, self.payload_sintomas, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_paciente_autenticado_reutiliza_mesmo_paciente_no_historico(self):
        user = User.objects.create_user(username='paciente1', email='paciente1@example.com', password='SenhaForte@123')
        Usuario.objects.create(
            usuario_auth=user,
            nome_completo='Paciente Um',
            email='paciente1@example.com',
            perfil=Usuario.Perfil.PACIENTE,
            ativo=True,
        )
        paciente = Paciente.objects.create(
            usuario_auth=user,
            nome_completo='Paciente Um',
            email='paciente1@example.com',
        )
        self.client.force_authenticate(user=user)

        response_1 = self.client.post(self.url_triagem_rapida, self.payload_sintomas, format='json')
        response_2 = self.client.post(self.url_triagem_rapida, self.payload_sintomas, format='json')

        self.assertEqual(response_1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Triagem.objects.filter(paciente=paciente).count(), 2)
        self.assertEqual(Paciente.objects.filter(usuario_auth=user).count(), 1)

    def test_paciente_consegue_listar_apenas_suas_triagens(self):
        user = User.objects.create_user(username='paciente2', email='paciente2@example.com', password='SenhaForte@123')
        Usuario.objects.create(
            usuario_auth=user,
            nome_completo='Paciente Dois',
            email='paciente2@example.com',
            perfil=Usuario.Perfil.PACIENTE,
            ativo=True,
        )
        paciente = Paciente.objects.create(
            usuario_auth=user,
            nome_completo='Paciente Dois',
            email='paciente2@example.com',
        )
        Triagem.objects.create(paciente=paciente, observacoes_gerais='Triagem da paciente 2')

        outro_user = User.objects.create_user(username='paciente3', email='paciente3@example.com', password='SenhaForte@123')
        Usuario.objects.create(
            usuario_auth=outro_user,
            nome_completo='Paciente Tres',
            email='paciente3@example.com',
            perfil=Usuario.Perfil.PACIENTE,
            ativo=True,
        )
        outro_paciente = Paciente.objects.create(
            usuario_auth=outro_user,
            nome_completo='Paciente Tres',
            email='paciente3@example.com',
        )
        Triagem.objects.create(paciente=outro_paciente, observacoes_gerais='Triagem da paciente 3')

        self.client.force_authenticate(user=user)
        response = self.client.get(self.url_minhas)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['paciente'], paciente.id)
