from django.db import models


class ClassificacaoRisco(models.Model):
    class Nivel(models.TextChoices):
        BAIXO = 'baixo', 'Baixo'
        MEDIO = 'medio', 'Médio'
        ALTO = 'alto', 'Alto'
        EMERGENCIA = 'emergencia', 'Emergência'

    triagem = models.OneToOneField('triagens.Triagem', on_delete=models.CASCADE, related_name='classificacao_risco')
    nivel = models.CharField(max_length=20, choices=Nivel.choices)
    pontuacao = models.PositiveSmallIntegerField(default=0)
    justificativa = models.TextField()
    protocolo_versao = models.CharField(max_length=30, default='v1')
    data_classificacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Classificação de Risco'
        verbose_name_plural = 'Classificações de Risco'

    def __str__(self):
        return f'Triagem #{self.triagem_id} - {self.get_nivel_display()}'
