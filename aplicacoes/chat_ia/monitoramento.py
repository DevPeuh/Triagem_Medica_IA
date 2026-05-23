from copy import deepcopy
from django.core.cache import cache
from django.utils.timezone import now

CHAVE_METRICAS_CHAT_IA = 'chat_ia:metricas:v1'


def _metricas_iniciais():
    return {
        'total_requisicoes': 0,
        'sucesso_ia': 0,
        'falhas_ia': 0,
        'timeouts_ia': 0,
        'fallbacks_heuristicos': 0,
        'latencia_total_ms': 0,
        'latencia_maxima_ms': 0,
        'ultima_atualizacao': None,
        'http_total_requisicoes': 0,
        'http_lentas': 0,
        'http_erros': 0,
        'http_latencia_total_ms': 0,
        'http_latencia_maxima_ms': 0,
    }


def _carregar_metricas():
    dados = cache.get(CHAVE_METRICAS_CHAT_IA)
    if not isinstance(dados, dict):
        dados = _metricas_iniciais()
    return dados


def _salvar_metricas(dados):
    dados['ultima_atualizacao'] = now().isoformat()
    cache.set(CHAVE_METRICAS_CHAT_IA, dados, timeout=None)


def registrar_execucao_ia(*, latencia_ms, sucesso, timeout=False, fallback=False):
    dados = _carregar_metricas()
    dados['total_requisicoes'] += 1
    dados['latencia_total_ms'] += max(0, int(latencia_ms))
    dados['latencia_maxima_ms'] = max(dados['latencia_maxima_ms'], max(0, int(latencia_ms)))

    if sucesso:
        dados['sucesso_ia'] += 1
    else:
        dados['falhas_ia'] += 1

    if timeout:
        dados['timeouts_ia'] += 1

    if fallback:
        dados['fallbacks_heuristicos'] += 1

    _salvar_metricas(dados)


def registrar_requisicao_http_chat(*, latencia_ms, status_code, limite_lento_ms):
    dados = _carregar_metricas()
    latencia_int = max(0, int(latencia_ms))

    dados['http_total_requisicoes'] += 1
    dados['http_latencia_total_ms'] += latencia_int
    dados['http_latencia_maxima_ms'] = max(dados['http_latencia_maxima_ms'], latencia_int)

    if latencia_int >= int(limite_lento_ms):
        dados['http_lentas'] += 1

    if int(status_code) >= 400:
        dados['http_erros'] += 1

    _salvar_metricas(dados)


def obter_metricas_chat_ia():
    dados = deepcopy(_carregar_metricas())

    total = max(1, dados['total_requisicoes'])
    http_total = max(1, dados['http_total_requisicoes'])

    dados['taxa_sucesso_ia'] = round((dados['sucesso_ia'] / total) * 100, 2)
    dados['latencia_media_ia_ms'] = round(dados['latencia_total_ms'] / total, 2)

    dados['taxa_http_lentas'] = round((dados['http_lentas'] / http_total) * 100, 2)
    dados['latencia_media_http_ms'] = round(dados['http_latencia_total_ms'] / http_total, 2)

    return dados
