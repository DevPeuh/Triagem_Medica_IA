from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from aplicacoes.pacientes.models import Paciente
from aplicacoes.usuarios.models import Usuario


class CadastroPacienteSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(write_only=True, min_length=8)
    confirmar_senha = serializers.CharField(write_only=True, min_length=8)
    nome_completo = serializers.CharField(max_length=200)
    data_nascimento = serializers.DateField(required=False, allow_null=True)
    sexo = serializers.ChoiceField(
        choices=Paciente.Sexo.choices,
        required=False,
        default=Paciente.Sexo.NAO_INFORMADO,
    )
    telefone = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def validate_username(self, value):
        username = value.strip()
        if User.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError('Nome de usuário já está em uso.')
        return username

    def validate_email(self, value):
        email = value.lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError('E-mail já está em uso.')
        if Usuario.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError('E-mail já está em uso.')
        return email

    def validate(self, attrs):
        password = attrs.get('password')
        confirmar_senha = attrs.get('confirmar_senha')
        if password != confirmar_senha:
            raise serializers.ValidationError({'confirmar_senha': 'As senhas não coincidem.'})

        user_temp = User(username=attrs['username'], email=attrs['email'])
        validate_password(password=password, user=user_temp)
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop('confirmar_senha')
        password = validated_data.pop('password')
        nome_completo = validated_data['nome_completo'].strip()
        email = validated_data['email']

        user = User.objects.create_user(
            username=validated_data['username'],
            email=email,
            password=password,
        )

        Usuario.objects.create(
            usuario_auth=user,
            nome_completo=nome_completo,
            email=email,
            perfil=Usuario.Perfil.PACIENTE,
            ativo=True,
        )

        paciente = Paciente.objects.create(
            usuario_auth=user,
            nome_completo=nome_completo,
            email=email,
            data_nascimento=validated_data.get('data_nascimento'),
            sexo=validated_data.get('sexo', Paciente.Sexo.NAO_INFORMADO),
            telefone=validated_data.get('telefone', ''),
        )

        return paciente
