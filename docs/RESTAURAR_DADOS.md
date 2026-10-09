# Restaurar database, textos e data pelo Telegram

Inicie por `python bot.py` ou `python start.py`. O `discloud.config` já aponta
para `bot.py`. O launcher mantém o bot em um processo separado e só troca os
arquivos depois que esse processo terminou; as conexões SQLite e os caches são
reabertos com os novos dados. Não execute `app/bot.py` diretamente.

1. Pare o bot de origem antes de compactar os dados. Se existirem arquivos
   `bot.db-wal` ou outros auxiliares do SQLite, inclua-os: podem conter dados
   que ainda não foram incorporados ao arquivo principal.
2. Crie um ZIP com **as três pastas diretamente na raiz**, sem pasta externa:

   ```text
   dados.zip
   ├── database/
   │   ├── bot.db
   │   └── ...
   ├── textos/
   │   └── ...
   └── data/
       └── ...
   ```

3. No privado do bot de destino, com a conta do dono configurado, envie
   `/restaurar_dados` e depois o ZIP como documento.
4. Confira o resumo e clique em **Substituir e reiniciar** em até 10 minutos.
   Para desistir, use o botão Cancelar ou `/cancelar_restauracao`.
5. Aguarde a mensagem de resultado após o reinício.

A substituição é integral: arquivos antigos ausentes no ZIP também saem das
três pastas. Nada é mesclado. Evite fazer isso durante compras/pagamentos em
andamento, pois a restauração volta ao estado do ZIP e reinicia as tarefas.
Credenciais em `settings/`, código e demais pastas não são importados.

Limites: ZIP até 20 MB (download da API padrão do Telegram), conteúdo expandido
até 200 MB, até 10.000 entradas. As três pastas são obrigatórias, podendo
`data/` e `textos/` estar vazias. `database/bot.db` precisa ser SQLite válido e
conter a tabela `users` com `user_id`, `data` e `saldo`. JSONs precisam ser UTF-8
válido. Arquivos fora das três pastas, links, caminhos relativos perigosos e
entradas duplicadas são recusados. O WAL recebido é incorporado em staging.
Referência do limite: https://core.telegram.org/bots/faq#how-do-i-download-files

Antes da troca, as pastas anteriores são movidas integralmente para
`.data_restore/backups/<identificador>/`, incluindo os auxiliares SQLite.
Esse backup fica no servidor, não é enviado ao Telegram nem removido pela
rotação dos backups normais. Mantenha uma cópia externa antes da migração;
um backup no próprio servidor não protege contra perda da hospedagem.

Falha durante a troca provoca reversão automática. Um journal permite reverter
uma troca interrompida na próxima inicialização, antes de importar o código
do bot. Se a própria reversão falhar, o launcher não inicia o bot com dados
parcialmente substituídos. Uma falha posterior de compatibilidade na execução
não provoca reversão automática: recupere o backup manualmente com o bot
parado, ou corrija a incompatibilidade. A validação estrutural não garante
compatibilidade de todo o conteúdo com todas as funcionalidades.

Para recuperar manualmente, pare a aplicação inteira, guarde as três pastas
atuais em outro local e copie `database`, `textos` e `data` do backup desejado
para a raiz. Só então reinicie. Nunca troque arquivos SQLite com o bot rodando.
Os backups antigos não expiram automaticamente; acompanhe o espaço em disco.

Essa funcionalidade importa dados; ela não configura deploy pelo Git nem muda
a política de persistência da Discloud. Quando preparar o repositório, exclua
`database/`, `textos/`, `data/`, `.data_restore/`, backups e credenciais do Git
e do pacote de atualização conforme a estratégia de deploy escolhida.
