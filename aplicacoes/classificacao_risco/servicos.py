import unicodedata
from dataclasses import dataclass


@dataclass
class ResultadoClassificacao:
    nivel: str
    pontuacao: int
    justificativa: str
    recomendacao: str
    descricao_recomendacao: str
    prazo_recomendado: str
    orientacao_paciente: str
    proximos_passos: list[str]


def _normalizar_texto(valor):
    texto = unicodedata.normalize('NFKD', valor or '')
    texto = ''.join(char for char in texto if not unicodedata.combining(char))
    return texto.lower()


def _contem_termo(texto, termos):
    return any(termo in texto for termo in termos)


def classificar_triagem(triagem):
    respostas = list(triagem.respostas.select_related('sintoma').all())

    pontuacao = 0
    motivos = []
    categorias_criticas = set()

    sinais_criticos = {
        'cardiaco': {
            'termos': ['dor no peito', 'dor toracica', 'aperto no peito', 'pressao no peito', 'peso no peito'],
            'peso': 5,
            'motivo': 'Sintoma cardiorrespiratório grave identificado.',
        },
        'respiratorio': {
            'termos': ['falta de ar', 'dificuldade para respirar', 'nao consigo respirar', 'ofegante', 'chiado no peito'],
            'peso': 5,
            'motivo': 'Comprometimento respiratório sugerido pelo relato.',
        },
        'neurologico': {
            'termos': ['desmaio', 'convulsao', 'confusao mental', 'fala enrolada', 'fraqueza de um lado', 'paralisia'],
            'peso': 6,
            'motivo': 'Sinal neurológico de alta gravidade identificado.',
        },
        'hemorragico': {
            'termos': ['sangramento intenso', 'vomito com sangue', 'fezes pretas', 'sangue nas fezes'],
            'peso': 5,
            'motivo': 'Sinal de possível sangramento importante identificado.',
        },
    }

    sinais_importantes = {
        'febre': {
            'termos': ['febre alta', '39', '40', 'calafrio intenso'],
            'peso': 2,
            'motivo': 'Relato compatível com quadro febril importante.',
        },
        'dor_abdominal_intensa': {
            'termos': ['dor abdominal intensa', 'barriga muito inchada', 'dor na barriga muito forte'],
            'peso': 2,
            'motivo': 'Dor abdominal intensa relatada.',
        },
        'desidratacao': {
            'termos': ['vomitando muito', 'diarreia intensa', 'sem urinar', 'boca muito seca'],
            'peso': 2,
            'motivo': 'Sinais de possível desidratação identificados.',
        },
    }

    for resposta in respostas:
        if resposta.possui_sinal_alerta:
            pontuacao += 4
            motivos.append('Paciente marcou sinal de alerta na triagem.')

        if resposta.intensidade >= 4:
            pontuacao += 2
            motivos.append(f'Intensidade alta informada para "{resposta.sintoma.nome}".')
        elif resposta.intensidade == 3:
            pontuacao += 1

        texto = _normalizar_texto(
            ' '.join(
                [
                    resposta.sintoma.nome,
                    resposta.observacao,
                    resposta.duracao,
                ]
            )
        )

        for chave, regra in sinais_criticos.items():
            if _contem_termo(texto, regra['termos']):
                pontuacao += regra['peso']
                categorias_criticas.add(chave)
                motivos.append(regra['motivo'])
                break

        for regra in sinais_importantes.values():
            if _contem_termo(texto, regra['termos']):
                pontuacao += regra['peso']
                motivos.append(regra['motivo'])
                break

    emergencia = len(categorias_criticas) >= 2 or pontuacao >= 10

    if emergencia:
        return ResultadoClassificacao(
            nivel='emergencia',
            pontuacao=pontuacao,
            justificativa=' '.join(motivos) or 'Critérios de emergência atendidos.',
            recomendacao='emergencia',
            descricao_recomendacao='Acionar serviço de emergência ou encaminhar imediatamente ao pronto atendimento.',
            prazo_recomendado='Imediato',
            orientacao_paciente='Procure atendimento de emergência agora. Se houver piora súbita, ligue para o SAMU (192).',
            proximos_passos=[
                'Ir imediatamente ao pronto atendimento mais próximo.',
                'Não dirigir sozinho em caso de mal-estar importante.',
                'Levar lista de sintomas e tempo de início para a equipe médica.',
            ],
        )

    if pontuacao >= 7:
        return ResultadoClassificacao(
            nivel='alto',
            pontuacao=pontuacao,
            justificativa=' '.join(motivos) or 'Critérios de alto risco atendidos.',
            recomendacao='urgencia',
            descricao_recomendacao='Buscar atendimento em unidade de urgência o quanto antes.',
            prazo_recomendado='Até 1 hora',
            orientacao_paciente='Procure uma unidade de urgência hoje, preferencialmente agora.',
            proximos_passos=[
                'Ir para uma UPA ou pronto atendimento.',
                'Evitar automedicação além do já prescrito.',
                'Retornar imediatamente se houver piora antes do atendimento.',
            ],
        )

    if pontuacao >= 4:
        return ResultadoClassificacao(
            nivel='medio',
            pontuacao=pontuacao,
            justificativa=' '.join(motivos) or 'Critérios de risco moderado atendidos.',
            recomendacao='consulta',
            descricao_recomendacao='Agendar consulta clínica para avaliação profissional.',
            prazo_recomendado='Até 24 horas',
            orientacao_paciente='Agende avaliação médica em até 24 horas e monitore evolução dos sintomas.',
            proximos_passos=[
                'Marcar consulta clínica no mesmo dia ou no dia seguinte.',
                'Anotar pioras, novos sintomas e horário de início.',
                'Se surgirem sinais de alerta, procurar urgência.',
            ],
        )

    return ResultadoClassificacao(
        nivel='baixo',
        pontuacao=pontuacao,
        justificativa=' '.join(motivos) or 'Sem sinais críticos no conjunto atual de respostas.',
        recomendacao='autocuidado',
        descricao_recomendacao='Manter autocuidado e monitorar sintomas.',
        prazo_recomendado='Reavaliar em 48 horas se persistir',
        orientacao_paciente='No momento, o quadro parece de baixo risco. Mantenha hidratação e observe sinais de piora.',
        proximos_passos=[
            'Manter repouso e hidratação.',
            'Reavaliar em até 48 horas se os sintomas persistirem.',
            'Procurar urgência se surgirem sinais de alerta.',
        ],
    )