import os
import json
import random
import string
from datetime import datetime, timedelta
from pytz import timezone as pytz_timezone
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# CORREÇÃO: as funções abaixo liam/gravavam diretamente em
# database/users/<id>.json, pasta que não existe mais após a migração
# para SQLite. Agora usam as mesmas funções que o resto do bot usa.
from app.database import load_user_data, save_user_data

def iniciar(call, bot, api):
    try:
        if not (api.Admin.verificar_admin(call.message.chat.id) or str(call.message.chat.id) == str(api.CredentialsChange.id_dono())):
            bot.answer_callback_query(call.id, "🚫 Sem permissão.", show_alert=True)
            return
    except:
        pass
        
    bot.answer_callback_query(call.id)
    
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("❌ Cancelar", callback_data="voltar_paineladm"))
    
    texto = (
        "🔄 <b>SISTEMA DE RENOVAÇÃO MANUAL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "<i>Passo 1 de 5</i>\n"
        "👉 Envie o <b>ID do Cliente</b> que receberá o aviso:"
    )
    
    msg = bot.edit_message_text(
        texto,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, step_receber_id_renov, bot, api)

def step_receber_id_renov(message, bot, api):
    if message.text.startswith('/'): return
    
    user_id_cliente = message.text.strip()
    if not user_id_cliente.isdigit():
        bot.reply_to(message, "❌ ID inválido. Volte ao painel e tente novamente.")
        return
        
    texto = (
        "🔄 <b>SISTEMA DE RENOVAÇÃO MANUAL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "<i>Passo 2 de 5</i>\n"
        f"✅ <b>ID Capturado:</b> <code>{user_id_cliente}</code>\n\n"
        "👉 Envie o <b>E-mail (ou Login)</b> da conta:"
    )
    msg = bot.reply_to(message, texto, parse_mode="HTML")
    bot.register_next_step_handler(msg, step_receber_email_renov, bot, api, user_id_cliente)

def step_receber_email_renov(message, bot, api, user_id_cliente):
    if message.text.startswith('/'): return
    email = message.text.strip()
    
    texto = (
        "🔄 <b>SISTEMA DE RENOVAÇÃO MANUAL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "<i>Passo 3 de 5</i>\n"
        f"✅ <b>Acesso Capturado:</b> <code>{email}</code>\n\n"
        "👉 Envie o <b>Nome do Serviço</b> (ex: Netflix 4K, Canva, Prime):"
    )
    msg = bot.reply_to(message, texto, parse_mode="HTML")
    bot.register_next_step_handler(msg, step_receber_servico_renov, bot, api, user_id_cliente, email)

def step_receber_servico_renov(message, bot, api, user_id_cliente, email):
    if message.text.startswith('/'): return
    servico = message.text.strip()
    
    texto = (
        "🔄 <b>SISTEMA DE RENOVAÇÃO MANUAL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "<i>Passo 4 de 5</i>\n"
        f"✅ <b>Serviço:</b> {servico}\n\n"
        "👉 Em <b>quantos dias</b> a conta vence? (Envie apenas o número. Ex: 30)"
    )
    msg = bot.reply_to(message, texto, parse_mode="HTML")
    bot.register_next_step_handler(msg, step_receber_dias_renov, bot, api, user_id_cliente, email, servico)

def step_receber_dias_renov(message, bot, api, user_id_cliente, email, servico):
    if message.text.startswith('/'): return
    dias_str = message.text.strip()
    
    if not dias_str.isdigit():
        bot.reply_to(message, "❌ Quantidade de dias inválida. Operação cancelada.")
        return
        
    dias = int(dias_str)
    
    texto = (
        "🔄 <b>SISTEMA DE RENOVAÇÃO MANUAL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "<i>Passo 5 de 5</i>\n"
        f"✅ <b>Dias:</b> {dias} dias\n\n"
        "👉 Qual o <b>Valor</b> cobrado por essa renovação? (Ex: 15.50 ou 20)"
    )
    msg = bot.reply_to(message, texto, parse_mode="HTML")
    bot.register_next_step_handler(msg, step_concluir_add_renov, bot, api, user_id_cliente, email, servico, dias)

def step_concluir_add_renov(message, bot, api, user_id_cliente, email, servico, dias):
    if message.text.startswith('/'): return
    valor_str = message.text.strip().replace(',', '.')
    
    try:
        valor = float(valor_str)
    except ValueError:
        bot.reply_to(message, "❌ Valor inválido. Use o formato como 15.90 ou 20. Operação cancelada.")
        return
        
    tz_brasil = pytz_timezone('America/Sao_Paulo')
    data_compra_obj = datetime.now(tz_brasil)
    data_venc_obj = data_compra_obj + timedelta(days=dias)
    
    data_compra_iso = data_compra_obj.isoformat()
    data_venc_iso = data_venc_obj.isoformat()
    data_venc_br = data_venc_obj.strftime("%d/%m/%Y %H:%M")
    
    compra_id = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

    user_data = load_user_data(user_id_cliente) or {}
        
    if 'purchases' not in user_data:
        user_data['purchases'] = []
        
    nova_compra = {
        "id": compra_id,
        "servico": servico,
        "email": email,
        "senha": "Adicionado Manualmente via Painel",
        "data_compra": data_compra_iso,
        "expires_at": data_venc_iso, 
        "valor": valor,
        "renovacao_manual": True
    }
    
    user_data['purchases'].append(nova_compra)
    
    save_user_data(user_id_cliente, user_data)
        
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🔔 Notificar Cliente Agora", callback_data=f"rnw_notif_{user_id_cliente}"))
    markup.row(InlineKeyboardButton("⬅️ Voltar ao Painel", callback_data="voltar_paineladm"))

    resumo = (
        f"✅ <b>RENOVAÇÃO CADASTRADA COM SUCESSO!</b> ✅\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 <b>Cliente (ID):</b> <code>{user_id_cliente}</code>\n"
        f"📧 <b>Acesso:</b> <code>{email}</code>\n"
        f"📺 <b>Serviço:</b> <b>{servico}</b>\n"
        f"💰 <b>Valor:</b> R$ {valor:.2f}\n"
        f"⏳ <b>Restam:</b> {dias} dias\n"
        f"📅 <b>Vencimento:</b> {data_venc_br}\n\n"
        f"🤖 <i>O sistema já agendou o aviso automático. Se quiser enviar uma notificação de confirmação para o cliente agora, clique no botão abaixo!</i>"
    )
    bot.reply_to(message, resumo, parse_mode="HTML", reply_markup=markup)


def notificar_agora(call, bot):
    try:
        user_id = int(call.data.split('_')[2])
        
        user_data = load_user_data(user_id)
        
        if not user_data:
            bot.answer_callback_query(call.id, "❌ Usuário não encontrado.", show_alert=True)
            return
            
        if 'purchases' not in user_data or len(user_data['purchases']) == 0:
            bot.answer_callback_query(call.id, "❌ Nenhuma compra encontrada.", show_alert=True)
            return
            
        ultima_compra = user_data['purchases'][-1]
        servico = ultima_compra.get('servico', 'Serviço')
        
        tz = pytz_timezone('America/Sao_Paulo')
        venc_formatado = "Indisponível"
        if 'expires_at' in ultima_compra:
             exp_dt = datetime.fromisoformat(ultima_compra['expires_at'])
             if exp_dt.tzinfo is None:
                 exp_dt = tz.localize(exp_dt)
             else:
                 exp_dt = exp_dt.astimezone(tz)
             venc_formatado = exp_dt.strftime("%d/%m/%Y às %H:%M")
        
        # MENSAGEM DO CLIENTE ATUALIZADA COM O TOQUE DA LOJA
        texto_cliente = (
            f"🔔 <b>SISTEMA DE AVISOS AUTOMÁTICOS!</b> 🔔\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Olá! Nossa administração acabou de registrar sua assinatura no nosso sistema automático.\n\n"
            f"📺 <b>Serviço:</b> <b>{servico}</b>\n"
            f"📅 <b>Seu Vencimento:</b> {venc_formatado}\n\n"
            f"📌 <i>Seu login e senha já se encontram salvos na sua central de renovações do aplicativo abaixo.</i>\n\n"
            f"<i>Fique tranquilo(a)! Quando estiver perto de vencer, nosso robô vai te notificar por aqui para você renovar sem perder o acesso.</i>"
        )
        
        # Cria o botão de redirecionamento para o cliente ir direto ao menu correto
        markup_cliente = InlineKeyboardMarkup()
        markup_cliente.add(InlineKeyboardButton("🔄 Renovar Aplicativo / Ver Login", callback_data="menu_renovacao"))
        
        bot.send_message(user_id, texto_cliente, parse_mode="HTML", reply_markup=markup_cliente)
        bot.answer_callback_query(call.id, "✅ Notificação enviada com sucesso!", show_alert=True)
        
        # Altera o painel do administrador removendo o botão de notificação após ser usado
        markup_admin = InlineKeyboardMarkup()
        markup_admin.row(InlineKeyboardButton("⬅️ Voltar ao Painel", callback_data="voltar_paineladm"))
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup_admin)
        
    except Exception as e:
        bot.answer_callback_query(call.id, "❌ Erro ao enviar notificação. O cliente pode ter bloqueado o bot.", show_alert=True)
