import unicodedata

from django.db import transaction

from .agendamento_servicos import (
    cancelar_pre_agendamento,
    confirmar_pre_agendamento,
    reagendar_pre_agendamento,
)
from .models import PreAgendamento


def _normalizar(texto):
    base = unicodedata.normalize('NFKD', texto or '')
    base = ''.join(c for c in base if not unicodedata.combining(c))
    return base.lower().strip()


def detectar_intencao_agendamento(mensagem):
    texto = _normalizar(mensagem)

    termos_reagendar = ('reagendar', 'remarcar', 'outro horario', 'trocar horario', 'mudar horario')
    termos_cancelar = ('cancelar', 'desmarcar', 'nao quero mais', 'nao vou')
    termos_confirmar = ('confirmar', 'confirmo', 'aceito', 'ok', 'pode marcar', 'fechar agendamento')

    if any(t in texto for t in termos_reagendar):
        return 'reagendar'
    if any(t in texto for t in termos_cancelar):
        return 'cancelar'
    if any(t in texto for t in termos_confirmar):
        return 'confirmar'

    return None


def _obter_mais_recente_do_paciente(user):
    return (
        PreAgendamento.objects.select_related('triagem__paciente', 'profissional', 'agenda_slot')
        .filter(triagem__paciente__usuario_auth=user)
        .order_by('-data_geracao')
        .first()
    )


@transaction.atomic
def processar_intencao_agendamento(user, mensagem):
    intencao = detectar_intencao_agendamento(mensagem)
    if intencao is None:
        return None

    pre = _obter_mais_recente_do_paciente(user)
    if pre is None:
        return {
            'mensagem_ia': 'Nao encontrei pre-agendamento ativo para sua conta ainda.',
            'pronto_para_classificar': False,
            'erro_ia_local': False,
            'meta_ia': {'origem': 'pre_agendamento', 'acao': intencao},
            'pre_agendamento': None,
        }

    if intencao == 'confirmar':
        dados = confirmar_pre_agendamento(pre)
    elif intencao == 'cancelar':
        dados = cancelar_pre_agendamento(pre)
    else:
        dados = reagendar_pre_agendamento(pre)

    return {
        'mensagem_ia': dados.get('mensagem', 'Atualizacao de agendamento concluida.'),
        'pronto_para_classificar': False,
        'erro_ia_local': False,
        'meta_ia': {'origem': 'pre_agendamento', 'acao': intencao},
        'pre_agendamento': dados,
    }
