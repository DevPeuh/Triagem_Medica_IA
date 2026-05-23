from django.db import models


class Sintoma(models.Model):
    nome = models.CharField(max_length=120, unique=True)
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Sintoma'
        verbose_name_plural = 'Sintomas'
        ordering = ['nome']

    def __str__(self):
        return self.nome
