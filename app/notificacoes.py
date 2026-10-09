"""Rotinas agrupadas de notificacoes."""

# ==================== ALERTA_PIX_VACUO ====================
"""Sistema de alerta de PIX gerado e não pago (vácuo)."""
import json
import os
from datetime import datetime
from telebot import types
from app import central as api


def registrar_nao_pagamento_diario(user_id):
    """Registra o não pagamento e retorna a contagem do dia."""
    arquivo_stats = 'database/pix_nao_pagos.json'
    hoje = datetime.now().strftime("%Y-%m-%d")

    if not os.path.exists('database'):
        os.makedirs('database')

    data = {}
    if os.path.exists(arquivo_stats):
        try:
            with open(arquivo_stats, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            data = {}

    # Se mudou o dia, reseta a contagem
    if data.get('data_atual') != hoje:
        data = {'data_atual': hoje, 'usuarios': {}}

    uid = str(user_id)
    contagem = data['usuarios'].get(uid, 0) + 1
    data['usuarios'][uid] = contagem

    with open(arquivo_stats, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    return contagem


def alertar_adm_pix_nao_pago(bot, user_id, valor):
    """Envia mensagem ao ADM informando o vácuo."""
    try:
        qtd_hoje = registrar_nao_pagamento_diario(user_id)

        try:
            chat = bot.get_chat(user_id)
            nome = chat.first_name + (f" {chat.last_name}" if chat.last_name else "")
            username = f"@{chat.username}" if chat.username else "Sem user"
        except:
            nome = "Desconhecido"
            username = "N/A"

        dono_id = api.CredentialsChange.id_dono()

        texto_alerta = (
            f"⚠️ <b>ALERTA: PIX NÃO PAGO (VÁCUO)</b>\n\n"
            f"👤 <b>Usuário:</b> {nome}\n"
            f"🔗 <b>User:</b> {username}\n"
            f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
            f"💸 <b>Gerou:</b> R$ {float(valor):.2f}\n\n"
            f"🤡 <b>Gerou e não pagou hoje:</b> {qtd_hoje}x"
        )

        bot.send_message(dono_id, texto_alerta, parse_mode='HTML')
    except Exception as e:
        print(f"Erro ao alertar ADM: {e}")

# ==================== VENCIMENTOS ====================
from datetime import datetime, timedelta
import pytz

from app import database


def _parse_data_compra(data_str):
    """Aceita tanto o formato brasileiro (dd/mm/aaaa, usado nas compras novas)
    quanto o ISO (aaaa-mm-dd, usado nas compras antigas migradas do JSON,
    que ficaram sem 'data_raw'). Retorna (date, hora_str) ou (None, '')."""
    if not data_str:
        return None, ""
    partes = data_str.split(' ', 1)
    data_part = partes[0]
    hora_part = partes[1] if len(partes) > 1 else ""
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(data_part, fmt).date(), hora_part
        except ValueError:
            continue
    return None, hora_part


def listar_contas(deslocamento_dias=0):
    tz_brasil = pytz.timezone('America/Sao_Paulo')
    hoje = datetime.now(tz_brasil).date()
    
    data_alvo = hoje + timedelta(days=deslocamento_dias)
    data_formatada = data_alvo.strftime("%d/%m/%Y")
    data_compra_buscada = data_alvo - timedelta(days=30)
    
    encontrados = []
    
    for user_id in database.get_all_user_ids():
        try:
            dados = database.load_user_data(user_id)
            if not dados:
                continue
            for compra in dados.get('compras', []):
                data_compra, hora_compra = _parse_data_compra(compra.get('data', ''))
                if data_compra is None:
                    continue
                try:
                    if data_compra == data_compra_buscada:
                        nome = dados.get('nome', 'Sem Nome')
                        
                        # Tenta capturar o login de várias formas comuns
                        login_conta = compra.get('login') or compra.get('email') or "N/A"
                        
                        encontrados.append({
                            'id': str(user_id),
                            'usuario': nome,
                            'produto': compra.get('servico', 'N/A').upper(),
                            'valor': compra.get('valor', '0.0'),
                            'login': login_conta,
                            'senha': compra.get('senha', 'N/A'),
                            'data_compra': compra.get('data', ''),
                            'data_exp': data_formatada + (" " + hora_compra if hora_compra else "")
                        })
                except:
                    continue
        except:
            continue
                    
    return encontrados, data_formatada

# ==================== NOTIFICACAO_ACESSO ====================
import threading
import re
from datetime import datetime
import pytz

# CORREÇÃO: este módulo tinha sua própria obter_dados_usuario() que lia o
# JSON antigo em database/users/<id>.json — um saldo desatualizado, diferente
# do saldo real (SQLite, database.py) que o menu do bot mostra ao usuário.
# Por isso o aviso "Um usuário acessou o bot" mostrava um valor e o próprio
# bot mostrava outro para a mesma pessoa. Agora os dois usam a mesma fonte:
from app.database import load_user_data as obter_dados_usuario

def notificar_admin_acesso(bot, message, admin_id):
    """Envia notificação para o admin e apaga após 30 segundos."""
    try:
        user_id = message.from_user.id
        nome = message.from_user.first_name or "Desconhecido"
        
        # Transforma o @username em um link clicável do Telegram
        if message.from_user.username:
            username = f"<a href='https://t.me/{message.from_user.username}'>@{message.from_user.username}</a>"
        else:
            username = "Sem username"
        
        user_data = obter_dados_usuario(user_id) or {}
        
        # Puxa o saldo atual e o WhatsApp bruto
        saldo_atual = float(user_data.get('saldo', 0.0))
        whatsapp_str = str(user_data.get('whatsapp', 'Não cadastrado'))
        
        # Transforma o WhatsApp em um link clicável para abrir o app
        if whatsapp_str != 'Não cadastrado':
            # Remove qualquer caractere que não seja número (espaços, traços, etc)
            numero_limpo = re.sub(r'\D', '', whatsapp_str)
            whatsapp = f"<a href='https://wa.me/{numero_limpo}'>{whatsapp_str}</a>"
        else:
            whatsapp = whatsapp_str
        
        # Puxa o fuso horário e a data de hoje para comparar as compras
        tz_brasil = pytz.timezone('America/Sao_Paulo')
        hoje_str = datetime.now(tz_brasil).strftime("%d/%m/%Y")
        
        compras_hoje = 0
        historico = user_data.get('compras', []) + user_data.get('purchases', [])
        compras_vistas = set()
        
        for compra in historico:
            data_compra = compra.get('data', '') or compra.get('data_compra', '')
            compra_id = str(compra.get('id', data_compra)) + str(compra.get('email', ''))
            
            if compra_id in compras_vistas:
                continue
            compras_vistas.add(compra_id)
            
            if hoje_str in data_compra:
                compras_hoje += 1

        # Verifica se o cadastro foi feito hoje (cliente novo) ou antes (recorrente)
        eh_cliente_novo = False
        data_registro = user_data.get('data_registro', '')
        if data_registro and hoje_str in data_registro:
            eh_cliente_novo = True

        # Monta a mensagem final formatada (versão compacta)
        emoji_status = "🆕" if eh_cliente_novo else "🔁"
        texto_aviso = (
            f"🚨 {emoji_status} <b>{nome}</b> ({username})\n"
            f"📞 {whatsapp}\n"
            f"🛒 {compras_hoje} compras hj | 💰 R$ {saldo_atual:.2f}"
        )
        
        # Envia a mensagem para o administrador sem gerar preview dos links
        sent_msg = bot.send_message(
            admin_id, 
            texto_aviso, 
            parse_mode="HTML", 
            disable_web_page_preview=True
        )
        
        # Função para deletar a mensagem
        def deletar_msg():
            try:
                bot.delete_message(chat_id=admin_id, message_id=sent_msg.message_id)
            except Exception as e:
                print(f"[Notificação] Erro ao deletar aviso de acesso: {e}")
                
        # Inicia o temporizador de 10 segundos
        timer = threading.Timer(10.0, deletar_msg)
        timer.start()
        
    except Exception as e:
        print(f"[Notificação] Erro geral ao enviar notificação de acesso: {e}")

# ==================== LEMBRETE_ABANDONO ====================
import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Dicionário para armazenar as contagens de tempo de cada usuário
pending_service_reminders = {}

def remind_abandoned_service(bot, admin_id, user_id, servico):
    """Notifica o usuário e o Admin que a compra de um serviço específico não foi concluída."""
    if user_id in pending_service_reminders:
        pending_service_reminders.pop(user_id, None)
        
        try:
            user_info = bot.get_chat(user_id)
            user_name = user_info.first_name or "visitante"
            username = f"@{user_info.username}" if user_info.username else "Sem user"
        except Exception:
            user_name = "visitante"
            username = "N/A"

        # 1. Mensagem de incentivo para o Cliente
        texto_lembrete_user = (
            f"Ei, <b>{user_name}</b>! Notei que você se interessou por <b>{servico}</b>, mas acabou não finalizando a compra... 🛒❌\n\n"
            f"Ainda temos esse produto em estoque! Que tal garantir o seu acesso agora mesmo antes que acabe? 👇"
        )
        
        markup_user = InlineKeyboardMarkup()
        markup_user.row(InlineKeyboardButton(f"🛒 COMPRAR {servico}", callback_data=f"confirmar_compra_prompt {servico}"))
        markup_user.row(InlineKeyboardButton("🏠 Voltar ao Menu", callback_data="menu_start"))
        
        try:
            bot.send_message(user_id, texto_lembrete_user, parse_mode="HTML", reply_markup=markup_user)
        except Exception as e:
            print(f"Erro ao enviar lembrete de abandono para {user_id}: {e}")
            
        # 2. Notificação de alerta para o Admin (Bolt)
        try:
            texto_admin = (
                f"⚠️ <b>Alerta: Produto Abandonado</b>\n\n"
                f"👤 <b>Usuário:</b> {user_name}\n"
                f"🔗 <b>User:</b> {username}\n"
                f"🆔 <b>ID:</b> <code>{user_id}</code>\n\n"
                f"O cliente olhou o serviço <b>{servico}</b>, mas <b>NÃO</b> finalizou a compra."
            )
            
            bot.send_message(admin_id, texto_admin, parse_mode="HTML")
        except Exception as admin_e:
            print(f"Erro ao notificar admin sobre abandono: {admin_e}")

def iniciar_contagem(bot, admin_id, user_id, servico):
    """Inicia o relógio invisível de 5 minutos (300 segundos)."""
    if user_id in pending_service_reminders:
        pending_service_reminders[user_id].cancel()
    
    timer_servico = threading.Timer(300.0, remind_abandoned_service, args=(bot, admin_id, user_id, servico))
    timer_servico.daemon = True
    timer_servico.start()
    pending_service_reminders[user_id] = timer_servico

def cancelar_contagem(user_id):
    """Cancela o aviso caso a compra seja feita."""
    t_servico = pending_service_reminders.pop(user_id, None)
    if t_servico:
        t_servico.cancel()

# ==================== ANTI_FLOOD ====================
import time
from collections import defaultdict

# ==========================================================
# 1. PROTEÇÃO GLOBAL (BOTÕES E MENSAGENS)
# ==========================================================
user_last_click = {}
TEMPO_ESPERA = 2  # Segundos de intervalo entre cliques

def verificar_spam(user_id):
    agora = time.time()
    ultimo_tempo = user_last_click.get(user_id, 0)
    
    # Se a diferença for menor que o tempo de espera, é spam
    if agora - ultimo_tempo < TEMPO_ESPERA:
        return True
    
    # Se passou tempo suficiente, atualiza o registro e libera
    user_last_click[user_id] = agora
    return False

def aplicar_antiflood(bot):
    """Aplica os middlewares no bot principal"""
    
    @bot.callback_query_handler(func=lambda call: verificar_spam(call.from_user.id))
    def bloquear_botoes(call):
        try:
            # Mesmo aviso de antes, mas como toast: some sozinho, sem exigir clicar em OK
            bot.answer_callback_query(call.id, f"⏳ Espere {float(TEMPO_ESPERA)}s antes de clicar novamente", show_alert=False)
        except Exception as e:
            # Callback pode ter expirado (ex: acumulado durante um restart do bot)
            print(f"[ANTI-FLOOD] Callback expirado/ignorado: {e}")

    @bot.message_handler(func=lambda message: verificar_spam(message.from_user.id), 
                         content_types=['text', 'photo', 'video', 'sticker', 'document', 'audio'])
    def bloquear_mensagens(message):
        bot.reply_to(message, f"⏳ Espere {float(TEMPO_ESPERA)}s antes de enviar outro comando")
        
    print("✅ Sistema Anti-Flood global ativado com sucesso!")


# ==========================================================
# 2. PROTEÇÃO ESPECÍFICA PARA O COMANDO /START
# ==========================================================
START_FLOOD_LIMITE = 3        # máximo de /start permitidos
START_FLOOD_TEMPO = 10        # em quantos segundos (janela de tempo)
START_FLOOD_COOLDOWN = 15     # tempo de bloqueio de uso em segundos

start_flood_dados = defaultdict(list)
start_flood_bloqueados = {}

def verificar_flood_start(user_id):
    """Verifica se o usuário cometeu flood no comando de /start"""
    agora = time.time()
    
    # Verifica se usuário está em cooldown (bloqueado temporariamente)
    if user_id in start_flood_bloqueados:
        if agora < start_flood_bloqueados[user_id]:
            return True
        else:
            del start_flood_bloqueados[user_id] # Cooldown acabou
    
    # Limpa timestamps antigos fora da janela de tempo
    start_flood_dados[user_id] = [
        timestamp for timestamp in start_flood_dados[user_id] 
        if agora - timestamp <= START_FLOOD_TEMPO
    ]
    
    # Adiciona a tentativa atual
    start_flood_dados[user_id].append(agora)
    
    # Verifica se passou dos limites configurados
    if len(start_flood_dados[user_id]) > START_FLOOD_LIMITE:
        start_flood_bloqueados[user_id] = agora + START_FLOOD_COOLDOWN
        return True
        
    return False

def enviar_aviso_flood_start(bot, message, admin_id):
    """Notifica o usuário e o administrador que o bloqueio ocorreu"""
    user_id = message.from_user.id
    username = message.from_user.username or "Sem_Username"
    first_name = message.from_user.first_name or "Usuário"
    
    # Avisa o cliente
    try:
        bot.reply_to(
            message,
            "⚠️ **Calma aí!** \n\n"
            f"Você usou o comando /start muitas vezes seguidas.\n"
            f"Para evitar sobrecarga no sistema:\n\n"
            f"⏳ Aguarde **{START_FLOOD_COOLDOWN} segundos** antes de tentar novamente.\n"
            f"✅ Depois disso, tudo voltará ao normal.\n\n"
            f"🤖 Esta proteção é ativada automaticamente por segurança."
        )
    except Exception as e:
        print(f"[ANTI-FLOOD] Erro ao avisar usuário: {e}")
    
    # Alerta o Dono (ADM)
    try:
        admin_msg = (
            "🚨 <b>ANTI-FLOOD DO /START ACIONADO</b>\n\n"
            f"👤 <b>Usuário:</b> {first_name}\n"
            f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
            f"📱 <b>Username:</b> @{username}\n\n"
            f"⚠️ <b>Motivo:</b> Mais de {START_FLOOD_LIMITE} comandos /start em {START_FLOOD_TEMPO}s\n"
            f"🔒 <b>Bloqueio Atual:</b> {START_FLOOD_COOLDOWN} segundos\n\n"
            f"🕐 <b>Horário:</b> {time.strftime('%H:%M:%S - %d/%m/%Y')}"
        )
        bot.send_message(admin_id, admin_msg, parse_mode="HTML")
        print(f"[ANTI-FLOOD] ADM alertado sobre uso excessivo do ID {user_id}")
    except Exception as e:
        print(f"[ANTI-FLOOD] Erro ao notificar administrador: {e}")
