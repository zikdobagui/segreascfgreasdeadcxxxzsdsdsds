import os
import json
import time
import threading
from datetime import datetime, timedelta
from pytz import timezone as pytz_timezone
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# CORREÇÃO: antes este módulo tinha load_user_data/save_user_data PRÓPRIOS,
# que liam/gravavam um JSON antigo em database/users/<id>.json — um saldo
# "fantasma" desatualizado, separado do saldo real usado pelo restante do
# bot (pagamentos PIX, etc.), que já roda em cima do SQLite (database.py).
# Isso causava "Saldo insuficiente" mesmo com saldo correto, e o erro não
# sumia nem depois do cliente depositar mais, pois o depósito ia para o
# SQLite e a renovação continuava lendo o JSON antigo, nunca atualizado.
# Agora usamos as MESMAS funções que o resto do bot usa:
from app.database import load_user_data, save_user_data, get_all_user_ids

CONFIG_FILE = 'database/config_renovacao.json'

# Variável de controle para evitar múltiplas threads duplicando mensagens
_thread_started = False

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"apps_bloqueados": []}

def save_config(config):
    os.makedirs('database', exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)

def check_expirations(bot):
    """Roda em background para checar vencimentos."""
    tz = pytz_timezone('America/Sao_Paulo')
    
    while True:
        agora = datetime.now(tz)
        config = load_config()
        apps_bloqueados = config.get("apps_bloqueados", [])
        
        for user_id in get_all_user_ids():
            user_data = load_user_data(user_id)

            if not user_data or 'purchases' not in user_data:
                continue

            modificado = False

            for purchase in user_data['purchases']:
                if 'expires_at' not in purchase:
                    continue

                servico = purchase.get('servico')
                if servico in apps_bloqueados:
                    continue

                try:
                    exp_dt = datetime.fromisoformat(purchase['expires_at'])
                    if exp_dt.tzinfo is None:
                        exp_dt = tz.localize(exp_dt)
                    else:
                        exp_dt = exp_dt.astimezone(tz)

                    dias_restantes = (exp_dt.date() - agora.date()).days

                    if dias_restantes == 1 and not purchase.get('notified_1_day'):
                        texto = (
                            f"⚠️ <b>Aviso de Vencimento</b> ⚠️\n\n"
                            f"Sua assinatura expira <b>AMANHÃ</b>!\n\n"
                            f"📦 <b>Serviço:</b> {purchase.get('servico')}\n"
                            f"📧 <b>Login:</b> <code>{purchase.get('email')}</code>\n"
                            f"📅 <b>Data da Compra:</b> {purchase.get('data_compra', '').split('T')[0]}\n"
                            f"⏳ <b>Vencimento:</b> {exp_dt.strftime('%d/%m/%Y')}\n\n"
                            f"🛑 <b>IMPORTANTE:</b> Antes de renovar, faça um teste: entre com seu e-mail e senha no serviço e verifique se a assinatura está funcionando. <b>Só clique em renovar se o acesso estiver correto!</b>\n\n"
                            f"<i>Renove agora ou até as 09:00 da manhã de amanhã para não perder o acesso!</i>"
                        )
                        markup = InlineKeyboardMarkup()
                        markup.add(InlineKeyboardButton("🔄 Renovar Agora", callback_data="menu_renovacao"))

                        try:
                            bot.send_message(user_id, texto, parse_mode='HTML', reply_markup=markup)
                            purchase['notified_1_day'] = True
                            modificado = True
                        except:
                            pass

                    elif dias_restantes == 0 and agora.hour < 9 and not purchase.get('notified_0_days'):
                        texto = (
                            f"🔴 <b>Sua assinatura vence HOJE!</b> 🔴\n\n"
                            f"📦 <b>Serviço:</b> {purchase.get('servico')}\n"
                            f"📧 <b>Login:</b> <code>{purchase.get('email')}</code>\n\n"
                            f"🛑 <b>IMPORTANTE:</b> Antes de renovar, teste seu login e senha. Só clique no botão abaixo se o acesso estiver funcionando perfeitamente!\n\n"
                            f"⚠️ <b>Atenção:</b> Você tem apenas até as <b>09:00 da manhã</b> para renovar!"
                        )
                        markup = InlineKeyboardMarkup()
                        markup.add(InlineKeyboardButton("🔄 Renovar Agora", callback_data="menu_renovacao"))

                        try:
                            bot.send_message(user_id, texto, parse_mode='HTML', reply_markup=markup)
                            purchase['notified_0_days'] = True
                            modificado = True
                        except:
                            pass

                except Exception as e:
                    print(f"Erro ao checar vencimento do user {user_id}: {e}")

            if modificado:
                save_user_data(user_id, user_data)

        time.sleep(3600)

def register_handlers(bot):
    @bot.callback_query_handler(func=lambda call: call.data == 'menu_renovacao')
    def menu_renovacao(call):
        user_id = call.from_user.id
        user_data = load_user_data(user_id)
        
        texto_vazio = (
            "🔄 <b>Central de Renovação</b>\n\n"
            "❌ <i>Nenhuma assinatura encontrada.</i>\n\n"
            "Você não possui assinaturas ativas ou próximas do vencimento para renovar no momento.\n"
            "Acesse a loja para adquirir um novo serviço!"
        )
        markup_vazio = InlineKeyboardMarkup()
        markup_vazio.add(InlineKeyboardButton("🔙 Voltar", callback_data="perfil"))

        def enviar_menu_vazio():
            bot.answer_callback_query(call.id)
            try:
                bot.edit_message_text(texto_vazio, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='HTML', reply_markup=markup_vazio)
            except Exception:
                bot.send_message(call.message.chat.id, texto_vazio, parse_mode='HTML', reply_markup=markup_vazio)

        if not user_data or 'purchases' not in user_data or not user_data['purchases']:
            enviar_menu_vazio()
            return

        tz = pytz_timezone('America/Sao_Paulo')
        agora = datetime.now(tz)
        contas_para_renovar = []
        config = load_config()
        
        for purchase in user_data['purchases']:
            servico = purchase.get('servico')
            if servico in config.get("apps_bloqueados", []):
                continue
                
            if 'expires_at' in purchase:
                try:
                    exp_dt = datetime.fromisoformat(purchase['expires_at'])
                    if exp_dt.tzinfo is None:
                        exp_dt = tz.localize(exp_dt)
                    else:
                        exp_dt = exp_dt.astimezone(tz)
                        
                    dias_restantes = (exp_dt.date() - agora.date()).days
                    
                    pode_renovar = False
                    if dias_restantes == 1:
                        pode_renovar = True
                    elif dias_restantes == 0 and agora.hour < 9:
                        pode_renovar = True
                        
                    if pode_renovar:
                        contas_para_renovar.append(purchase)
                except:
                    pass
                    
        if not contas_para_renovar:
            enviar_menu_vazio()
            return
            
        bot.answer_callback_query(call.id)
        texto = "🔄 <b>Menu de Renovação</b>\n\nSelecione a conta que deseja renovar:"
        markup = InlineKeyboardMarkup(row_width=1)
        
        for conta in contas_para_renovar:
            servico = conta.get('servico', 'Desconhecido')
            email = conta.get('email', 'Sem Email')
            btn_texto = f"{servico} | {email}"
            # ENCAMINHA PARA A TELA DE CONFIRMAÇÃO
            markup.add(InlineKeyboardButton(btn_texto, callback_data=f"pre_renovar_{conta['id']}"))
            
        markup.add(InlineKeyboardButton("🔙 Voltar", callback_data="menu_start"))
        
        try:
            bot.edit_message_text(texto, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='HTML', reply_markup=markup)
        except Exception as e:
            if "message is not modified" not in str(e).lower():
                bot.send_message(call.message.chat.id, texto, parse_mode='HTML', reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('pre_renovar_'))
    def pre_renovar(call):
        """Nova função: Pergunta se o usuário realmente quer renovar antes de cobrar."""
        compra_id = call.data.replace('pre_renovar_', '')
        user_id = call.from_user.id
        user_data = load_user_data(user_id)
        
        if not user_data:
            return
            
        compra_alvo = None
        for p in user_data.get('purchases', []):
            if p.get('id') == compra_id:
                compra_alvo = p
                break
                
        if not compra_alvo:
            bot.answer_callback_query(call.id, "Conta não encontrada.", show_alert=True)
            return
            
        valor = float(compra_alvo.get('valor', 0))
        servico = compra_alvo.get('servico', 'Desconhecido')
        
        texto = (
            f"❓ <b>Confirmação de Renovação</b>\n\n"
            f"Você deseja realmente renovar o serviço <b>{servico}</b>?\n"
            f"💰 <b>Valor a ser descontado:</b> R$ {valor:.2f}\n\n"
            f"<i>O saldo será deduzido automaticamente ao confirmar.</i>"
        )
        
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("✅ Sim, Renovar", callback_data=f"executar_renovacao_{compra_id}"),
            InlineKeyboardButton("❌ Cancelar", callback_data="menu_renovacao")
        )
        
        try:
            bot.edit_message_text(texto, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='HTML', reply_markup=markup)
        except:
            pass

    @bot.callback_query_handler(func=lambda call: call.data.startswith('executar_renovacao_'))
    def executar_renovacao(call):
        """Executa a cobrança e atualiza a data de vencimento."""
        compra_id = call.data.replace('executar_renovacao_', '')
        user_id = call.from_user.id
        user_data = load_user_data(user_id)
        
        if not user_data:
            return
            
        compra_alvo = None
        for p in user_data.get('purchases', []):
            if p.get('id') == compra_id:
                compra_alvo = p
                break
                
        if not compra_alvo:
            bot.answer_callback_query(call.id, "Conta não encontrada.", show_alert=True)
            return
            
        valor = float(compra_alvo.get('valor', 0))
        saldo_atual = float(user_data.get('saldo', 0))
        
        if saldo_atual < valor:
            falta = valor - saldo_atual
            bot.answer_callback_query(call.id, f"Saldo insuficiente! Faltam R$ {falta:.2f}.", show_alert=True)
            return
            
        # Deduz saldo e atualiza vencimento
        user_data['saldo'] -= valor
        
        tz = pytz_timezone('America/Sao_Paulo')
        agora = datetime.now(tz)
        
        # Lógica para adicionar 30 dias ao vencimento atual ou a partir de hoje
        try:
            exp_atual = datetime.fromisoformat(compra_alvo['expires_at'])
            if exp_atual.tzinfo is None: exp_atual = tz.localize(exp_atual)
            novo_vencimento = exp_atual + timedelta(days=30)
        except:
            novo_vencimento = agora + timedelta(days=30)
        
        compra_alvo['expires_at'] = novo_vencimento.isoformat()
        compra_alvo['notified_1_day'] = False 
        compra_alvo['notified_0_days'] = False
        compra_alvo['last_renewal'] = agora.isoformat()
        
        save_user_data(user_id, user_data)
        
        texto_sucesso = (
            f"✅ <b>Renovação Concluída!</b>\n\n"
            f"📦 <b>Serviço:</b> {compra_alvo.get('servico')}\n"
            f"✉️ <b>email:</b> {compra_alvo.get('email')}\n"
            f"💰 <b>Valor Pago:</b> R$ {valor:.2f}\n"
            f"⏳ <b>Novo Vencimento:</b> {novo_vencimento.strftime('%d/%m/%Y')}\n\n"
            f"Seu acesso foi estendido com sucesso!"
        )
        
        try:
            bot.edit_message_text(texto_sucesso, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='HTML')
        except:
            bot.send_message(call.message.chat.id, texto_sucesso, parse_mode='HTML')
        
        # Avisar Admin
        from app import central as api
        try:
            dono_id = api.CredentialsChange.id_dono()
            texto_adm = (
    f"🔄 <b>RENOVAÇÃO REALIZADA</b>\n\n"
    f"👤 <b>ID:</b> <code>{user_id}</code>\n"
    f"📦 <b>Serviço:</b> {compra_alvo.get('servico')}\n"
    f"📧 <b>Login:</b> <code>{compra_alvo.get('email')}</code>\n"
    f"💰 <b>Valor:</b> R$ {valor:.2f}\n"
    f"⏳ <b>Novo Vencimento:</b> {novo_vencimento.strftime('%d/%m/%Y')}"
)
            bot.send_message(dono_id, texto_adm, parse_mode='HTML')
        except:
            pass

    @bot.callback_query_handler(func=lambda call: call.data == 'adm_renov_apps')
    def adm_renov_apps(call):
        config = load_config()
        from app import central as api
        try:
            servicos = api.ControleLogins.pegar_servicos()
            categorias = sorted(list(set([s.get('nome') for s in servicos if s.get('nome')])))
        except:
            categorias = []

        texto = "⚙️ <b>Gestão de Renovações</b>\n\nAtive/Desative a renovação por serviço:"
        markup = InlineKeyboardMarkup(row_width=1)
        
        if categorias:
            for cat in categorias:
                status = "✅ Ativo" if cat not in config.get("apps_bloqueados", []) else "❌ Bloqueado"
                markup.add(InlineKeyboardButton(f"{cat}: {status}", callback_data=f"tgl_renov_{cat}"))
        else:
            markup.add(InlineKeyboardButton("Nenhuma categoria encontrada", callback_data="noop"))
            
        markup.add(InlineKeyboardButton("📊 Contas Renovadas (Relatório)", callback_data="menu_ver_renovadas"))
        markup.add(InlineKeyboardButton("🔙 Voltar", callback_data="voltar_paineladm"))
        
        try:
            bot.edit_message_text(texto, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='HTML', reply_markup=markup)
        except:
            bot.send_message(call.message.chat.id, texto, parse_mode='HTML', reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('tgl_renov_'))
    def toggle_renov(call):
        servico = call.data.replace('tgl_renov_', '')
        config = load_config()
        if "apps_bloqueados" not in config: config["apps_bloqueados"] = []
        if servico in config["apps_bloqueados"]:
            config["apps_bloqueados"].remove(servico)
        else:
            config["apps_bloqueados"].append(servico)
        save_config(config)
        adm_renov_apps(call)

    @bot.callback_query_handler(func=lambda call: call.data == 'menu_ver_renovadas')
    def menu_ver_renovadas(call):
        markup = InlineKeyboardMarkup(row_width=3)
        markup.add(
            InlineKeyboardButton("1 Dia", callback_data="rel_renov_1"),
            InlineKeyboardButton("2 Dias", callback_data="rel_renov_2"),
            InlineKeyboardButton("3 Dias", callback_data="rel_renov_3")
        )
        markup.add(
            InlineKeyboardButton("7 Dias", callback_data="rel_renov_7"),
            InlineKeyboardButton("15 Dias", callback_data="rel_renov_15"),
            InlineKeyboardButton("30 Dias", callback_data="rel_renov_30")
        )
        markup.row(InlineKeyboardButton("🔙 Voltar", callback_data="adm_renov_apps"))
        
        bot.edit_message_text(
            "📅 <b>Relatório de Renovações</b>\n\nSelecione de quantos dias atrás deseja gerar o relatório de contas renovadas:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode='HTML',
            reply_markup=markup
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith('rel_renov_'))
    def callback_rel_renov_rapido(call):
        dias = int(call.data.split('_')[2])
        bot.answer_callback_query(call.id, f"Gerando relatório de {dias} dias...")
        gerar_relatorio_renovadas_rapido(bot, call.message.chat.id, dias)
        
    def gerar_relatorio_renovadas_rapido(bot, chat_id, dias):
        import os
        tz = pytz_timezone('America/Sao_Paulo')
        now = datetime.now(tz)
        cutoff = now - timedelta(days=dias)

        encontrados = []
        for uid in get_all_user_ids():
            ud = load_user_data(uid) or {}

            username = ud.get('username', None)
            if not username:
                try:
                    chat = bot.get_chat(uid)
                    username = f"@{chat.username}" if chat.username else (chat.first_name or str(uid))
                except Exception:
                    username = str(uid)

            for p in ud.get('purchases', []):
                lr = p.get('last_renewal')
                if not lr:
                    continue
                try:
                    renov_dt = datetime.fromisoformat(lr).astimezone(tz)
                    if renov_dt >= cutoff:
                        exp_dt = datetime.fromisoformat(p['expires_at']).astimezone(tz)
                        encontrados.append({
                            'user_id':     uid,
                            'username':    username,
                            'servico':     p.get('servico','—'),
                            'login':       p.get('email','—'),
                            'senha':       p.get('senha','—'),
                            'renovado_em': renov_dt.strftime('%d/%m/%Y %H:%M'),
                            'vencimento':  exp_dt.strftime('%d/%m/%Y %H:%M')
                        })
                except:
                    pass

        if not encontrados:
            bot.send_message(chat_id, f"🚫 Nenhuma conta renovada nos últimos {dias} dias.")
            return

        lines = []
        for e in encontrados:
            lines.append(
                f"👤 Usuário: {e['username']} (`{e['user_id']}`)\n"
                f"🔹 Serviço: *{e['servico']}*\n"
                f"🔑 Login: `{e['login']}`\n"
                f"🔒 Senha: `{e['senha']}`\n"
                f"🗓 Renovado em: *{e['renovado_em']}*\n"
                f"⏳ Vence em: *{e['vencimento']}*\n"
                + "─"*30
            )
        content = "\n\n".join(lines)

        fname = f"renovadas_{dias}dias.txt"
        with open(fname, 'w', encoding='utf-8') as f:
            f.write(content)
        
        with open(fname, 'rb') as doc:
            bot.send_document(chat_id, doc, caption=f"📄 Relatório de contas renovadas ({dias} dias)")
        os.remove(fname)

def setup(bot):
    global _thread_started
    register_handlers(bot)
    if not _thread_started:
        threading.Thread(target=check_expirations, args=(bot,), daemon=True).start()
        _thread_started = True
