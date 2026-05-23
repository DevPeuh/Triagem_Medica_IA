from django.utils import timezone

from aplicacoes.classificacao_risco.models import ClassificacaoRisco
from aplicacoes.classificacao_risco.servicos import classificar_triagem
from aplicacoes.encaminhamentos.agendamento_servicos import gerar_pre_agendamento
from aplicacoes.encaminhamentos.models import Encaminhamento

from .models import Triagem


def classificar_e_gerar_resultado(triagem):
    resultado = classificar_triagem(triagem)

    classificacao, _ = ClassificacaoRisco.objects.update_or_create(
        triagem=triagem,
        defaults={
            'nivel': resultado.nivel,
            'pontuacao': resultado.pontuacao,
            'justificativa': resultado.justificativa,
            'protocolo_versao': 'v2',
        },
    )

    encaminhamento, _ = Encaminhamento.objects.update_or_create(
        triagem=triagem,
        defaults={
            'recomendacao': resultado.recomendacao,
            'descricao': resultado.descricao_recomendacao,
            'prazo_recomendado': resultado.prazo_recomendado,
        },
    )

    pre_agendamento = gerar_pre_agendamento(triagem=triagem, encaminhamento=encaminhamento)

    if triagem.status != Triagem.Status.CONCLUIDA:
        triagem.status = Triagem.Status.CONCLUIDA
        triagem.data_hora_fim = timezone.now()
        triagem.save(update_fields=['status', 'data_hora_fim'])

    return {
        'triagem_id': triagem.id,
        'classificacao': {
            'nivel': classificacao.nivel,
            'pontuacao': classificacao.pontuacao,
            'justificativa': classificacao.justificativa,
        },
        'encaminhamento': {
            'recomendacao': encaminhamento.recomendacao,
            'descricao': encaminhamento.descricao,
            'prazo_recomendado': encaminhamento.prazo_recomendado,
        },
        'pre_agendamento': pre_agendamento,
        'orientacao_paciente': resultado.orientacao_paciente,
        'proximos_passos': resultado.proximos_passos,
    }
