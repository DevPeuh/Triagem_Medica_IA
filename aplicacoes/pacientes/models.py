from django.conf import settings
from django.db import models


class Paciente(models.Model):
    class Sexo(models.TextChoices):
        FEMININO = 'feminino', 'Feminino'
        MASCULINO = 'masculino', 'Masculino'
        OUTRO = 'outro', 'Outro'
        NAO_INFORMADO = 'nao_informado', 'Não informado'

    usuario_auth = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='paciente_perfil',
        null=True,
        blank=True,
    )
    nome_completo = models.CharField(max_length=200)
    data_nascimento = models.DateField(null=True, blank=True)
    sexo = models.CharField(max_length=20, choices=Sexo.choices, default=Sexo.NAO_INFORMADO)
    cpf = models.CharField(max_length=14, unique=True, null=True, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    endereco = models.CharField(max_length=255, blank=True)
    alergias = models.TextField(blank=True)
    comorbidades = models.TextField(blank=True)
    medicamentos_em_uso = models.TextField(blank=True)
    contato_emergencia_nome = models.CharField(max_length=200, blank=True)
    contato_emergencia_telefone = models.CharField(max_length=20, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'
        ordering = ['nome_completo']

    def __str__(self):
        return self.nome_completo
