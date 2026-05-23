from rest_framework import serializers

from .models import ClassificacaoRisco


class ClassificacaoRiscoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassificacaoRisco
        fields = '__all__'
        read_only_fields = ['data_classificacao']
