"""Configuração da API restrita a administradores em conversa privada."""
import html
import json

from app import estoque_api


def registrar(bot, api):
    from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

    def autorizado(user_id, chat):
        return chat.type == 'private' and (str(user_id) == str(api.CredentialsChange.id_dono()) or api.Admin.verificar_admin(user_id))

    def menu(chat_id):
        cfg = estoque_api.config()
        key = cfg.get('key', '')
        masked = ('••••' + key[-4:]) if len(key) > 4 else ('configurada' if key else 'não configurada')
        markup = InlineKeyboardMarkup()
        pricing = (f'Acréscimo sobre o custo: <b>{html.escape(str(cfg.get("porcentagem_lucro", 0)))}%</b> em todos os produtos.\n'
                   if cfg.get('modo_preco') == 'porcentagem' else 'Preços fixos; sem ajuste, vale o custo informado pela API.\n')
        for label, action in [('🔑 Definir chave', 'chave'), ('🔎 Testar conexão', 'teste'),
                              ('📈 Lucro em porcentagem', 'porcentagem'), ('💰 Usar preços fixos', 'preco'),
                              ('👀 Ver custos e ganhos', 'previa'), ('⏳ Duração padrão', 'duracao'),
                              ('📋 Conferir reservas', 'reservas')]:
            markup.row(InlineKeyboardButton(label, callback_data='stock_api_' + action))
        markup.row(InlineKeyboardButton('↩ Voltar', callback_data='voltar_paineladm'))
        bot.send_message(chat_id,
            '🌐 <b>API de estoque</b>\n\nFornecedor: vendasdoramon.squareweb.app\n'
            f'Chave: <code>{html.escape(masked)}</code>\n'
            'Estoque e acessos vêm exclusivamente da API.\n'
            'O custo é descontado do seu saldo no bot raiz em cada reserva, inclusive trocas.\n'
            + pricing +
            f'Duração quando o fornecedor não informar: {cfg.get("duracao_padrao", 30)} dias.',
            parse_mode='HTML', reply_markup=markup)

    def receber(message, action, owner):
        if message.from_user.id != owner or not autorizado(owner, message.chat):
            return
        value = (message.text or '').strip()
        if value.lower() in ('/cancel', '/cancelar', 'cancelar'):
            return menu(message.chat.id)
        try:
            if action == 'chave':
                try:
                    bot.delete_message(message.chat.id, message.message_id)
                except Exception:
                    pass
                if not value or any(c.isspace() for c in value):
                    raise ValueError('Envie apenas a chave, sem espaços.')
                estoque_api.catalogo(key=value)
                estoque_api.salvar_config(key=value)
            elif action == 'preco':
                name, price = value.rsplit('|', 1)
                if not api.ControleLogins.mudar_valor_por_nome(name.strip(), float(price.strip().replace(',', '.'))):
                    raise ValueError('Produto não encontrado ou preço inválido.')
            elif action == 'porcentagem':
                estoque_api.definir_porcentagem(value)
            elif action == 'duracao':
                days = int(value)
                if days < 1 or days > 3650:
                    raise ValueError('Use uma duração de 1 a 3650 dias.')
                estoque_api.salvar_config(duracao_padrao=days)
            bot.send_message(message.chat.id, '✅ Configuração salva.')
        except estoque_api.EstoqueAPIError as exc:
            bot.send_message(message.chat.id, f'Não foi possível salvar:\n{exc.diagnostico}', parse_mode=None)
        except ValueError:
            bot.send_message(message.chat.id, 'Não foi possível salvar: valor ou formato inválido. Confira o formato solicitado.', parse_mode=None)
        except OSError:
            bot.send_message(message.chat.id, 'Não foi possível salvar a configuração no disco. Verifique as permissões da pasta settings e o espaço disponível.', parse_mode=None)
        menu(message.chat.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith('stock_api_'))
    def callback(call):
        if not autorizado(call.from_user.id, call.message.chat):
            return bot.answer_callback_query(call.id, 'Acesso restrito ao admin no privado.', show_alert=True)
        bot.answer_callback_query(call.id)
        action = call.data.removeprefix('stock_api_')
        if action == 'menu':
            return menu(call.message.chat.id)
        if action == 'teste':
            try:
                rows = estoque_api.catalogo()
                bot.send_message(call.message.chat.id, f'✅ API conectada: {len(rows)} produtos, {sum(r["quantidade"] for r in rows)} unidades. Nenhuma reserva realizada.')
            except estoque_api.EstoqueAPIError as exc:
                bot.send_message(call.message.chat.id, exc.diagnostico, parse_mode=None)
            return
        if action == 'previa':
            try:
                rows = estoque_api.catalogo()
                if not rows:
                    return bot.send_message(call.message.chat.id, 'Catálogo vazio.')
                for start in range(0, len(rows), 10):
                    text = '📈 Custos e preços de revenda\nGanho bruto antes de descontos e taxas:\n\n'
                    for row in rows[start:start + 10]:
                        text += (f'{row["nome"]}\nCusto: R$ {row["custo"]:.2f} | Venda: R$ {row["valor"]:.2f}'
                                 f' | Ganho: R$ {row["valor"] - row["custo"]:.2f}\n\n')
                    bot.send_message(call.message.chat.id, text)
            except estoque_api.EstoqueAPIError as exc:
                bot.send_message(call.message.chat.id, exc.diagnostico, parse_mode=None)
            return
        if action == 'reservas':
            with estoque_api.journal() as db:
                rows = db.execute('SELECT rowid, sale_id, buyer_id, service, status FROM reservas ORDER BY rowid DESC LIMIT 10').fetchall()
            text = '\n'.join(f'#{rowid} | {sale} | cliente {buyer} | {service} | {status}' for rowid, sale, buyer, service, status in rows)
            markup = InlineKeyboardMarkup()
            for rowid, sale, buyer, service, status in rows:
                if status == 'recebida':
                    markup.row(InlineKeyboardButton(f'Ver acesso #{rowid}', callback_data=f'stock_api_acesso_{rowid}'))
            bot.send_message(call.message.chat.id, ('Últimas reservas (recebida = acesso salvo; verificar = conferir no fornecedor):\n' + (text or 'Nenhuma reserva.'))[:4000], reply_markup=markup)
            return
        if action.startswith('acesso_'):
            with estoque_api.journal() as db:
                row = db.execute("SELECT buyer_id, service, access FROM reservas WHERE rowid=? AND status='recebida'", (action.removeprefix('acesso_'),)).fetchone()
            if row:
                access = json.loads(row[2])['access']
                bot.send_message(call.message.chat.id, f'Cliente: {row[0]}\nProduto: {row[1]}\nEmail: {access["email"]}\nSenha: {access["senha"]}')
            return
        prompts = {'chave': 'Envie a chave X-Stock-Key. Ela será testada antes de salvar.',
                   'preco': 'Isso troca o catálogo para preços fixos, desativando a porcentagem global. Envie NOME EXATO DO PRODUTO | PREÇO FINAL. Exemplo: Netflix | 25,00',
                   'porcentagem': 'Envie a porcentagem que deseja acrescentar ao custo de TODOS os produtos. Exemplo: 50 ou 50%. Custo R$ 10 → venda R$ 15. Substitui os preços fixos enquanto este modo estiver ativo. Ofertas e promoções continuam aplicando seus descontos.',
                   'duracao': 'Envie a duração em dias para produtos cuja API não informa duração.'}
        if action in prompts:
            msg = bot.send_message(call.message.chat.id, prompts[action] + '\n/cancelar para sair.')
            bot.register_next_step_handler(msg, receber, action, call.from_user.id)
