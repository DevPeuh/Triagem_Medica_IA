from django.test import TestCase

from aplicacoes.classificacao_risco.servicos import classificar_triagem
from aplicacoes.pacientes.models import Paciente
from aplicacoes.sintomas.models import Sintoma
from aplicacoes.triagens.models import RespostaTriagem, Triagem


class ClassificacaoRiscoServiceTests(TestCase):
    def setUp(self):
        self.paciente = Paciente.objects.create(nome_completo='Paciente Teste')

    def test_classifica_como_baixo_quando_sem_criterios_criticos(self):
        triagem = Triagem.objects.create(paciente=self.paciente)
        sintoma = Sintoma.objects.create(nome='Dor de cabeça leve')
        RespostaTriagem.objects.create(
            triagem=triagem,
            sintoma=sintoma,
            intensidade=2,
            duracao='1 dia',
            possui_sinal_alerta=False,
            observacao='Dor de cabeça leve desde ontem.',
        )

        resultado = classificar_triagem(triagem)

        self.assertEqual(resultado.nivel, 'baixo')
        self.assertEqual(resultado.recomendacao, 'autocuidado')

    def test_classifica_como_emergencia_com_sinais_criticos_sem_sinais_vitais(self):
        triagem = Triagem.objects.create(paciente=self.paciente)
        sintoma_1 = Sintoma.objects.create(nome='Aperto no peito muito forte')
        sintoma_2 = Sintoma.objects.create(nome='Dificuldade para respirar')

        RespostaTriagem.objects.create(
            triagem=triagem,
            sintoma=sintoma_1,
            intensidade=5,
            duracao='2 horas',
            possui_sinal_alerta=True,
            observacao='Aperto no peito piorando rapidamente.',
        )
        RespostaTriagem.objects.create(
            triagem=triagem,
            sintoma=sintoma_2,
            intensidade=5,
            duracao='2 horas',
            possui_sinal_alerta=True,
            observacao='Está ofegante e com muita falta de ar.',
        )

        resultado = classificar_triagem(triagem)

        self.assertEqual(resultado.nivel, 'emergencia')
        self.assertEqual(resultado.recomendacao, 'emergencia')
        self.assertGreaterEqual(resultado.pontuacao, 10)