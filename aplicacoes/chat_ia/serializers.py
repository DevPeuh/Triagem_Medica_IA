from rest_framework import serializers


class MensagemChatTriagemSerializer(serializers.Serializer):
    mensagem = serializers.CharField(max_length=1200)
    historico = serializers.ListField(child=serializers.DictField(), required=False, default=list)