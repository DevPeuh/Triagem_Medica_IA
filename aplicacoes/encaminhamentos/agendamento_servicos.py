from datetime import timedelta

from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from aplicacoes.usuarios.models import Usuario
from .models import AgendaProfissional, Encaminhamento, PreAgendamento


def _normalizar(valor):
    return (valor or '').strip().lower()


def _inferir_especialidade(triagem):
    texto = ' '.join(
        [
            ' '.join([
                _normalizar(resposta.sintoma.nome),
                _normalizar(resposta.observacao),
                _normalizar(resposta.duracao),
            ])
            for resposta in triagem.respostas.select_related('sintoma').all()
        ]
    )

    if any(t in texto for t in ('peito', 'cardi', 'palpitacao')):
        return 'cardiologia'
    if any(t in texto for t in ('cabeca', 'enxaqueca', 'tontura', 'desmaio')):
        return 'neurologia'
    if any(t in texto for t in ('falta de ar', 'respirar', 'tosse')):
        return 'pneumologia'
    if any(t in texto for t in ('barriga', 'abdominal', 'vomito', 'diarreia')):
        return 'gastroenterologia'
    return 'clinica_geral'


def selecionar_slot(especialidade, janela_horas=None, excluir_slot_id=None):
    agora = timezone.now()

    base = (
        AgendaProfissional.objects.select_related('profissional')
        .filter(
            ativo=True,
            reservado=False,
            inicio_atendimento__gte=agora,
            profissional__ativo=True,
            profissional__perfil='profissional',
        )
        .order_by('inicio_atendimento')
    )

    if excluir_slot_id:
        base = base.exclude(id=excluir_slot_id)

    if janela_horas is not None:
        base = base.filter(inicio_atendimento__lte=agora + timedelta(hours=janela_horas))

    slot = base.filter(especialidade=especialidade).first()
    if slot is None and especialidade != 'clinica_geral':
        slot = base.filter(especialidade='clinica_geral').first()
    return slot


def _dados_agendamento(pre_agendamento):
    profissional = None
    if pre_agendamento.profissional_id:
        profissional = {
            'id': pre_agendamento.profissional_id,
            'nome_completo': pre_agendamento.profissional.nome_completo,
            'email': pre_agendamento.profissional.email,
            'especialidade': pre_agendamento.profissional.especialidade,
        }

    return {
        'status': pre_agendamento.status,
        'especialidade': pre_agendamento.especialidade,
        'horario_sugerido': pre_agendamento.horario_sugerido.isoformat() if pre_agendamento.horario_sugerido else None,
        'profissional': profissional,
        'mensagem': pre_agendamento.mensagem,
    }


def _selecionar_profissional_ativo(especialidade):
    base = Usuario.objects.filter(
        ativo=True,
        perfil=Usuario.Perfil.PROFISSIONAL,
    ).order_by('nome_completo')

    profissional = base.filter(especialidade=especialidade).first()
    if profissional is None and especialidade != Usuario.Especialidade.CLINICA_GERAL:
        profissional = base.filter(especialidade=Usuario.Especialidade.CLINICA_GERAL).first()
    if profissional is None:
        profissional = base.first()
    return profissional


def _obter_ou_criar_profissional_demo(especialidade):
    profissional = _selecionar_profissional_ativo(especialidade)
    if profissional:
        return profissional

    especialidade = especialidade or Usuario.Especialidade.CLINICA_GERAL
    nomes_demo = {
        Usuario.Especialidade.CARDIOLOGIA: 'Dr. Demo Cardio',
        Usuario.Especialidade.NEUROLOGIA: 'Dra. Demo Neuro',
        Usuario.Especialidade.PNEUMOLOGIA: 'Dr. Demo Pneumo',
        Usuario.Especialidade.GASTROENTEROLOGIA: 'Dra. Demo Gastro',
        Usuario.Especialidade.CLINICA_GERAL: 'Dra. Demo Clinica',
    }
    nome = nomes_demo.get(especialidade, 'Dra. Demo Clinica')
    username = f'demo.{especialidade}'
    email = f'{username}@curala.demo'

    auth_user, _ = User.objects.get_or_create(
        username=username,
        defaults={'email': email},
    )
    if not auth_user.has_usable_password():
        auth_user.set_password('SenhaForte@123')
        auth_user.save(update_fields=['password'])

    profissional, _ = Usuario.objects.update_or_create(
        usuario_auth=auth_user,
        defaults={
            'nome_completo': nome,
            'email': email,
            'perfil': Usuario.Perfil.PROFISSIONAL,
            'especialidade': especialidade,
            'ativo': True,
        },
    )
    return profissional


def _proximo_horario_simulado(recomendacao, horario_anterior=None):
    deslocamento_horas = 1 if recomendacao == Encaminhamento.Recomendacao.URGENCIA else 4
    horario = timezone.localtime(timezone.now()) + timedelta(hours=deslocamento_horas)
    horario = horario.replace(minute=0, second=0, microsecond=0)

    if horario_anterior is None:
        return horario

    incremento_horas = 1 if recomendacao == Encaminhamento.Recomendacao.URGENCIA else 2
    proximo_minimo = timezone.localtime(horario_anterior) + timedelta(hours=incremento_horas)
    proximo_minimo = proximo_minimo.replace(minute=0, second=0, microsecond=0)
    if horario <= proximo_minimo:
        horario = proximo_minimo
    return horario


def _aplicar_agendamento_simulado(pre_agendamento, especialidade, recomendacao, status, horario_anterior=None):
    profissional = _obter_ou_criar_profissional_demo(especialidade)
    especialidade_final = profissional.especialidade or especialidade or Usuario.Especialidade.CLINICA_GERAL
    horario = _proximo_horario_simulado(recomendacao, horario_anterior=horario_anterior)
    horario_local = timezone.localtime(horario).strftime('%d/%m/%Y %H:%M')
    mensagem = (
        f'Pre-agendamento sugerido com {profissional.nome_completo} '
        f'({profissional.get_especialidade_display()}) em {horario_local}.'
    )

    pre_agendamento.agenda_slot = None
    pre_agendamento.profissional = profissional
    pre_agendamento.especialidade = especialidade_final
    pre_agendamento.horario_sugerido = horario
    pre_agendamento.status = status
    pre_agendamento.mensagem = mensagem
    pre_agendamento.save(
        update_fields=[
            'agenda_slot',
            'profissional',
            'especialidade',
            'horario_sugerido',
            'status',
            'mensagem',
            'data_atualizacao',
        ]
    )


def _liberar_slot(pre_agendamento):
    slot = pre_agendamento.agenda_slot
    if slot is None:
        return
    if slot.reservado:
        slot.reservado = False
        slot.save(update_fields=['reservado'])


def _reservar_slot(pre_agendamento, slot, status):
    slot.reservado = True
    slot.save(update_fields=['reservado'])

    horario_local = timezone.localtime(slot.inicio_atendimento).strftime('%d/%m/%Y %H:%M')
    mensagem = (
        f'Pre-agendamento sugerido com {slot.profissional.nome_completo} '
        f'({slot.get_especialidade_display()}) em {horario_local}.'
    )

    pre_agendamento.agenda_slot = slot
    pre_agendamento.profissional = slot.profissional
    pre_agendamento.especialidade = slot.especialidade
    pre_agendamento.horario_sugerido = slot.inicio_atendimento
    pre_agendamento.status = status
    pre_agendamento.mensagem = mensagem
    pre_agendamento.save(
        update_fields=[
            'agenda_slot',
            'profissional',
            'especialidade',
            'horario_sugerido',
            'status',
            'mensagem',
            'data_atualizacao',
        ]
    )


@transaction.atomic
def gerar_pre_agendamento(triagem, encaminhamento):
    recomendacao = encaminhamento.recomendacao

    if recomendacao in {Encaminhamento.Recomendacao.EMERGENCIA, Encaminhamento.Recomendacao.AUTOCUIDADO}:
        mensagem = (
            'Encaminhamento imediato para emergencia. Procure UPA/Hospital ou SAMU 192.'
            if recomendacao == Encaminhamento.Recomendacao.EMERGENCIA
            else 'Sem necessidade de agendamento imediato. Reavalie se houver piora.'
        )
        pre, _ = PreAgendamento.objects.update_or_create(
            triagem=triagem,
            encaminhamento=encaminhamento,
            defaults={
                'agenda_slot': None,
                'profissional': None,
                'especialidade': '',
                'horario_sugerido': None,
                'status': PreAgendamento.Status.ENCAMINHAMENTO_DIRETO,
                'mensagem': mensagem,
            },
        )
        return _dados_agendamento(pre)

    especialidade = _inferir_especialidade(triagem)

    janela_horas = 24
    if recomendacao == Encaminhamento.Recomendacao.URGENCIA:
        janela_horas = 2

    slot = selecionar_slot(especialidade=especialidade, janela_horas=janela_horas)
    if slot is None:
        slot = selecionar_slot(especialidade=especialidade, janela_horas=None)

    if slot is None:
        pre, _ = PreAgendamento.objects.get_or_create(
            triagem=triagem,
            encaminhamento=encaminhamento,
            defaults={
                'agenda_slot': None,
                'profissional': None,
                'especialidade': especialidade,
                'horario_sugerido': None,
                'status': PreAgendamento.Status.SEM_VAGA,
                'mensagem': '',
            },
        )
        if pre.agenda_slot_id:
            _liberar_slot(pre)
        _aplicar_agendamento_simulado(
            pre_agendamento=pre,
            especialidade=especialidade,
            recomendacao=recomendacao,
            status=PreAgendamento.Status.SUGERIDO,
        )
        return _dados_agendamento(pre)

    pre, _ = PreAgendamento.objects.get_or_create(
        triagem=triagem,
        encaminhamento=encaminhamento,
        defaults={
            'agenda_slot': None,
            'profissional': None,
            'especialidade': especialidade,
            'horario_sugerido': None,
            'status': PreAgendamento.Status.SEM_VAGA,
            'mensagem': '',
        },
    )

    if pre.agenda_slot_id and pre.agenda_slot_id != slot.id:
        _liberar_slot(pre)

    _reservar_slot(pre, slot, status=PreAgendamento.Status.SUGERIDO)
    return _dados_agendamento(pre)


@transaction.atomic
def confirmar_pre_agendamento(pre_agendamento):
    if pre_agendamento.status == PreAgendamento.Status.CANCELADO:
        pre_agendamento.mensagem = 'Esse pre-agendamento ja foi cancelado. Digite "reagendar" para nova sugestao.'
        pre_agendamento.save(update_fields=['mensagem', 'data_atualizacao'])
        return _dados_agendamento(pre_agendamento)

    if pre_agendamento.status in {PreAgendamento.Status.SEM_VAGA, PreAgendamento.Status.ENCAMINHAMENTO_DIRETO}:
        return _dados_agendamento(pre_agendamento)

    pre_agendamento.status = PreAgendamento.Status.CONFIRMADO
    if pre_agendamento.agenda_slot and not pre_agendamento.agenda_slot.reservado:
        pre_agendamento.agenda_slot.reservado = True
        pre_agendamento.agenda_slot.save(update_fields=['reservado'])

    horario = timezone.localtime(pre_agendamento.horario_sugerido).strftime('%d/%m/%Y %H:%M') if pre_agendamento.horario_sugerido else 'a definir'
    nome = pre_agendamento.profissional.nome_completo if pre_agendamento.profissional else 'profissional da equipe'
    pre_agendamento.mensagem = f'Pre-agendamento confirmado com {nome} em {horario}.'
    pre_agendamento.save(update_fields=['status', 'mensagem', 'data_atualizacao'])
    return _dados_agendamento(pre_agendamento)


@transaction.atomic
def cancelar_pre_agendamento(pre_agendamento):
    if pre_agendamento.status == PreAgendamento.Status.CANCELADO:
        return _dados_agendamento(pre_agendamento)

    _liberar_slot(pre_agendamento)

    pre_agendamento.status = PreAgendamento.Status.CANCELADO
    pre_agendamento.mensagem = 'Pre-agendamento cancelado. Se quiser nova sugestao, digite "reagendar".'
    pre_agendamento.agenda_slot = None
    pre_agendamento.save(update_fields=['status', 'mensagem', 'agenda_slot', 'data_atualizacao'])
    return _dados_agendamento(pre_agendamento)


@transaction.atomic
def reagendar_pre_agendamento(pre_agendamento):
    especialidade = pre_agendamento.especialidade or 'clinica_geral'
    slot_atual_id = pre_agendamento.agenda_slot_id
    horario_anterior = pre_agendamento.horario_sugerido

    _liberar_slot(pre_agendamento)

    novo_slot = selecionar_slot(especialidade=especialidade, janela_horas=None, excluir_slot_id=slot_atual_id)
    if novo_slot is None:
        _aplicar_agendamento_simulado(
            pre_agendamento=pre_agendamento,
            especialidade=especialidade,
            recomendacao=pre_agendamento.encaminhamento.recomendacao,
            status=PreAgendamento.Status.REAGENDADO,
            horario_anterior=horario_anterior,
        )
        return _dados_agendamento(pre_agendamento)

    _reservar_slot(pre_agendamento, novo_slot, status=PreAgendamento.Status.REAGENDADO)
    return _dados_agendamento(pre_agendamento)
