from django.contrib import admin
from django.urls import include, path

from configuracao.views import cadastro, chat_teste, home, status_api

urlpatterns = [
    path('', home, name='home'),
    path('cadastro/', cadastro, name='cadastro'),
    path('admin/', admin.site.urls),
    path('api/', include('configuracao.rotas_api')),
    path('api/status/', status_api, name='status-api'),
    path('chat-teste/', chat_teste, name='chat-teste'),
]