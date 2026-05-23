# Projeto de Faculdade - Sistema Web de Triagem Médica com IA (Regras)

## Migracao para pasta nova sem historico antigo

Consulte: `README_MIGRACAO_NOVA_PASTA.md`

## Como executar

1. Criar ambiente virtual:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Instalar dependências:

```powershell
pip install -r requirements.txt
```

3. Criar arquivo `.env` com base em `.env.exemplo`.
   O projeto esta configurado para usar `PostgreSQL 18` (`DB_ENGINE=django.db.backends.postgresql`) na porta `5433`.
   Preencha `SECRET_KEY` com uma chave forte e os campos `DB_*` com os dados do seu banco.

4. Rodar migrações:

```powershell
py manage.py makemigrations
py manage.py migrate
```

5. Criar superusuário:

```powershell
py manage.py createsuperuser
```

6. Subir servidor:

```powershell
py manage.py runserver
```

## Endpoints principais

- `GET /api/status/`
- `POST /api/autenticacao/cadastro/`
- `POST /api/autenticacao/login/`
- `POST /api/autenticacao/logout/`
- `GET /api/autenticacao/sessao/`
- `CRUD /api/pacientes/`
- `CRUD /api/sintomas/`
- `CRUD /api/triagens/`
- `POST /api/triagens/{id}/classificar/`
- `POST /api/triagens/triagem-rapida/`
- `POST /api/chat-ia/triagem/`
- `GET /api/triagens/minhas/`
- `CRUD /api/classificacao-risco/`
- `CRUD /api/encaminhamentos/`
- `GET/POST /api/encaminhamentos/agenda-profissionais/`
- `GET /api/encaminhamentos/pre-agendamentos/`
- `CRUD /api/usuarios/`

## Observação do projeto

A classificação de risco inicial foi implementada como motor de regras clínicas explicáveis (MVP acadêmico), permitindo rastreabilidade da decisão e evolução posterior para modelos de IA mais avançados.

## Fluxo de paciente (cadastro + chat de triagem)

1. O paciente cria conta em `POST /api/autenticacao/cadastro/`.
2. Faz login em `POST /api/autenticacao/login/`.
3. Usa o chat de triagem em `POST /api/chat-ia/triagem/`.
4. Consulta histórico salvo em `GET /api/triagens/minhas/`.

### Exemplo de cadastro

```json
{
  "username": "maria.silva",
  "email": "maria@example.com",
  "password": "SenhaForte@123",
  "confirmar_senha": "SenhaForte@123",
  "nome_completo": "Maria Silva",
  "sexo": "feminino",
  "telefone": "11999999999"
}
```

### Exemplo de triagem rápida para paciente autenticado

```json
{
  "sintomas": [
    {
      "descricao": "dor de cabeça leve",
      "intensidade": 2,
      "duracao": "2 dias",
      "possui_sinal_alerta": false
    }
  ],
  "observacoes_gerais": "início da conversa"
}
```

## Teste de IA local (sem custo)

1. Instale e rode o Ollama na máquina.
2. Baixe um modelo, por exemplo: `ollama pull llama3.1:8b`.
3. Garanta no `.env`:
   - `OLLAMA_URL=http://localhost:11434`
   - `OLLAMA_MODEL=llama3.1:8b`
4. Abra `http://127.0.0.1:8000/chat-teste/` para testar o chat.


## Performance e estabilidade do chat IA

A API de chat agora possui:

- Retry automatico em falhas temporarias da IA local.
- Fallback seguro (nao classifica automaticamente quando a IA falha).
- Header X-Response-Time-ms em todas as respostas.
- Endpoint de monitoramento em `GET /api/chat-ia/monitoramento/`.

Variaveis recomendadas no .env:

- OLLAMA_TIMEOUT_SECONDS=45
- OLLAMA_RETRY_ATTEMPTS=2
- OLLAMA_RETRY_BACKOFF_SECONDS=0.4
- OLLAMA_NUM_PREDICT=180
- OLLAMA_NUM_PREDICT_FAST=140
- OLLAMA_MAX_HISTORY_MESSAGES=3
- OLLAMA_MAX_INPUT_CHARS=700
- OLLAMA_KEEP_ALIVE=10m
- CHAT_IA_SLOW_REQUEST_MS=12000



## Pre-agendamento automatico

A triagem agora gera pre-agendamento automatico quando a recomendacao for `consulta` ou `urgencia`.

1. Rode migrações:

```powershell
py manage.py migrate
```

2. Popule agenda demo:

```powershell
py manage.py popular_agenda_demo
```

3. Durante o chat, ao finalizar a triagem, o retorno inclui:

- `triagem.pre_agendamento.profissional`
- `triagem.pre_agendamento.horario_sugerido`
- `mensagem_encaminhamento` (texto pronto para o paciente)


