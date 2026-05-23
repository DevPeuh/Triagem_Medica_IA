import logging
import time

from django.conf import settings

from .monitoramento import registrar_requisicao_http_chat

LOGGER = logging.getLogger(__name__)


class TempoRespostaChatIAMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        inicio = time.perf_counter()
        response = self.get_response(request)
        duracao_ms = int((time.perf_counter() - inicio) * 1000)

        response['X-Response-Time-ms'] = str(duracao_ms)

        if request.path.startswith('/api/chat-ia/'):
            limite_lento_ms = max(1000, int(getattr(settings, 'CHAT_IA_SLOW_REQUEST_MS', 12000)))
            registrar_requisicao_http_chat(
                latencia_ms=duracao_ms,
                status_code=response.status_code,
                limite_lento_ms=limite_lento_ms,
            )

            if duracao_ms >= limite_lento_ms:
                LOGGER.warning(
                    'Requisicao lenta no chat IA: path=%s status=%s duracao_ms=%s limite_ms=%s',
                    request.path,
                    response.status_code,
                    duracao_ms,
                    limite_lento_ms,
                )

        return response
