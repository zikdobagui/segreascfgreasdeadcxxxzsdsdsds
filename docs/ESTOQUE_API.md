# Estoque de revenda

Depois de reiniciar o bot, abra `/admin` no privado e escolha **API de estoque**.

1. Use **Definir chave** para cadastrar o valor completo de `X-Stock-Key`.
2. Use **Testar conexão** para consultar produtos e quantidades, sem gastar saldo.
   Falhas aparecem no privado do administrador com a operação, o código HTTP e
   o corpo real da resposta, inclusive HTML ou texto (com chave e campos de
   credenciais ocultados). Respostas longas exibem os primeiros 1500 caracteres
   e um aviso de truncamento. `403` indica acesso negado pelo servidor, sem
   presumir problema de saldo. `401 unauthorized`
   significa que o fornecedor recusou a chave: confirme ou gere uma nova
   `X-Stock-Key` no bot raiz e cadastre novamente. A chave anterior é preservada
   quando o teste da nova chave falha. Erros de rede, TLS e tempo limite também
   são identificados, sem repetir reservas automaticamente.
3. Configure **Lucro em porcentagem**: `50` ou `50%` acrescenta 50% ao custo
   de todos os produtos (R$ 10 vira R$ 15). O preço acompanha o custo da API,
   arredondado para centavos. **Ver custos e ganhos** exibe a prévia ao admin.
   O ganho exibido é bruto, antes de taxas, cashback e descontos de promoções.
   **Usar preços fixos** desativa a porcentagem global e permite configurar
   `NOME EXATO DO PRODUTO | PREÇO FINAL`. Nesse modo, sem preço definido,
   o bot usa o valor informado no catálogo da API.
4. Confira **Duração padrão**. Quando o fornecedor não informar duração, são
   usados 30 dias por padrão; esse valor pode ser alterado no painel.

O fornecedor é `https://vendasdoramon.squareweb.app`. Consultas usam
`GET /api/stock`; compras normais, inline, quantidade, carrinho, promoções e
trocas usam `POST /api/stock/reserve`, com `service`, `buyer_id` e `sale_id`.
Cada reserva também desconta o custo do saldo do revendedor no bot raiz,
inclusive quando for uma troca oferecida gratuitamente ao cliente.

O bot não usa `database/acessos.json` como estoque nem como alternativa se a
API falhar. Os comandos antigos de abastecimento, remoção e renomeação foram
desativados; essas operações devem ser realizadas no fornecedor. Históricos
de compras e acessos já entregues continuam locais.

As configurações ficam em `settings/estoque_api.json`, criado ao salvar pelo
painel. A chave não aparece por inteiro nas mensagens do painel.
Não publique esse arquivo nem os bancos com credenciais de clientes.

Reservas ficam em `database/reservas_api.sqlite3`. Um pedido já registrado
não dispara outro POST, mesmo após reiniciar. **Conferir reservas** mostra os
últimos pedidos e permite ao administrador recuperar os acessos recebidos.
`recebida` significa que a API retornou um acesso e ele foi salvo; não comprova
que o Telegram entregou a mensagem. `pendente`/`verificar` exigem conferir o
pedido no fornecedor antes de fazer uma nova reserva. Não há endpoint
documentado para consultar ou cancelar uma reserva incerta.

Falhas de reserva estornam a cobrança daquela unidade no saldo do cliente.
Carrinho cobra somente as unidades reservadas. Promoções dividem o preço do
pacote entre as unidades (com ajuste de centavos) e cobram apenas as reservadas
se houver falha parcial. Interrupção do processo durante uma operação exige
conferir o saldo local e a reserva no fornecedor.

Validação local: `python -m unittest discover -s tests -v`.
Os testes usam respostas simuladas, sem efetuar reservas reais.
O formato autenticado do catálogo ainda precisa ser validado com a chave:
a documentação fornecida não incluía exemplo do retorno de `GET /api/stock`.
Formatos não reconhecidos são rejeitados, sem recorrer ao estoque local.
