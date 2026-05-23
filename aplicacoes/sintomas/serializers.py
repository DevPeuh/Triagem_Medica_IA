from rest_framework import serializers

from .models import Sintoma


class SintomaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sintoma
        fields = '__all__'
