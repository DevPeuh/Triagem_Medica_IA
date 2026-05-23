from django.conf import settings
from django.db import models


class Usuario(models.Model):
    class Perfil(models.TextChoices):
        ADMINISTRADOR = 'administrador', 'Administrador'
        PROFISSIONAL = 'profissional', 'Profissional de Saude'
        PACIENTE = 'paciente', 'Paciente'

    class Especialidade(models.TextChoices):
        CLINICA_GERAL = 'clinica_geral', 'Clinica Geral'
        CARDIOLOGIA = 'cardiologia', 'Cardiologia'
        NEUROLOGIA = 'neurologia', 'Neurologia'
        PNEUMOLOGIA = 'pneumologia', 'Pneumologia'
        GASTROENTEROLOGIA = 'gastroenterologia', 'Gastroenterologia'

    usuario_auth = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil_sistema',
        null=True,
        blank=True,
    )
    nome_completo = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    perfil = models.CharField(max_length=20, choices=Perfil.choices)
    especialidade = models.CharField(
        max_length=32,
        choices=Especialidade.choices,
        blank=True,
        default='',
        help_text='Aplicavel principalmente para perfis profissionais.',
    )
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['nome_completo']

    def __str__(self):
        return f'{self.nome_completo} ({self.get_perfil_display()})'

    def save(self, *args, **kwargs):
        self.email = self.email.lower().strip()
        super().save(*args, **kwargs)
