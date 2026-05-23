# DER Textual

## Entidades e relacionamentos

1. Usuário (1) --- (N) LogAuditoria
2. Usuário (1) --- (N) Triagem (como profissional responsável)
3. Paciente (1) --- (N) Triagem
4. Triagem (1) --- (N) RespostaTriagem
5. Sintoma (1) --- (N) RespostaTriagem
6. Triagem (1) --- (1) ClassificaçãoRisco
7. Triagem (1) --- (1) Encaminhamento
8. Triagem (1) --- (0..1) Relatório

## Observações

- Cada triagem pertence a exatamente um paciente.
- Cada triagem possui uma classificação final e uma recomendação final.
- Logs de auditoria devem registrar ação, usuário e data/hora.