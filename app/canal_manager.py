from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply

# Variáveis globais para compartilhar as instâncias do bot.py
bot = None
api = None
painel_admin = None
handle_start = None

def init_canal(bot_instance, api_module, painel_func, start_func):
    """Inicializa o módulo do canal passando as dependências do bot.py"""
    global bot, api, painel_admin, handle_start
    bot = bot_instance
    api = api_module
    painel_admin = painel_func
    handle_start = start_func
    registrar_handlers()

def verificar_inscricao_canal(user_id):
    """Verifica inscrição com relatórios de erro no terminal (DEBUG)."""
    print(f"\n--- VERIFICANDO USUÁRIO {user_id} ---")
    
    if not api.CanalObrigatorio.status_ativo():
        print("CANAL OBRIGATÓRIO DESATIVADO: Liberando acesso.")
        return True
    
    ID_CANAL_OBRIGATORIO = api.CanalObrigatorio.get_id_canal()
    
    if ID_CANAL_OBRIGATORIO == "@NOMEDOCANAL": 
        print("ALERTA: ID do canal não foi alterado no código! Liberando acesso.")
        return True
        
    try:
        member = bot.get_chat_member(ID_CANAL_OBRIGATORIO, user_id)
        if member.status in ['creator', 'administrator', 'member']:
            print("RESULTADO: Acesso Permitido (Usuário está no canal).")
            return True
            
        print("RESULTADO: Acesso Bloqueado (Usuário NÃO está no canal).")
        return False
    except Exception as e:
        print(f"ERRO CRÍTICO: O bot falhou ao verificar o canal.")
        print(f"MENSAGEM DE ERRO: {e}")
        return True

def obter_markup_canal():
    """Gera os botões com o link para o canal"""
    LINK_CANAL_OBRIGATORIO = api.CanalObrigatorio.get_link_canal()
    markup_canal = InlineKeyboardMarkup()
    markup_canal.add(InlineKeyboardButton("🔗 Entrar no Canal", url=LINK_CANAL_OBRIGATORIO))
    markup_canal.add(InlineKeyboardButton("✅ Já Entrei / Confirmar", callback_data="check_subscription"))
    return markup_canal

def registrar_handlers():
    # TRUQUE DE PRIORIDADE: Salva os handlers antigos para forçar os novos no topo
    callbacks_antigos = list(bot.callback_query_handlers)
    bot.callback_query_handlers.clear()

    @bot.callback_query_handler(func=lambda call: call.data == 'check_subscription')
    def callback_check_subscription(call):
        try:
            if verificar_inscricao_canal(call.from_user.id):
                bot.answer_callback_query(call.id, "✅ Inscrição confirmada!")
                try:
                    bot.delete_message(call.message.chat.id, call.message.message_id)
                except: pass
                
                # Simula o comando /start novamente
                call.message.from_user = call.from_user
                handle_start(call.message)
            else:
                bot.answer_callback_query(call.id, "❌ Você ainda não entrou no canal!", show_alert=True)
        except Exception as e:
            print(f"Erro no check_subscription: {e}")

    @bot.callback_query_handler(func=lambda c: c.data == 'config_canal_obrigatorio')
    def callback_config_canal_obrigatorio(call):
        bot.answer_callback_query(call.id)
        status_ativo = api.CanalObrigatorio.status_ativo()
        id_canal = api.CanalObrigatorio.get_id_canal()
        link_canal = api.CanalObrigatorio.get_link_canal()
        
        status_emoji = "🟢 ATIVO" if status_ativo else "🔴 DESATIVADO"
        status_texto = "Os usuários PRECISAM entrar no canal para usar o bot." if status_ativo else "Os usuários NÃO precisam entrar no canal."
        
        texto = (
            f"🔒 <b>Configuração de Canal Obrigatório</b>\n\n"
            f"<b>Status Atual:</b> {status_emoji}\n"
            f"{status_texto}\n\n"
            f"<b>ID do Canal:</b> <code>{id_canal}</code>\n"
            f"<b>Link do Canal:</b> {link_canal}\n\n"
            f"<i>Use os botões abaixo para gerenciar:</i>"
        )
        
        markup = InlineKeyboardMarkup()
        btn_toggle_text = "🔴 Desativar" if status_ativo else "🟢 Ativar"
        markup.row(InlineKeyboardButton(btn_toggle_text, callback_data='toggle_canal_obrigatorio'))
        markup.row(
            InlineKeyboardButton('✏️ Editar ID do Canal', callback_data='editar_id_canal'),
            InlineKeyboardButton('✏️ Editar Link', callback_data='editar_link_canal')
        )
        markup.row(InlineKeyboardButton('↩ Voltar ao Painel', callback_data='voltar_paineladm'))
        
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=texto, parse_mode='HTML', reply_markup=markup)

    @bot.callback_query_handler(func=lambda c: c.data == 'toggle_canal_obrigatorio')
    def callback_toggle_canal_obrigatorio(call):
        bot.answer_callback_query(call.id)
        novo_status = api.CanalObrigatorio.alternar_status()
        status_texto = "ativado" if novo_status else "desativado"
        bot.answer_callback_query(call.id, f"✅ Canal obrigatório {status_texto}!", show_alert=True)
        callback_config_canal_obrigatorio(call)

    @bot.callback_query_handler(func=lambda c: c.data == 'editar_id_canal')
    def callback_editar_id_canal(call):
        bot.answer_callback_query(call.id)
        msg = bot.send_message(
            call.message.chat.id,
            "📝 <b>Digite o novo ID do canal:</b>\n\n<i>Exemplo: -1002787400901</i>\n<i>O ID deve começar com '-' para canais/grupos.</i>",
            parse_mode='HTML', reply_markup=ForceReply(selective=True)
        )
        bot.register_next_step_handler(msg, handle_editar_id_canal)

    def handle_editar_id_canal(message):
        novo_id = message.text.strip()
        try:
            api.CanalObrigatorio.set_id_canal(novo_id)
            bot.reply_to(message, f"✅ ID do canal atualizado para: <code>{novo_id}</code>", parse_mode='HTML')
        except Exception as e:
            bot.reply_to(message, f"❌ Erro ao atualizar ID: {e}")
        painel_admin(message)

    @bot.callback_query_handler(func=lambda c: c.data == 'editar_link_canal')
    def callback_editar_link_canal(call):
        bot.answer_callback_query(call.id)
        msg = bot.send_message(
            call.message.chat.id,
            "📝 <b>Digite o novo link do canal:</b>\n\n<i>Exemplo: https://t.me/seu_canal</i>",
            parse_mode='HTML', reply_markup=ForceReply(selective=True)
        )
        bot.register_next_step_handler(msg, handle_editar_link_canal)

    def handle_editar_link_canal(message):
        novo_link = message.text.strip()
        try:
            api.CanalObrigatorio.set_link_canal(novo_link)
            bot.reply_to(message, f"✅ Link do canal atualizado!", parse_mode='HTML')
        except Exception as e:
            bot.reply_to(message, f"❌ Erro ao atualizar link: {e}")
        painel_admin(message)

    # DEVOLVE OS ANTIGOS PRO FINAL DA LISTA (Garante prioridade 1 para os do canal)
    bot.callback_query_handlers.extend(callbacks_antigos)
