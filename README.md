# Bot Telegram

Código do bot com restauração das pastas `database/`, `textos/` e `data/`
por ZIP enviado pelo dono no privado. Consulte
[as instruções de restauração](docs/RESTAURAR_DADOS.md).

## Instalação e configuração privada

```sh
python -m pip install -r requirements.txt
python bot.py
```

Antes de iniciar, transfira as configurações privadas da instalação existente
para o servidor, em especial `settings/credenciais.json` (token do Telegram,
ID do dono e demais opções). Preserve também as outras configurações de
`settings/` e os arquivos JSON privados da raiz usados pela sua instalação.
Esses arquivos não são publicados neste repositório. Um clone sozinho não
contém a configuração necessária para colocar o bot em funcionamento.

Se utilizar VirtualPay, configure `VIRTUALPAY_TOKEN` no ambiente da hospedagem
ou crie `settings/virtualpay.json` com a estrutura `{"token": "SUA_CHAVE"}`.
O arquivo local é ignorado pelo Git. O bot não carrega arquivos `.env`
automaticamente.

Depois de iniciar o bot configurado, use `/restaurar_dados` para enviar os
dados existentes. O arquivo ZIP precisa conter as três pastas na raiz.
O comando é exclusivo do dono e solicita confirmação antes da substituição.

## Discloud

O ponto de entrada está definido em `discloud.config` como `bot.py`.
O launcher reinicia o processo após uma restauração para reabrir o banco e
recarregar os dados. `python start.py` também é suportado.

O `.gitignore` impede o envio de dados e segredos para o Git; ele não define
a persistência de arquivos na hospedagem. Antes de ativar deploy automático,
confirme a preservação das configurações e dados entre deploys e mantenha
um backup externo. A integração de deploy ainda precisa ser configurada na
Discloud.

## Testes

```sh
python -m unittest discover -s tests -v
```
