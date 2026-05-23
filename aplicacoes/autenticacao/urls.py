from django.urls import path

from .views import CadastroPacienteAPIView, LoginAPIView, LogoutAPIView, SessaoAPIView

urlpatterns = [
    path('cadastro/', CadastroPacienteAPIView.as_view(), name='cadastro'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path('sessao/', SessaoAPIView.as_view(), name='sessao'),
]
