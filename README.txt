Handlers de confirmacao inseridos ANTES do handler generico e com exclusoes no decorador.


Organização do código
Os 12 arquivos modulo_*.py e failover_pagamentos.py foram incorporados ao bot.py,
em seções identificadas e na mesma ordem de execução. Edite essas rotinas no bot.py.
Os demais módulos continuam separados porque possuem imports próprios.
Inicialização: python start.py (supervisor) ou python bot.py (somente o bot).
Cópia do código anterior: backups/codigo_antes_consolidacao.zip.

Mais módulos reunidos:
- interface.py: menus, perfil, fotos, rankings e favoritos.
- notificacoes.py: alertas PIX, vencimentos, acessos, abandono e antiflood.
- suporte.py: logs e encerramento seguro.
Os 13 arquivos substituídos foram removidos e os imports atualizados.
Backup: backups/codigo_antes_segunda_consolidacao.zip.

Organização por pastas
- app/: todo o código do bot e módulos de suporte.
- docs/: guias e documentação.
- tests/: testes automatizados.
- tools/: ferramentas de migração.
- assets/ e textos/: imagens e mensagens.
- database/, data/ e settings/: dados e configurações.
- backups/: cópias de segurança.

Iniciar tudo: python start.py
Iniciar somente o bot: python bot.py
Atualizar usernames: python -m app.update_usernames
Testes: python -m unittest discover -s tests -v
Os comandos devem ser executados na raiz do projeto.
Os caminhos bot.py, interface.py, notificacoes.py e suporte.py citados acima
agora correspondem aos arquivos dentro de app/.
Backup anterior à organização: backups/codigo_antes_organizacao_pastas.zip.
