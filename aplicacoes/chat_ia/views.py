import logging
import time

from django.conf import settings
from django.db import transaction
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from aplicacoes.encaminhamentos.interacao_servicos import processar_intencao_agendamento
from aplicacoes.permissoes import obter_perfil_usuario
from aplicacoes.triagens.serializers import TriagemRapidaSerializer, criar_triagem_rapida
from aplicacoes.triagens.servicos import classificar_e_gerar_resultado
from aplicacoes.usuarios.models import Usuario

from .monitoramento import obter_metricas_chat_ia
from .serializers import MensagemChatTriagemSerializer
from .servicos import gerar_resposta_chat_triagem

LOGGER = logging.getLogger(__name__)


def _mensagem_encaminhamento(resultado):
    pre = (resultado or {}).get('pre_agendamento') or {}
    if pre.get('mensagem'):
        return pre['mensagem']

    encaminhamento = (resultado or {}).get('encaminhamento') or {}
    recomendacao = (encaminhamento.get('recomendacao') or '').lower()
    prazo = encaminhamento.get('prazo_recomendado') or ''

    if recomendacao == 'emergencia':
        return 'Encaminhamento: emergencia imediata. Va agora para UPA/Hospital mais proximo ou SAMU 192.'
    if recomendacao == 'urgencia':
        return f'Encaminhamento: urgencia. Procure UPA/pronto atendimento em {prazo or "ate 1 hora"}.'
    if recomendacao == 'consulta':
        return f'Encaminhamento: consulta clinica prioritaria em {prazo or "ate 24 horas"}. Sugestao: primeiro horario disponivel com clinica medica.'
    return 'Encaminhamento: autocuidado orientado e reavaliacao se houver piora.'


class ChatTriagemAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        inicio = time.perf_counter()

        serializer = MensagemChatTriagemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        mensagem = serializer.validated_data['mensagem']

        interacao = processar_intencao_agendamento(request.user, mensagem)
        if interacao is not None:
            return Response(interacao, status=status.HTTP_200_OK)

        dados_chat = gerar_resposta_chat_triagem(
            mensagem=mensagem,
            historico=serializer.validated_data.get('historico', []),
        )

        resposta = {
            'mensagem_ia': dados_chat.get('mensagem_ia', ''),
            'pronto_para_classificar': dados_chat.get('pronto_para_classificar', False),
            'erro_ia_local': dados_chat.get('erro_ia_local', False),
            'meta_ia': dados_chat.get('meta_ia', {}),
        }

        if not dados_chat.get('pronto_para_classificar'):
            return Response(resposta, status=status.HTTP_200_OK)

        perfil = obter_perfil_usuario(request.user)
        if perfil is None:
            resposta['mensagem_ia'] = 'Seu usuario nao possui perfil ativo para continuar a triagem.'
            resposta['pronto_para_classificar'] = False
            return Response(resposta, status=status.HTTP_403_FORBIDDEN)

        payload_triagem = {
            'paciente': dados_chat.get('paciente') or {'nome_completo': 'Paciente'},
            'sintomas': dados_chat.get('sintomas') or [],
            'observacoes_gerais': dados_chat.get('observacoes_gerais', ''),
        }

        profissional = None
        paciente = None

        if perfil in (Usuario.Perfil.ADMINISTRADOR, Usuario.Perfil.PROFISSIONAL):
            profissional = getattr(request.user, 'perfil_sistema', None)
        elif perfil == Usuario.Perfil.PACIENTE:
            paciente = getattr(request.user, 'paciente_perfil', None)
        else:
            return Response({'detalhe': 'Perfil sem permissao para triagem.'}, status=status.HTTP_403_FORBIDDEN)

        with transaction.atomic():
            triagem_serializer = TriagemRapidaSerializer(data=payload_triagem)
            triagem_serializer.is_valid(raise_exception=True)

            triagem = criar_triagem_rapida(
                triagem_serializer.validated_data,
                profissional_responsavel=profissional,
                paciente=paciente,
            )
            resultado = classificar_e_gerar_resultado(triagem)

        resposta['triagem'] = resultado
        resposta['mensagem_encaminhamento'] = _mensagem_encaminhamento(resultado)

        duracao_total_ms = int((time.perf_counter() - inicio) * 1000)
        limite_lento = max(1000, int(getattr(settings, 'CHAT_IA_SLOW_REQUEST_MS', 12000)))
        if duracao_total_ms >= limite_lento:
            LOGGER.warning(
                'Fluxo completo de triagem lento: duracao_ms=%s limite_ms=%s triagem_id=%s',
                duracao_total_ms,
                limite_lento,
                triagem.id,
            )

        return Response(resposta, status=status.HTTP_201_CREATED)


class ChatIAMonitoramentoAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(obter_metricas_chat_ia(), status=status.HTTP_200_OK)
