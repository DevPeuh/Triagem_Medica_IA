from django.db import transaction
from rest_framework import serializers

from aplicacoes.pacientes.models import Paciente
from aplicacoes.sintomas.models import Sintoma

from .models import RespostaTriagem, Triagem


class RespostaTriagemSerializer(serializers.ModelSerializer):
    class Meta:
        model = RespostaTriagem
        fields = '__all__'


class TriagemSerializer(serializers.ModelSerializer):
    respostas = RespostaTriagemSerializer(many=True, required=False)

    class Meta:
        model = Triagem
        fields = [
            'id',
            'paciente',
            'profissional_responsavel',
            'data_hora_inicio',
            'data_hora_fim',
            'status',
            'observacoes_gerais',
            'respostas',
        ]
        read_only_fields = ['data_hora_inicio']

    @transaction.atomic
    def create(self, validated_data):
        respostas_data = validated_data.pop('respostas', [])
        triagem = Triagem.objects.create(**validated_data)

        for resposta in respostas_data:
            RespostaTriagem.objects.create(triagem=triagem, **resposta)

        return triagem

    @transaction.atomic
    def update(self, instance, validated_data):
        respostas_data = validated_data.pop('respostas', None)

        for atributo, valor in validated_data.items():
            setattr(instance, atributo, valor)
        instance.save()

        if respostas_data is not None:
            instance.respostas.all().delete()
            for resposta in respostas_data:
                RespostaTriagem.objects.create(triagem=instance, **resposta)

        return instance


class PacienteRapidoSerializer(serializers.Serializer):
    nome_completo = serializers.CharField(max_length=200)
    data_nascimento = serializers.DateField(required=False, allow_null=True)
    sexo = serializers.ChoiceField(
        choices=Paciente.Sexo.choices,
        required=False,
        default=Paciente.Sexo.NAO_INFORMADO,
    )
    telefone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)


class SintomaRapidoSerializer(serializers.Serializer):
    descricao = serializers.CharField(max_length=500)
    intensidade = serializers.IntegerField(min_value=1, max_value=5, required=False, default=3)
    duracao = serializers.CharField(max_length=120, required=False, allow_blank=True, default='')
    possui_sinal_alerta = serializers.BooleanField(required=False, default=False)


class TriagemRapidaSerializer(serializers.Serializer):
    paciente = PacienteRapidoSerializer(required=False)
    sintomas = SintomaRapidoSerializer(many=True, min_length=1)
    observacoes_gerais = serializers.CharField(required=False, allow_blank=True, default='')


def _nome_sintoma_para_catalogo(descricao):
    nome = ' '.join(descricao.split()).strip()
    if not nome:
        nome = 'Sintoma informado'
    if len(nome) > 120:
        nome = nome[:117].rstrip() + '...'
    return nome


@transaction.atomic
def criar_triagem_rapida(validated_data, profissional_responsavel=None, paciente=None):
    paciente_data = validated_data.get('paciente')
    sintomas_data = validated_data['sintomas']

    if paciente is None:
        if not paciente_data:
            raise serializers.ValidationError({'paciente': 'Dados do paciente são obrigatórios.'})
        paciente = Paciente.objects.create(**paciente_data)
    elif paciente_data:
        campos_editaveis = ['nome_completo', 'data_nascimento', 'sexo', 'telefone', 'email']
        for campo in campos_editaveis:
            if campo in paciente_data:
                setattr(paciente, campo, paciente_data[campo])
        paciente.save(update_fields=[c for c in campos_editaveis if c in paciente_data])

    triagem = Triagem.objects.create(
        paciente=paciente,
        profissional_responsavel=profissional_responsavel,
        observacoes_gerais=validated_data.get('observacoes_gerais', ''),
    )

    for sintoma_data in sintomas_data:
        descricao = sintoma_data['descricao']
        nome_sintoma = _nome_sintoma_para_catalogo(descricao)

        sintoma, criado = Sintoma.objects.get_or_create(
            nome=nome_sintoma,
            defaults={'descricao': descricao},
        )

        if not criado and not sintoma.descricao:
            sintoma.descricao = descricao
            sintoma.save(update_fields=['descricao'])

        RespostaTriagem.objects.create(
            triagem=triagem,
            sintoma=sintoma,
            intensidade=sintoma_data.get('intensidade', 3),
            duracao=sintoma_data.get('duracao', ''),
            possui_sinal_alerta=sintoma_data.get('possui_sinal_alerta', False),
            observacao=descricao,
        )

    return triagem
