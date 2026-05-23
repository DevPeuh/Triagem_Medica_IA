from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from aplicacoes.encaminhamentos.agendamento_servicos import gerar_pre_agendamento, reagendar_pre_agendamento
from aplicacoes.encaminhamentos.models import AgendaProfissional, Encaminhamento, PreAgendamento
from aplicacoes.pacientes.models import Paciente
from aplicacoes.sintomas.models import Sintoma
from aplicacoes.triagens.models import RespostaTriagem, Triagem
from aplicacoes.usuarios.models import Usuario


class PreAgendamentoTests(TestCase):
    def setUp(self):
        user_paciente = User.objects.create_user(username='pac1', email='pac1@example.com', password='SenhaForte@123')
        self.paciente_usuario = Usuario.objects.create(
            usuario_auth=user_paciente,
            nome_completo='Paciente Um',
            email='pac1@example.com',
            perfil=Usuario.Perfil.PACIENTE,
            ativo=True,
        )
        self.paciente = Paciente.objects.create(
            usuario_auth=user_paciente,
            nome_completo='Paciente Um',
            email='pac1@example.com',
        )

        self.sintoma_cabeca = Sintoma.objects.create(nome='dor de cabeca', descricao='Dor de cabeca intensa')

    def _criar_triagem(self, intensidade=5):
        triagem = Triagem.objects.create(paciente=self.paciente)
        RespostaTriagem.objects.create(
            triagem=triagem,
            sintoma=self.sintoma_cabeca,
            intensidade=intensidade,
            duracao='2 dias',
            possui_sinal_alerta=True,
            observacao='dor de cabeca forte',
        )
        return triagem

    def test_pre_agendamento_sugerido_quando_ha_vaga(self):
        user_medico = User.objects.create_user(username='med1', email='med1@example.com', password='SenhaForte@123')
        medico = Usuario.objects.create(
            usuario_auth=user_medico,
            nome_completo='Dra. Ana Neuro',
            email='med1@example.com',
            perfil=Usuario.Perfil.PROFISSIONAL,
            especialidade=Usuario.Especialidade.NEUROLOGIA,
            ativo=True,
        )

        inicio = timezone.now() + timedelta(hours=1)
        fim = inicio + timedelta(minutes=30)
        slot = AgendaProfissional.objects.create(
            profissional=medico,
            especialidade=Usuario.Especialidade.NEUROLOGIA,
            inicio_atendimento=inicio,
            fim_atendimento=fim,
            reservado=False,
            ativo=True,
        )

        triagem = self._criar_triagem(intensidade=4)
        encaminhamento = Encaminhamento.objects.create(
            triagem=triagem,
            recomendacao=Encaminhamento.Recomendacao.CONSULTA,
            descricao='Agendar consulta clinica',
            prazo_recomendado='Ate 24 horas',
        )

        dados = gerar_pre_agendamento(triagem=triagem, encaminhamento=encaminhamento)
        slot.refresh_from_db()

        self.assertEqual(dados['status'], PreAgendamento.Status.SUGERIDO)
        self.assertTrue(slot.reservado)
        self.assertIsNotNone(dados['profissional'])
        self.assertIn('Pre-agendamento sugerido', dados['mensagem'])

    def test_pre_agendamento_quando_sem_slot(self):
        triagem = self._criar_triagem(intensidade=3)
        encaminhamento = Encaminhamento.objects.create(
            triagem=triagem,
            recomendacao=Encaminhamento.Recomendacao.CONSULTA,
            descricao='Agendar consulta clinica',
            prazo_recomendado='Ate 24 horas',
        )

        dados = gerar_pre_agendamento(triagem=triagem, encaminhamento=encaminhamento)

        self.assertEqual(dados['status'], PreAgendamento.Status.SUGERIDO)
        self.assertIsNotNone(dados['profissional'])
        self.assertIsNotNone(dados['horario_sugerido'])
        self.assertIn('pre-agendamento sugerido', dados['mensagem'].lower())

    def test_pre_agendamento_emergencia_direta(self):
        triagem = self._criar_triagem(intensidade=5)
        encaminhamento = Encaminhamento.objects.create(
            triagem=triagem,
            recomendacao=Encaminhamento.Recomendacao.EMERGENCIA,
            descricao='Emergencia imediata',
            prazo_recomendado='Imediato',
        )

        dados = gerar_pre_agendamento(triagem=triagem, encaminhamento=encaminhamento)

        self.assertEqual(dados['status'], PreAgendamento.Status.ENCAMINHAMENTO_DIRETO)
        self.assertIsNone(dados['profissional'])
        self.assertIn('emergencia', dados['mensagem'].lower())

    def test_reagendar_sem_slot_real_altera_horario(self):
        triagem = self._criar_triagem(intensidade=3)
        encaminhamento = Encaminhamento.objects.create(
            triagem=triagem,
            recomendacao=Encaminhamento.Recomendacao.CONSULTA,
            descricao='Agendar consulta clinica',
            prazo_recomendado='Ate 24 horas',
        )

        gerar_pre_agendamento(triagem=triagem, encaminhamento=encaminhamento)
        pre = PreAgendamento.objects.get(triagem=triagem, encaminhamento=encaminhamento)
        horario_inicial = pre.horario_sugerido

        dados = reagendar_pre_agendamento(pre)
        pre.refresh_from_db()

        self.assertEqual(dados['status'], PreAgendamento.Status.REAGENDADO)
        self.assertIsNotNone(pre.horario_sugerido)
        self.assertNotEqual(pre.horario_sugerido, horario_inicial)
        self.assertGreater(pre.horario_sugerido, horario_inicial)
