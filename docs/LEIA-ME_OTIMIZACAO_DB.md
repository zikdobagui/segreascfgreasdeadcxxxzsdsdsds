# Banco de dados otimizado — este pacote já vem pronto para rodar

## O que mudou
O bot armazenava cada usuário num arquivo `.json` separado em
`database/users/` (251 arquivos neste backup). Rankings e verificação de
pagamento liam e varriam TODOS esses arquivos a cada chamada — o gargalo
que deixava tudo lento com muitos usuários.

Troquei por **SQLite** (`database/bot.db`, modo WAL, com índices). As
funções em `database.py` e `rankings.py` mantêm os mesmos nomes e formatos
de retorno de antes, então **nenhum outro arquivo do bot foi alterado**
(bot.py, central.py, afiliados_sistema.py, modulo_pagamentos_pix.py etc.
continuam exatamente como estavam).

## Este pacote já inclui:
- Todos os arquivos e pastas do seu backup original (código, `assets/`,
  `botoes/`, `settings/`, `database/` com os JSONs de configuração, etc.)
- `database.py` e `rankings.py` já otimizados
- `database/bot.db` — **já migrado e validado**: rodei a migração dos 251
  usuários reais do seu `database/users/` e conferi saldo, pagamentos e
  compras de cada um contra os arquivos `.json` originais → 0 divergências.
- Os arquivos `.json` originais de `database/users/` foram mantidos
  intactos como backup (não apague).
- `migrate_json_to_sqlite.py` — só é necessário se você adicionar/alterar
  usuários manualmente nos JSONs depois; pode rodar de novo a qualquer
  momento (idempotente).

O que **não** veio neste pacote: `logs.txt` (só histórico de log, ~20MB,
não é necessário para o bot funcionar) e o `bot_instance.lock` antigo
(removido para não travar a inicialização).

## Para hospedar
1. Suba esta pasta inteira para o seu servidor/host (Discloud, SquareCloud,
   VPS etc. — os arquivos `discloud.config` e `squarecloud.config` já
   estão inclusos).
2. Confira `settings/credenciais.json` e `config.json` para garantir que
   tokens e configurações de pagamento (PIX) ainda são os corretos para
   esse ambiente.
3. Instale as dependências: `pip install -r requirements.txt`
   (SQLite já vem embutido no Python, não precisa instalar nada a mais).
4. Rode `start.py` (ou `bot.py` diretamente, conforme seu fluxo atual).

## Recomendação de segurança
Sistemas de pagamento merecem cautela extra: antes de apontar para
produção com usuários reais, rode em um ambiente de teste e confirme que
uma compra e um pagamento PIX completo funcionam ponta a ponta. Eu validei
os dados migrados e o desempenho das consultas, mas não tenho como testar
o fluxo completo do bot (webhooks, gateways reais) fora do seu ambiente.
