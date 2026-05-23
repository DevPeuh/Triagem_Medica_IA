from rest_framework import serializers

from .models import Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = [
            'id',
            'usuario_auth',
            'nome_completo',
            'email',
            'perfil',
            'especialidade',
            'ativo',
            'data_criacao',
            'data_atualizacao',
        ]
        read_only_fields = ['data_criacao', 'data_atualizacao']
