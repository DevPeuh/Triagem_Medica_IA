from django.contrib.auth.models import User
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from aplicacoes.pacientes.models import Paciente
from aplicacoes.usuarios.models import Usuario


@override_settings(SECURE_SSL_REDIRECT=False)
class CadastroPacienteAPITests(APITestCase):
    def setUp(self):
        self.url = '/api/autenticacao/cadastro/'
        self.payload = {
            'username': 'paciente.teste',
            'email': 'paciente@example.com',
            'password': 'SenhaForte@123',
            'confirmar_senha': 'SenhaForte@123',
            'nome_completo': 'Paciente Teste',
            'sexo': 'feminino',
            'telefone': '11999999999',
        }

    def test_deve_cadastrar_paciente_com_sucesso(self):
        response = self.client.post(self.url, self.payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='paciente.teste')
        self.assertTrue(Usuario.objects.filter(usuario_auth=user, perfil=Usuario.Perfil.PACIENTE).exists())
        self.assertTrue(Paciente.objects.filter(usuario_auth=user).exists())

    def test_nao_deve_cadastrar_com_username_duplicado(self):
        User.objects.create_user(username='paciente.teste', email='x@x.com', password='SenhaForte@123')

        response = self.client.post(self.url, self.payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_nao_deve_cadastrar_com_email_duplicado(self):
        outro_user = User.objects.create_user(username='outro', email='paciente@example.com', password='SenhaForte@123')
        Usuario.objects.create(
            usuario_auth=outro_user,
            nome_completo='Outro',
            email='paciente@example.com',
            perfil=Usuario.Perfil.PACIENTE,
            ativo=True,
        )

        response = self.client.post(self.url, self.payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)


@override_settings(SECURE_SSL_REDIRECT=False)
class LoginAPITests(APITestCase):
    def setUp(self):
        self.url = '/api/autenticacao/login/'
        self.user = User.objects.create_user(
            username='usuario.login',
            email='login@example.com',
            password='SenhaForte@123',
        )
        Usuario.objects.create(
            usuario_auth=self.user,
            nome_completo='Usuário Login',
            email='login@example.com',
            perfil=Usuario.Perfil.PACIENTE,
            ativo=True,
        )

    def test_deve_fazer_login_com_credenciais_validas(self):
        response = self.client.post(
            self.url,
            {'username': 'usuario.login', 'password': 'SenhaForte@123'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['usuario']['username'], 'usuario.login')

    def test_nao_deve_fazer_login_com_credenciais_invalidas(self):
        response = self.client.post(
            self.url,
            {'username': 'usuario.login', 'password': 'senha_errada'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
