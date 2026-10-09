from app import estoque_api
import os
import json
import time
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

PROMO_FILE = os.path.join('database', 'promocoes.json')

def load_promos():
    if not os.path.exists(PROMO_FILE):
        return {}
    try:
        with open(PROMO_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_promos(data):
    os.makedirs(os.path.dirname(PROMO_FILE), exist_ok=True)
    with open(PROMO_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def registrar_handlers(bot, api, entregar_func):

    # =========================================================
    # LÓGICA DE EXIBIÇÃO E COMPRA DE PROMOÇÕES (CLIENTE)
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data == 'mostrar_promocoes')
    def callback_mostrar_promocoes(call):
        promos = load_promos()
        servicos_disponiveis = []

        def verificar_estoque(promo_data):
            try:
                for item, qtd_necessaria in promo_data.get('itens', {}).items():
                    if api.ControleLogins.pegar_estoque(item) < qtd_necessaria:
                        return False
            except Exception:
                return False
            return True

        for nome, data in promos.items():
            if verificar_estoque(data):
                servicos_disponiveis.append({"nome": nome, "valor": data['valor']})

        markup = InlineKeyboardMarkup(row_width=1)
        if not servicos_disponiveis:
            markup.add(InlineKeyboardButton('❌ Nenhuma promoção ativa', callback_data='noop'))
        else:
            for p in servicos_disponiveis:
                nome = p["nome"]
                valor = p["valor"]
                markup.add(InlineKeyboardButton(f"🎉 {nome} - R${float(valor):.2f}", callback_data=f"exibir_promocao {nome}"))

        markup.add(InlineKeyboardButton('↩️ Voltar', callback_data='menu_premios'))
        
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="🎉 <b>Nossas Promoções Especiais:</b>",
                parse_mode='HTML',
                reply_markup=markup
            )
        except Exception:
            bot.send_message(call.message.chat.id, "🎉 <b>Nossas Promoções Especiais:</b>", parse_mode='HTML', reply_markup=markup)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('exibir_promocao '))
    def callback_exibir_promocao(call):
        try:
            nome_promo = call.data.replace('exibir_promocao ', '', 1).strip()
            promos = load_promos()
            promo_data = promos.get(nome_promo)

            if not promo_data:
                return bot.answer_callback_query(call.id, "Promoção esgotada ou removida.", show_alert=True)

            itens = promo_data.get('itens', {})
            itens_str = "\n".join([f" - {item} (x{qtd})" for item, qtd in itens.items()]) if itens else " - (sem itens)"
            valor_promo = float(promo_data.get('valor', 0))

            texto = (
                f"🎉 <b>Promoção: {nome_promo}</b>\n\n"
                f"💰 <b>Valor:</b> R${valor_promo:.2f}\n"
                f"ℹ️ <b>Descrição:</b> {promo_data.get('descricao', '—')}\n\n"
                f"<b>Itens Inclusos:</b>\n{itens_str}"
            )

            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton('✅ Comprar Promoção', callback_data=f'comprar_promocao {nome_promo}'))
            markup.row(InlineKeyboardButton('↩️ Voltar', callback_data='mostrar_promocoes'))

            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=texto,
                parse_mode='HTML',
                reply_markup=markup
            )
        except Exception as e:
            bot.answer_callback_query(call.id, f"Erro: {e}", show_alert=True)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('comprar_promocao '))
    @estoque_api.serializar(bot)
    def callback_comprar_promocao(call):
        try:
            nome_promo = call.data.replace('comprar_promocao ', '', 1).strip()
            user_id = call.from_user.id

            promos = load_promos()
            promo_data = promos.get(nome_promo)
            if not promo_data:
                return bot.answer_callback_query(call.id, "Promoção não encontrada.", show_alert=True)

            valor_promo = float(promo_data.get('valor', 0))
            saldo_user = float(api.InfoUser.saldo(user_id))

            if saldo_user < valor_promo:
                falta = valor_promo - saldo_user
                bot.answer_callback_query(call.id, "Saldo insuficiente!", show_alert=False)

                markup_pix = InlineKeyboardMarkup()
                markup_pix.row(InlineKeyboardButton(f"💳 Depositar R$ {falta:.2f} via PIX", callback_data=f"pix_quick {falta:.2f}"))
                markup_pix.row(InlineKeyboardButton("↩️ Voltar à Promoção", callback_data=f"exibir_promocao {nome_promo}"))

                texto_falta = (
                    f"❌ <b>Saldo Insuficiente</b>\n\n"
                    f"Faltam <b>R$ {falta:.2f}</b> para você adquirir o pacote promocional: <i>{nome_promo}</i>.\n\n"
                    f"👇 Clique no botão abaixo para gerar o PIX no valor exato que falta e concluir sua compra:"
                )

                try:
                    bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text=texto_falta,
                        parse_mode='HTML',
                        reply_markup=markup_pix
                    )
                except Exception:
                    bot.send_message(call.message.chat.id, texto_falta, parse_mode='HTML', reply_markup=markup_pix)
                return

            logins_para_entregar = []
            
            # 1. Verificação dupla de segurança no estoque
            for item, qtd_necessaria in promo_data.get('itens', {}).items():
                if api.ControleLogins.pegar_estoque(item) < qtd_necessaria:
                    return bot.answer_callback_query(call.id, f"O estoque de '{item}' acabou enquanto você decidia. Tente depois.", show_alert=True)

            # A API reserva por unidade: em falha parcial cobra só a parte entregue.
            total_unidades = sum(int(q) for q in promo_data.get('itens', {}).values())
            if total_unidades < 1:
                return bot.answer_callback_query(call.id, "Promoção sem produtos.", show_alert=True)
            total_centavos = round(valor_promo * 100)
            parcela, resto = divmod(total_centavos, total_unidades)
            total_pago = 0.0
            indice = 0
            interrompido = False
            for item, qtd_necessaria in promo_data.get('itens', {}).items():
                if interrompido:
                    break
                for unidade in range(int(qtd_necessaria)):
                    preco = (parcela + (1 if indice < resto else 0)) / 100
                    try:
                        login_data = estoque_api.comprar(api, item, user_id,
                            f"promo:{user_id}:{call.message.message_id}:{indice}", preco)
                    except estoque_api.EstoqueAPIError as exc:
                        bot.send_message(user_id, str(exc))
                        interrompido = True
                        break
                    if not login_data:
                        interrompido = True
                        break
                    indice += 1
                    logins_para_entregar.append(login_data)
                    total_pago += preco
                    nome, valor, email, senha, descricao, duracao = login_data
                    entregar_func(call.message, nome, valor, email, senha, descricao, duracao)
            bot.answer_callback_query(call.id, "Processamento finalizado.", show_alert=False)
            saldo_final = float(api.InfoUser.saldo(user_id))
            bot.send_message(
                user_id,
                f"🎉 <b>Resumo da Promoção: {nome_promo}</b> 🎉\n\n"
                f"Entregues {len(logins_para_entregar)} de {total_unidades} acessos do pacote.\n"
                f"Valor pago: R${total_pago:.2f}\n"
                f"Seu saldo atualizado: R${saldo_final:.2f}",
                parse_mode='HTML'
            )
        except Exception as e:
            bot.answer_callback_query(call.id, f"Erro na compra: {e}", show_alert=True)

    # =========================================================
    # GERENCIAMENTO E CONFIGURAÇÃO DE PROMOÇÕES (ADMINISTRADOR)
    # =========================================================
    @bot.callback_query_handler(func=lambda call: call.data == 'configurar_promocoes')
    def handle_configurar_promocoes(call):
        if not (api.Admin.verificar_admin(call.message.chat.id) or int(call.message.chat.id) == int(api.CredentialsChange.id_dono())):
            return bot.answer_callback_query(call.id, "🚫 Acesso Negado!", show_alert=True)

        texto = "🎉 <b>Gerenciamento de Promoções Especiais</b>\n\nSelecione uma opção abaixo para configurar."
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton('➕ Criar Promoção', callback_data='promo_criar_novo'))
        markup.row(InlineKeyboardButton('📋 Listar/Excluir', callback_data='promo_listar_todos'))
        markup.row(InlineKeyboardButton('↩ Voltar ao Painel Admin', callback_data='voltar_paineladm'))

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=texto,
            parse_mode='HTML',
            reply_markup=markup
        )

    @bot.callback_query_handler(func=lambda call: call.data == 'promo_criar_novo')
    def callback_promo_criar_novo(call):
        bot.answer_callback_query(call.id)
        msg = bot.send_message(
            call.message.chat.id,
            "PASSO 1/4: Digite o nome para a nova promoção (ex: Promocão Fim de Semana).",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, process_promo_nome)

    def process_promo_nome(message):
        promo_data = {'nome': message.text.strip()}
        msg = bot.reply_to(message, "PASSO 2/4: Digite o valor total da promoção (ex: 25.50).", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_promo_valor, promo_data)

    def process_promo_valor(message, promo_data):
        try:
            promo_data['valor'] = float(message.text.strip().replace(',', '.'))
        except ValueError:
            return bot.reply_to(message, "Valor inválido. Operação Cancelada.")
        msg = bot.reply_to(message, "PASSO 3/4: Digite uma breve descrição para a promoção (mostrada ao cliente).", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_promo_descricao, promo_data)

    def process_promo_descricao(message, promo_data):
        promo_data['descricao'] = message.text.strip()
        msg = bot.reply_to(
            message,
            (
                "PASSO 4/4: Especifique os produtos inclusos e a quantidade deles.\n\n"
                "Use o formato exato: Produto:Quantidade\n"
                "Separe múltiplos itens com uma nova linha (Enter).\n\n"
                "Exemplo:\nNetflix Tela:1\nDisney+ Conta:2"
            ),
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, process_promo_itens, promo_data)

    def process_promo_itens(message, promo_data):
        itens_texto = message.text.strip().split('\n')
        itens_dict = {}
        erros = []
        
        try:
            servicos_disponiveis = list(set([s['nome'] for s in api.ControleLogins.pegar_servicos()]))
        except Exception:
            servicos_disponiveis = []

        for linha in itens_texto:
            try:
                nome, qtd_str = linha.split(':')
                nome = nome.strip()
                qtd = int(qtd_str.strip())
                if nome not in servicos_disponiveis:
                    erros.append(f"O produto '{nome}' não existe ou está escrito diferente do estoque.")
                    continue
                itens_dict[nome] = qtd
            except Exception:
                erros.append(f"Formato inválido na linha: '{linha}'")

        if erros:
            return bot.reply_to(message, "❌ Erros encontrados:\n" + "\n".join(erros) + "\n\nA Promoção foi cancelada. Tente novamente.")

        promo_data['itens'] = itens_dict
        promos = load_promos()
        promos[promo_data['nome']] = promo_data
        save_promos(promos)
        bot.reply_to(message, f"✅ Promoção '{promo_data['nome']}' criada com sucesso no sistema!")

    @bot.callback_query_handler(func=lambda call: call.data == 'promo_listar_todos')
    def callback_promo_listar_todos(call):
        promos = load_promos()
        if not promos:
            return bot.answer_callback_query(call.id, "Nenhuma promoção cadastrada.", show_alert=True)

        texto = "🎉 <b>Promoções Atuais no Banco de Dados:</b>\n\n"
        markup = InlineKeyboardMarkup()
        for nome, data in promos.items():
            itens_str = ", ".join([f"{i} (x{q})" for i, q in data['itens'].items()])
            texto += f"<b>{nome}</b> - R${data['valor']:.2f}\n  - Pacote: <i>{itens_str}</i>\n\n"
            markup.add(InlineKeyboardButton(f'❌ Excluir: {nome}', callback_data=f'promo_excluir|{nome}'))

        markup.add(InlineKeyboardButton('↩ Voltar', callback_data='configurar_promocoes'))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=texto, parse_mode='HTML', reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('promo_excluir|'))
    def callback_promo_excluir(call):
        nome_promo = call.data.split('|', 1)[1]
        promos = load_promos()
        if nome_promo in promos:
            del promos[nome_promo]
            save_promos(promos)
            bot.answer_callback_query(call.id, f"Promoção '{nome_promo}' excluída.", show_alert=True)
            callback_promo_listar_todos(call)
        else:
            bot.answer_callback_query(call.id, "Promoção não encontrada.", show_alert=True)
