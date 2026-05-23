from rest_framework import serializers

from .models import AgendaProfissional, Encaminhamento, PreAgendamento


class EncaminhamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Encaminhamento
        fields = '__all__'
        read_only_fields = ['data_geracao']


class AgendaProfissionalSerializer(serializers.ModelSerializer):
    profissional_nome = serializers.CharField(source='profissional.nome_completo', read_only=True)

    class Meta:
        model = AgendaProfissional
        fields = [
            'id',
            'profissional',
            'profissional_nome',
            'especialidade',
            'inicio_atendimento',
            'fim_atendimento',
            'reservado',
            'ativo',
        ]


class PreAgendamentoSerializer(serializers.ModelSerializer):
    profissional_nome = serializers.CharField(source='profissional.nome_completo', read_only=True)

    class Meta:
        model = PreAgendamento
        fields = [
            'id',
            'triagem',
            'encaminhamento',
            'profissional',
            'profissional_nome',
            'especialidade',
            'horario_sugerido',
            'status',
            'mensagem',
            'data_geracao',
            'data_atualizacao',
        ]
        read_only_fields = ['data_geracao', 'data_atualizacao']
