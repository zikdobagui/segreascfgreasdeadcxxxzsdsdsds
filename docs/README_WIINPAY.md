# Integração WiinPay - Gateway de Pagamento

## 📋 Descrição

O WiinPay foi integrado como uma nova opção de gateway de pagamento no seu bot. Agora você pode aceitar pagamentos via PIX usando a API do WiinPay.

## ⚙️ Configuração

### 1. Obter Token da API

Primeiro, você precisa obter sua chave de API (token) do WiinPay. Entre em contato com o suporte do WiinPay para receber suas credenciais.

### 2. Configurar no Bot

1. Acesse o painel administrativo do bot
2. Vá em **Configurações de Pagamento**
3. Clique em **✏️ Token WiinPay**
4. Envie o token fornecido pelo WiinPay
5. Clique em **✅ Usar WiinPay** para ativar

## 🔧 Funcionalidades

### Criação de Pagamento

- **Endpoint**: `POST https://api.wiinpay.com.br/payment/create`
- **Valor mínimo**: R$ 3,00 (configurável)
- **Formato**: PIX com QR Code

### Parâmetros Enviados

```json
{
  "api_key": "sua_chave_api",
  "value": 10.50,
  "name": "Nome do Cliente",
  "email": "cliente@example.com",
  "description": "Recarga de saldo - ID_USUARIO",
  "webhook_url": "",
  "metadata": {
    "user_id"
tor momenay a qualqueiinPay e WshinPo Pago, Pue Mercadlternar entrde aê po- Vocte
ltaneamensimuways plas gateuporta múltiema s O sists
-15 minutoapós m tos expirapagamen
- Os  R$ 3,00Pay éPI Wiin Ao da valor mínim
- Orvações

## 📌 Obsey
inPao Wie dsuporttato com o m con
4. Entre ero de ernsagenst para me logs do bo os3. VerifiqueR$ 3,00)
mo (ima do mínior está acue o val. Confirme qmente
2ado corretanfigur está co o token seVerifiqueas:

1. probleme so de

Em cartupo🆘 S
## ervidor
interno do sro  Er **500**:s
- inválidoos vazios ou422**: Camp)
- **lidoinvá (token o autorizadoNã: 01**
- **4com sucessocriado ento 1**: Pagama

- **20 Respostigos de Cód# 📝es

# as transaçõdashados de toalogs detvação
- L aprode apósica do QR Coão automátdos
- Remoçplicaamentos duação de pag Verificuração
-configrquivo de o agura nrma se fozenado de Token armaa

-# 🔒 Seguranço

#ansaçãa trata e hora do
- Dment pagaeferência do
- Rualnterior e at
- Saldo aeditado
- Total crdonus aplicacebido
- Bôor reo
- Val do usuáriIDcliente
- me do userna
- Nome e min recebe:rovado, o adento é apamndo um pagua
Q
istradordmino A# Para eal

## r em tempo saldozação do
- Atualiaprovadomento agaficação de p
- Notiia e colam código cope do PIX co QR Codiente

- Para o Cl
###ificações


## 📊 Notpositado o valor deregem sobentam porc ealculados é cnu- O bôado
gurfio cono mínim igual aouor maior  depósito fr do- O valodo quando:
 configura o bônusticamentemauto aplica asistematico

O utomá### Bônus Aamento

uardando pagding**: Ag
- 🔄 **penlado canceo ouiradgamento expcelled**: Pad/can*expirente
- ⏰ *automaticameeditado  saldo crrovado -o apentPagamapproved**: ✅ **paid/nutos:

- é 15 midos por atda 3 segungamento a cas do pante o statuticametomarifica au
O bot ve
camátitorificação AuVe

### `}
``  }
suario"
ame": "uern"us   ,
 56"234: "1