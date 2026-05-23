from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from aplicacoes.encaminhamentos.models import AgendaProfissional
from aplicacoes.usuarios.models import Usuario


class Command(BaseCommand):
    help = 'Cria profissionais e agenda de demonstracao para pre-agendamento da triagem IA.'

    profissionais_demo = [
        {
            'username': 'dra.ana.neuro',
            'email': 'ana.neuro@curala.demo',
            'nome': 'Dra. Ana Neuro',
            'especialidade': Usuario.Especialidade.NEUROLOGIA,
        },
        {
            'username': 'dr.carlos.cardio',
            'email': 'carlos.cardio@curala.demo',
            'nome': 'Dr. Carlos Cardio',
            'especialidade': Usuario.Especialidade.CARDIOLOGIA,
        },
        {
            'username': 'dra.bia.clinica',
            'email': 'bia.clinica@curala.demo',
            'nome': 'Dra. Beatriz Clinica',
            'especialidade': Usuario.Especialidade.CLINICA_GERAL,
        },
    ]

    @transaction.atomic
    def handle(self, *args, **options):
        agora = timezone.now().replace(minute=0, second=0, microsecond=0)
        criados = 0

        for item in self.profissionais_demo:
            auth_user, _ = User.objects.get_or_create(
                username=item['username'],
                defaults={'email': item['email']},
            )
            if not auth_user.has_usable_password():
                auth_user.set_password('SenhaForte@123')
                auth_user.save(update_fields=['password'])

            perfil, _ = Usuario.objects.update_or_create(
                usuario_auth=auth_user,
                defaults={
                    'nome_completo': item['nome'],
                    'email': item['email'],
                    'perfil': Usuario.Perfil.PROFISSIONAL,
                    'especialidade': item['especialidade'],
                    'ativo': True,
                },
            )

            for offset_horas in (1, 2, 4, 24):
                inicio = agora + timedelta(hours=offset_horas)
                fim = inicio + timedelta(minutes=30)
                _, was_created = AgendaProfissional.objects.get_or_create(
                    profissional=perfil,
                    especialidade=item['especialidade'],
                    inicio_atendimento=inicio,
                    defaults={
                        'fim_atendimento': fim,
                        'reservado': False,
                        'ativo': True,
                    },
                )
                criados += int(was_created)

        self.stdout.write(self.style.SUCCESS(f'Agenda demo pronta. Slots criados: {criados}.'))
