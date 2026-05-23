# Modelo de Dados (Campos sugeridos)

## Usuário
- id
- nome_completo
- email (único)
- senha_hash
- perfil (administrador, profissional, paciente)
- ativo
- data_criacao
- data_atualizacao

## Paciente
- id
- nome_completo
- data_nascimento
- sexo
- cpf (opcional)
- telefone
- email
- endereco
- alergias (texto)
- comorbidades (texto)
- medicamentos_em_uso (texto)
- contato_emergencia_nome
- contato_emergencia_telefone
- data_criacao
- data_atualizacao

## Triagem
- id
- paciente_id (FK)
- profissional_id (FK Usuário, opcional)
- data_hora_inicio
- data_hora_fim
- status (em_andamento, concluida, cancelada)
- observacoes_gerais

## Sintoma
- id
- nome
- descricao
- ativo

## RespostaTriagem
- id
- triagem_id (FK)
- sintoma_id (FK)
- intensidade (1 a 5)
- duracao
- possui_sinal_alerta (bool)
- observacao

## ClassificaçãoRisco
- id
- triagem_id (FK, unique)
- nivel (baixo, medio, alto, emergencia)
- pontuacao
- justificativa
- protocolo_versao
- data_classificacao

## Encaminhamento
- id
- triagem_id (FK, unique)
- recomendacao (autocuidado, consulta, urgencia, emergencia)
- descricao
- prazo_recomendado
- data_geracao

## Relatório
- id
- triagem_id (FK, unique)
- resumo_clinico
- conclusao
- arquivo_pdf (opcional)
- data_geracao

## LogAuditoria
- id
- usuario_id (FK)
- entidade
- entidade_id
- acao (criou, atualizou, removeu, visualizou)
- detalhes
- ip_origem
- data_hora
