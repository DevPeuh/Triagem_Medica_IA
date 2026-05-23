# Triagem Medica IA

Sistema web de triagem medica com classificacao de risco por regras, fluxo de encaminhamento e pre-agendamento, com interface de chat para coleta guiada de sintomas.

## Visao Geral

O projeto registra sintomas informados pelo paciente, calcula nivel de risco clinico, gera orientacoes e encaminha para o proximo passo adequado:

- autocuidado orientado
- consulta prioritaria
- urgencia
- emergencia

Quando aplicavel, o sistema tambem gera pre-agendamento e permite confirmar, reagendar ou cancelar.

## Principais Funcionalidades

- autenticacao e cadastro de usuarios
- cadastro e gestao de pacientes
- catalogo de sintomas
- triagem tradicional e triagem rapida
- chat de triagem com IA local
- classificacao de risco com justificativa
- encaminhamento clinico
- pre-agendamento com acoes de confirmacao, reagendamento e cancelamento
- endpoint de monitoramento do modulo de chat

## Stack Tecnica

- Python 3
- Django
- Django REST Framework
- PostgreSQL
- Integracao com IA local (Ollama)

## Estrutura do Projeto

- `aplicacoes/`: apps de dominio (autenticacao, triagens, encaminhamentos, chat, usuarios, pacientes, sintomas)
- `configuracao/`: configuracoes globais e roteamento principal
- `templates/`: paginas HTML, incluindo tela de teste do chat
- `estaticos/`: CSS, JS e imagens
- `docs/`: documentacao de banco e modelagem

## Como Executar Localmente

1. Criar e ativar ambiente virtual:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Instalar dependencias:

```powershell
pip install -r requirements.txt
```

3. Criar arquivo de configuracao local a partir do exemplo:

```powershell
copy .env.exemplo .env
```

4. Executar migracoes:

```powershell
py manage.py migrate
```

5. (Opcional) Criar superusuario:

```powershell
py manage.py createsuperuser
```

6. (Opcional) Popular agenda de demonstracao para fluxo de agendamento:

```powershell
py manage.py popular_agenda_demo
```

7. Iniciar servidor:

```powershell
py manage.py runserver
```

## Acesso Rapido

- Home: `http://127.0.0.1:8000/`
- Tela de teste do chat: `http://127.0.0.1:8000/chat-teste/`
- API base: `http://127.0.0.1:8000/api/`

## Endpoints Relevantes

- `POST /api/autenticacao/cadastro/`
- `POST /api/autenticacao/login/`
- `POST /api/autenticacao/logout/`
- `GET /api/autenticacao/sessao/`
- `POST /api/chat-ia/triagem/`
- `GET /api/chat-ia/monitoramento/`
- `POST /api/triagens/triagem-rapida/`
- `POST /api/triagens/{id}/classificar/`
- `GET /api/triagens/minhas/`
- `GET/POST /api/encaminhamentos/agenda-profissionais/`
- `GET /api/encaminhamentos/pre-agendamentos/`

## Testes

Para executar a suite de testes:

```powershell
py manage.py test
```

## Documentacao Complementar

- [Entrega de banco de dados](docs/01_entrega_banco_dados.md)
- [DDL PostgreSQL](docs/02_ddl_postgresql.sql)
- [MER/DER](docs/03_mer_der.mmd)
- [Migrations e regras](docs/04_migrations_orm_e_regras.md)
