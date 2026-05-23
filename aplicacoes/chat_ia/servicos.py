import json
import logging
import re
import socket
import time
from urllib import error, request

from django.conf import settings

from .monitoramento import registrar_execucao_ia

LOGGER = logging.getLogger(__name__)

PROMPT_SISTEMA_TRIAGEM = '''Voce e um assistente de triagem inicial.
Seja objetivo, use frases curtas e pergunte apenas o minimo necessario.
Nao forneca diagnostico definitivo.
Se houver sinal de alerta, oriente urgencia imediatamente.

Responda SOMENTE JSON valido neste formato:
{
  "mensagem_ia": "texto curto para o paciente",
  "pronto_para_classificar": false,
  "paciente": {
    "nome_completo": "",
    "data_nascimento": null,
    "sexo": "nao_informado",
    "telefone": "",
    "email": ""
  },
  "sintomas": [
    {
      "descricao": "",
      "intensidade": 3,
      "duracao": "",
      "possui_sinal_alerta": false
    }
  ],
  "observacoes_gerais": ""
}
'''

TERMO_ALERTA = (
    'dor no peito',
    'falta de ar',
    'nao consigo respirar',
    'desmaio',
    'convuls',
    'sangramento intenso',
    'vomito com sangue',
    'fraqueza de um lado',
    'fala enrolada',
    'confus',
    'pior dor da vida',
    'dor muito forte',
    'rigidez na nuca',
    'febre alta',
)

TERMO_SINTOMA = (
    'dor',
    'febre',
    'vomit',
    'nause',
    'enjoo',
    'tontura',
    'falta de ar',
    'tosse',
    'diarre',
    'fraqueza',
    'cansaco',
    'desmaio',
    'sangue',
    'cabeca',
    'barriga',
    'peito',
    'garganta',
)

PERGUNTA_INTENSIDADE = 'De 1 a 5, qual a intensidade da dor agora?'
PERGUNTA_DURACAO = 'Ha quanto tempo comecou? (ex.: 2 horas, 3 dias)'
PERGUNTA_ALERTA = 'Tem falta de ar, desmaio, confusao, dor no peito, febre alta ou vomito continuo? (sim/nao)'


def _normalizar_texto(valor):
    return (valor or '').strip().lower()


def _resposta_ia_indisponivel(mensagem=None, duracao_ms=0, tentativas=1):
    return {
        'mensagem_ia': mensagem or 'Nao consegui acessar a IA local agora. Tente novamente em alguns segundos.',
        'pronto_para_classificar': False,
        'paciente': {},
        'sintomas': [],
        'observacoes_gerais': '',
        'erro_ia_local': True,
        'meta_ia': {
            'duracao_ms': int(max(0, duracao_ms)),
            'tentativas': int(max(1, tentativas)),
            'origem': 'indisponivel',
        },
    }


def _extrair_json(texto):
    texto = (texto or '').strip()
    if texto.startswith('```'):
        texto = texto.strip('`')
        if '\n' in texto:
            texto = texto.split('\n', 1)[1]
    inicio = texto.find('{')
    fim = texto.rfind('}')
    if inicio == -1 or fim == -1 or fim <= inicio:
        raise ValueError('Resposta sem JSON valido.')
    return json.loads(texto[inicio:fim + 1])


def _limpar_historico(historico):
    itens = []
    limite = max(0, int(getattr(settings, 'OLLAMA_MAX_HISTORY_MESSAGES', 3)))
    max_chars = max(120, int(getattr(settings, 'OLLAMA_MAX_INPUT_CHARS', 700)))
    for item in historico[-limite:] if limite else []:
        role = item.get('role')
        content = item.get('content')
        if role in {'user', 'assistant'} and isinstance(content, str) and content.strip():
            itens.append({'role': role, 'content': content.strip()[:max_chars]})
    return itens


def _normalizar_saida(payload):
    paciente = payload.get('paciente') or {}
    sintomas = payload.get('sintomas') or []

    sintomas_normalizados = []
    for sintoma in sintomas:
        if not isinstance(sintoma, dict):
            continue
        descricao = (sintoma.get('descricao') or '').strip()
        if not descricao:
            continue
        intensidade = sintoma.get('intensidade', 3)
        if not isinstance(intensidade, int):
            intensidade = 3
        intensidade = min(5, max(1, intensidade))
        sintomas_normalizados.append(
            {
                'descricao': descricao[:500],
                'intensidade': intensidade,
                'duracao': (sintoma.get('duracao') or '').strip()[:120],
                'possui_sinal_alerta': bool(sintoma.get('possui_sinal_alerta', False)),
            }
        )

    return {
        'mensagem_ia': (payload.get('mensagem_ia') or '').strip(),
        'pronto_para_classificar': bool(payload.get('pronto_para_classificar', False)) and len(sintomas_normalizados) > 0,
        'paciente': {
            'nome_completo': (paciente.get('nome_completo') or '').strip(),
            'data_nascimento': paciente.get('data_nascimento') or None,
            'sexo': (paciente.get('sexo') or 'nao_informado'),
            'telefone': (paciente.get('telefone') or '').strip(),
            'email': (paciente.get('email') or '').strip(),
        },
        'sintomas': sintomas_normalizados,
        'observacoes_gerais': (payload.get('observacoes_gerais') or '').strip()[:1000],
    }


def _extrair_intensidade_texto(texto):
    if not texto:
        return None

    match = re.search(r'\b([1-5])\s*/\s*5\b', texto)
    if match:
        return int(match.group(1))

    match = re.search(r'\b(?:nivel|intensidade|dor)\D{0,12}([1-5])\b', texto)
    if match:
        return int(match.group(1))

    if re.fullmatch(r'\s*[1-5]\s*', texto):
        return int(texto.strip())

    return None


def _extrair_duracao_texto(texto):
    if not texto:
        return ''
    match = re.search(r'\b\d+\s*(hora|horas|dia|dias|semana|semanas|mes|meses)\b', texto)
    return match.group(0) if match else ''


def _texto_tem_sintoma(texto):
    base = _normalizar_texto(texto)
    return any(termo in base for termo in TERMO_SINTOMA)


def _extrair_sintoma_principal(mensagens_usuario):
    for texto in mensagens_usuario:
        texto_limpo = (texto or '').strip()
        if len(texto_limpo) < 4:
            continue
        if _texto_tem_sintoma(texto_limpo):
            return texto_limpo[:500]
    return ''


def _tem_alerta(texto):
    base = _normalizar_texto(texto)
    return any(termo in base for termo in TERMO_ALERTA)


def _resposta_sim_nao(texto):
    base = _normalizar_texto(texto)
    if base in {'sim', 's', 'tenho', 'tenho sim'}:
        return 'sim'
    if base in {'nao', 'n', 'nao tenho', 'nao tenho nao'}:
        return 'nao'
    return ''


def _ultimo_assistente(historico):
    for item in reversed(historico or []):
        if item.get('role') == 'assistant':
            return _normalizar_texto(item.get('content'))
    return ''


def _heuristica_sintomas_texto(mensagem):
    texto = (mensagem or '').strip()
    if not texto:
        return []

    intensidade = _extrair_intensidade_texto(texto) or 3
    duracao = _extrair_duracao_texto(texto)

    partes = [p.strip(' .;') for p in re.split(r',|;|\.| e ', texto, flags=re.IGNORECASE) if p.strip()]
    sintomas = []
    for parte in partes[:4]:
        if len(parte) < 4:
            continue
        sintomas.append(
            {
                'descricao': parte[:500],
                'intensidade': intensidade,
                'duracao': duracao[:120],
                'possui_sinal_alerta': _tem_alerta(parte),
            }
        )

    return sintomas


def _montar_payload_chat(mensagem, historico, num_predict):
    mensagens = [{'role': 'system', 'content': PROMPT_SISTEMA_TRIAGEM}]
    mensagens.extend(_limpar_historico(historico))
    max_chars = max(120, int(getattr(settings, 'OLLAMA_MAX_INPUT_CHARS', 700)))
    mensagens.append({'role': 'user', 'content': (mensagem or '').strip()[:max_chars]})

    return {
        'model': settings.OLLAMA_MODEL,
        'messages': mensagens,
        'stream': False,
        'format': 'json',
        'keep_alive': getattr(settings, 'OLLAMA_KEEP_ALIVE', '10m'),
        'options': {
            'temperature': settings.OLLAMA_TEMPERATURE,
            'num_predict': int(max(80, num_predict)),
            'num_ctx': int(max(512, getattr(settings, 'OLLAMA_NUM_CTX', 1024))),
        },
    }


def _chamar_ollama(payload):
    endpoint = settings.OLLAMA_URL.rstrip('/') + '/api/chat'
    req = request.Request(
        endpoint,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    with request.urlopen(req, timeout=settings.OLLAMA_TIMEOUT_SECONDS) as resp:
        return json.loads(resp.read().decode('utf-8'))


def _coletar_fluxo_rapido(mensagem, historico):
    mensagens_usuario = []
    for item in historico or []:
        if item.get('role') == 'user':
            mensagens_usuario.append((item.get('content') or '').strip())
    mensagens_usuario.append((mensagem or '').strip())

    texto_total = ' '.join([t for t in mensagens_usuario if t]).strip()
    if not texto_total:
        return None

    intensidade = None
    duracao = ''
    for texto in mensagens_usuario:
        intensidade_atual = _extrair_intensidade_texto(texto)
        if intensidade_atual is not None:
            intensidade = intensidade_atual
        duracao_atual = _extrair_duracao_texto(texto)
        if duracao_atual:
            duracao = duracao_atual

    sintoma_principal = _extrair_sintoma_principal(mensagens_usuario)

    alerta_por_texto = _tem_alerta(texto_total)
    resp_alerta = ''
    ultimo_assistente = _ultimo_assistente(historico)
    if 'falta de ar' in ultimo_assistente or 'sim/nao' in ultimo_assistente:
        resp_alerta = _resposta_sim_nao(mensagens_usuario[-1])

    if resp_alerta == 'sim':
        alerta_por_texto = True

    if 'emergencia' in _normalizar_texto(texto_total) or 'pronto socorro' in _normalizar_texto(texto_total):
        alerta_por_texto = True

    if not sintoma_principal:
        return {
            'mensagem_ia': 'Qual e o sintoma principal agora?',
            'pronto_para_classificar': False,
            'paciente': {},
            'sintomas': [],
            'observacoes_gerais': '',
            'erro_ia_local': False,
            'meta_ia': {'origem': 'fluxo_rapido_local', 'tentativas': 0, 'duracao_ms': 0},
        }

    if intensidade is None:
        return {
            'mensagem_ia': PERGUNTA_INTENSIDADE,
            'pronto_para_classificar': False,
            'paciente': {},
            'sintomas': [],
            'observacoes_gerais': '',
            'erro_ia_local': False,
            'meta_ia': {'origem': 'fluxo_rapido_local', 'tentativas': 0, 'duracao_ms': 0},
        }

    if not duracao:
        return {
            'mensagem_ia': PERGUNTA_DURACAO,
            'pronto_para_classificar': False,
            'paciente': {},
            'sintomas': [],
            'observacoes_gerais': '',
            'erro_ia_local': False,
            'meta_ia': {'origem': 'fluxo_rapido_local', 'tentativas': 0, 'duracao_ms': 0},
        }

    if not alerta_por_texto and resp_alerta == '':
        return {
            'mensagem_ia': PERGUNTA_ALERTA,
            'pronto_para_classificar': False,
            'paciente': {},
            'sintomas': [],
            'observacoes_gerais': '',
            'erro_ia_local': False,
            'meta_ia': {'origem': 'fluxo_rapido_local', 'tentativas': 0, 'duracao_ms': 0},
        }

    prioridade_alta = bool(alerta_por_texto or intensidade >= 5)
    mensagem_final = 'Triagem concluida. Vou calcular o nivel de risco e gerar o encaminhamento agora.'
    if prioridade_alta:
        mensagem_final = 'Sinal de gravidade identificado. Vou gerar encaminhamento prioritario agora.'

    return {
        'mensagem_ia': mensagem_final,
        'pronto_para_classificar': True,
        'paciente': {},
        'sintomas': [
            {
                'descricao': sintoma_principal[:500],
                'intensidade': int(min(5, max(1, intensidade))),
                'duracao': duracao[:120],
                'possui_sinal_alerta': bool(prioridade_alta),
            }
        ],
        'observacoes_gerais': 'Coleta rapida local com foco em objetividade e seguranca.',
        'erro_ia_local': False,
        'meta_ia': {'origem': 'fluxo_rapido_local', 'tentativas': 0, 'duracao_ms': 0},
    }


def gerar_resposta_chat_triagem(mensagem, historico):
    inicio = time.perf_counter()

    if bool(getattr(settings, 'CHAT_IA_MODO_RAPIDO_LOCAL', True)):
        fluxo = _coletar_fluxo_rapido(mensagem=mensagem, historico=historico)
        if fluxo is not None:
            fluxo['meta_ia']['duracao_ms'] = int((time.perf_counter() - inicio) * 1000)
            registrar_execucao_ia(latencia_ms=fluxo['meta_ia']['duracao_ms'], sucesso=not fluxo.get('erro_ia_local', False), timeout=False, fallback=False)
            return fluxo

    tentativas = max(1, int(getattr(settings, 'OLLAMA_RETRY_ATTEMPTS', 2)))
    backoff = max(0.0, float(getattr(settings, 'OLLAMA_RETRY_BACKOFF_SECONDS', 0.4)))
    num_predict_padrao = int(getattr(settings, 'OLLAMA_NUM_PREDICT', 180))
    num_predict_rapido = int(getattr(settings, 'OLLAMA_NUM_PREDICT_FAST', min(160, num_predict_padrao)))

    ultima_excecao = None
    for tentativa in range(1, tentativas + 1):
        payload = _montar_payload_chat(
            mensagem=mensagem,
            historico=historico,
            num_predict=(num_predict_rapido if tentativa == 1 else num_predict_padrao),
        )
        try:
            resposta = _chamar_ollama(payload)
            conteudo = ((resposta.get('message') or {}).get('content') or '').strip()
            estruturado = _normalizar_saida(_extrair_json(conteudo))

            if not estruturado['mensagem_ia']:
                estruturado['mensagem_ia'] = 'Me descreva os sintomas principais em uma frase.'

            duracao_ms = int((time.perf_counter() - inicio) * 1000)
            estruturado['erro_ia_local'] = False
            estruturado['meta_ia'] = {'duracao_ms': duracao_ms, 'tentativas': tentativa, 'origem': 'ollama'}
            registrar_execucao_ia(latencia_ms=duracao_ms, sucesso=True, timeout=False, fallback=False)
            return estruturado
        except (TimeoutError, socket.timeout, error.URLError, error.HTTPError, json.JSONDecodeError, UnicodeDecodeError, OSError, ValueError) as exc:
            ultima_excecao = exc
            if tentativa < tentativas:
                time.sleep(backoff)

    duracao_ms = int((time.perf_counter() - inicio) * 1000)
    sintomas_heuristicos = _heuristica_sintomas_texto(mensagem)
    if sintomas_heuristicos:
        resposta_fallback = {
            'mensagem_ia': 'Nao consegui concluir pela IA agora. Confirme intensidade (1-5) e duracao para eu finalizar a triagem.',
            'pronto_para_classificar': False,
            'paciente': {},
            'sintomas': sintomas_heuristicos,
            'observacoes_gerais': 'Fallback heuristico por indisponibilidade temporaria da IA.',
            'erro_ia_local': True,
            'meta_ia': {'duracao_ms': duracao_ms, 'tentativas': tentativas, 'origem': 'fallback_heuristico'},
        }
        registrar_execucao_ia(
            latencia_ms=duracao_ms,
            sucesso=False,
            timeout=isinstance(ultima_excecao, (TimeoutError, socket.timeout)),
            fallback=True,
        )
        LOGGER.warning('Fallback heuristico acionado no chat IA apos %s tentativas. erro=%s', tentativas, type(ultima_excecao).__name__ if ultima_excecao else 'desconhecido')
        return resposta_fallback

    timeout_msg = None
    if isinstance(ultima_excecao, (TimeoutError, socket.timeout)):
        timeout_msg = f'A IA local demorou mais de {settings.OLLAMA_TIMEOUT_SECONDS}s para responder apos {tentativas} tentativa(s).'

    registrar_execucao_ia(
        latencia_ms=duracao_ms,
        sucesso=False,
        timeout=isinstance(ultima_excecao, (TimeoutError, socket.timeout)),
        fallback=False,
    )
    LOGGER.error('Falha no chat IA. tentativas=%s duracao_ms=%s erro=%s', tentativas, duracao_ms, type(ultima_excecao).__name__ if ultima_excecao else 'desconhecido')
    return _resposta_ia_indisponivel(mensagem=timeout_msg, duracao_ms=duracao_ms, tentativas=tentativas)

