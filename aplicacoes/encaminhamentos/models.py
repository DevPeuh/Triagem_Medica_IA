from django.db import models

from aplicacoes.usuarios.models import Usuario


class Encaminhamento(models.Model):
    class Recomendacao(models.TextChoices):
        AUTOCUIDADO = 'autocuidado', 'Autocuidado'
        CONSULTA = 'consulta', 'Consulta agendada'
        URGENCIA = 'urgencia', 'Buscar urgencia'
        EMERGENCIA = 'emergencia', 'Acionar emergencia'

    triagem = models.OneToOneField('triagens.Triagem', on_delete=models.CASCADE, related_name='encaminhamento')
    recomendacao = models.CharField(max_length=20, choices=Recomendacao.choices)
    descricao = models.TextField()
    prazo_recomendado = models.CharField(max_length=120, blank=True)
    data_geracao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Encaminhamento'
        verbose_name_plural = 'Encaminhamentos'

    def __str__(self):
        return f'Encaminhamento da triagem #{self.triagem_id}'


class AgendaProfissional(models.Model):
    profissional = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.CASCADE,
        related_name='agenda_profissional',
    )
    especialidade = models.CharField(max_length=32, choices=Usuario.Especialidade.choices)
    inicio_atendimento = models.DateTimeField()
    fim_atendimento = models.DateTimeField()
    reservado = models.BooleanField(default=False)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Agenda de Profissional'
        verbose_name_plural = 'Agendas de Profissionais'
        ordering = ['inicio_atendimento']

    def __str__(self):
        return f'{self.profissional.nome_completo} - {self.especialidade} - {self.inicio_atendimento}'


class PreAgendamento(models.Model):
    class Status(models.TextChoices):
        SUGERIDO = 'sugerido', 'Sugerido'
        CONFIRMADO = 'confirmado', 'Confirmado'
        REAGENDADO = 'reagendado', 'Reagendado'
        CANCELADO = 'cancelado', 'Cancelado'
        SEM_VAGA = 'sem_vaga', 'Sem vaga'
        ENCAMINHAMENTO_DIRETO = 'encaminhamento_direto', 'Encaminhamento direto'

    triagem = models.OneToOneField('triagens.Triagem', on_delete=models.CASCADE, related_name='pre_agendamento')
    encaminhamento = models.OneToOneField('encaminhamentos.Encaminhamento', on_delete=models.CASCADE, related_name='pre_agendamento')
    agenda_slot = models.ForeignKey(
        'encaminhamentos.AgendaProfissional',
        on_delete=models.SET_NULL,
        related_name='pre_agendamentos',
        null=True,
        blank=True,
    )
    profissional = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        related_name='pre_agendamentos_sugeridos',
        null=True,
        blank=True,
    )
    especialidade = models.CharField(max_length=32, blank=True, default='')
    horario_sugerido = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.SEM_VAGA)
    mensagem = models.TextField(blank=True, default='')
    data_geracao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Pre-agendamento'
        verbose_name_plural = 'Pre-agendamentos'
        ordering = ['-data_geracao']

    def __str__(self):
        return f'Pre-agendamento triagem #{self.triagem_id} - {self.status}'
