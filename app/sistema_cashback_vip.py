import json
import os
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
# CORREÇÃO: este módulo tinha load_user_vip_data/save_user_vip_data PRÓPRIOS,
# que liam/gravavam um JSON antigo em database/users/<id>.json — arquivos que
# nunca existiam de fato, pois o resto do bot já roda em cima do SQLite
# (database.py). Por isso o cashback nunca era processado (load retornava
# None e a função saía sem fazer nada) e o ranking/gasto sempre ficava
# zerado mesmo após compras reais. Agora usamos as MESMAS funções que o
# resto do bot usa para ler/gravar o saldo e os dados do usuário.
from app.database import load_user_data, save_user_data, get_all_user_ids

# Configuração Padrão dos Níveis VIP (agora dinâmica via config)
NIVEIS_VIP_PADRAO = {
    "BRONZE": {"gasto_minimo": 50.0, "cashback": 0, "emoji": "🥉"},
    "PRATA": {"gasto_minimo": 150.0, "cashback": 5, "emoji": "🥈"},
    "OURO": {"gasto_minimo": 300.0, "cashback": 10, "emoji": "🥇"},
    "DIAMANTE": {"gasto_minimo": 600.0, "cashback": 15, "emoji": "💎"}
}

ARQUIVO_CONFIG = 'database/config_cashback.json'

def carregar_config():
    if not os.path.exists('database'):
        os.makedirs('database')
        
    config_padrao = {
        "ativo": True, 
        "total_distribuido": 0.0,
        "auto_reset_dias": 0,
        "ultimo_reset": time.time(),
        "niveis_vip": NIVEIS_VIP_PADRAO
    }
    
    if os.path.exists(ARQUIVO_CONFIG):
        try:
            with open(ARQUIVO_CONFIG, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Mescla a configuração carregada com as chaves padrão caso falte alguma
                for key, value in config_padrao.items():
                    if key not in data:
                        data[key] = value
                return data
        except:
            return config_padrao
    return config_padrao

def salvar_config(data):
    with open(ARQUIVO_CONFIG, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def load_user_vip_data(user_id):
    return load_user_data(user_id)

def save_user_vip_data(user_id, data):
    save_user_data(user_id, data)

def verificar_auto_reset():
    """Verifica se já passou o tempo para zerar o ciclo VIP automaticamente."""
    config = carregar_config()
    dias_limite = config.get("auto_reset_dias", 0)
    
    if dias_limite <= 0:
        return # Desativado
        
    ultimo_reset = config.get("ultimo_reset", time.time())
    agora = time.time()
    segundos_limite = dias_limite * 86400 # Dias convertidos em segundos
    
    if (agora - ultimo_reset) >= segundos_limite:
        for uid in get_all_user_ids():
            try:
                data = load_user_data(uid)
                if not data:
                    continue

                mudou = False
                if 'gasto_semanal_vip' in data:
                    data['gasto_semanal_vip'] = 0.0
                    mudou = True
                if 'cashback_total_ganho' in data:
                    data['cashback_total_ganho'] = 0.0
                    mudou = True

                if mudou:
                    save_user_data(uid, data)
            except:
                continue

        config['ultimo_reset'] = agora
        salvar_config(config)

def obter_nivel_vip(gasto_semanal):
    config = carregar_config()
    niveis_vip = config.get("niveis_vip", NIVEIS_VIP_PADRAO)
    
    nivel_atual = {"nome": "INICIANTE", "cashback": 0, "emoji": "👶"}
    proximo_nivel = niveis_vip["BRONZE"]
    falta_para_proximo = niveis_vip["BRONZE"]["gasto_minimo"] - gasto_semanal

    for nome, dados in sorted(niveis_vip.items(), key=lambda x: x[1]["gasto_minimo"]):
        if gasto_semanal >= dados["gasto_minimo"]:
            nivel_atual = {"nome": nome, "cashback": dados["cashback"], "emoji": dados["emoji"]}
            proximo_nivel = None
            falta_para_proximo = 0
        elif proximo_nivel is None:
            proximo_nivel = dados
            falta_para_proximo = dados["gasto_minimo"] - gasto_semanal
            break
            
    return nivel_atual, proximo_nivel, falta_para_proximo

def processar_compra_cashback(bot, user_id, valor_compra):
    # Antes de processar a compra, verifica se precisa zerar o ciclo
    verificar_auto_reset()
    
    config = carregar_config()
    if not config.get("ativo", True):
        return

    user_data = load_user_vip_data(user_id)
    if not user_data:
        return

    # Atualiza o gasto semanal
    gasto_semanal = user_data.get('gasto_semanal_vip', 0.0) + valor_compra
    user_data['gasto_semanal_vip'] = gasto_semanal

    # Calcula o cashback baseado no nível atualizado
    nivel_atual, _, _ = obter_nivel_vip(gasto_semanal)
    cashback_pct = nivel_atual['cashback']
    
    if cashback_pct > 0:
        valor_cashback = valor_compra * (cashback_pct / 100.0)
        user_data['saldo'] = user_data.get('saldo', 0.0) + valor_cashback
        user_data['cashback_total_ganho'] = user_data.get('cashback_total_ganho', 0.0) + valor_cashback
        
        # Atualiza config global
        config['total_distribuido'] += valor_cashback
        salvar_config(config)

    # Notifica o usuário
        try:
            bot.send_message(
                user_id,
                f"🎉 <b>CASHBACK RECEBIDO!</b>\n\n"
                f"Por ser do nível <b>{nivel_atual['emoji']} {nivel_atual['nome']}</b>, recebeu <b>{cashback_pct}%</b> de volta nesta compra!\n\n"
                f"💰 <b>+ R$ {valor_cashback:.2f}</b> adicionados à sua carteira.",
                parse_mode='HTML'
            )
        except:
            pass

    save_user_vip_data(user_id, user_data)

# ==================== RANKING VIP ====================
def obter_ranking_vip():
    usuarios_vip = []

    for uid in get_all_user_ids():
        try:
            data = load_user_data(uid)
            if not data:
                continue

            gasto = float(data.get('gasto_semanal_vip', 0.0))
            ganho = float(data.get('cashback_total_ganho', 0.0))
            username = data.get('username', f"User {uid}")

            # Consideramos no ranking quem já ganhou cashback ou já gastou na semana
            if ganho > 0 or gasto > 0:
                usuarios_vip.append({
                    'id': uid,
                    'username': username,
                    'gasto': gasto,
                    'ganho': ganho
                })
        except:
            continue

    # Ordena pelo cashback total ganho (maior para menor)
    usuarios_vip.sort(key=lambda x: x['ganho'], reverse=True)
    return usuarios_vip[:20]  # Retorna os top 20

def exibir_ranking(bot, message, origem):
    # Verifica o tempo do ciclo antes de exibir o ranking!
    verificar_auto_reset()
    
    ranking = obter_ranking_vip()
    config = carregar_config()
    dias_auto = config.get("auto_reset_dias", 0)
    
    texto = "🏆 <b>RANKING DE CASHBACK VIP</b> 🏆\n\n"
    texto += "<i>Os maiores revendedores e acumuladores de cashback do nosso sistema!</i>\n\n"
    
    # --- CÁLCULO DE TEMPO RESTANTE PARA ZERAR ---
    if dias_auto > 0:
        ultimo_reset = config.get("ultimo_reset", time.time())
        tempo_restante = (ultimo_reset + (dias_auto * 86400)) - time.time()
        
        if tempo_restante > 0:
            dias_restantes = int(tempo_restante // 86400)
            horas_restantes = int((tempo_restante % 86400) // 3600)
            minutos_restantes = int((tempo_restante % 3600) // 60)
            
            if dias_restantes > 0:
                texto += f"⏳ <b>Atenção:</b> Falta {dias_restantes} dias e {horas_restantes} horas para o Cashback zerar!\n\n"
            elif horas_restantes > 0:
                texto += f"⏳ <b>Atenção:</b> Falta {horas_restantes} horas e {minutos_restantes} minutos para o Cashback zerar!\n\n"
            else:
                texto += f"⏳ <b>Atenção:</b> Falta {minutos_restantes} minutos para o Cashback zerar!\n\n"
        else:
            texto += "⏳ <b>Atenção:</b> O ciclo será zerado a qualquer momento!\n\n"
            
    if not ranking:
        texto += "Nenhum utilizador com dados de cashback registados ainda."
    else:
        for idx, u in enumerate(ranking):
            medalha = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else f"{idx+1}º"
            # Ocultando @ para proteger a privacidade
            user_display = str(u['username']).replace('@', '')
            texto += f"{medalha} <b>{user_display}</b>\n└ Cashback Acumulado: R$ {u['ganho']:.2f} | Gasto Semanal: R$ {u['gasto']:.2f}\n\n"
            
    markup = InlineKeyboardMarkup()
    if origem == "admin":
        markup.add(InlineKeyboardButton("↩️ Voltar ao Painel Admin VIP", callback_data="admin_cashback_vip"))
    else:
        markup.add(InlineKeyboardButton("↩️ Voltar ao Clube VIP", callback_data="painel_revenda_vip"))
        
    bot.edit_message_text(texto, chat_id=message.chat.id, message_id=message.message_id, parse_mode='HTML', reply_markup=markup)


# ==================== PAINEL DO CLIENTE ====================
def painel_revenda(bot, message):
    user_id = message.chat.id
    
    # Verifica o reset automático antes de exibir o painel
    verificar_auto_reset()
    
    # Verifica se o sistema VIP está ativo
    config = carregar_config()
    niveis_vip = config.get("niveis_vip", NIVEIS_VIP_PADRAO)
    
    if not config.get("ativo", True):
        texto = (
            "⚠️ <b>SISTEMA VIP DESATIVADO</b> ⚠️\n\n"
            "O nosso Clube de Revendedores VIP e o sistema de Cashback estão temporariamente desligados.\n\n"
            "Fique atento ao canal para saber quando o sistema retornará!"
        )
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("↩️ Voltar aos Prêmios", callback_data="menu_premios"))
        bot.send_message(user_id, texto, parse_mode='HTML', reply_markup=markup)
        return

    # Se estiver ativo, carrega os dados normalmente
    user_data = load_user_vip_data(user_id) or {}
    gasto_semanal = user_data.get('gasto_semanal_vip', 0.0)
    cashback_total = user_data.get('cashback_total_ganho', 0.0)
    
    nivel_atual, proximo_nivel, falta = obter_nivel_vip(gasto_semanal)

    texto = (
        f"👑 <b>CLUBE DE REVENDEDORES VIP</b> 👑\n\n"
        f"A cada compra, acumula gastos.\n"
        f"Quanto maior o seu nível, maior o <b>Cashback</b> que volta para a sua carteira!\n\n"
        f"📊 <b>SEU STATUS DESTE CICLO:</b>\n"
        f"├ <b>Nível Atual:</b> {nivel_atual['emoji']} {nivel_atual['nome']}\n"
        f"├ <b>Gasto no Ciclo:</b> R$ {gasto_semanal:.2f}\n"
        f"├ <b>Cashback Atual:</b> {nivel_atual['cashback']}%\n"
        f"└ <b>Total ganho no bot:</b> R$ {cashback_total:.2f}\n\n"
    )

    if proximo_nivel:
        nome_prox = list(niveis_vip.keys())[list(niveis_vip.values()).index(proximo_nivel)]
        texto += (
            f"🚀 <b>PRÓXIMO NÍVEL: {proximo_nivel['emoji']} {nome_prox}</b>\n"
            f"Faltam apenas <b>R$ {falta:.2f}</b> em compras neste ciclo para desbloquear <b>{proximo_nivel['cashback']}% de Cashback</b>!\n"
        )
    else:
        texto += "🎉 Atingiu o Nível Máximo deste ciclo!\n"
        texto += "Aproveite o seu cashback gigante."

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🛒 Comprar para Subir de Nível", callback_data="servicos"))
    markup.add(InlineKeyboardButton("🏆 Ver Ranking VIP", callback_data="ranking_vip_cliente"))
    markup.add(InlineKeyboardButton("↩️ Voltar aos Prêmios", callback_data="menu_premios"))

    bot.send_message(user_id, texto, parse_mode='HTML', reply_markup=markup)

# ==================== PAINEL ADMIN ====================
def painel_admin_vip(bot, message):
    config = carregar_config()
    status = "🟢 LIGADO" if config.get("ativo", True) else "🔴 DESLIGADO"
    dias_auto = config.get("auto_reset_dias", 0)
    
    # Lógica para calcular o tempo restante
    if dias_auto == 0:
        texto_auto = "Desativado"
    else:
        ultimo_reset = config.get("ultimo_reset", time.time())
        tempo_restante = (ultimo_reset + (dias_auto * 86400)) - time.time()
        
        if tempo_restante > 0:
            dias_restantes = int(tempo_restante // 86400)
            horas_restantes = int((tempo_restante % 86400) // 3600)
            minutos_restantes = int((tempo_restante % 3600) // 60)
            
            if dias_restantes > 0:
                texto_auto = f"A cada {dias_auto} dias (Falta {dias_restantes}d e {horas_restantes}h)"
            elif horas_restantes > 0:
                texto_auto = f"A cada {dias_auto} dias (Falta {horas_restantes}h e {minutos_restantes}m)"
            else:
                texto_auto = f"A cada {dias_auto} dias (Falta {minutos_restantes} minutos)"
        else:
            texto_auto = f"A cada {dias_auto} dias (Reset pendente...)"
            
    texto = (
        f"⚙️ <b>PAINEL ADMIN - VIP & CASHBACK</b>\n\n"
        f"<b>Status do Sistema:</b> {status}\n"
        f"<b>Total Distribuído:</b> R$ {config.get('total_distribuido', 0.0):.2f}\n"
        f"<b>Reset Automático do Ciclo:</b> {texto_auto}\n\n"
        f"⚠️ <i>Pode forçar a exclusão dos gastos atuais no botão abaixo, ou escolher uma opção automática.</i>"
    )

    markup = InlineKeyboardMarkup()
    
    markup.row(InlineKeyboardButton("✏️ Editar Níveis VIP (Requisitos e %)", callback_data="admin_vip_editar_niveis"))
    markup.row(InlineKeyboardButton("👤 Editar Gasto/Cashback de Usuário", callback_data="admin_vip_editar_user_id"))
    
    markup.row(InlineKeyboardButton("🔄 Zerar Gastos de Todos (Manual)", callback_data="admin_vip_zerar_ciclo"))
    
    if dias_auto == 0:
        markup.row(InlineKeyboardButton("🟢 Ligar Auto-Reset", callback_data="admin_vip_toggle_auto"))
    else:
        markup.row(InlineKeyboardButton("🔴 Desligar Auto-Reset", callback_data="admin_vip_toggle_auto"))
        
    markup.row(
        InlineKeyboardButton("⏱ 5 Dias", callback_data="admin_vip_auto_5"),
        InlineKeyboardButton("⏱ 15 Dias", callback_data="admin_vip_auto_15"),
        InlineKeyboardButton("⏱ 30 Dias", callback_data="admin_vip_auto_30")
    )
    
    markup.row(InlineKeyboardButton("🏆 Ver Ranking VIP", callback_data="ranking_vip_admin"))
    
    acao_status = "Desativar Sistema" if config.get("ativo", True) else "Ativar Sistema"
    markup.row(InlineKeyboardButton(f"⚙️ {acao_status}", callback_data="admin_vip_toggle"))
    markup.row(InlineKeyboardButton("↩️ Voltar ao Painel Admin", callback_data="voltar_paineladm"))

    bot.edit_message_text(texto, chat_id=message.chat.id, message_id=message.message_id, parse_mode='HTML', reply_markup=markup)

def registrar_handlers(bot):
    @bot.callback_query_handler(func=lambda call: call.data == 'painel_revenda_vip')
    def cb_painel_revenda(call):
        bot.answer_callback_query(call.id)
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        painel_revenda(bot, call.message)

    @bot.callback_query_handler(func=lambda call: call.data == 'admin_cashback_vip')
    def cb_admin_vip(call):
        bot.answer_callback_query(call.id)
        painel_admin_vip(bot, call.message)
        
    @bot.callback_query_handler(func=lambda call: call.data == 'ranking_vip_cliente')
    def cb_ranking_cliente(call):
        bot.answer_callback_query(call.id)
        exibir_ranking(bot, call.message, origem="cliente")

    @bot.callback_query_handler(func=lambda call: call.data == 'ranking_vip_admin')
    def cb_ranking_admin(call):
        bot.answer_callback_query(call.id)
        exibir_ranking(bot, call.message, origem="admin")

    @bot.callback_query_handler(func=lambda call: call.data == 'admin_vip_toggle')
    def cb_admin_toggle(call):
        config = carregar_config()
        config['ativo'] = not config.get('ativo', True)
        salvar_config(config)
        bot.answer_callback_query(call.id, "Status alterado!", show_alert=True)
        painel_admin_vip(bot, call.message)

    @bot.callback_query_handler(func=lambda call: call.data == 'admin_vip_toggle_auto')
    def cb_admin_toggle_auto(call):
        config = carregar_config()
        
        # Se estiver ativado (> 0), desativamos.
        if config.get('auto_reset_dias', 0) > 0:
            config['auto_reset_dias'] = 0
            msg = "❌ Ciclo Automático Desativado com sucesso!"
        else:
            # Se estiver desativado, ligamos com um padrão de 30 dias.
            config['auto_reset_dias'] = 30
            config['ultimo_reset'] = time.time()
            msg = "✅ Ciclo Automático Ligado (Padrão: 30 Dias)!"
            
        salvar_config(config)
        bot.answer_callback_query(call.id, msg, show_alert=True)
        painel_admin_vip(bot, call.message)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('admin_vip_auto_'))
    def cb_admin_auto(call):
        dias = int(call.data.split('_')[-1])
        config = carregar_config()
        config['auto_reset_dias'] = dias
        config['ultimo_reset'] = time.time()  # Começa a contar a partir do momento do clique
        salvar_config(config)
        
        msg = f"✅ Ciclo Automático configurado para {dias} dias!"
        bot.answer_callback_query(call.id, msg, show_alert=True)
        painel_admin_vip(bot, call.message)

    @bot.callback_query_handler(func=lambda call: call.data == 'admin_vip_zerar_ciclo')
    def cb_admin_zerar(call):
        for uid in get_all_user_ids():
            try:
                data = load_user_data(uid)
                if not data:
                    continue

                mudou = False
                if 'gasto_semanal_vip' in data:
                    data['gasto_semanal_vip'] = 0.0
                    mudou = True
                if 'cashback_total_ganho' in data:
                    data['cashback_total_ganho'] = 0.0
                    mudou = True

                if mudou:
                    save_user_data(uid, data)
            except:
                continue
        
        # Atualiza a data do último reset para não apagar novamente muito cedo
        config = carregar_config()
        config['ultimo_reset'] = time.time()
        salvar_config(config)
        
        bot.answer_callback_query(call.id, "✅ Ciclo de gastos e cashback zerado para todos os clientes!", show_alert=True)
        painel_admin_vip(bot, call.message)

    # ================= NOVOS HANDLERS DE EDIÇÃO =================

    # --- Edição dos Níveis (Global: % e Requisitos de Gasto) ---
    @bot.callback_query_handler(func=lambda call: call.data == 'admin_vip_editar_niveis')
    def cb_admin_editar_niveis(call):
        config = carregar_config()
        niveis = config.get("niveis_vip", NIVEIS_VIP_PADRAO)
        
        texto = "✏️ <b>ESCOLHA O NÍVEL PARA EDITAR:</b>\n\n"
        for nome, dados in niveis.items():
            texto += f"{dados['emoji']} <b>{nome}</b>: Gasto R$ {dados['gasto_minimo']} | Cashback {dados['cashback']}%\n"
            
        markup = InlineKeyboardMarkup()
        for nome in niveis.keys():
            markup.row(InlineKeyboardButton(f"Editar {nome}", callback_data=f"edit_vip_lvl_{nome}"))
        markup.row(InlineKeyboardButton("↩️ Voltar", callback_data="admin_cashback_vip"))
        
        bot.edit_message_text(texto, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='HTML', reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('edit_vip_lvl_'))
    def cb_admin_escolher_attr(call):
        nivel_nome = call.data.replace('edit_vip_lvl_', '')
        
        texto = f"⚙️ <b>A editar o nível: {nivel_nome}</b>\nO que deseja alterar?"
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("💰 Gasto Mínimo", callback_data=f"edit_vip_attr_{nivel_nome}_gasto"),
            InlineKeyboardButton("💸 % de Cashback", callback_data=f"edit_vip_attr_{nivel_nome}_cashback")
        )
        markup.row(InlineKeyboardButton("↩️ Voltar", callback_data="admin_vip_editar_niveis"))
        
        bot.edit_message_text(texto, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='HTML', reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('edit_vip_attr_'))
    def cb_admin_receber_valor(call):
        # Ex: edit_vip_attr_BRONZE_gasto
        partes = call.data.split('_')
        nivel_nome = partes[3]
        atributo = partes[4] # 'gasto' ou 'cashback'
        
        attr_dict_key = 'gasto_minimo' if atributo == 'gasto' else 'cashback'
        attr_display = "Gasto Mínimo (R$)" if atributo == 'gasto' else "Percentagem de Cashback (%)"
        
        msg = bot.send_message(call.message.chat.id, f"Digite o novo valor para <b>{attr_display}</b> do nível <b>{nivel_nome}</b> (Apenas números, use ponto ou vírgula):", parse_mode='HTML')
        bot.register_next_step_handler(msg, processar_edicao_nivel, bot, nivel_nome, attr_dict_key)

    def processar_edicao_nivel(message, bot, nivel_nome, atributo):
        try:
            novo_valor = float(message.text.replace(',', '.'))
            if novo_valor < 0:
                raise ValueError
                
            config = carregar_config()
            if "niveis_vip" not in config:
                config["niveis_vip"] = NIVEIS_VIP_PADRAO
                
            # O cashback pode ser int ou float, gasto é float
            config["niveis_vip"][nivel_nome][atributo] = novo_valor if atributo == "gasto_minimo" else int(novo_valor)
            salvar_config(config)
            
            bot.send_message(message.chat.id, f"✅ O valor do nível <b>{nivel_nome}</b> foi atualizado com sucesso! Abra o painel para verificar.", parse_mode='HTML')
        except ValueError:
            bot.send_message(message.chat.id, "❌ Valor inválido. Digite apenas números positivos. Acesso cancelado.")

    # --- Edição dos Dados do Utilizador (Gasto Atual e Cashback Atual) ---
    @bot.callback_query_handler(func=lambda call: call.data == 'admin_vip_editar_user_id')
    def cb_admin_editar_user_id(call):
        msg = bot.send_message(call.message.chat.id, "👤 Digite o <b>ID do utilizador</b> que deseja alterar os dados do ciclo:", parse_mode='HTML')
        bot.register_next_step_handler(msg, admin_vip_edit_user_select, bot)

    def admin_vip_edit_user_select(message, bot):
        user_id = message.text.strip()
        user_data = load_user_vip_data(user_id)
        if not user_data:
            bot.send_message(message.chat.id, "❌ Utilizador não encontrado na base de dados VIP. Verifique o ID e tente novamente.")
            return
            
        texto = f"👤 <b>A Editar Utilizador:</b> <code>{user_id}</code>\n\nO que deseja alterar para este utilizador?"
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("💰 Gasto Atual do Ciclo", callback_data=f"edit_u_{user_id}_gasto"))
        markup.row(InlineKeyboardButton("💸 Cashback Acumulado", callback_data=f"edit_u_{user_id}_cashback"))
        bot.send_message(message.chat.id, texto, parse_mode='HTML', reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('edit_u_'))
    def cb_admin_edit_user_attr(call):
        partes = call.data.split('_')
        user_id = partes[2]
        attr = partes[3] # 'gasto' ou 'cashback'
        
        tipo_nome = "Gasto no Ciclo Atual" if attr == "gasto" else "Cashback Total Ganho"
        msg = bot.send_message(call.message.chat.id, f"Digite o novo valor para <b>{tipo_nome}</b> do utilizador <code>{user_id}</code> (Use ponto ou vírgula):", parse_mode='HTML')
        bot.register_next_step_handler(msg, admin_vip_save_user_attr, bot, user_id, attr)

    def admin_vip_save_user_attr(message, bot, user_id, attr):
        try:
            valor = float(message.text.replace(',', '.'))
            user_data = load_user_vip_data(user_id)
            if not user_data:
                return
            
            if attr == "gasto":
                user_data['gasto_semanal_vip'] = valor
            else:
                user_data['cashback_total_ganho'] = valor
                user_data['saldo'] = valor # Assume que você também está gerindo o saldo
                
            save_user_vip_data(user_id, user_data)
            bot.send_message(message.chat.id, "✅ Valor do utilizador atualizado com sucesso na base de dados!")
        except ValueError:
            bot.send_message(message.chat.id, "❌ Valor numérico inválido. Acesso cancelado.")
