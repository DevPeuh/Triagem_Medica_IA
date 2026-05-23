# Entrega - Banco de Dados (Projeto Triagem Medica com IA)

## 1) Objetivo do banco
Este banco foi modelado para suportar o fluxo completo de triagem medica:
- cadastro e autenticacao de usuario/paciente
- abertura de triagem
- registro de sintomas e respostas
- classificacao de risco
- geracao de encaminhamento
- pre-agendamento com profissional

## 2) Lista de tabelas do projeto
Tabelas principais da aplicacao:
1. usuarios_usuario
2. pacientes_paciente
3. sintomas_sintoma
4. triagens_triagem
5. triagens_resposta_triagem
6. classificacao_risco
7. encaminhamentos_encaminhamento
8. encaminhamentos_agendaprofissional
9. encaminhamentos_preagendamento

Tabelas de autenticacao do Django (suporte a login e permissoes):
1. auth_user
2. auth_group
3. auth_permission
4. django_content_type
5. django_session
6. django_admin_log
7. django_migrations

## 3) DER / MER (descricao textual)
- Um auth_user pode se relacionar com no maximo um usuarios_usuario (1:1)
- Um auth_user pode se relacionar com no maximo um pacientes_paciente (1:1)
- Um pacientes_paciente pode ter varias triagens (1:N)
- Um usuarios_usuario (profissional) pode atender varias triagens (1:N)
- Uma triagens_triagem pode ter varias triagens_respostatriagem (1:N)
- Um sintomas_sintoma pode aparecer em varias triagens_respostatriagem (1:N)
- Uma triagens_triagem tem no maximo uma classificacao_risco_classificacaorisco (1:1)
- Uma triagens_triagem tem no maximo um encaminhamentos_encaminhamento (1:1)
- Um usuarios_usuario (profissional) pode ter varios encaminhamentos_agendaprofissional (1:N)
- Uma triagens_triagem tem no maximo um encaminhamentos_preagendamento (1:1)
- Um encaminhamentos_encaminhamento tem no maximo um encaminhamentos_preagendamento (1:1)
- Um encaminhamentos_agendaprofissional pode estar em varios pre-agendamentos historicos (1:N)

## 4) Integridades exigidas

### 4.1 Integridade semantica
Regras de negocio aplicadas:
- intensidade da resposta entre 1 e 5
- status da triagem controlado por lista valida
- nivel de risco controlado por lista valida
- recomendacao do encaminhamento controlada por lista valida
- status do pre-agendamento controlado por lista valida
- horario de fim da agenda obrigatoriamente maior que horario de inicio
- pre-agendamento confirmado exige slot e profissional

### 4.2 Integridade de dominio
Cada atributo tem dominio definido:
- tipos corretos (DATE, TIMESTAMP, VARCHAR, BOOLEAN, INTEGER)
- limites de tamanho (ex.: nome 120/200)
- CHECK para valores permitidos em campos de status/perfil/sexo/nivel
- NOT NULL nos campos obrigatorios

### 4.3 Integridade de entidade
Garantida por:
- PK em todas as tabelas
- UNIQUE em atributos chave (ex.: email usuario, nome de sintoma)
- O2O implementado com UNIQUE em FKs (triagem em classificacao/encaminhamento/pre-agendamento)

### 4.4 Integridade de relacionamento
Garantida por:
- FKs entre todas as tabelas relacionadas
- on delete apropriado para cada caso:
  - CASCADE quando o filho nao pode existir sem o pai
  - PROTECT/RESTRICT quando nao pode apagar registro com historico
  - SET NULL quando o relacionamento e opcional

## 5) Itens extra
### 5.1 Gatilho funcional (trigger)
Implementado no SQL de entrega:
- trigger de validacao da agenda (fim > inicio)
- trigger de consistencia do pre-agendamento confirmado

### 5.2 View e indice
Implementado no SQL de entrega:
- VIEW vw_agenda_disponivel
- indices para acelerar busca de agenda, triagem e status

## 6) Evidencias para enviar ao professor
1. DER/MER (arquivo mermaid ou imagem exportada)
2. Script SQL DDL completo (arquivo .sql)
3. Migrations Django (pasta migrations de cada app)
4. Video curto mostrando:
   - criacao do banco
   - execucao do SQL
   - tabelas criadas
   - constraints, trigger, view e indices

## 7) Checklist de avaliacao (rubrica)
- [x] tabelas completas
- [x] MER/DER
- [x] integridade semantica
- [x] integridade de dominio
- [x] integridade de entidade
- [x] integridade de relacionamento
- [x] extra: trigger funcional
- [x] extra: view e indices

## 8) Como executar (passo a passo rapido)
1. Criar database no pgAdmin: triagem_medica
2. Abrir Query Tool
3. Executar o arquivo `docs/02_ddl_postgresql.sql`
4. Conferir tabelas e objetos criados
5. (Opcional para app Django) rodar `python manage.py migrate`

## 9) Observacao importante
Como o projeto usa Django ORM, a forma oficial de prova tecnica tambem pode ser feita com migrations.
Mesmo assim, o script SQL manual foi montado com todas as regras de integridade pedidas para entrega da disciplina de Banco de Dados.
