from django.urls import include, path

urlpatterns = [
    path('autenticacao/', include('aplicacoes.autenticacao.urls')),
    path('usuarios/', include('aplicacoes.usuarios.urls')),
    path('pacientes/', include('aplicacoes.pacientes.urls')),
    path('triagens/', include('aplicacoes.triagens.urls')),
    path('encaminhamentos/', include('aplicacoes.encaminhamentos.urls')),
    path('sintomas/', include('aplicacoes.sintomas.urls')),
    path('classificacao-risco/', include('aplicacoes.classificacao_risco.urls')),
    path('chat-ia/', include('aplicacoes.chat_ia.urls')),
]
