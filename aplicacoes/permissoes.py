from rest_framework import permissions

from aplicacoes.usuarios.models import Usuario


def obter_perfil_usuario(user):
    if not user or not user.is_authenticated:
        return None

    if user.is_superuser:
        return Usuario.Perfil.ADMINISTRADOR

    perfil_sistema = getattr(user, 'perfil_sistema', None)
    if not perfil_sistema or not perfil_sistema.ativo:
        return None

    return perfil_sistema.perfil


class IsAdministrador(permissions.BasePermission):
    def has_permission(self, request, view):
        return obter_perfil_usuario(request.user) == Usuario.Perfil.ADMINISTRADOR


class IsAdministradorOuProfissional(permissions.BasePermission):
    def has_permission(self, request, view):
        perfil = obter_perfil_usuario(request.user)
        return perfil in (Usuario.Perfil.ADMINISTRADOR, Usuario.Perfil.PROFISSIONAL)
