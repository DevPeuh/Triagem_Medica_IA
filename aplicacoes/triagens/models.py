from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Triagem(models.Model):
    class Status(models.TextChoices):
        EM_ANDAMENTO = 'em_andamento', 'Em andamento'
        CONCLUIDA = 'concluida', 'Concluída'
        CANCELADA = 'cancelada', 'Cancelada'

    paciente = models.ForeignKey('pacientes.Paciente', on_delete=models.PROTECT, related_name='triagens')
    profissional_responsavel = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        related_name='triagens_realizadas',
        null=True,
        blank=True,
    )
    data_hora_inicio = models.DateTimeField(auto_now_add=True)
    data_hora_fim = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.EM_ANDAMENTO)
    observacoes_gerais = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Triagem'
        verbose_name_plural = 'Triagens'
        ordering = ['-data_hora_inicio']

    def __str__(self):
        return f'Triagem #{self.pk} - {self.paciente.nome_completo}'


class RespostaTriagem(models.Model):
    triagem = models.ForeignKey(Triagem, on_delete=models.CASCADE, related_name='respostas')
    sintoma = models.ForeignKey('sintomas.Sintoma', on_delete=models.PROTECT, related_name='respostas')
    intensidade = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Escala de 1 a 5',
    )
    duracao = models.CharField(max_length=120)
    possui_sinal_alerta = models.BooleanField(default=False)
    observacao = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Resposta de Triagem'
        verbose_name_plural = 'Respostas de Triagem'
        unique_together = ('triagem', 'sintoma')

    def __str__(self):
        return f'{self.triagem} - {self.sintoma.nome}'
