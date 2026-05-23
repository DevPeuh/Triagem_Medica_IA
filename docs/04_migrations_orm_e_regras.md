# Migrations do ORM com regras aplicadas (Django)

## Projeto
Triagem Medica com IA - Django ORM

## Onde estao as migrations
- `aplicacoes/usuarios/migrations/`
- `aplicacoes/pacientes/migrations/`
- `aplicacoes/sintomas/migrations/`
- `aplicacoes/triagens/migrations/`
- `aplicacoes/classificacao_risco/migrations/`
- `aplicacoes/encaminhamentos/migrations/`

## Migrations principais e regras

### 1) usuarios
- `0001_initial.py`
  - cria tabela `usuarios_usuario`
  - `email` com `unique=True` (integridade de entidade)
  - `perfil` com choices (dominio/semantica)
  - `usuario_auth` OneToOne com `auth_user` (relacionamento 1:1)
- `0002_alter_usuario_options_usuario_especialidade_and_more.py`
  - adiciona `especialidade` com choices (dominio)
  - ajusta opcoes do modelo

### 2) pacientes
- `0001_initial.py`
  - cria tabela `pacientes_paciente`
  - `cpf` com `unique=True` (entidade)
  - `sexo` com choices (dominio)
- `0002_alter_paciente_data_nascimento_and_more.py`
  - flexibiliza `data_nascimento` e `telefone`
- `0003_paciente_usuario_auth.py`
  - adiciona `usuario_auth` OneToOne com `auth_user` (1:1)

### 3) sintomas
- `0001_initial.py`
  - cria tabela `sintomas_sintoma`
  - `nome` unico (entidade)

### 4) triagens
- `0001_initial.py`
  - cria tabela `triagens_triagem`
  - FK para paciente com `on_delete=PROTECT` (integridade de relacionamento)
  - FK para profissional com `on_delete=SET_NULL`
  - `status` com choices
  - cria `triagens_respostatriagem`
  - `intensidade` com validadores 1..5 (semantica/dominio)
  - `unique_together (triagem, sintoma)` (entidade/semantica)
- `0002_remove_sinais_vitais_table.py`
  - remove tabela de sinais vitais (escopo ajustado)

### 5) classificacao_risco
- `0001_initial.py`
  - cria `classificacao_risco_classificacaorisco`
  - OneToOne com triagem (1:1)
  - `nivel` com choices

### 6) encaminhamentos
- `0001_initial.py`
  - cria `encaminhamentos_encaminhamento`
  - OneToOne com triagem (1:1)
  - `recomendacao` com choices
- `0002_alter_encaminhamento_recomendacao_agendaprofissional_and_more.py`
  - cria `encaminhamentos_agendaprofissional`
  - cria `encaminhamentos_preagendamento`
  - FKs e status de pre-agendamento
- `0003_preagendamento_agenda_slot_and_more.py`
  - adiciona FK `agenda_slot`
  - amplia choices de status para confirmado/reagendado/cancelado

## Como provar para o professor (rapido)
1. Mostrar as pastas de migrations no projeto.
2. Rodar:
   - `python manage.py showmigrations`
3. Mostrar SQL gerado pelo ORM (exemplos):
   - `python manage.py sqlmigrate usuarios 0001`
   - `python manage.py sqlmigrate triagens 0001`
   - `python manage.py sqlmigrate encaminhamentos 0003`
4. Mostrar o MER:
   - arquivo `docs/03_mer_der.mmd`

## MER
- arquivo: `docs/03_mer_der.mmd`
- pode exportar para imagem/PDF e anexar junto do documento/video.

## Observacao
- Regras avancadas de trigger/view/index estao no SQL manual em:
  - `docs/02_ddl_postgresql.sql`
- Isso soma pontos extra da disciplina de Banco de Dados.
