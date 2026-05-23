from django.contrib import admin

from .models import AgendaProfissional, Encaminhamento, PreAgendamento

admin.site.register(Encaminhamento)
admin.site.register(AgendaProfissional)
admin.site.register(PreAgendamento)
