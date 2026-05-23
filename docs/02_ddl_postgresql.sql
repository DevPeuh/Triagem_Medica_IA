-- =====================================================
-- PROJETO: Triagem Medica com IA
-- BANCO: PostgreSQL
-- OBS: Este script cria as tabelas principais da aplicacao.
-- Para autenticao do Django (auth_user e outras), rode migrate.
-- =====================================================

BEGIN;

-- -----------------------------------------------------
-- 0) TABELA BASE PARA AUTENTICACAO
-- -----------------------------------------------------
-- Se o projeto Django ja executou migrations, esta tabela ja existe.
-- Se nao existir, este bloco cria uma versao minima para suportar FKs.
CREATE TABLE IF NOT EXISTS auth_user (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(128) NOT NULL,
    email VARCHAR(254) NOT NULL DEFAULT '',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    date_joined TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- -----------------------------------------------------
-- 1) TABELA DE USUARIOS DO SISTEMA
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios_usuario (
    id BIGSERIAL PRIMARY KEY,
    usuario_auth_id BIGINT UNIQUE,
    nome_completo VARCHAR(200) NOT NULL,
    email VARCHAR(254) NOT NULL UNIQUE,
    perfil VARCHAR(20) NOT NULL,
    especialidade VARCHAR(32) NOT NULL DEFAULT '',
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    data_criacao TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    data_atualizacao TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_usuarios_perfil
        CHECK (perfil IN ('administrador', 'profissional', 'paciente')),

    CONSTRAINT ck_usuarios_especialidade
        CHECK (
            especialidade IN ('', 'clinica_geral', 'cardiologia', 'neurologia', 'pneumologia', 'gastroenterologia')
        ),

    CONSTRAINT fk_usuarios_auth_user
        FOREIGN KEY (usuario_auth_id)
        REFERENCES auth_user(id)
        ON DELETE CASCADE
);

-- -----------------------------------------------------
-- 2) TABELA DE PACIENTES
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS pacientes_paciente (
    id BIGSERIAL PRIMARY KEY,
    usuario_auth_id BIGINT UNIQUE,
    nome_completo VARCHAR(200) NOT NULL,
    data_nascimento DATE NULL,
    sexo VARCHAR(20) NOT NULL DEFAULT 'nao_informado',
    cpf VARCHAR(14) UNIQUE NULL,
    telefone VARCHAR(20) NOT NULL DEFAULT '',
    email VARCHAR(254) NOT NULL DEFAULT '',
    endereco VARCHAR(255) NOT NULL DEFAULT '',
    alergias TEXT NOT NULL DEFAULT '',
    comorbidades TEXT NOT NULL DEFAULT '',
    medicamentos_em_uso TEXT NOT NULL DEFAULT '',
    contato_emergencia_nome VARCHAR(200) NOT NULL DEFAULT '',
    contato_emergencia_telefone VARCHAR(20) NOT NULL DEFAULT '',
    data_criacao TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    data_atualizacao TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_paciente_sexo
        CHECK (sexo IN ('feminino', 'masculino', 'outro', 'nao_informado')),

    CONSTRAINT fk_paciente_auth_user
        FOREIGN KEY (usuario_auth_id)
        REFERENCES auth_user(id)
        ON DELETE SET NULL
);

-- -----------------------------------------------------
-- 3) TABELA DE SINTOMAS
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS sintomas_sintoma (
    id BIGSERIAL PRIMARY KEY,
    nome VARCHAR(120) NOT NULL UNIQUE,
    descricao TEXT NOT NULL DEFAULT '',
    ativo BOOLEAN NOT NULL DEFAULT TRUE
);

-- -----------------------------------------------------
-- 4) TABELA DE TRIAGENS
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS triagens_triagem (
    id BIGSERIAL PRIMARY KEY,
    paciente_id BIGINT NOT NULL,
    profissional_responsavel_id BIGINT NULL,
    data_hora_inicio TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    data_hora_fim TIMESTAMPTZ NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'em_andamento',
    observacoes_gerais TEXT NOT NULL DEFAULT '',

    CONSTRAINT ck_triagem_status
        CHECK (status IN ('em_andamento', 'concluida', 'cancelada')),

    CONSTRAINT fk_triagem_paciente
        FOREIGN KEY (paciente_id)
        REFERENCES pacientes_paciente(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_triagem_profissional
        FOREIGN KEY (profissional_responsavel_id)
        REFERENCES usuarios_usuario(id)
        ON DELETE SET NULL
);

-- -----------------------------------------------------
-- 5) RESPOSTAS DA TRIAGEM
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS triagens_respostatriagem (
    id BIGSERIAL PRIMARY KEY,
    triagem_id BIGINT NOT NULL,
    sintoma_id BIGINT NOT NULL,
    intensidade SMALLINT NOT NULL,
    duracao VARCHAR(120) NOT NULL,
    possui_sinal_alerta BOOLEAN NOT NULL DEFAULT FALSE,
    observacao TEXT NOT NULL DEFAULT '',

    CONSTRAINT ck_resposta_intensidade
        CHECK (intensidade BETWEEN 1 AND 5),

    CONSTRAINT uq_resposta_triagem_sintoma
        UNIQUE (triagem_id, sintoma_id),

    CONSTRAINT fk_resposta_triagem
        FOREIGN KEY (triagem_id)
        REFERENCES triagens_triagem(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_resposta_sintoma
        FOREIGN KEY (sintoma_id)
        REFERENCES sintomas_sintoma(id)
        ON DELETE RESTRICT
);

-- -----------------------------------------------------
-- 6) CLASSIFICACAO DE RISCO
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS classificacao_risco_classificacaorisco (
    id BIGSERIAL PRIMARY KEY,
    triagem_id BIGINT NOT NULL UNIQUE,
    nivel VARCHAR(20) NOT NULL,
    pontuacao SMALLINT NOT NULL DEFAULT 0,
    justificativa TEXT NOT NULL,
    protocolo_versao VARCHAR(30) NOT NULL DEFAULT 'v1',
    data_classificacao TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_classificacao_nivel
        CHECK (nivel IN ('baixo', 'medio', 'alto', 'emergencia')),

    CONSTRAINT ck_classificacao_pontuacao
        CHECK (pontuacao >= 0),

    CONSTRAINT fk_classificacao_triagem
        FOREIGN KEY (triagem_id)
        REFERENCES triagens_triagem(id)
        ON DELETE CASCADE
);

-- -----------------------------------------------------
-- 7) ENCAMINHAMENTO
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS encaminhamentos_encaminhamento (
    id BIGSERIAL PRIMARY KEY,
    triagem_id BIGINT NOT NULL UNIQUE,
    recomendacao VARCHAR(20) NOT NULL,
    descricao TEXT NOT NULL,
    prazo_recomendado VARCHAR(120) NOT NULL DEFAULT '',
    data_geracao TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_enc_recomendacao
        CHECK (recomendacao IN ('autocuidado', 'consulta', 'urgencia', 'emergencia')),

    CONSTRAINT fk_enc_triagem
        FOREIGN KEY (triagem_id)
        REFERENCES triagens_triagem(id)
        ON DELETE CASCADE
);

-- -----------------------------------------------------
-- 8) AGENDA DE PROFISSIONAIS
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS encaminhamentos_agendaprofissional (
    id BIGSERIAL PRIMARY KEY,
    profissional_id BIGINT NOT NULL,
    especialidade VARCHAR(32) NOT NULL,
    inicio_atendimento TIMESTAMPTZ NOT NULL,
    fim_atendimento TIMESTAMPTZ NOT NULL,
    reservado BOOLEAN NOT NULL DEFAULT FALSE,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT ck_agenda_especialidade
        CHECK (especialidade IN ('clinica_geral', 'cardiologia', 'neurologia', 'pneumologia', 'gastroenterologia')),

    CONSTRAINT ck_agenda_intervalo
        CHECK (fim_atendimento > inicio_atendimento),

    CONSTRAINT fk_agenda_profissional
        FOREIGN KEY (profissional_id)
        REFERENCES usuarios_usuario(id)
        ON DELETE CASCADE
);

-- -----------------------------------------------------
-- 9) PRE-AGENDAMENTO
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS encaminhamentos_preagendamento (
    id BIGSERIAL PRIMARY KEY,
    triagem_id BIGINT NOT NULL UNIQUE,
    encaminhamento_id BIGINT NOT NULL UNIQUE,
    agenda_slot_id BIGINT NULL,
    profissional_id BIGINT NULL,
    especialidade VARCHAR(32) NOT NULL DEFAULT '',
    horario_sugerido TIMESTAMPTZ NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'sem_vaga',
    mensagem TEXT NOT NULL DEFAULT '',
    data_geracao TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    data_atualizacao TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_preag_status
        CHECK (status IN ('sugerido', 'confirmado', 'reagendado', 'cancelado', 'sem_vaga', 'encaminhamento_direto')),

    CONSTRAINT ck_preag_especialidade
        CHECK (especialidade IN ('', 'clinica_geral', 'cardiologia', 'neurologia', 'pneumologia', 'gastroenterologia')),

    CONSTRAINT fk_preag_triagem
        FOREIGN KEY (triagem_id)
        REFERENCES triagens_triagem(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_preag_encaminhamento
        FOREIGN KEY (encaminhamento_id)
        REFERENCES encaminhamentos_encaminhamento(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_preag_slot
        FOREIGN KEY (agenda_slot_id)
        REFERENCES encaminhamentos_agendaprofissional(id)
        ON DELETE SET NULL,

    CONSTRAINT fk_preag_profissional
        FOREIGN KEY (profissional_id)
        REFERENCES usuarios_usuario(id)
        ON DELETE SET NULL
);

-- -----------------------------------------------------
-- TRIGGERS (EXTRA)
-- -----------------------------------------------------

-- Trigger 1: valida intervalo de agenda
CREATE OR REPLACE FUNCTION fn_validar_intervalo_agenda()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.fim_atendimento <= NEW.inicio_atendimento THEN
        RAISE EXCEPTION 'fim_atendimento deve ser maior que inicio_atendimento';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_validar_intervalo_agenda ON encaminhamentos_agendaprofissional;
CREATE TRIGGER trg_validar_intervalo_agenda
BEFORE INSERT OR UPDATE ON encaminhamentos_agendaprofissional
FOR EACH ROW
EXECUTE FUNCTION fn_validar_intervalo_agenda();

-- Trigger 2: consistencia de pre-agendamento confirmado
CREATE OR REPLACE FUNCTION fn_validar_preagendamento_confirmado()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'confirmado' THEN
        IF NEW.agenda_slot_id IS NULL OR NEW.profissional_id IS NULL OR NEW.horario_sugerido IS NULL THEN
            RAISE EXCEPTION 'Pre-agendamento confirmado exige agenda_slot_id, profissional_id e horario_sugerido';
        END IF;

        UPDATE encaminhamentos_agendaprofissional
           SET reservado = TRUE
         WHERE id = NEW.agenda_slot_id;
    END IF;

    IF NEW.status = 'cancelado' AND OLD.agenda_slot_id IS NOT NULL THEN
        UPDATE encaminhamentos_agendaprofissional
           SET reservado = FALSE
         WHERE id = OLD.agenda_slot_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_validar_preagendamento_confirmado ON encaminhamentos_preagendamento;
CREATE TRIGGER trg_validar_preagendamento_confirmado
BEFORE UPDATE ON encaminhamentos_preagendamento
FOR EACH ROW
EXECUTE FUNCTION fn_validar_preagendamento_confirmado();

-- -----------------------------------------------------
-- INDICES (EXTRA)
-- -----------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_triagem_paciente_status
    ON triagens_triagem (paciente_id, status);

CREATE INDEX IF NOT EXISTS idx_resposta_triagem
    ON triagens_respostatriagem (triagem_id);

CREATE INDEX IF NOT EXISTS idx_agenda_busca_rapida
    ON encaminhamentos_agendaprofissional (especialidade, inicio_atendimento)
    WHERE reservado = FALSE AND ativo = TRUE;

CREATE INDEX IF NOT EXISTS idx_preag_status
    ON encaminhamentos_preagendamento (status, data_geracao DESC);

-- -----------------------------------------------------
-- VIEW (EXTRA)
-- -----------------------------------------------------

CREATE OR REPLACE VIEW vw_agenda_disponivel AS
SELECT
    a.id AS agenda_slot_id,
    a.especialidade,
    a.inicio_atendimento,
    a.fim_atendimento,
    u.id AS profissional_id,
    u.nome_completo AS profissional_nome
FROM encaminhamentos_agendaprofissional a
JOIN usuarios_usuario u ON u.id = a.profissional_id
WHERE a.ativo = TRUE
  AND a.reservado = FALSE
ORDER BY a.inicio_atendimento;

COMMIT;
