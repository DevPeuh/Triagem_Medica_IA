from django.urls import path

from .views import ChatIAMonitoramentoAPIView, ChatTriagemAPIView

urlpatterns = [
    path('triagem/', ChatTriagemAPIView.as_view(), name='chat-ia-triagem'),
    path('monitoramento/', ChatIAMonitoramentoAPIView.as_view(), name='chat-ia-monitoramento'),
]
