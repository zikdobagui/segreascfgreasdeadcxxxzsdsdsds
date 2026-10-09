# Migração aplicada a este backup (2026-08-04_16-26-26)

Este backup é mais novo que o anterior (depósitos e vendas aconteceram
entre um e outro) e ainda estava com o **código antigo** (sem a correção).
Isso teve uma consequência real: o painel de renovação manual gravou 3
vendas de um cliente em `database/users/8352063472.json` (arquivo solto)
em vez de no banco, porque nesse momento o código ainda tinha o bug.

## O que foi feito, na ordem

1. Apliquei nos arquivos deste backup exatamente as mesmas correções já
   explicadas no backup anterior (`bot.py`, `troca_automatica.py`,
   `modulo_logins_saldos.py`, `rankings.py`, `relatorio_avancado.py`,
   `rl_maintenance.py`, `update_usernames.py`, `renovacao_painel.py`,
   `gerenciador.py`) — confirmei que o código aqui era idêntico, byte a
   byte, ao do backup original (ou seja, ainda sem a correção).

2. **Recuperei as 3 vendas órfãs** encontradas em
   `database/users/8352063472.json` (cliente `kimerioostreaming`):
   - `NETFLIX PREMIUM COM CÓDIGO` — as566@apmail.org — R$ 15,00 (04/08 09:56)
   - `NETFLIX PREMIUM` — was305@wwtake.com — R$ 25,00 (04/08 09:58)
   - `NETFLIX PREMIUM COM CÓDIGO` — as566@apmail.org — R$ 15,00 (04/08 10:19)

   Elas foram mescladas (não sobrescritas) no histórico de compras já
   existente desse cliente dentro de `database/bot.db` — ele já tinha 12
   compras registradas no banco; agora tem 15, com nenhuma duplicada.

3. Removi o arquivo órfão `database/users/8352063472.json` e a pasta
   `database/users/` (que ficou vazia) depois de confirmar que os dados
   estavam salvos no banco.

4. Verifiquei que não havia **nenhum outro** arquivo solto de usuário
   (`database/users/`) além desse — foi o único caso.

## Importante: implante o código corrigido o quanto antes

Enquanto o código antigo continuar rodando no seu host, qualquer nova
renovação manual cadastrada pelo painel (`renovacao_painel.py`) volta a
cair em `database/users/<id>.json` em vez do banco — ou seja, o mesmo
problema pode se repetir com vendas feitas depois deste backup. Assim que
você subir esta versão corrigida, o problema para de acontecer.

Se acontecerem mais vendas/depósitos entre agora e o deploy, me mande o
backup mais recente que eu repito esse processo (aplicar correção +
recuperar qualquer venda/depósito que tenha ficado solto em JSON) antes
de você substituir o código em produção.
