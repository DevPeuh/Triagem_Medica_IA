import socket
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from aplicacoes.chat_ia.servicos import gerar_resposta_chat_triagem
from aplicacoes.encaminhamentos.models import AgendaProfissional, Encaminhamento, PreAgendamento
from aplicacoes.pacientes.models import Paciente
from aplicacoes.triagens.models import Triagem
from aplicacoes.usuarios.models import Usuario


@override_settings(SECURE_SSL_REDIRECT=False)
class ChatIAServicosTests(APITestCase):
    def setUp(self):
        cache.clear()

    @override_settings(CHAT_IA_MODO_RAPIDO_LOCAL=False, OLLAMA_RETRY_ATTEMPTS=2, OLLAMA_TIMEOUT_SECONDS=1)
    @patch('aplicacoes.chat_ia.servicos._chamar_ollama', side_effect=socket.timeout())
    def test_timeout_gera_fallback_seguro_sem_classificar(self, _mock_ollama):
        dados = gerar_resposta_chat_triagem(
            mensagem='Dor de cabeca ha 3 dias com enjoo.',
            historico=[{'role': 'user', 'content': 'Comecou ontem'}],
        )

        self.assertTrue(dados['erro_ia_local'])
        self.assertFalse(dados['pronto_para_classificar'])
        self.assertIn('meta_ia', dados)
        self.assertEqual(dados['meta_ia']['tentativas'], 2)

    @override_settings(CHAT_IA_MODO_RAPIDO_LOCAL=False, OLLAMA_RETRY_ATTEMPTS=2)
    @patch(
        'aplicacoes.chat_ia.servicos._chamar_ollama',
        side_effect=[
            socket.timeout(),
            {'message': {'content': '{"mensagem_ia":"ok","pronto_para_classificar":false,"paciente":{},"sintomas":[],"observacoes_gerais":""}'}},
        ],
    )
    def test_retry_recupera_sem_falhar(self, _mock_ollama):
        dados = gerar_resposta_chat_triagem(
            mensagem='Dor de garganta.',
            historico=[],
        )

        self.assertFalse(dados['erro_ia_local'])
        self.assertEqual(dados['meta_ia']['tentativas'], 2)
        self.assertEqual(dados['meta_ia']['origem'], 'ollama')

    @override_settings(CHAT_IA_MODO_RAPIDO_LOCAL=True)
    def test_fluxo_rapido_nao_repete_pergunta_e_avanca_para_duracao(self):
        historico = [
            {'role': 'assistant', 'content': 'De 1 a 5, qual a intensidade da dor agora?'},
            {'role': 'user', 'content': '5'},
            {'role': 'assistant', 'content': 'Voce esta sentindo dor de cabeca severa. Ha outros sintomas?'},
            {'role': 'user', 'content': 'apenas dor de cabeca'},
        ]

        dados = gerar_resposta_chat_triagem(mensagem='5', historico=historico)

        self.assertFalse(dados['pronto_para_classificar'])
        self.assertIn('Ha quanto tempo', dados['mensagem_ia'])


@override_settings(SECURE_SSL_REDIRECT=False)
class ChatIAAPIViewTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.url_triagem_chat = '/api/chat-ia/triagem/'
        self.url_monitoramento = '/api/chat-ia/monitoramento/'

        self.user = User.objects.create_user(
            username='paciente_chat',
            email='paciente_chat@example.com',
            password='SenhaForte@123',
        )
        Usuario.objects.create(
            usuario_auth=self.user,
            nome_completo='Paciente Chat',
            email='paciente_chat@example.com',
            perfil=Usuario.Perfil.PACIENTE,
            ativo=True,
        )
        self.paciente = Paciente.objects.create(
            usuario_auth=self.user,
            nome_completo='Paciente Chat',
            email='paciente_chat@example.com',
        )
        self.client.force_authenticate(user=self.user)

    @patch('aplicacoes.chat_ia.views.gerar_resposta_chat_triagem')
    def test_triagem_chat_retorna_meta_e_status_200_quando_sem_classificacao(self, mock_gerar):
        mock_gerar.return_value = {
            'mensagem_ia': 'Informe a intensidade de 1 a 5.',
            'pronto_para_classificar': False,
            'erro_ia_local': False,
            'meta_ia': {'duracao_ms': 120, 'tentativas': 1, 'origem': 'ollama'},
        }

        response = self.client.post(
            self.url_triagem_chat,
            {'mensagem': 'Sinto dor no peito', 'historico': []},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('meta_ia', response.data)
        self.assertEqual(response.data['meta_ia']['origem'], 'ollama')
        self.assertIn('X-Response-Time-ms', response)

    @patch('aplicacoes.chat_ia.views.gerar_resposta_chat_triagem')
    def test_monitoramento_retorna_metricas(self, mock_gerar):
        mock_gerar.return_value = {
            'mensagem_ia': 'Pergunta objetiva',
            'pronto_para_classificar': False,
            'erro_ia_local': True,
            'meta_ia': {'duracao_ms': 210, 'tentativas': 2, 'origem': 'fallback_heuristico'},
        }

        self.client.post(
            self.url_triagem_chat,
            {'mensagem': 'Dor de cabeca', 'historico': []},
            format='json',
        )

        metrics = self.client.get(self.url_monitoramento)

        self.assertEqual(metrics.status_code, status.HTTP_200_OK)
        self.assertIn('http_total_requisicoes', metrics.data)
        self.assertIn('taxa_sucesso_ia', metrics.data)

    def test_confirmar_pre_agendamento_pelo_chat(self):
        user_medico = User.objects.create_user(username='med_chat', email='med_chat@example.com', password='SenhaForte@123')
        medico = Usuario.objects.create(
            usuario_auth=user_medico,
            nome_completo='Dr. Confirmado',
            email='med_chat@example.com',
            perfil=Usuario.Perfil.PROFISSIONAL,
            especialidade=Usuario.Especialidade.NEUROLOGIA,
            ativo=True,
        )

        inicio = timezone.now() + timedelta(hours=2)
        slot = AgendaProfissional.objects.create(
            profissional=medico,
            especialidade=Usuario.Especialidade.NEUROLOGIA,
            inicio_atendimento=inicio,
            fim_atendimento=inicio + timedelta(minutes=30),
            reservado=True,
            ativo=True,
        )

        triagem = Triagem.objects.create(paciente=self.paciente)
        enc = Encaminhamento.objects.create(
            triagem=triagem,
            recomendacao=Encaminhamento.Recomendacao.CONSULTA,
            descricao='Consulta prioritaria',
            prazo_recomendado='Ate 24 horas',
        )
        PreAgendamento.objects.create(
            triagem=triagem,
            encaminhamento=enc,
            agenda_slot=slot,
            profissional=medico,
            especialidade=Usuario.Especialidade.NEUROLOGIA,
            horario_sugerido=inicio,
            status=PreAgendamento.Status.SUGERIDO,
            mensagem='Pre-agendamento sugerido.',
        )

        response = self.client.post(
            self.url_triagem_chat,
            {'mensagem': 'confirmar agendamento', 'historico': []},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['meta_ia']['origem'], 'pre_agendamento')
        self.assertIn('confirmado', response.data['mensagem_ia'].lower())
        self.assertEqual(response.data['pre_agendamento']['status'], PreAgendamento.Status.CONFIRMADO)

    def test_reagendar_pre_agendamento_pelo_chat(self):
        user_medico = User.objects.create_user(username='med_reag', email='med_reag@example.com', password='SenhaForte@123')
        medico = Usuario.objects.create(
            usuario_auth=user_medico,
            nome_completo='Dra. Reagenda',
            email='med_reag@example.com',
            perfil=Usuario.Perfil.PROFISSIONAL,
            especialidade=Usuario.Especialidade.CLINICA_GERAL,
            ativo=True,
        )

        inicio1 = timezone.now() + timedelta(hours=2)
        slot1 = AgendaProfissional.objects.create(
            profissional=medico,
            especialidade=Usuario.Especialidade.CLINICA_GERAL,
            inicio_atendimento=inicio1,
            fim_atendimento=inicio1 + timedelta(minutes=30),
            reservado=True,
            ativo=True,
        )
        inicio2 = timezone.now() + timedelta(hours=4)
        slot2 = AgendaProfissional.objects.create(
            profissional=medico,
            especialidade=Usuario.Especialidade.CLINICA_GERAL,
            inicio_atendimento=inicio2,
            fim_atendimento=inicio2 + timedelta(minutes=30),
            reservado=False,
            ativo=True,
        )

        triagem = Triagem.objects.create(paciente=self.paciente)
        enc = Encaminhamento.objects.create(
            triagem=triagem,
            recomendacao=Encaminhamento.Recomendacao.CONSULTA,
            descricao='Consulta prioritaria',
            prazo_recomendado='Ate 24 horas',
        )
        pre = PreAgendamento.objects.create(
            triagem=triagem,
            encaminhamento=enc,
            agenda_slot=slot1,
            profissional=medico,
            especialidade=Usuario.Especialidade.CLINICA_GERAL,
            horario_sugerido=inicio1,
            status=PreAgendamento.Status.SUGERIDO,
            mensagem='Pre-agendamento sugerido.',
        )

        response = self.client.post(
            self.url_triagem_chat,
            {'mensagem': 'quero reagendar', 'historico': []},
            format='json',
        )

        pre.refresh_from_db()
        slot1.refresh_from_db()
        slot2.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['pre_agendamento']['status'], PreAgendamento.Status.REAGENDADO)
        self.assertEqual(pre.agenda_slot_id, slot2.id)
        self.assertFalse(slot1.reservado)
        self.assertTrue(slot2.reservado)
