import schedule
import threading
import time
from app import backup_manager
from app.interface import gerar_menu_principal
from app import relatorio_avancado
from app import Oferta_relampago
from app import notificacoes as lembrete_abandono
from app import canal_manager
from app import renovacao_painel
from app import gerenciamento_logins
from datetime import datetime
import os
_lock_file_handle = None  # mantém referência ao arquivo de lock aberto (flock) durante toda a vida do processo
import pytz
import json
from app import notificacoes as notificacao_acesso
from app import notificacoes as vencimentos
from app import notificacoes as anti_flood
from app import recompensas 
from app import renovacao_automatica
from app import sistema_cashback_vip
from app.rl_maintenance import install_maintenance_filter, maintenance_on, maintenance_off, notify_all_users, is_on, get_maintenance_message, set_maintenance_message
# ==========================================================
# SISTEMA DE ALERTA DE PIX NÃO PAGO
# ==========================================================
from app.notificacoes import registrar_nao_pagamento_diario, alertar_adm_pix_nao_pago
# ==========================================================
# --- Console/Logging UTF-8 Safety (Windows) ---
try:
    import sys, os, logging
    os.environ.setdefault("PYTHONUTF8", "1")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        force=True,
        encoding="utf-8",
    )
except Exception:
    pass
# ===== Saída segura e handlers globais de erro/sinal =====
from app.suporte import safe_exit, handle_uncaught_exception, handle_signal, instalar_handlers_globais
instalar_handlers_globais()
import string
import telebot
import telebot.apihelper
import sys
import requests
import uuid
import httpx
from threading import Timer
import base64
from telebot.apihelper import ApiTelegramException
from app import database
from html import escape  
import re
from datetime import datetime, timedelta
from pytz import timezone as pytz_timezone# ... código anterior ...
import subprocess
import random
from app import central as api  # <-- import global para uso em threads
from app import troca_automatica # <<<---- COLOQUE A LINHA EXATAMENTE AQUI
from app import afiliados_sistema
from collections import Counter
import math
# ... código posterior ...
# --- Compat: garante api.novo_usuario mesmo se central não expor no módulo ---
if not hasattr(api, "novo_usuario"):
    def _novo_usuario_alias(id):
        return api.InfoUser.novo_usuario(id)
    api.novo_usuario = _novo_usuario_alias
# ---------------------------------------------------------------------------
from io import BytesIO
from os import system
from telebot import types
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import timezone
from pytz import timezone
from app.database import get_user_balance, add_saldo, add_pagamento, get_top_users
from app.database import update_usernames
from app.utils import hc, virtualPayToken
from time import time                    
import logging
# Dicionário para o cache de estatísticas do painel admin
admin_stats_cache = {
    "data": None,
    "timestamp": 0
}
CACHE_TTL = 300  # Tempo de vida do cache em segundos (300s = 15 minutos)
logger = logging.getLogger("bot_logger")
logging.basicConfig(level=logging.INFO)
#
# ✅ ADICIONE ESTE BLOCO NO TOPO DO SEU ARQUIVO ✅
#
# Dicionário para o cache de estatísticas do painel admin
admin_stats_cache = {
    "data": None,
    "timestamp": 0
}# (Linha 402)
CACHE_TTL = 300  # Tempo de vida do cache em segundos (300s = 15 minutos)
# Dicionário para o cache de estatísticas do painel admin
admin_stats_cache = {
    "data": None,
    "timestamp": 0
}
CACHE_TTL = 300  # Tempo de vida do cache em segundos (900s = 15 minutos)
ADMIN_ID = int(api.CredentialsChange.id_dono())    
try:
    update_usernames()
except Exception as e:
    import logging
    logging.exception("update_usernames failed: %s", e)
# ==========================================================================
# ==========================================================================
# Stalker 24/04/2025
# Stalker 17/05/2025
# Stalker 08/06/2025
# ==========================================================================
# ==========================================================================
ALERTS_FILE = 'alerts.json'
ultimo_menu = {}
# [REMOVIDO] Variável auxiliar do painel antigo removida = {}  # Para rastrear a página atual do painel de avisos por usuário
# Sistema de avisos de acesso ao bot
user_access_notifications = {}  # Para controlar avisos de acesso por usuário
ACCESS_NOTIFICATION_COOLDOWN = 1800  # 30 minutos em segundos
user_carts: dict[int, dict[str, int]] = {}         
user_cart_msgs: dict[int, int] = {}                
CART_TTL = 1800          
cart_timers: dict[int, threading.Timer] = {}
def notificar_acesso_admin(user_id, username=None, first_name=None):
    """
    Notifica o admin sobre acesso de usuário ao bot, respeitando cooldown de 30 minutos
    """
    try:
        current_time = time.time()
        # Verifica se já foi enviado aviso para este usuário recentemente
        if user_id in user_access_notifications:
            last_notification = user_access_notifications[user_id]
            if current_time - last_notification < ACCESS_NOTIFICATION_COOLDOWN:
                return  # Ainda está no período de cooldown
        # Atualiza o timestamp do último aviso
        user_access_notifications[user_id] = current_time
        # --- Coleta de Novas Informações ---
        from datetime import datetime
        import pytz
        # Fuso horário do Brasil
        tz_brasil = pytz.timezone('America/Sao_Paulo')
        agora = datetime.now(tz_brasil)
        data_formatada = agora.strftime("%d/%m/%Y às %H:%M:%S")
        # Pega o nome do bot e o nome de exibição do usuário
        bot_username = api.CredentialsChange.user_bot()
        user_display_name = first_name or "Usuário"
        # Pega o saldo do usuário
        try:
            saldo_usuario = api.InfoUser.saldo(user_id)
        except Exception:
            saldo_usuario = 0.0
        # Calcula compras e gastos do dia
        compras_hoje = 0
        gasto_hoje = 0.0
        try:
            user_data = load_user_data(user_id)
            if user_data and 'compras' in user_data:
                hoje = agora.date()
                for compra in user_data['compras']:
                    try:
                        data_compra_str = compra.get('data', '').split(' ')[0]
                        data_compra_obj = datetime.strptime(data_compra_str, "%d/%m/%Y").date()
                        if data_compra_obj == hoje:
                            compras_hoje += 1
                            gasto_hoje += float(compra.get('valor', 0.0))
                    except (ValueError, KeyError, IndexError):
                        continue
        except Exception as e:
            print(f"Erro ao calcular estatísticas diárias do usuário {user_id}: {e}")
        # Monta a mensagem de aviso no novo formato com ID
        texto_aviso = (
            f"🕵️ <b>Acesso ao Bot</b>\n"
            f"👤 <b>Usuário:</b> {user_display_name}\n"
            f"📱 <b>Username:</b> @{username if username else 'Não definido'}\n"
            f"🆔 <b>ID:</b> <code>{user_id}</code>\n\n"
            f"💰 <b>Saldo Atual:</b> R$ {saldo_usuario:.2f}\n"
            f"🛒 <b>Compras no Dia:</b> {compras_hoje}\n"
            f"💸 <b>Gasto no Dia:</b> R$ {gasto_hoje:.2f}\n\n"
            f"🕐 <b>Data/Hora:</b> {data_formatada}"
        )
        # Envia para o admin
        sent_message = bot.send_message(
            chat_id=ADMIN_ID,
            text=texto_aviso,
            parse_mode="HTML"
        )
        # === Adicione este bloco para exclusão automática ===
        # Excluir a mensagem após 60 segundos
        def delete_notification():
            try:
                bot.delete_message(chat_id=ADMIN_ID, message_id=sent_message.message_id)
            except Exception as e:
                print(f"Erro ao excluir a notificação: {e}")
        # Cria um timer para executar a função de exclusão
        timer = threading.Timer(60.0, delete_notification) # 60 segundos
        timer.start()
        # =======================================================
    except Exception as e:
        print(f"Erro ao enviar notificação de acesso: {e}")
def abrir_menu_principal(msg):
    chat_id = msg.chat.id
    texto = api.Textos.start(msg)
    markup = gerar_menu_principal(msg)
    from app import interface as fotos_menus
    # Usa a foto customizada do /start se houver uma salva, senão a padrão.
    # exibir_com_foto SEMPRE força essa foto certa, mesmo que a mensagem atual
    # já esteja mostrando a foto de outro menu (perfil, saldo, etc.) — evita
    # herdar a imagem errada ao voltar para o menu principal.
    foto = fotos_menus.obter_foto_menu('start') or api.FOTO_MENU_PRINCIPAL
    resultado = fotos_menus.exibir_com_foto(bot, chat_id, msg.message_id, foto, texto, reply_markup=markup)
    if resultado is True:
        ultimo_menu[chat_id] = msg.message_id
    elif resultado is not None:
        ultimo_menu[chat_id] = resultado.message_id
    else:
        # Último recurso: manda só o texto, sem foto, pra garantir que o
        # usuário não fique sem o menu de jeito nenhum.
        try:
            sent = bot.send_message(chat_id, texto, parse_mode='HTML', reply_markup=markup)
            ultimo_menu[chat_id] = sent.message_id
        except Exception as e:
            print(f"Erro crítico ao abrir menu principal: {e}")
pending_reminders: dict[int, Timer] = {}
# (Existing code...)
SETTINGS_FILE = 'settings.json'
def _load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                # Load existing settings
                settings = json.load(f)
                # Ensure the new key exists with a default value (True = enabled)
                settings.setdefault("reportar_problema_enabled", True)
                return settings
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
    # Return default values if file doesn't exist or is invalid
    return {"menu_categorias": True, "reportar_problema_enabled": True}
def _save_settings(cfg: dict):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
_settings_cache = _load_settings()
def menu_categorias_ativado() -> bool:
    return _settings_cache.get("menu_categorias", True)
def alternar_menu_categorias():
    _settings_cache["menu_categorias"] = not _settings_cache.get("menu_categorias", True)
    _save_settings(_settings_cache)
    return _settings_cache["menu_categorias"]
# --- NEW FUNCTIONS FOR REPORT PROBLEM TOGGLE ---
def is_reportar_problema_enabled() -> bool:
    """Checks if the 'Report Problem' button feature is enabled."""
    return _settings_cache.get("reportar_problema_enabled", True)
def toggle_reportar_problema():
    """Toggles the 'Report Problem' button feature on/off and saves the setting."""
    current_state = _settings_cache.get("reportar_problema_enabled", True)
    _settings_cache["reportar_problema_enabled"] = not current_state
    _save_settings(_settings_cache)
    return _settings_cache["reportar_problema_enabled"]
# --- END OF NEW FUNCTIONS ---
# (Rest of the code...)
def remind_no_purchase(user_id: int):
    # This function is called by a timer if the user doesn't purchase
    # after interacting with the bot via /start.
    if user_id in pending_reminders:
        try:
            # The timer has fired, so we remove its record.
            pending_reminders.pop(user_id, None)
            # Get user's first name for a personalized message
            try:
                user_info = bot.get_chat(user_id)
                user_name = user_info.first_name or "visitante"
            except Exception:
                user_name = "visitante"
            # Mensagem idêntica à foto com o gatilho de escassez
            texto_lembrete = (
                f"Ei, <b>{user_name}</b>! Notei que você iniciou nosso robô, mas acabou não finalizando nenhuma compra... 🛒❌\n\n"
                "Pensando em te dar uma força, separei um CUPOM EXCLUSIVO de 10% de desconto para sua primeira compra! 🎁⚠️\n\n"
                "🎟️ CUPOM: <b>PRIMEIRACOMPRA</b>\n\n"
                "Aproveite agora mesmo, pois ele expira em poucos minutos! ⏰👇"
            )
            # Estrutura com os 4 botões solicitados
            markup = InlineKeyboardMarkup()
            # Botão 1: Comprar Agora (ocupando a linha toda)
            markup.row(
                InlineKeyboardButton("🛒 COMPRAR AGORA", callback_data="servicos")
            )
            # Botões 2 e 3: Termos e Carrinho (lado a lado na mesma linha)
            markup.row(
                InlineKeyboardButton("📜 TERMOS", callback_data="ver_termos"),
                InlineKeyboardButton("🛒 CARRINHO", callback_data="mostrar_carrinho")
            )
            # Botão 4: Suporte (ocupando a linha toda no final)
            markup.row(
                InlineKeyboardButton("🆘 SUPORTE", url=api.CredentialsChange.SuporteInfo.link_suporte())
            )
            # URL do banner/imagem que aparece na foto
            LINK_DA_FOTO = "https://seu-servidor.com/sua-imagem.jpg" 
            try:
                # Tenta enviar a foto promocional junto com o texto e os 4 botões
                bot.send_photo(
                    user_id,
                    photo=LINK_DA_FOTO,
                    caption=texto_lembrete,
                    reply_markup=markup,
                    parse_mode="HTML"
                )
            except Exception:
                # Sistema de segurança: se a foto falhar, envia apenas o texto para o bot não travar
                bot.send_message(
                    user_id,
                    texto_lembrete,
                    reply_markup=markup,
                    parse_mode="HTML"
                )
        except Exception as e:
            # Avoid crashing if sending fails.
            print(f"Could not send detailed 'no purchase' reminder to user {user_id}: {e}")
def load_alerts():
    if os.path.exists(ALERTS_FILE):
        with open(ALERTS_FILE, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        return {
            chave: [int(uid) for uid in subs]
            for chave, subs in raw.items()
        }
    return {}
def save_alerts(alerts):
    with open(ALERTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(alerts, f, ensure_ascii=False, indent=2)
alerts = load_alerts()
# ==========================================================================
# ==========================================================================
termos_texto = """LEIA COM ATENÇÃO ANTES DE FINALIZAR SUA COMPRA
⚠️ LEIA ANTES DE FINALIZAR SUA COMPRA ⚠️
Ao confirmar, você aceita TODOS os termos abaixo:
🕒 HORÁRIOS DE ATENDIMENTO  
📅 Seg a Sex: 10h às 12h / 14:00 às 23h  
📅 Sáb: 10h às 12h / 14:00 às 22h  
📅 Dom e feriados: até 12h
💻 SUPORTE: 1h a 24h (pode demorar + se houver queda em massa)
1️⃣ Clique em SUPORTE no bot  
2️⃣ Descreva seu problema detalhadamente  
3️⃣ Envie:
• Print do erro  
• Login como recebido  
• Data da compra
❗ REGRAS IMPORTANTES  
• NÃO altere o e-mail da conta  
• NÃO fazemos reembolso por PIX (somente saldo no bot)  
• SEM respeito = BANIMENTO e PERDA de saldo
⏳ PROBLEMAS FORA DO HORÁRIO?  
Os dias serão compensados ✅
⚠️ Ao continuar, você confirma estar de acordo com tudo acima.
"""
REQUIRED_GROUP_ID = -1002787400901
JOIN_GROUP_LINK = "https://t.me/+z06ZYa4CplVlMWMx"  
SALES_GROUP_ID = -1002787400901
# CORREÇÃO: load_user_data/save_user_data eram funções LOCAIS que liam e
# gravavam em database/users/<id>.json (pasta que não existe mais após a
# migração para SQLite). As chamadas a load_user_data/save_user_data
# usam o banco SQLite compartilhado por todo o bot.
# Agora usamos as mesmas funções SQLite que o resto do bot usa.
from app.database import load_user_data, save_user_data, get_all_user_ids
print("Codigo iniciado...")
# ===== Sistema centralizado de emojis premium =====
try:
    from app import premium_emojis
    premium_emojis.install()
except Exception as e:
    print(f"[premium_emojis] Falha ao instalar: {e}")
# =================================================
bot = telebot.TeleBot(api.CredentialsChange.token_bot())
from app import restore_handlers
restore_handlers.registrar(bot, ADMIN_ID)
from app import estoque_api
from app import painel_estoque_api
painel_estoque_api.registrar(bot, api)
anti_flood.aplicar_antiflood(bot)
# --- Inicializações dos sistemas ---
# Inicializa o sistema de troca automática
troca_automatica.setup(bot, montar_botoes_extras=lambda *args: _montar_botoes_extras(*args))
# Inicializa o sistema de recompensas diárias
recompensas.setup(bot)
# Inicializa o sistema de renovação automática
renovacao_automatica.setup(bot)
# Inicializa o sistema de Cashback VIP
sistema_cashback_vip.registrar_handlers(bot)
# Inicializa o Sistema de Favoritos
from app import interface as sistema_favoritos
sistema_favoritos.registrar_favoritos(bot, api)
# Inicializa o novo sistema de Ranking separado
from app import interface as rankings
rankings.registrar_rankings(bot)
# Inicializa o sistema de Fotos de Produtos (comando /setfoto)
from app import interface as fotos_produtos
fotos_produtos.registrar_fotos_produtos(bot)

# Inicializa o sistema de Fotos de Menus (comando /setfotomenu)
from app import interface as fotos_menus
fotos_menus.registrar_fotos_menus(bot)
# Inicializa os botões de renovação do dono do bot
from app import renovacao_bot
renovacao_bot.registrar_handlers_renovacao(bot)
# ... (aqui ficam as outras funções do seu bot, inclusive a def painel_admin(message):) ...
# ...
# ...
def painel_admin(message):
    # Todo o código da sua função painel_admin termina aqui
    # ...
    pass
# AGORA, após a função ter sido criada, inicializamos a caixa:
from app import caixa_misteriosa
caixa_misteriosa.registrar_handlers(bot, api, painel_admin)
from app import sistema_promocoes
sistema_promocoes.registrar_handlers(bot, api, lambda *args: entregar(*args))
Oferta_relampago.setup_admin_handlers(bot, api)
# ... código final do seu bot ...
# ==== Quick buttons para PIX =====
@bot.callback_query_handler(func=lambda c: getattr(c, 'data', '').startswith('pix_quick '))
def __rl_pix_quick_cb(call):
    try:
        valor_txt = call.data.split(' ', 1)[1].strip()
        # Construímos um "Message-like" com tudo que o fluxo pode usar
        try:
            from types import SimpleNamespace
        except Exception:
            class SimpleNamespace: pass
        fake_msg = SimpleNamespace()
        fake_msg.text = f"/pix {valor_txt}"
        fake_msg.chat = getattr(call, "message", None).chat if getattr(call, "message", None) else None
        fake_msg.from_user = call.from_user
        fake_msg.message_id = getattr(call.message, "message_id", None)
        # Atributos de conveniência (alguns trechos do código usam direto em message)
        fake_msg.first_name = getattr(call.from_user, "first_name", None)
        fake_msg.username = getattr(call.from_user, "username", None)
        fake_msg.id = getattr(call.from_user, "id", None)
        gerar_pix_por_comando(fake_msg)
        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass
    except Exception as e:
        try:
            bot.answer_callback_query(call.id, f"Erro: {e}", show_alert=True)
        except Exception:
            pass
# ==== fim quick buttons =====
# ===== [/pix sem valor → instruções + ForceReply] =====
@bot.message_handler(func=lambda m: (m.text or "").strip().lower() in ["/pix", f"/pix@{api.CredentialsChange.user_bot().lower()}"])
def __rl_pix_sem_valor(message):
    """Quando o usuário envia apenas /pix, explicamos e pedimos o valor."""
    try:
        # Imports compatíveis com diferentes versões
        try:
            from telebot.types import ForceReply, InlineKeyboardMarkup, InlineKeyboardButton
        except Exception:
            from telebot import types as _t
            ForceReply = getattr(_t, "ForceReply", None)
            InlineKeyboardMarkup = _t.InlineKeyboardMarkup
            InlineKeyboardButton = _t.InlineKeyboardButton
        # Texto das instruções (triple quotes para evitar erros de sintaxe)
        texto = """💳 *Recarregar via PIX*
Para gerar o pagamento, envie o valor em reais.
*Exemplos:*
• `/pix 5`
• `/pix 10`
• `/pix 20`
_Dica:_ você pode usar ponto ou vírgula. Ex.: `/pix 12,50`"""
        # Envia instruções + ForceReply (se disponível)
        if ForceReply:
            force = ForceReply(selective=True)
            ask = bot.send_message(message.chat.id, texto, parse_mode="Markdown", reply_markup=force)
        else:
            ask = bot.send_message(message.chat.id, texto, parse_mode="Markdown")
        # Teclado com valores rápidos (fora de try/except para evitar blocos quebrados)
        kb = InlineKeyboardMarkup()
        kb.row(
            InlineKeyboardButton("R$5", callback_data="pix_quick 5"),
            InlineKeyboardButton("R$10", callback_data="pix_quick 10"),
            InlineKeyboardButton("R$20", callback_data="pix_quick 20")
        )
        # --- LINHA ADICIONADA ---
        kb.row(
            InlineKeyboardButton("R$50", callback_data="pix_quick 50"),
            InlineKeyboardButton("R$100", callback_data="pix_quick 100")
        )
        # ------------------------
        bot.send_message(message.chat.id, "Valores rápidos:", reply_markup=kb)
        # Próximo passo: validar resposta do usuário e acionar o fluxo oficial
        def _pix_step(resp):
            try:
                valor_txt = (resp.text or "").strip().replace(",", ".")
                _ = float(valor_txt)  # valida
                # Reaproveitar fluxo do /pix oficial
                try:
                    resp.text = f"/pix {valor_txt}"
                    gerar_pix_por_comando(resp)
                except Exception as e:
                    try:
                        bot.reply_to(resp, f"❌ Erro ao processar PIX: {e}")
                    except Exception:
                        pass
            except Exception:
                bot.reply_to(resp, "❌ Valor inválido. Envie apenas números. Ex.: 10 ou 12,50")
        # Registrar o handler de próximo passo na mensagem de instrução
        bot.register_next_step_handler(ask, _pix_step)
    except Exception as e:
        try:
            bot.reply_to(message, f"❌ Erro: {e}")
        except Exception:
            pass
# ===== [fim /pix sem valor] =====
@bot.message_handler(commands=['pix'])
def __rl_pix_handler(message):
    try:
        gerar_pix_por_comando(message)
    except Exception as e:
        try:
            bot.reply_to(message, f"❌ Erro ao processar PIX: {e}")
        except Exception:
            pass
# Função para obter todos os IDs de admin (dono + admins adicionais)
def get_all_admin_ids():
    admin_ids = set()
    try:
        # Adicionar o dono do bot
        admin_ids.add(int(api.CredentialsChange.id_dono()))
        # Adicionar outros admins se existir a função
        try:
            # Tentar obter lista de admins do sistema
            if hasattr(api.Admin, 'listar_admins'):
                outros_admins = api.Admin.listar_admins()
                if isinstance(outros_admins, (list, tuple)):
                    for admin_id in outros_admins:
                        admin_ids.add(int(admin_id))
        except Exception as e:
            print(f"[MAINTENANCE] Aviso: não consegui obter lista de admins: {e}")
    except Exception as e:
        print(f"[MAINTENANCE] Erro ao obter admin IDs: {e}")
        # Fallback para ID hardcoded se necessário
        admin_ids.add(7619679574)
    return list(admin_ids)
# Adicionar função de verificação de admin ao bot
def check_admin_function(uid):
    try:
        return (api.Admin.verificar_admin(uid) or int(uid) == int(api.CredentialsChange.id_dono()))
    except Exception:
        return False
bot._check_admin_function = check_admin_function
try:
    all_admin_ids = get_all_admin_ids()
    print(f"[MAINTENANCE] Instalando filtro para admins: {all_admin_ids}")
    install_maintenance_filter(bot, all_admin_ids)
except Exception as _e:
    print(f"[maintenance] aviso: não consegui instalar filtro: {_e}")
# ===== [RL AUTO-BACKUP TOGGLE - high priority] =====
try:
    from app import backup_manager
except Exception as _e:
    print("[backup-toggle] import error:", _e)
# ================================================================================================
# <<<---- INÍCIO DO CÓDIGO RESTAURADO ---->>>
@bot.callback_query_handler(func=lambda c: c.data.startswith('confirmar_compra_prompt '))
def callback_confirmar_compra_prompt(call):
    """
    Exibe a tela de confirmação antes da compra final, garantindo a verificação da Oferta Relâmpago.
    """
    try:
        dados = call.data.replace('confirmar_compra_prompt ', '').strip().split('|')
        servico = dados[0]
        preco_oferta = float(dados[1]) if len(dados) > 1 else None
        user_id = call.from_user.id
        # Verifica estoque e obtém o preço original do serviço
        resultado_peek = api.ControleLogins.peek_primeiro_disponivel(servico)
        if not resultado_peek:
            bot.answer_callback_query(call.id, "Ops! O estoque acabou enquanto você decidia.", show_alert=True)
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            return
        _, valor_str, *_ = resultado_peek
        valor_original = float(valor_str)
# DEPOIS: Faz a checagem correta usando o módulo de ofertas do bot
        # Se o preço da oferta não veio pelo callback_data, checa se há oferta ativa
        if preco_oferta is None:
            try:
                # Usa a verificação integrada do módulo Oferta_relampago
                preco_com_desconto = Oferta_relampago.verificar_preco(servico, valor_original)
                if preco_com_desconto < valor_original:
                    preco_oferta = preco_com_desconto
            except Exception as e:
                print(f"Erro ao verificar preço da oferta relâmpago: {e}")
        # Define o valor final a ser cobrado e mostrado
        valor_final = preco_oferta if preco_oferta is not None else valor_original
        saldo = float(api.InfoUser.saldo(user_id))
        saldo_apos = saldo - valor_final
        # --- BUSCA A DESCRIÇÃO DO PRODUTO PARA EXIBIR ANTES DA CONFIRMAÇÃO ---
        descricao_servico = None
        try:
            info = api.ControleLogins.pegar_info(servico)
            if info and len(info) >= 3 and info[2]:
                descricao_servico = info[2]
        except Exception as e:
            print(f"Erro ao buscar descrição do produto na confirmação: {e}")
        texto_confirmacao = (
            f"<b>🛒 Confirmar Compra</b>\n\n"
            f"<b>Serviço:</b> {servico}\n"
            f"<b>Valor:</b> R$ {valor_final:.2f}\n"
            f"<b>Seu saldo:</b> R$ {saldo:.2f}\n"
            f"<b>Saldo após compra:</b> R$ {saldo_apos:.2f}\n"
        )
        if descricao_servico:
            texto_confirmacao += (
                f"\n📋 <b>Descrição do produto:</b>\n"
                f"<i>{descricao_servico}</i>\n"
                f"\n⚠️ Leia a descrição antes de comprar."
            )
        texto_confirmacao += (
            f"\n\nAo confirmar, você declara que está ciente das condições do produto.\n\n"
            f"Deseja continuar com a compra?"
        )
        markup = InlineKeyboardMarkup()
        # IMPORTANTE: Sempre repassa o valor_final para o callback_final
        callback_final = f"comprar_final {servico}|{valor_final}"
        markup.row(
            InlineKeyboardButton(f"✅ Sim, comprar {servico}", callback_data=callback_final),
            InlineKeyboardButton("↩️ Voltar ao produto", callback_data=f"exibir_servico {servico}")
        )
        safe_edit_message(call.message, texto_confirmacao, reply_markup=markup)
        bot.answer_callback_query(call.id)
    except Exception as e:
        bot.answer_callback_query(call.id, f"Erro: {e}", show_alert=True)
@bot.callback_query_handler(func=lambda c: c.data.startswith('comprar_final '))
@estoque_api.serializar(bot)
def callback_comprar_final(call):
    """
    Executa a lógica de compra após a confirmação do usuário e deleta a msg de confirmação.
    """
    try:
        dados = call.data.replace('comprar_final ', '').strip().split('|')
        servico = dados[0]
        preco_oferta = float(dados[1]) if len(dados) > 1 else None
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        message_id_to_delete = call.message.message_id
        # Checagem final de estoque
        resultado_peek = api.ControleLogins.peek_primeiro_disponivel(servico)
        if not resultado_peek:
            bot.answer_callback_query(call.id, "Serviço esgotado!", show_alert=True)
            try:
                bot.delete_message(chat_id, message_id_to_delete)
            except Exception:
                pass
            return
        _, valor_original, *_ = resultado_peek
        # Garante o uso do valor com desconto repassado no callback
        valor_float = preco_oferta if preco_oferta is not None else float(valor_original)
        try:
            try:
                from app.database import get_user_balance
            except ImportError:
                 saldo_atual = float(api.InfoUser.saldo(user_id))
            else:
                 saldo_atual = get_user_balance(user_id)
        except NameError:
             saldo_atual = float(api.InfoUser.saldo(user_id))
        # CORREÇÃO: Arredondar para evitar erro de casas decimais do Python
        saldo_atual = round(saldo_atual, 2)
        valor_float = round(valor_float, 2)
        if saldo_atual < valor_float:
            falta = valor_float - saldo_atual
            bot.answer_callback_query(call.id, "Saldo insuficiente!", show_alert=False)
            markup_pix = InlineKeyboardMarkup()
            markup_pix.row(InlineKeyboardButton(f"💳 Depositar R$ {falta:.2f} via PIX", callback_data=f"pix_quick {falta:.2f}"))
            markup_pix.row(InlineKeyboardButton("↩️ Voltar ao produto", callback_data=f"exibir_servico {servico}"))
            texto_falta = (
                f"❌ <b>Saldo Insuficiente</b>\n\n"
                f"Faltam <b>R$ {falta:.2f}</b> para você adquirir: <i>{servico}</i>.\n\n"
                f"👇 Clique no botão abaixo para gerar o PIX no valor exato que falta e concluir sua compra:"
            )
            try:
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id_to_delete,
                    text=texto_falta,
                    parse_mode='HTML',
                    reply_markup=markup_pix
                )
            except Exception:
                bot.send_message(chat_id, texto_falta, parse_mode='HTML', reply_markup=markup_pix)
            return
        resultado = estoque_api.comprar(api, servico, user_id, f"venda:{user_id}:{call.message.message_id}", valor_float)
        if not resultado:
            bot.answer_callback_query(call.id, "Serviço esgotado! (Alguém comprou antes)", show_alert=True)
            try:
                bot.delete_message(chat_id, message_id_to_delete)
            except Exception:
                pass
            return
        nome, valor_compra, email, senha, descricao, duracao = resultado
        # CORREÇÃO: Usar 'valor_float' (que já aplica o desconto da Oferta Relâmpago, se houver)
        valor_compra_float = valor_float 
        entregar(call.message, nome, valor_compra_float, email, senha, descricao, duracao)
        sistema_cashback_vip.processar_compra_cashback(bot, call.from_user.id, valor_compra_float)
        bot.answer_callback_query(call.id, "✅ Compra realizada com sucesso!", show_alert=True)
        try:
            bot.delete_message(chat_id, message_id_to_delete)
        except Exception as e:
            print(f"Não foi possível deletar a mensagem de confirmação {message_id_to_delete} no chat {chat_id}: {e}")
    except Exception as e:
        print(f"Erro em callback_comprar_final para o serviço '{servico}': {e}")
        import traceback
        traceback.print_exc()
        try:
            bot.answer_callback_query(call.id, f"Erro ao finalizar a compra. Tente novamente ou contate o suporte.", show_alert=True)
        except Exception:
             print(f"Falha ao responder callback query durante tratamento de erro para o serviço '{servico}'")
# <<<---- FIM DO CÓDIGO RESTAURADO ---->>>
# ================================================================================================
# <<<---- ADICIONE TODO ESTE NOVO BLOCO DE CÓDIGO ---->>>
@bot.callback_query_handler(func=lambda call: call.data == 'resgatar_recompensa')
def callback_resgatar_recompensa(call):
    """Handler para o botão de Recompensa Diária por tarefas."""
    user_id = call.from_user.id
    try:
        status, data = recompensas.resgatar_recompensa(user_id)
        if status == "sucesso":
            valor = data
            bot.answer_callback_query(call.id, f"🎉 Parabéns! Você ganhou R$ {valor:.2f} de recompensa!", show_alert=True)
        elif status == "ja_resgatado":
            bot.answer_callback_query(call.id, "Você já resgatou sua recompensa de tarefas hoje. Tente novamente amanhã.", show_alert=True)
        elif status == "desativado":
            bot.answer_callback_query(call.id, "O sistema de recompensas está desativado no momento.", show_alert=True)
        elif status == "nao_cumpriu":
            comprou = data.get('comprou', False)
            recarregou = data.get('recarregou', False)
            mensagem = "Você ainda não cumpriu as tarefas de hoje:\n\n"
            mensagem += f"{'✅' if comprou else '❌'} Fazer pelo menos 1 compra no dia.\n"
            mensagem += f"{'✅' if recarregou else '❌'} Fazer pelo menos 1 recarga no dia.\n\n"
            mensagem += "Volte quando completar as tarefas!"
            bot.answer_callback_query(call.id, mensagem, show_alert=True)
        elif status == "erro":
            bot.answer_callback_query(call.id, f"Ocorreu um erro: {data}", show_alert=True)
    except Exception as e:
        print(f"[Recompensas] Erro no callback_resgatar_recompensa: {e}")
        bot.answer_callback_query(call.id, "Erro ao processar sua recompensa.", show_alert=True)
# ================================================================================================
# ======================= [/BÔNUS DIÁRIO - PRIORIDADE] =========================
@bot.callback_query_handler(func=lambda c: getattr(c, 'data', '') == "admin_backup_toggle")
def cb_admin_backup_toggle(c):
    try:
        if str(c.from_user.id) != str(ADMIN_ID):
            return bot.answer_callback_query(c.id, "Acesso negado.", show_alert=True)
        new_state = not backup_manager.is_enabled()
        backup_manager.set_enabled(new_state)
        status = "ligado 🟢" if new_state else "desligado 🔴"
        bot.answer_callback_query(c.id, f"Auto-Backup {status}!", show_alert=True)
        # Tenta re-renderizar o menu de BACKUP
        try:
            exibir_menu_backup(c.message)
        except Exception as _e:
            pass
    except Exception as e:
        try:
            bot.answer_callback_query(c.id, f"Erro: {e}", show_alert=True)
        except Exception:
            pass
# ===== [END RL AUTO-BACKUP TOGGLE] =====
# ===== [RL BACKUP BUTTONS - high priority handler BEFORE generic catch-alls] =====
try:
    from app import backup_manager
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
except Exception as _e:
    print("[backup] imports:", _e)
@bot.callback_query_handler(func=lambda c: c.data in {"admin_backup_now", "admin_backup_path"})
def cb_admin_backup(c):
    try:
        if str(c.from_user.id) != str(ADMIN_ID):
            return bot.answer_callback_query(c.id, "Acesso negado.", show_alert=True)
        if c.data == "admin_backup_path":
            import os
            try:
                bp = os.path.abspath(backup_manager.BACKUP_DIR)
                bot.answer_callback_query(c.id, "Ok!")
                bot.send_message(c.message.chat.id, f"📁 Pasta de backups:\n`{bp}`", parse_mode="Markdown")
            except Exception as e:
                bot.answer_callback_query(c.id, "Erro", show_alert=True)
                bot.send_message(c.message.chat.id, f"⚠️ Erro ao obter pasta: {e}")
            return
        if c.data == "admin_backup_now":
            bot.answer_callback_query(c.id, "Iniciando backup…")
            try:
                bot.send_message(c.message.chat.id, "⏳ Fazendo backup… (você receberá o arquivo/link ao concluir)")
                backup_manager.run_backup_async(bot=bot, admin_id=ADMIN_ID, label="manual")
            except Exception as e:
                bot.send_message(c.message.chat.id, f"⚠️ Erro ao iniciar backup: {e}")
    except Exception as e:
        try:
            bot.answer_callback_query(c.id, f"Erro: {e}", show_alert=True)
        except Exception:
            pass
# ===== [END RL BACKUP BUTTONS] =====
# ======================= [INÍCIO] GERENCIAMENTO DE COMBOS (ADMIN) =======================
@bot.message_handler(commands=['setpixmin'])
def command_mudar_deposito_minimo(message):
    """
    Comando para admin: Altera o valor mínimo de depósito PIX.
    Uso: /setpixmin 5.00
    """
    try:
        # Verifica se o usuário é o dono do bot
        if str(message.from_user.id) != str(api.CredentialsChange.id_dono()):
            bot.reply_to(message, "🚫 Você não tem permissão para usar este comando.")
            return
        parts = (message.text or "").strip().split(maxsplit=1)
        if len(parts) < 2:
            current_min = api.CredentialsChange.InfoPix.deposito_minimo_pix()
            bot.reply_to(message, f"ℹ️ **Valor mínimo atual:** R$ {current_min:.2f}\nUse assim: <b>/setpixmin 10.00</b>", parse_mode='HTML')
            return
        try:
            novo_minimo = float(str(parts[1]).replace(",", "."))
        except ValueError:
            bot.reply_to(message, "❌ Valor inválido. Exemplo: <b>/setpixmin 5.00</b>", parse_mode='HTML')
            return
        if novo_minimo <= 0:
            bot.reply_to(message, "❌ O valor mínimo deve ser positivo.", parse_mode='HTML')
            return
        api.CredentialsChange.InfoPix.trocar_deposito_minimo_pix(novo_minimo)
        bot.reply_to(message, f"✅ Depósito mínimo PIX atualizado para <b>R${novo_minimo:.2f}</b>", parse_mode='HTML')
    except Exception as e:
        bot.reply_to(message, f"⚠️ Não foi possível salvar o mínimo: {e}")
@bot.message_handler(commands=['setpixmax'])
def command_mudar_deposito_maximo(message):
    """
    Comando para admin: Altera o valor máximo de depósito PIX.
    Uso: /setpixmax 500.00
    """
    try:
        # Verifica se o usuário é o dono do bot
        if str(message.from_user.id) != str(api.CredentialsChange.id_dono()):
            bot.reply_to(message, "🚫 Você não tem permissão para usar este comando.")
            return
        parts = (message.text or "").strip().split(maxsplit=1)
        if len(parts) < 2:
            current_max = api.CredentialsChange.InfoPix.deposito_maximo_pix()
            bot.reply_to(message, f"ℹ️ **Valor máximo atual:** R$ {current_max:.2f}\nUse assim: <b>/setpixmax 500.00</b>", parse_mode='HTML')
            return
        try:
            novo_maximo = float(str(parts[1]).replace(",", "."))
        except ValueError:
            bot.reply_to(message, "❌ Valor inválido. Exemplo: <b>/setpixmax 500.00</b>", parse_mode='HTML')
            return
        if novo_maximo <= 0:
            bot.reply_to(message, "❌ O valor máximo deve ser positivo.", parse_mode='HTML')
            return
        api.CredentialsChange.InfoPix.trocar_deposito_maximo_pix(novo_maximo)
        bot.reply_to(message, f"✅ Depósito máximo PIX atualizado para <b>R${novo_maximo:.2f}</b>", parse_mode='HTML')
    except Exception as e:
        bot.reply_to(message, f"⚠️ Não foi possível salvar o máximo: {e}")
# Menu principal de configuração de combos
# === HEALTHCHECK COMMAND ===
# ===== [RL BACKUP INTERVAL CONFIG] =====
@bot.callback_query_handler(func=lambda c: getattr(c, 'data', '') == 'admin_backup_interval')
def cb_admin_backup_interval(c):
    try:
        if str(c.from_user.id) != str(ADMIN_ID):
            return bot.answer_callback_query(c.id, "Acesso negado.", show_alert=True)
        kb = InlineKeyboardMarkup()
        kb.row(
            InlineKeyboardButton("30 min", callback_data="admin_backup_interval_set_30"),
            InlineKeyboardButton("1h", callback_data="admin_backup_interval_set_60"),
        )
        kb.row(
            InlineKeyboardButton("6h", callback_data="admin_backup_interval_set_360"),
            InlineKeyboardButton("12h", callback_data="admin_backup_interval_set_720"),
        )
        kb.row(
            InlineKeyboardButton("24h", callback_data="admin_backup_interval_set_1440"),
        )
        cur = backup_manager._humanize_minutes(backup_manager.get_backup_interval_minutes())
        try:
            bot.edit_message_text(f"⏱️ Intervalo atual: *{cur}*\nEscolha um novo intervalo:", c.message.chat.id, c.message.message_id, reply_markup=kb, parse_mode="Markdown")
        except Exception:
            bot.send_message(c.message.chat.id, f"⏱️ Intervalo atual: *{cur}*\nEscolha um novo intervalo:", reply_markup=kb, parse_mode="Markdown")
        bot.answer_callback_query(c.id)
    except Exception as e:
        bot.answer_callback_query(c.id, f"Erro: {e}", show_alert=True)
@bot.callback_query_handler(func=lambda c: getattr(c, 'data', '').startswith('admin_backup_interval_set_'))
def cb_admin_backup_interval_set(c):
    """Callback para definir um novo intervalo de backup e reagendar."""
    try:
        # Verifica permissão
        if str(c.from_user.id) != str(ADMIN_ID):
            return bot.answer_callback_query(c.id, "Acesso negado.", show_alert=True)
        # Extrai os minutos do callback data
        minutes_str = c.data.split('_')[-1]
        minutes = int(minutes_str)
        # Atualiza a configuração usando a função do backup_manager
        # Esta função agora retorna o valor validado que foi salvo
        saved_minutes = backup_manager.set_backup_interval_minutes(minutes) # <--- Não chama mais reschedule_backup daqui
        # Reagenda o job no bot.py com o novo intervalo
        update_schedule() # <--- Chama a nova função update_schedule() definida no bot.py
        # Responde ao admin
        bot.answer_callback_query(c.id, f"✅ Intervalo definido para {backup_manager._humanize_minutes(saved_minutes)} e reagendado!", show_alert=True)
        # Tenta reabrir o MENU DE BACKUP para refletir a mudança
        try:
            exibir_menu_backup(c.message)
        except Exception as e:
            print(f"[Admin Panel] Não foi possível reabrir menu backup: {e}")
            pass
    except ValueError:
        bot.answer_callback_query(c.id, "Erro: Valor de intervalo inválido.", show_alert=True)
    except Exception as e:
        print(f"[Callback Error] Erro em cb_admin_backup_interval_set: {e}")
        bot.answer_callback_query(c.id, f"Erro ao definir intervalo: {e}", show_alert=True)
# <<<---- ADICIONE TODO ESTE NOVO BLOCO DE CÓDIGO ---->>>
# ===== [PRIORITY] Comando ADM /setrecompensa (para o novo sistema) =====
@bot.message_handler(commands=['setrecompensa'])
def __rl_cmd_setrecompensa_priority(message):
    try:
        if str(message.from_user.id) != str(api.CredentialsChange.id_dono()):
            bot.reply_to(message, "🚫 Você não tem permissão para usar este comando.")
            return
        parts = (message.text or "").strip().split(maxsplit=1)
        if len(parts) < 2:
            bot.reply_to(message, "ℹ️ Use assim: <b>/setrecompensa 1.00</b> (Valor da recompensa por tarefas)", parse_mode='HTML')
            return
        try:
            novo_valor = float(str(parts[1]).replace(",", "."))
        except ValueError:
            bot.reply_to(message, "❌ Valor inválido. Exemplo: <b>/setrecompensa 1.00</b>", parse_mode='HTML')
            return
        api.CredentialsChange.RecompensaDiaria.mudar_valor(novo_valor)
        bot.reply_to(message, f"✅ Recompensa diária por tarefas atualizada para <b>R${novo_valor:.2f}</b>", parse_mode='HTML')
    except AttributeError:
        bot.reply_to(message, "⚠️ A função para configurar a recompensa diária não foi encontrada no 'central.py'.")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Não foi possível salvar a recompensa: {e}")
# ================================================================================================
@bot.message_handler(commands=['ping'])
def _cmd_ping(message):
    try:
        bot.reply_to(message, "pong 🏓")
    except Exception as e:
        try:
            bot.send_message(message.chat.id, f"pong (com aviso): {e}")
        except Exception:
            pass
# === FIM HEALTHCHECK COMMAND ===
@bot.message_handler(commands=['togglepixmanual'])
def command_toggle_pix_manual(message):
    """
    Comando de admin para ligar ou desligar o PIX Manual rapidamente.
    """
    # 1. Verificar permissão
    if not is_admin_user(message.from_user.id):
         bot.reply_to(message, "🚫 Você não tem permissão para usar este comando.")
         return
    try:
        # 2. Chamar a função que alterna (toggle) o status
        # (Esta é a mesma função que o seu painel de admin usa)
        api.CredentialsChange.ChangeStatusPix.change_pix_manual()
        # 3. Verificar o novo estado
        novo_status = api.CredentialsChange.StatusPix.pix_manual()
        # 4. Enviar feedback para o admin
        if novo_status:
            feedback = "✅ *PIX Manual ativado!* \nO botão agora está visível para os clientes no menu de recarga."
        else:
            feedback = "🔴 *PIX Manual desativado!* \nO botão foi ocultado dos clientes."
        bot.reply_to(message, feedback, parse_mode="Markdown")
    except Exception as e:
        print(f"[ERRO] /togglepixmanual: {e}")
        bot.reply_to(message, f"Ocorreu um erro ao tentar alterar o status: {e}")
# ======================= [FIM COMANDOS ADM] =======================
# ==== [AUTO-ICON DELIVERY PATCH v4b] Robust ====
import re as _reAI4
try:
    from app.bot import enviar_icone_servico as _enviar_icone_servico
except Exception:
    _enviar_icone_servico = globals().get("enviar_icone_servico")
__orig_send_message__v4 = bot.send_message
_RX_NOME = _reAI4.compile(r"(?is)(?:Servi[cç]o|Produto)[^:\n]*[:：]\s*(?:<b>)?([^<\n]+)")
_REMOVE_TOKENS = _reAI4.compile(r"\b(\d+\s*(m[eê]s|mes|meses|dias?)|premium|platinum|padr[aã]o|plus|pro|ultra|hd|uhd|4k|family|conta|perfil|combo|mensal|anual|trial)\b", _reAI4.IGNORECASE)
def _base_service_name(name: str) -> str:
    n = _REMOVE_TOKENS.sub(" ", name)
    n = _reAI4.sub(r"[^A-Za-zÀ-ÖØ-öø-ÿ\s]", " ", n)
    n = _reAI4.sub(r"\s+", " ", n).strip()
    parts = n.split()
    if len(parts) >= 2:
        return " ".join(parts[:2])
    return parts[0] if parts else (name or "").strip()
def _looks_like_delivery(text: str) -> bool:
    if not isinstance(text, str):
        return False
    t = text
    has_kind = ("Produto" in t) or ("Serviço" in t) or ("Servico" in t)
    has_email = ("Email" in t) or ("E-mail" in t) or ("@")
    has_senha = ("Senha" in t)
    return has_kind and has_email and has_senha
def _send_with_icon_if_possible(chat_id, text, reply_markup=None):
    if not callable(_enviar_icone_servico):
        return False
    try:
        m = _RX_NOME.search(text or "")
        if not m:
            return False
        full = (m.group(1) or "").strip()
        if _enviar_icone_servico(bot, chat_id, full, caption=text, reply_markup=reply_markup):
            return True
        base = _base_service_name(full)
        if base and base.lower() != full.lower():
            if _enviar_icone_servico(bot, chat_id, base, caption=text, reply_markup=reply_markup):
                return True
        first = (base.split()[0] if base else (full.split()[0] if full else "")).strip()
        if first and first.lower() not in (base.lower() if base else ""):
            if _enviar_icone_servico(bot, chat_id, first, caption=text, reply_markup=reply_markup):
                return True
    except Exception:
        pass
    return False
def __icon_aware_send_message_v4__(chat_id, text, *args, **kwargs):
    try:
        if _looks_like_delivery(text):
            if _send_with_icon_if_possible(chat_id, text, reply_markup=kwargs.get("reply_markup")):
                return True
    except Exception:
        pass
    return __orig_send_message__v4(chat_id, text, *args, **kwargs)
if not getattr(bot, "_auto_icon_delivery_patched_v4", False):
    bot.send_message = __icon_aware_send_message_v4__
    bot._auto_icon_delivery_patched_v4 = True
    print("[auto-icon v4b] ativo: detecta 'Produto:'/'Serviço:' e variações.")
# ==== [/AUTO-ICON DELIVERY PATCH v4b] =============================================
# ===== TERMS V2 - COMPLETE (CORRIGIDO) =====
try:
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    print("[TERMS] Sistema de Termos V2 carregando...")
    # Funções de suporte para carregar e salvar dados do usuário
    def _th_load(uid):
        try:
            return load_user_data(uid) or {}
        except Exception:
            return {}
    def _th_save(uid, data):
        try:
            save_user_data(uid, data)
        except Exception as e:
            print("[TERMS] Falha ao salvar dados do usuário:", e)
    # Lógica que decide QUANDO mostrar os termos
    def _th_need_after_inc(uid) -> bool:
        import time
        d = _th_load(uid)
        count = int(d.get('start_count', 0)) + 1
        d['start_count'] = count
        # Regra: mostrar termos se nunca aceitou OU a cada 5 usos do /start
        need = (not bool(d.get('accepted_once', False))) or (count % 50 == 0)
        if need:
            d['last_terms_time'] = time.time()
        d['pending_terms'] = need
        _th_save(uid, d)
        print(f"[TERMS] ID:{uid} | Contagem de /start: {count} | Aceitou antes: {d.get('accepted_once', False)} | Precisa aceitar agora: {need}")
        return need
    # Verifica se o usuário tem um aceite pendente
    def _th_pending(uid) -> bool:
        p = bool(_th_load(uid).get('pending_terms', False))
        return p
    # Marca os termos como aceitos
    def _th_accept(uid):
        d = _th_load(uid)
        d['pending_terms'] = False
        d['accepted_once'] = True
        _th_save(uid, d)
        print(f"[TERMS] ID:{uid} marcou os termos como aceitos.")
    # Gera o teclado da primeira etapa
    def _th_initial_markup():
        mk = InlineKeyboardMarkup()
        # O botão 'Ler Novamente' foi removido da primeira tela
        mk.row(
            InlineKeyboardButton("✅ Aceitar", callback_data="aceitar_termos_step1_v2"),
            InlineKeyboardButton("❌ Recusar", callback_data="recusar_termos_v2")
        )
        return mk
    # Função que exibe os termos
    def _th_show(chat_id):
        bot.send_message(chat_id, termos_texto, parse_mode="HTML", reply_markup=_th_initial_markup())
    # --- Handlers para o fluxo de 2 etapas ---
    @bot.callback_query_handler(func=lambda call: call.data == "aceitar_termos_step1_v2")
    def _th_on_accept_step1(call):
        try:
            bot.answer_callback_query(call.id)
            mk = InlineKeyboardMarkup()
            mk.row(InlineKeyboardButton("✅ Confirmo que li e aceito", callback_data="confirmar_termos_v2"))
            mk.row(InlineKeyboardButton("🔄 Ler Novamente", callback_data="ler_termos_v2"))
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=(
                    "📘 <b>Confirmação de Aceite</b>\n\n"
                    "Você confirma que <b>leu</b> e <b>aceita</b> todos os termos acima?\n\n"
                    "<i>Sem aceitar, não é possível prosseguir.</i>"
                ),
                parse_mode="HTML",
                reply_markup=mk
            )
        except Exception as e:
            print("[TERMS] Erro na etapa 1 de aceite:", e)
    @bot.callback_query_handler(func=lambda call: call.data == "confirmar_termos_v2")
    def _th_on_accept_final(call):
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        try:
            _th_accept(user_id)
            # Primeiro responder ao callback
            try:
                bot.answer_callback_query(call.id, "✅ Termos aceitos. Bem-vindo(a)!")
            except:
                pass  # Se falhar, continua mesmo assim
            # Deletar a mensagem dos termos
            try:
                bot.delete_message(chat_id, call.message.message_id)
            except:
                pass  # Se não conseguir deletar, continua
            # Antes de abrir o menu, respeitar manutenção
            try:
                if is_on():
                    # Permitir somente admin/dono durante manutenção
                    if not (api.Admin.verificar_admin(user_id) or int(user_id) == int(api.CredentialsChange.id_dono())):
                        bot.send_message(chat_id, get_maintenance_message(), allow_sending_without_reply=True)
                        return
                elif api.CredentialsChange.status_manutencao():
                    if not api.Admin.verificar_admin(user_id) and api.CredentialsChange.id_dono() != int(user_id):
                        bot.send_message(chat_id, "🔧 O bot está em manutenção, voltaremos em breve!", allow_sending_without_reply=True)
                        return
            except Exception as guard_error:
                print(f"[TERMS] Falha ao checar manutenção após aceite: {guard_error}")
            # Enviar o menu principal como nova mensagem
            try:
                abrir_menu_principal(call.message)
                print(f"[TERMS] Menu principal enviado para {user_id}")
            except Exception as menu_error:
                print(f"[TERMS] Erro ao abrir menu para {user_id}: {menu_error}")
                # Fallback: enviar mensagem simples
                bot.send_message(chat_id, "✅ Termos aceitos! Use /start para ver o menu principal.")
        except ApiTelegramException as api_error:
            # Erro específico da API do Telegram (ex: mensagem expirada para editar)
            print(f"[TERMS][ERROR] Erro de API no aceite final para {user_id}: {api_error}")
            try:
                bot.answer_callback_query(call.id, "⚠️ Ocorreu um erro de comunicação. Por favor, tente usar o comando /start novamente.", show_alert=True)
            except:
                pass
        except Exception as e:
            # Captura outros erros inesperados
            print(f"[TERMS][FATAL] Erro inesperado no aceite final para {user_id}: {e}")
            try:
                bot.answer_callback_query(call.id, "⚠️ Um erro crítico ocorreu. O administrador já foi notificado.", show_alert=True)
            except:
                pass
            # Tenta notificar o administrador sobre o erro grave
            try:
                bot.send_message(ADMIN_ID, f"⚠️ Erro crítico no aceite final dos termos pelo usuário {user_id}:\n\n`{e}`", parse_mode="Markdown")
            except Exception as admin_notify_error:
                print(f"[TERMS][FATAL] Falha ao notificar admin sobre erro: {admin_notify_error}")
    @bot.callback_query_handler(func=lambda call: call.data == "ler_termos_v2")
    def _th_on_read_again(call):
        try:
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=termos_texto,
                parse_mode="HTML",
                reply_markup=_th_initial_markup()
            )
        except Exception as e:
            print("[TERMS] Erro ao reabrir termos:", e)
    @bot.callback_query_handler(func=lambda call: call.data == "recusar_termos_v2")
    def _th_on_decline(call):
        try:
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=(
                    "⚠️ Você recusou os termos de uso.\n\n"
                    "Para utilizar o bot, é necessário aceitar as regras. "
                    "Use /start novamente quando desejar revê-los."
                )
            )
            # Mantém o status de pendente para a próxima vez que usar /start
            d = _th_load(call.from_user.id)
            d['pending_terms'] = True
            _th_save(call.from_user.id, d)
        except Exception as e:
            print("[TERMS] Erro ao recusar termos:", e)
    print("[TERMS] Sistema de Termos V2 (Completo) ativo.")
except Exception as e:
    print("[TERMS] Sistema de Termos V2 falhou ao carregar:", e)
# ===== /TERMS V2 - COMPLETE (CORRIGIDO) =====
# ====== AntiFlood: desabilitado globalmente ======
# Anti-flood agora só funciona no comando /start
# ===========================================================
# ========================= Comando ADM: /limparcache =========================
@bot.message_handler(commands=['limparcache'])
def cmd_limpar_cache(message):
    try:
        # Verifica se é o dono
        if str(message.from_user.id) != str(api.CredentialsChange.id_dono()):
            bot.reply_to(message, "🚫 Você não tem permissão para usar este comando.")
            return
        from app import limpeza_cache_boot
        # Executa a limpeza enviando o feedback em tempo real para o chat atual
        limpeza_cache_boot.limpar_cache_boot(bot, message.chat.id)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Erro ao tentar limpar o cache: {e}")
# ========================= Comando ADM: /setbonus =========================
@bot.message_handler(commands=['setbonus'])
def _cmd_setbonus(message):
    try:
        if str(message.from_user.id) != str(api.CredentialsChange.id_dono()):
            bot.reply_to(message, "🚫 Você não tem permissão para usar este comando.")
            return
        parts = message.text.strip().split(maxsplit=1)
        if len(parts) < 2:
            bot.reply_to(message, "ℹ️ Use assim: <b>/setbonus 5.0</b>", parse_mode='HTML')
            return
        try:
            novo_valor = float(str(parts[1]).replace(",", "."))
        except ValueError:
            bot.reply_to(message, "❌ Valor inválido. Exemplo: <b>/setbonus 3.50</b>", parse_mode='HTML')
            return
        api.CredentialsChange.BonusRegistro.mudar_bonus(novo_valor)
        bot.reply_to(message, f"✅ Bônus de registro atualizado para <b>R${novo_valor:.2f}</b>", parse_mode='HTML')
    except Exception as e:
        bot.reply_to(message, f"⚠️ Não foi possível salvar o bônus: {e}")
# =========================================================================
# =========================================================================
# ======================= [INÍCIO] PAINEL DE GERENCIAMENTO DE BÔNUS =======================
# [FUNÇÃO ADICIONADA]
def exibir_painel_bonus(message, edit=False):
    """
    Exibe o painel de gerenciamento de todos os bônus.
    """
    try:
        # 1. Coletar todos os valores de bônus da API
        try:
            b_registro = api.CredentialsChange.BonusRegistro.bonus()
        except Exception: b_registro = 0.0
        try:
            # Tenta pegar o bônus diário (login)
            b_diario = api.CredentialsChange.BonusDiario.valor()
        except Exception: b_diario = 0.0
        try:
            b_recompensa = api.CredentialsChange.RecompensaDiaria.valor()
        except Exception: b_recompensa = 0.0
        try:
            b_pix_pct = api.CredentialsChange.BonusPix.quantidade_bonus()
        except Exception: b_pix_pct = 0.0
        try:
            b_pix_min = api.CredentialsChange.BonusPix.valor_minimo_para_bonus()
        except Exception: b_pix_min = 0.0
        # 2. Montar o texto
        texto = (
            f"<b>🎉 Painel de Gerenciamento de Bônus</b>\n\n"
            f"Configure os valores de recompensa para seus usuários.\n\n"
            f"<b>Bônus de Registro:</b> R$ {b_registro:.2f}\n"
            f"<b>Bônus Diário (Login):</b> R$ {b_diario:.2f}\n"
            f"<b>Recompensa (Tarefas):</b> R$ {b_recompensa:.2f}\n\n"
            f"<b>Bônus PIX:</b> {b_pix_pct:.0f}% ativado\n"
            f"<b>Mínimo p/ Bônus PIX:</b> R$ {b_pix_min:.2f}"
        )
        # 3. Montar os botões
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("Bônus Registro", callback_data="bonus_set_registro"),
            InlineKeyboardButton("Bônus Diário", callback_data="bonus_set_diario")
        )
        markup.row(
            InlineKeyboardButton("Recompensa Tarefas", callback_data="bonus_set_recompensa")
        )
        markup.row(
            InlineKeyboardButton("Bônus PIX %", callback_data="bonus_set_pix_pct"),
            InlineKeyboardButton("Mínimo PIX", callback_data="bonus_set_pix_min")
        )
        markup.row(InlineKeyboardButton("↩ Voltar ao Painel Admin", callback_data="voltar_paineladm"))
        # 4. Enviar ou editar
        if edit:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=message.message_id,
                text=texto,
                parse_mode='HTML',
                reply_markup=markup
            )
        else:
            bot.send_message(
                message.chat.id,
                text=texto,
                parse_mode='HTML',
                reply_markup=markup
            )
    except Exception as e:
        print(f"[ERRO] Falha ao exibir painel de bônus: {e}")
        # Tenta enviar uma mensagem de erro para o admin
        try:
            bot.send_message(message.chat.id, f"Ocorreu um erro ao abrir o painel de bônus: {e}")
        except:
            pass
# [FIM DA FUNÇÃO ADICIONADA]
@bot.callback_query_handler(func=lambda call: call.data == 'admin_gerenciar_bonus')
def callback_gerenciar_bonus(call):
    """Callback do botão principal do painel admin."""
    if not is_admin_user(call.from_user.id):
        return bot.answer_callback_query(call.id, "🚫 Acesso Negado!", show_alert=True)
    bot.answer_callback_query(call.id)
    exibir_painel_bonus(call.message, edit=True) # Agora esta função existe
@bot.callback_query_handler(func=lambda call: call.data.startswith('bonus_set_'))
def callback_alterar_bonus(call):
    """Handler para os 4 botões de alteração."""
    if not is_admin_user(call.from_user.id):
        return bot.answer_callback_query(call.id, "🚫 Acesso Negado!", show_alert=True)
    tipo_bonus = call.data.replace('bonus_set_', '')
    # Mapeia os tipos para prompts amigáveis (usando a versão completa)
    prompts = {
        'registro': "Digite o novo <b>Bônus de Registro</b> (ex: 5.00):",
        'diario': "Digite o novo <b>Bônus Diário (Login)</b> (ex: 0.50):",
        'recompensa': "Digite a nova <b>Recompensa Diária (Tarefas)</b> (ex: 1.00):",
        'pix_pct': "Digite a nova <b>Porcentagem de Bônus PIX</b> (ex: 10 para 10%):",
        'pix_min': "Digite o novo <b>Valor Mínimo para Bônus PIX</b> (ex: 50.00):"
    }
    prompt_texto = prompts.get(tipo_bonus, "Digite o novo valor:")
    bot.answer_callback_query(call.id)
    msg = bot.send_message(
        call.message.chat.id,
        prompt_texto,
        parse_mode='HTML',
        reply_markup=types.ForceReply()
    )
    # Passa o 'message' original do painel para que possamos editá-lo depois
    bot.register_next_step_handler(msg, processar_novo_bonus, tipo_bonus, call.message)
def processar_novo_bonus(message, tipo_bonus, painel_message):
    """
    Recebe o valor do admin, salva na API e atualiza o painel de bônus.
    (Usando a versão completa)
    """
    try:
        novo_valor_str = message.text.strip().replace(',', '.').replace('%', '')
        novo_valor_float = float(novo_valor_str)
        if novo_valor_float < 0:
            bot.reply_to(message, "❌ Valor inválido. O número deve ser 0 ou positivo.")
            # Reexibe o painel sem salvar
            exibir_painel_bonus(painel_message, edit=True)
            return
        # Salva o valor usando a API correspondente
        if tipo_bonus == 'registro':
            api.CredentialsChange.BonusRegistro.mudar_bonus(novo_valor_float)
            feedback = f"✅ Bônus de Registro atualizado para R$ {novo_valor_float:.2f}"
        elif tipo_bonus == 'diario':
            api.CredentialsChange.BonusDiario.mudar_valor(novo_valor_float)
            feedback = f"✅ Bônus Diário (Login) atualizado para R$ {novo_valor_float:.2f}"
        elif tipo_bonus == 'recompensa':
            api.CredentialsChange.RecompensaDiaria.mudar_valor(novo_valor_float)
            feedback = f"✅ Recompensa Diária (Tarefas) atualizada para R$ {novo_valor_float:.2f}"
        elif tipo_bonus == 'pix_pct':
            api.CredentialsChange.BonusPix.mudar_quantidade_bonus(novo_valor_float)
            feedback = f"✅ Bônus PIX atualizado para {novo_valor_float:.0f}%"
        elif tipo_bonus == 'pix_min':
            api.CredentialsChange.BonusPix.mudar_valor_minimo_para_bonus(novo_valor_float)
            feedback = f"✅ Mínimo para Bônus PIX atualizado para R$ {novo_valor_float:.2f}"
        else:
            feedback = "❌ Erro: Tipo de bônus desconhecido."
        bot.reply_to(message, feedback)
    except ValueError:
        bot.reply_to(message, "❌ Valor inválido. Envie apenas números (ex: 5.00 ou 10).")
    except Exception as e:
        bot.reply_to(message, f"❌ Erro ao salvar: {e}")
    # Sempre atualiza o painel de bônus no final
    try:
        # Deleta a mensagem do admin (o valor digitado)
        bot.delete_message(message.chat.id, message.message_id)
    except Exception:
        pass 
    exibir_painel_bonus(painel_message, edit=True)
# ======================= [FIM] PAINEL DE GERENCIAMENTO DE BÔNUS =======================
# Verificar se o usuário tem um username
@bot.message_handler(func=lambda message: not message.from_user.username)
# Verificar se o usuário tem um username
@bot.message_handler(func=lambda message: not message.from_user.username)
def bloquear_sem_username(message):
    bot.send_message(
        message.chat.id,
        "⚠️ Você precisa definir um nome de usuário no Telegram para usar este bot!\n\n"
        "Vá nas configurações do Telegram e adicione um @username ao seu perfil.",
    )
    return
# ======================= [INÍCIO] LÓGICA DE STARTUP E POLLING =======================
def send_startup_notification():
    restore_handlers.notify_result(bot, ADMIN_ID)
    try:
        bot.send_message(
            chat_id=api.CredentialsChange.id_dono(),
            text='🤖 <b>𝗕𝗢𝗧 𝗥𝗘𝗜𝗡𝗜𝗖𝗜𝗔𝗗𝗢!</b> 🤖',
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton('🔧 𝐏𝐀𝐈𝐍𝐄𝐋 𝐀𝐃𝐌𝐈𝐍', callback_data='voltar_paineladm')]]
            )
        )
    except Exception as e:
        print(f"[BOOT] Erro ao enviar notificação: {e}")
def start_polling():
    import os
    import time
    from app import limpeza_cache_boot
    # Verificar se já existe uma instância rodando (lock real de arquivo via flock,
    # liberado automaticamente pelo SO quando o processo dono termina — funciona
    # mesmo em containers onde o PID pode ser reaproveitado, ex: sempre PID 1)
    global _lock_file_handle
    lockfile = "bot_instance.lock"
    _lock_file_handle = open(lockfile, 'a+')
    try:
        if os.name == 'nt':
            import msvcrt
            if os.path.getsize(lockfile) == 0:
                _lock_file_handle.write(' ')
                _lock_file_handle.flush()
            _lock_file_handle.seek(0)
            msvcrt.locking(_lock_file_handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(_lock_file_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (OSError, BlockingIOError):
        print("[ERROR] Já existe uma instância do bot rodando (lock ativo)! Abortando esta inicialização para evitar polling duplicado.")
        _lock_file_handle.close()
        return
    _lock_file_handle.seek(0)
    _lock_file_handle.truncate()
    _lock_file_handle.write(str(os.getpid()))
    _lock_file_handle.flush()
    print(f"[BOOT] Instância única confirmada (PID: {os.getpid()})")
    # Sobe o servidor de healthcheck HTTP (/health, /status) em thread separada.
    # Sem isso, a plataforma de hospedagem não recebe resposta de saúde do processo
    # e pode ficar reiniciando o bot periodicamente (SIGTERM) achando que está travado.
    if os.environ.get("BOT_EXTERNAL_HEALTHCHECK") != "1":
        try:
            from app import healthcheck
            threading.Thread(target=healthcheck.start_healthcheck_server, daemon=True).start()
            print("[BOOT] Servidor de healthcheck iniciado em thread separada.")
        except Exception as e:
            print(f"[ERROR] Falha ao iniciar healthcheck: {e}")
    # A limpeza é local: chamadas ao Telegram não devem atrasar o polling.
    limpeza_cache_boot.limpar_cache_boot()
    threading.Thread(target=send_startup_notification, daemon=True).start()
    # (AQUI VOCÊ APAGOU A LINHA REPETIDA)
    print("[BOOT] removendo webhook e iniciando polling…")
    # ... o resto do código continua igual ...
    try:
        info = bot.get_webhook_info()
        print(f"[TG] getWebhookInfo(pytelebot): url={getattr(info, 'url', None)}, pending={getattr(info, 'pending_update_count', None)}")
    except Exception as e:
        print(f"[TG] getWebhookInfo erro: {e}")
    try:
        bot.remove_webhook()
        print("[TG] remove_webhook() chamado com sucesso.")
    except Exception as e:
        print(f"[TG] remove_webhook() erro: {e}")
    # loop robusto com backoff exponencial
    reconnect_attempts = 0
    max_attempts = 20
    try:
        while True:
            try:
                print(f"[TG] Iniciando polling (tentativa {reconnect_attempts + 1})")
                bot.infinity_polling(timeout=20, long_polling_timeout=20)
                # Se chegou aqui, reset counter
                reconnect_attempts = 0
            except KeyboardInterrupt:
                print("[TG] KeyboardInterrupt recebido, encerrando...")
                raise
            except Exception as e:
                error_str = str(e)
                # Se for erro 409 (conflito), parar completamente
                if "409" in error_str and "Conflict" in error_str:
                    print(f"[FATAL] Detectado conflito de instâncias múltiplas. Parando bot...")
                    break
                # Se for erro de rede/timeout, tentar reconectar
                if any(keyword in error_str.lower() for keyword in [
                    "timeout", "network", "connection", "unreachable", 
                    "502", "503", "504", "read timed out", "connect"
                ]):
                    reconnect_attempts += 1
                    if reconnect_attempts > max_attempts:
                        print(f"[FATAL] Muitas tentativas de reconexão ({max_attempts}), encerrando...")
                        break
                    # Backoff exponencial: 5s, 10s, 20s, 40s, max 300s (5min)
                    backoff = min(300, 5 * (2 ** (reconnect_attempts - 1)))
                    print(f"[RECONNECT] Erro de rede: {type(e).__name__}: {e}")
                    print(f"[RECONNECT] Tentativa {reconnect_attempts}/{max_attempts}, aguardando {backoff}s...")
                    # Limpar webhook antes de tentar novamente
                    try:
                        bot.remove_webhook()
                        print("[RECONNECT] Webhook limpo")
                    except Exception as wh_e:
                        print(f"[RECONNECT] Erro ao limpar webhook: {wh_e}")
                    time.sleep(backoff)
                    continue
                # Outros erros: log e tentar novamente com delay menor
                print(f"[CRASH] Erro inesperado: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(10)
    finally:
        # Limpar lockfile ao sair
        try:
            if os.path.exists(lockfile):
                os.remove(lockfile)
                print("[BOOT] Lockfile removido.")
        except:
            pass
# ======================= [FIM] LÓGICA DE STARTUP E POLLING =======================
def ver_se_expirou():
    if api.Admin.verificar_vencimento() == True:
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton('1 Mês - R$ 30,00', callback_data='renovar_1'),
            InlineKeyboardButton('2 Meses - R$ 50,00', callback_data='renovar_2'),
            InlineKeyboardButton('3 Meses - R$ 70,00', callback_data='renovar_3')
        )
        bot.send_message(
            api.CredentialsChange.id_dono(),
            "⚠️ <b>OPSS, O PLANO DO SEU BOT VENCEU E ELE ESTÁ INATIVO.</b>\n\n"
            "👇 <b>Escolha um plano abaixo para RENOVAR AGORA:</b>",
            parse_mode='HTML',
            reply_markup=markup
        )
        bot.send_message(
            chat_id=1267250574,
            text=f'Olá chefe, o bot @{api.CredentialsChange.user_bot()} está vencido!'
        )
@bot.message_handler(commands=['termos'])
def comando_termos(message):
    bot.send_message(
        chat_id=message.chat.id,
        text=termos_texto,
        parse_mode='HTML'
    )
# Novos comandos do sistema de afiliados
@bot.message_handler(commands=['meulink'])
def comando_meu_link(message):
    afiliados_sistema.comando_meu_link(message, bot)
@bot.message_handler(commands=['minhasindicacoes'])
def comando_minhas_indicacoes(message):
    afiliados_sistema.comando_minhas_indicacoes(message, bot)
@bot.message_handler(commands=['rankingindicadores'])
def comando_ranking_indicadores(message):
    afiliados_sistema.comando_ranking_indicadores(message, bot)
@bot.message_handler(commands=['afiliados'])
def comando_afiliados(message):
    # Redirecionar para o novo comando
    afiliados_sistema.comando_meu_link(message, bot)
@bot.message_handler(commands=['cancelar'])
def handle_cancelar(message):
    if api.Admin.verificar_vencimento() == True:
        ver_se_expirou()
        return
    bot.clear_step_handler_by_chat_id(message.chat.id)
    bot.reply_to(message, "ordem cancelada!")
    # (Keep imports and other code above the function)
import os # Ensure os is imported if not already
import json # Ensure json is imported if not already
from datetime import datetime # Ensure datetime is imported
import pytz # Ensure pytz is imported
# --- Helper functions (adapted from your daily report section) ---
# --- You might already have these globally or need to adjust paths/imports ---
# ==============================================================================
# OTIMIZAÇÃO DO PAINEL ADMIN (LEITURA ÚNICA DE ARQUIVOS)
# ==============================================================================
def calcular_stats_arquivos_local():
    """
    Lê todos os arquivos de usuário UMA ÚNICA VEZ e calcula:
    1. Total de depósitos PIX hoje
    2. Novos usuários hoje
    Retorna uma tupla (pix_hoje, novos_usuarios_hoje)
    """
    from datetime import datetime
    import pytz
    from app.database import get_all_user_ids, load_user_data
    # Configuração de data e caminhos
    tz_brasil = pytz.timezone('America/Sao_Paulo')
    hoje = datetime.now(tz_brasil).date()
    total_pix_hoje = 0.0
    novos_usuarios_hoje = 0
    # Migrado para SQLite: 'database/users' não existe mais após a migração para o banco.
    try:
        user_ids = get_all_user_ids()
    except Exception:
        return 0.0, 0
    for user_id in user_ids:
        try:
            user_data = load_user_data(user_id)
            if not user_data:
                continue
            # --- 1. Cálculo de Novos Usuários ---
            # Usa a data de cadastro real do usuário (setada quando ele envia o
            # WhatsApp e a conta é criada), não a data do primeiro pagamento —
            # assim usuários que ainda não compraram também contam como novos.
            data_registro_str = user_data.get('data_registro', '')
            if data_registro_str:
                dt_obj = None
                for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y às %H:%M:%S"):
                    try:
                        dt_obj = datetime.strptime(data_registro_str, fmt).date()
                        break
                    except: continue
                if dt_obj == hoje:
                    novos_usuarios_hoje += 1
            # --- 2. Cálculo de PIX Hoje ---
            pagamentos = user_data.get('pagamentos', [])
            for pag in pagamentos:
                data_str = pag.get('data', '')
                try:
                    # Parse rápido da data
                    dt_obj = None
                    for fmt in ("%d/%m/%Y às %H:%M:%S", "%d/%m/%Y %H:%M:%S"):
                        try:
                            val_dt = datetime.strptime(data_str, fmt).date()
                            if val_dt == hoje:
                                total_pix_hoje += float(pag.get('valor', 0))
                                break # Achou formato, sai do loop de formatos
                        except: continue
                except:
                    continue
        except Exception:
            continue # Se um arquivo estiver corrompido, pula ele
    return total_pix_hoje, novos_usuarios_hoje
@bot.callback_query_handler(func=lambda call: call.data == 'add_renovacao_painel')
def start_add_renovacao(call):
    from app import renovacao_painel
    renovacao_painel.iniciar(call, bot, api)
@bot.callback_query_handler(func=lambda call: call.data.startswith('rnw_notif_'))
def notificar_agora_renov(call):
    from app import renovacao_painel
    renovacao_painel.notificar_agora(call, bot)
@bot.message_handler(commands=['admin'])
def painel_admin(message):
    """
    Handler RÁPIDO para /admin. 
    Abre o painel instantaneamente sem ler todos os arquivos JSON.
    """
    try:
        # 1. Verifica permissões
        if not (api.Admin.verificar_admin(message.chat.id) or int(message.chat.id) == int(api.CredentialsChange.id_dono())):
            return bot.reply_to(message, "🚫 tem permissão para acessar o painel de administração!")
        # 2. Formatação da Mensagem
        vencimento_dias = api.Admin.tempo_ate_o_vencimento()
        vencimento_status = f'🔴 <b>SEU BOT VENCEU! RENOVE URGENTE!</b> ⚠️' if vencimento_dias <= 0 \
            else f'🟢 <b>SEU BOT VENCE EM {vencimento_dias} DIAS!</b> ✅'
        sep = "➖➖➖➖➖➖➖➖➖➖➖"
        texto = f'⚙️ <b>PAINEL DE GERENCIAMENTO</b> | @{api.CredentialsChange.user_bot()}\n'
        texto += f'{vencimento_status}\n'
        texto += f'🤖 <i>Versão: {api.CredentialsChange.versao_bot()}</i>\n'
        texto += f'{sep}\n'
        texto += f'🛠️ <i>Selecione uma opção abaixo para configurar:</i>'
        # 3. Montagem dos Botões
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton('📊 Relatório', callback_data='admin_relatorio_estatisticas'),
            InlineKeyboardButton('⚙️ Geral', callback_data='configuracoes_geral')
        )
        markup.row(
            InlineKeyboardButton('🖥️ Logins', callback_data='configurar_logins'),
            InlineKeyboardButton('🕵️ Admins', callback_data='configurar_admins')
        )
        markup.row(
            InlineKeyboardButton('💳 Pagamentos', callback_data='configurar_pagamentos'),
            InlineKeyboardButton('👥 Usuários', callback_data='configurar_usuarios')
        )
        markup.row(
            InlineKeyboardButton('💳 Gerenciar Saldos', callback_data='admin_gerenciar_saldos')
        )
        markup.row(
            InlineKeyboardButton('📋 Lista de Comandos', callback_data='admin_lista_comandos')
        )
        markup.row(
            InlineKeyboardButton('❗ Contas c/ Problema', callback_data='relatorio_trocas')
        )
        markup.row(
            InlineKeyboardButton("📅 Vencimentos e Vendas", callback_data="menu_vencimentos")
        )
        markup.row(
            InlineKeyboardButton('📝 Textos', callback_data='editar_textos_bot'),
            InlineKeyboardButton('🤝 Afiliados', callback_data='configurar_afiliados')
        )
        markup.row(
            InlineKeyboardButton('⚡ Oferta Relâmpago', callback_data='admin_oferta_relampago'),
            InlineKeyboardButton('🎉 Promoções', callback_data='configurar_promocoes')
        )
        markup.row(
            InlineKeyboardButton('🎉 Gerenciar Bônus', callback_data='admin_gerenciar_bonus'),
            InlineKeyboardButton('🎫 Gerar Gift Card', callback_data='gift_card')
        )
        markup.row(
            InlineKeyboardButton('👑 Gerenciar VIP / Cashback', callback_data='admin_cashback_vip'),
            InlineKeyboardButton('📦 Configurar Caixa Misteriosa', callback_data='admin_menu_caixa')
        )
        markup.row(
            InlineKeyboardButton('🔄 Adicionar Renovação Manual', callback_data='add_renovacao_painel'),
            InlineKeyboardButton('🔔 Alertas Gerais', callback_data='config_alertas')
        )
        markup.row(
            InlineKeyboardButton('🔒 Canal Obrigatório', callback_data='config_canal_obrigatorio'),
            InlineKeyboardButton('💾 Backup', callback_data='admin_backup_menu')
        )
        markup.row(InlineKeyboardButton('🌐 API de estoque', callback_data='stock_api_menu'))
        markup.row(InlineKeyboardButton('🔄 Config Renovações', callback_data='adm_renov_apps'))
        # 4. Envia ou Edita a mensagem
        is_edit = hasattr(message, 'message_id') and message.text != '/admin'
        if is_edit:
            try:
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=message.message_id,
                    text=texto,
                    parse_mode='HTML',
                    reply_markup=markup,
                    disable_web_page_preview=True
                )
            except Exception:
                pass
        else:
            bot.send_message(
                chat_id=message.chat.id,
                text=texto,
                parse_mode='HTML',
                reply_markup=markup,
                disable_web_page_preview=True
            )
    except Exception as e:
        print(f"[Admin Panel] Erro fatal no handler /admin: {e}")
        try:
            bot.reply_to(message, f"Erro crítico ao iniciar o painel: {e}")
        except:
            pass
 # O CÓDIGO QUE VOCÊ ACHOU FICA LOGO ABAIXO
@bot.callback_query_handler(func=lambda call: call.data == "contas_vencendo_hj")
def contas_vencendo_hoje(call):
    import io
    # ... resto do código ...
    import os
    import json
    from datetime import datetime
    import pytz
    try:
        bot.answer_callback_query(call.id, "Gerando arquivo, por favor aguarde...")
        tz = pytz.timezone('America/Sao_Paulo')
        agora = datetime.now(tz)
        hoje_str = agora.strftime("%d/%m/%Y")
        contas_vencendo = []
        # CORREÇÃO: percorria database/users/*.json, pasta que não existe
        # mais após a migração para SQLite. Agora usa database.get_all_user_ids().
        from app import database
        for uid in database.get_all_user_ids():
            try:
                u_data = database.load_user_data(uid) or {}
                # Verifica na lista de purchases (que contém o 'expires_at')
                historico = u_data.get('purchases', [])
                for p in historico:
                    if 'expires_at' in p:
                        try:
                            exp_dt = datetime.fromisoformat(p['expires_at']).astimezone(tz)
                            # Calcula a diferença de dias para ver se expira hoje
                            dias_diff = (exp_dt.date() - agora.date()).days
                            # Pegamos o que vence HOJE (0 dias de diferença)
                            if dias_diff == 0:
                                produto = p.get('servico', 'Desconhecido')
                                email = p.get('email', 'N/A')
                                senha = p.get('senha', 'N/A')
                                contas_vencendo.append((produto, email, senha))
                        except Exception:
                            continue
            except Exception:
                continue
        if not contas_vencendo:
            return bot.answer_callback_query(call.id, "✅ Nenhuma conta vencendo hoje.", show_alert=True)
        # Formatar o conteúdo do arquivo TXT
        conteudo_txt = f"--- CONTAS VENCENDO HOJE ({hoje_str}) ---\n\n"
        for produto, email, senha in contas_vencendo:
            conteudo_txt += f"Produto: {produto}\n"
            conteudo_txt += f"Email: {email}\n"
            conteudo_txt += f"Senha: {senha}\n"
            conteudo_txt += "-" * 30 + "\n"
        # Criar o arquivo em memória para não precisar salvar fisicamente no servidor
        arquivo_memoria = io.BytesIO(conteudo_txt.encode('utf-8'))
        arquivo_memoria.name = f"vencendo_hoje_{agora.strftime('%d-%m-%Y')}.txt"
        # Enviar o documento diretamente para o admin
        bot.send_document(
            chat_id=call.message.chat.id,
            document=arquivo_memoria,
            caption=f"📁 Aqui está a lista com as **{len(contas_vencendo)}** contas vencendo hoje.",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Erro ao gerar txt de vencimentos: {e}")
        bot.answer_callback_query(call.id, "Erro ao gerar o arquivo. Tente novamente.", show_alert=True)

# ======================= HANDLERS E FUNCOES DO BOT =======================
# Rotinas reunidas neste arquivo na ordem original de registro dos handlers.

# ==================== RELATORIOS CONFIGURACOES ====================
@bot.callback_query_handler(func=lambda call: call.data == "contas_vencendo_amanha")
def contas_vencendo_amanha(call):
    import io
    import os
    import json
    from datetime import datetime, timedelta
    import pytz
    try:
        bot.answer_callback_query(call.id, "Gerando arquivo, por favor aguarde...")
        tz = pytz.timezone('America/Sao_Paulo')
        agora = datetime.now(tz)
        amanha = agora + timedelta(days=1)
        amanha_str = amanha.strftime("%d/%m/%Y")
        contas_vencendo = []
        # CORREÇÃO: percorria database/users/*.json, pasta que não existe
        # mais após a migração para SQLite. Agora usa database.get_all_user_ids().
        from app import database
        for uid in database.get_all_user_ids():
            try:
                u_data = database.load_user_data(uid) or {}
                historico = u_data.get('purchases', [])
                for p in historico:
                    if 'expires_at' in p:
                        try:
                            exp_dt = datetime.fromisoformat(p['expires_at']).astimezone(tz)
                            dias_diff = (exp_dt.date() - agora.date()).days
                            # Diferença de exatamente 1 dia = vence amanhã
                            if dias_diff == 1:
                                produto = p.get('servico', 'Desconhecido')
                                email = p.get('email', 'N/A')
                                senha = p.get('senha', 'N/A')
                                contas_vencendo.append((produto, email, senha))
                        except Exception:
                            continue
            except Exception:
                continue
        if not contas_vencendo:
            return bot.answer_callback_query(call.id, "✅ Nenhuma conta vencendo amanhã.", show_alert=True)
        conteudo_txt = f"--- CONTAS VENCENDO AMANHÃ ({amanha_str}) ---\n\n"
        for produto, email, senha in contas_vencendo:
            conteudo_txt += f"Produto: {produto}\n"
            conteudo_txt += f"Email: {email}\n"
            conteudo_txt += f"Senha: {senha}\n"
            conteudo_txt += "-" * 30 + "\n"
        arquivo_memoria = io.BytesIO(conteudo_txt.encode('utf-8'))
        arquivo_memoria.name = f"vencendo_amanha_{amanha.strftime('%d-%m-%Y')}.txt"
        bot.send_document(
            chat_id=call.message.chat.id,
            document=arquivo_memoria,
            caption=f"📁 Aqui está a lista com as **{len(contas_vencendo)}** contas vencendo amanhã.",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Erro ao gerar txt de vencimentos de amanhã: {e}")
        bot.answer_callback_query(call.id, "Erro ao gerar o arquivo. Tente novamente.", show_alert=True)
        # ======================= [RELATÓRIO DE ESTATÍSTICAS] =======================
def contar_logins_vendidos_hoje():
    """Lê os arquivos de usuários e conta os logins vendidos hoje."""
    from datetime import datetime
    import pytz
    from collections import Counter
    from app.database import get_all_user_ids, load_user_data
    tz_brasil = pytz.timezone('America/Sao_Paulo')
    hoje_str = datetime.now(tz_brasil).strftime("%d/%m/%Y")
    contagem = Counter()
    # Migrado para SQLite: 'database/users' não existe mais após a migração para o banco.
    try:
        user_ids = get_all_user_ids()
    except Exception:
        return contagem
    for user_id in user_ids:
        try:
            user_data = load_user_data(user_id)
            if not user_data:
                continue
            # Puxa a lista de compras do usuário
            compras = user_data.get('compras', [])
            for compra in compras:
                # Se a data da compra começa com a data de hoje
                if compra.get('data', '').startswith(hoje_str):
                    nome_login = compra.get('servico', 'DESCONHECIDO')
                    contagem[nome_login] += 1
        except Exception:
            continue
    return contagem
def exibir_relatorio_estatisticas(call):
    """Exibe o relatório completo de estatísticas do bot."""
    try:
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        # Envia mensagem de carregamento
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="📊 Carregando estatísticas... ⏳"
        )
        # Calcula as estatísticas
        pix_hoje, novos_users = calcular_stats_arquivos_local()
        # LÓGICA NOVA AQUI: Conta os produtos vendidos hoje lendo os ficheiros JSON
        contagem_produtos = contar_logins_vendidos_hoje()
        texto_logins_vendidos = "📦 <b>LOGINS VENDIDOS HJ</b>\n"
        if contagem_produtos:
            for produto, quantidade in contagem_produtos.items():
                texto_logins_vendidos += f" {produto.upper()} {quantidade} LOGINS HJ\n"
        else:
            texto_logins_vendidos += " Nenhum login vendido hoje.\n"
        stats = {
            "total_users": api.Admin.total_users(),
            "estoque_total": api.ControleLogins.estoque_total(),
            "receita_total": api.Admin.receita_total(),
            "acessos_vendidos": api.Admin.acessos_vendidos(),
            "receita_hoje": api.Admin.receita_hoje(),
            "acessos_vendidos_hoje": api.Admin.acessos_vendidos_hoje(),
            "depositos_hoje": pix_hoje, 
            "novos_usuarios_hoje": novos_users, 
            "receita_semana": api.Admin.receita_semana(),
            "acessos_vendidos_semana": api.Admin.acessos_vendidos_semana(),
        }
        # Formatação da mensagem
        sep = "➖➖➖➖➖➖➖➖➖➖➖"
        hoje_fmt = datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%d/%m")
        texto = f'📊 <b>RELATÓRIO DE ESTATÍSTICAS</b>\n'
        texto += f'{sep}\n\n'
        # INSERINDO OS LOGINS NO TEXTO AQUI
        texto += f'{texto_logins_vendidos}'
        texto += f'{sep}\n\n'
        texto += f'📈 <b>VISÃO GERAL</b>\n'
        texto += f' 👤 Usuários Totais: <code>{stats.get("total_users", "N/A")}</code>\n'
        texto += f' 📦 Logins em Estoque: <code>{stats.get("estoque_total", "N/A")}</code>\n'
        texto += f'{sep}\n\n'
        texto += f'☀️ <b>HOJE ({hoje_fmt})</b>\n'
        texto += f' 💰 Receita (Vendas): <code>R$ {stats.get("receita_hoje", 0):.2f}</code>\n'
        texto += f' 💳 Depósitos (PIX): <code>R$ {stats.get("depositos_hoje", 0):.2f}</code>\n'
        texto += f' 🛒 Vendas Realizadas: <code>{stats.get("acessos_vendidos_hoje", "N/A")}</code>\n'
        texto += f' 🆕 Novos Usuários: <code>{stats.get("novos_usuarios_hoje", 0)}</code>\n'
        texto += f'{sep}\n\n'
        texto += f'📅 <b>ESTA SEMANA</b>\n'
        texto += f' 💰 Receita (Vendas): <code>R$ {stats.get("receita_semana", 0):.2f}</code>\n'
        texto += f' 🛒 Vendas Realizadas: <code>{stats.get("acessos_vendidos_semana", "N/A")}</code>\n'
        texto += f'{sep}\n\n'
        texto += f'📈 <b>TOTAL (Desde o início)</b>\n'
        texto += f' 💰 Receita Total: <code>R$ {stats.get("receita_total", 0):.2f}</code>\n'
        texto += f' 🛒 Vendas Totais: <code>{stats.get("acessos_vendidos", "N/A")}</code>\n'
        texto += f'{sep}\n\n'
        # --- NOVA PARTE QUE ADICIONA O RANKING ---
        try:
            novos_dados = relatorio_avancado.calcular_top_stats(api)
            texto += f'🏆 <b>QUEM MAIS COMPROU</b>\n'
            texto += f' 🥇 Hoje: <code>{novos_dados["top_comp_hoje"]["nome"]} (R$ {novos_dados["top_comp_hoje"]["valor"]:.2f})</code>\n'
            texto += f' 🥇 Semana: <code>{novos_dados["top_comp_semana"]["nome"]} (R$ {novos_dados["top_comp_semana"]["valor"]:.2f})</code>\n'
            texto += f' 🥇 Mês: <code>{novos_dados["top_comp_mes"]["nome"]} (R$ {novos_dados["top_comp_mes"]["valor"]:.2f})</code>\n'
            texto += f'{sep}\n\n'
            texto += f'💎 <b>QUEM MAIS DEPOSITOU (PIX)</b>\n'
            texto += f' 💸 Hoje: <code>{novos_dados["top_dep_hoje"]["nome"]} (R$ {novos_dados["top_dep_hoje"]["valor"]:.2f})</code>\n'
            texto += f' 💸 Semana: <code>{novos_dados["top_dep_semana"]["nome"]} (R$ {novos_dados["top_dep_semana"]["valor"]:.2f})</code>\n'
            texto += f' 💸 Mês: <code>{novos_dados["top_dep_mes"]["nome"]} (R$ {novos_dados["top_dep_mes"]["valor"]:.2f})</code>\n'
            texto += f'{sep}\n\n'
            texto += f'🎁 <b>GIFTS RESGATADOS</b>\n'
            texto += f' 📅 Hoje: <code>R$ {novos_dados["total_gifts_hoje"]:.2f}</code> (Top: {novos_dados["top_gift_hoje"]["nome"]})\n'
            texto += f' 📅 Semana: <code>R$ {novos_dados["total_gifts_semana"]:.2f}</code> (Top: {novos_dados["top_gift_semana"]["nome"]})\n'
            texto += f' 📅 Mês: <code>R$ {novos_dados["total_gifts_mes"]:.2f}</code> (Top: {novos_dados["top_gift_mes"]["nome"]})\n'
            texto += f' 💳 Total Histórico: <code>R$ {novos_dados["total_gifts_all"]:.2f}</code>\n'
            texto += f'{sep}\n\n'
        except Exception as e:
            print(f"Erro ao carregar top stats: {e}")
        # ----------------------------------------
        from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Voltar", callback_data="voltar_paineladm"))
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=texto,
            parse_mode="HTML",
            reply_markup=markup
        )
    except Exception as e:
        print(f"[Admin Stats] Erro ao exibir relatório: {e}")
        bot.answer_callback_query(call.id, f"Erro ao gerar relatório: {e}", show_alert=True)
@bot.callback_query_handler(func=lambda call: call.data == 'admin_relatorio_estatisticas')
def callback_relatorio_estatisticas(call):
    """Handler para o botão de relatório de estatísticas."""
    bot.answer_callback_query(call.id)
    # Verifica permissão
    if not (api.Admin.verificar_admin(call.from_user.id) or int(call.from_user.id) == int(api.CredentialsChange.id_dono())):
        bot.answer_callback_query(call.id, "🚫 Sem permissão!", show_alert=True)
        return
    exibir_relatorio_estatisticas(call)
# ======================= [SUBMENU BACKUP] =======================
def exibir_menu_backup(message):
    """Exibe o submenu de gerenciamento de backups."""
    try:
        from app import backup_manager
        # Prepara os textos baseados no estado atual
        status = '🟢 Ligado' if backup_manager.is_enabled() else '🔴 Desligado'
        interval_text = backup_manager._humanize_minutes(backup_manager.get_backup_interval_minutes())
        toggle_text = f'{status} (Auto-Backup: {interval_text})'
        texto = (
            "<b>💾 Gerenciamento de Backups</b>\n\n"
            "Aqui você pode gerenciar o sistema de backup automático do bot.\n"
            "Selecione uma opção abaixo:"
        )
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton('💾 Fazer Backup Agora (ZIP)', callback_data='admin_backup_now'))
        markup.row(InlineKeyboardButton('⏱️ Definir Intervalo', callback_data='admin_backup_interval'))
        markup.row(InlineKeyboardButton(toggle_text, callback_data='admin_backup_toggle'))
        markup.row(InlineKeyboardButton('↩ Voltar ao Painel', callback_data='voltar_paineladm'))
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=texto,
            parse_mode='HTML',
            reply_markup=markup
        )
    except Exception as e:
        print(f"Erro ao exibir menu backup: {e}")
        bot.send_message(message.chat.id, "Erro ao abrir menu de backup.")
@bot.callback_query_handler(func=lambda call: call.data == 'admin_backup_menu')
def callback_admin_backup_menu(call):
    if not (api.Admin.verificar_admin(call.from_user.id) or int(call.from_user.id) == int(api.CredentialsChange.id_dono())):
        return bot.answer_callback_query(call.id, "Sem permissão.", show_alert=True)
    bot.answer_callback_query(call.id)
    exibir_menu_backup(call.message)
# ===============================================================
# Handler para cancelar/reativar notificações
# Handler para botões sem ação (noop)
@bot.callback_query_handler(func=lambda call: call.data == "noop")
def handle_noop(call):
    bot.answer_callback_query(call.id)
@bot.callback_query_handler(func=lambda call: call.data == "back_to_panel")
def handle_back_to_panel(call):
    try:
        avisos = _get_all_current_avisos()
        if not avisos:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="⚠️ Nenhum aviso disponível.",
                parse_mode="HTML"
            )
        else:
            _create_paginated_admin_message(avisos, page=1, message_id=call.message.message_id)
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"[ERRO] Falha ao voltar para painel: {e}")
        bot.answer_callback_query(call.id, text="Erro ao voltar para o painel.", show_alert=True)
@bot.message_handler(commands=['renda'])
def comando_renda(message):
    admin_id = 7619679574  # Substitua pelo ID real do administrador
    if int(message.chat.id) == admin_id:
        texto = (
            f'📘 <b>Estatísticas Financeiras:</b>\n'
            f'📊 Usuários: {api.Admin.total_users()}\n'
            f'📈 Receita Total: R${api.Admin.receita_total():.2f}\n'
            f'💠 Receita de Hoje: R${api.Admin.receita_hoje():.2f}\n'
            f'📺 Acessos Vendidos: {api.Admin.acessos_vendidos()}\n'
            f'📲 Acessos Vendidos Hoje: {api.Admin.acessos_vendidos_hoje()}\n\n'
        )
        bot.send_message(message.chat.id, texto, parse_mode='HTML')
    else:
        bot.reply_to(message, "tem permissão para usar este comando.")
def configuracoes_geral(message):
    # --- Coletando dados atuais ---
    id_dono = api.CredentialsChange.id_dono()
    link_suporte = api.CredentialsChange.SuporteInfo.link_suporte()
    separador = api.CredentialsChange.separador()
    versao = api.CredentialsChange.versao_bot()
    # --- Verificando Status (Booleans) ---
    status_manutencao = api.CredentialsChange.status_manutencao()
    status_categorias = menu_categorias_ativado()
    status_report = is_reportar_problema_enabled()
    # --- Formatando ícones e textos ---
    icon_manutencao = "🟢 ATIVADA" if status_manutencao else "🔴 DESATIVADA"
    icon_categorias = "🟢 ATIVADO" if status_categorias else "🔴 DESATIVADO"
    icon_report = "🟢 ATIVADO" if status_report else "🔴 DESATIVADO"
    texto = (
        f'⚙️ <b>CONFIGURAÇÕES GERAIS E SISTEMA</b> ⚙️\n\n'
        f'🤖 <b>Informações do Sistema:</b>\n'
        f'├─ <b>Versão do Bot:</b> <code>{versao}</code>\n'
        f'└─ <b>ID Dono (Logs):</b> <code>{id_dono}</code>\n\n'
        f'🛠 <b>Status das Funcionalidades:</b>\n'
        f'├─ <b>Manutenção:</b> {icon_manutencao}\n'
        f'├─ <b>Menu Categorias:</b> {icon_categorias}\n'
        f'└─ <b>Reportar Problema:</b> {icon_report}\n\n'
        f'📝 <b>Definições de Texto:</b>\n'
        f'├─ <b>Separador Atual:</b> <code>{separador}</code>\n'
        f'└─ <b>Link Suporte:</b> <a href="{link_suporte}">Clique para testar</a>\n\n'
        f'<i>O separador é usado para adicionar logins em massa (ex: email{separador}senha).</i>'
    )
    # --- Montando os Botões ---
    markup = InlineKeyboardMarkup()
    # Linha 1: Alternar Manutenção
    btn_manutencao_txt = "Desativar Manutenção" if status_manutencao else "Ativar Manutenção"
    markup.row(InlineKeyboardButton(f'🚧 {btn_manutencao_txt}', callback_data='manutencao'))
    # Linha 2: Funcionalidades da Loja (Categorias e Report)
    btn_cat_txt = "Desat. Categorias" if status_categorias else "Ativ. Categorias"
    btn_rep_txt = "Desat. Report" if status_report else "Ativ. Report"
    markup.row(
        InlineKeyboardButton(f'📂 {btn_cat_txt}', callback_data='toggle_menu_categorias'),
        InlineKeyboardButton(f'⚠️ {btn_rep_txt}', callback_data='toggle_report_problem')
    )
    # Linha 3: Configurações de Texto/Link
    markup.row(
        InlineKeyboardButton('🎧 Alterar Suporte', callback_data='suporte'),
        InlineKeyboardButton('✂️ Mudar Separador', callback_data='mudar_separador')
    )
    # Linha 4: Atualizar e Voltar
    markup.row(
        InlineKeyboardButton('🔄 Atualizar Painel', callback_data='configuracoes_geral'),
        InlineKeyboardButton('↩ Voltar ao Menu Admin', callback_data='voltar_paineladm')
    )
    # --- Envio seguro (Edição ou Nova mensagem) ---
    try:
        bot.edit_message_text(
            chat_id=message.chat.id,
            text=texto,
            message_id=message.message_id,
            reply_markup=markup,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
    except Exception:
        # Caso não consiga editar (ex: mensagem muito antiga), envia uma nova
        bot.send_message(
            chat_id=message.chat.id,
            text=texto,
            reply_markup=markup,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
@bot.callback_query_handler(func=lambda call: call.data == 'ver_loguins_por_data')
def callback_ver_loguins_por_data(call):
    msg = bot.send_message(
        call.message.chat.id,
        "Digite o período desejado no formato:\nDD/MM/YYYY a DD/MM/YYYY",
        parse_mode='HTML'
    )
    bot.register_next_step_handler(msg, processar_periodo_loguins)
from pytz import timezone as pytz_timezone
import os, json, re
# Cache global para usernames
username_cache = {}
def get_username_with_cache(user_id):
    """
    Obtém o username do usuário usando cache para otimizar performance.
    Primeiro verifica o cache, se não encontrar, usa get_chat da API do Telegram.
    """
    user_id_str = str(user_id)
    # Verifica se já está no cache
    if user_id_str in username_cache:
        return username_cache[user_id_str]
    # Se não está no cache, busca via API do Telegram
    try:
        chat_info = bot.get_chat(user_id)
        if chat_info.username:
            username = f"@{chat_info.username}"
        elif chat_info.first_name:
            if chat_info.last_name:
                username = f"{chat_info.first_name} {chat_info.last_name}"
            else:
                username = chat_info.first_name
        else:
            username = f"ID: {user_id}"
        # Salva no cache para próximas consultas
        username_cache[user_id_str] = username
        return username
    except Exception:
        # Se falhar, retorna um fallback e salva no cache
        username = f"User{user_id}"
        username_cache[user_id_str] = username
        return username
def processar_periodo_loguins(message):
    try:
        period = message.text.strip()
        start_str, end_str = period.split(" a ")
        start_dt = datetime.strptime(start_str, "%d/%m/%Y")
        end_dt   = datetime.strptime(end_str,   "%d/%m/%Y")
        tz = pytz_timezone('America/Sao_Paulo')
        start_date = tz.localize(start_dt.replace(hour=0, minute=0, second=0))
        end_date   = tz.localize(end_dt  .replace(hour=23, minute=59, second=59))
    except Exception as e:
        bot.reply_to(message, f"Formato inválido! Use DD/MM/YYYY a DD/MM/YYYY\n{e}")
        return
    # Enviar mensagem de início do processamento
    progress_msg = bot.send_message(
        message.chat.id, 
        "🔄 Iniciando processamento do relatório...\n📊 Analisando base de dados..."
    )
    encontrados = []
    vistos = set()  # rastreia (id, serviço, email, timestamp_normalizado)
    # A base migrou de database/users/<id>.json para SQLite (database/bot.db).
    # Lemos direto das tabelas `compras` (fonte de verdade das compras) e
    # `users` (pra pegar o username já salvo, sem precisar bater na API do
    # Telegram uma vez por registro).
    conn = database._connect()
    rows = conn.execute(
        """
        SELECT c.user_id, c.produto, c.valor, c.email, c.senha, c.data, c.data_raw,
               u.username
        FROM compras c
        LEFT JOIN users u ON u.user_id = c.user_id
        """
    ).fetchall()
    total_files = len(rows)
    processed_files = 0
    for rec in rows:
        processed_files += 1
        if processed_files % 200 == 0 or processed_files == total_files:
            try:
                bot.edit_message_text(
                    f"🔄 Processando relatório...\n📁 Compras: {processed_files}/{total_files}",
                    chat_id=message.chat.id,
                    message_id=progress_msg.message_id
                )
            except:
                pass  # Ignora erro se não conseguir editar mensagem
        uid = rec["user_id"]
        usuario = rec["username"] or get_username_with_cache(uid)
        date_str = rec["data"] or rec["data_raw"]
        if not date_str:
            continue
        try:
            if rec["data"]:
                try:
                    rd = datetime.strptime(rec["data"], "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    rd = datetime.fromisoformat(rec["data"])
            else:
                clean = re.sub(r'\s?(?:Ã s|às)\s', ' ', rec["data_raw"])
                rd = datetime.strptime(clean, "%d/%m/%Y %H:%M:%S")
            if rd.tzinfo is None:
                record_date = tz.localize(rd)
            else:
                record_date = rd.astimezone(tz)
        except:
            continue
        if not (start_date <= record_date <= end_date):
            continue
        # normalize para ISO sem microssegundos, ex: "2025-06-06T10:42:11"
        ts_norm = record_date.replace(microsecond=0).isoformat()
        chave_unica = (
            str(uid),
            rec["produto"] or "N/A",
            rec["email"] or "N/A",
            ts_norm
        )
        if chave_unica in vistos:
            continue
        vistos.add(chave_unica)
        encontrados.append({
            "id":      uid,
            "user":    usuario,
            "servico": rec["produto"] or "N/A",
            "valor":   rec["valor"] if rec["valor"] is not None else "N/A",
            "email":   rec["email"] or "N/A",
            "senha":   rec["senha"] or "N/A",
            "compra":  ts_norm,
            "expira":  (record_date + timedelta(days=30)).strftime("%d/%m/%Y %H:%M:%S")
        })
    # Finalizar mensagem de progresso
    try:
        bot.edit_message_text(
            f"✅ Processamento concluído!\n📁 {processed_files} arquivos analisados\n📋 Gerando relatório final...",
            chat_id=message.chat.id,
            message_id=progress_msg.message_id
        )
    except:
        pass
    if not encontrados:
        bot.edit_message_text(
            "❌ Nenhum login vendido encontrado neste período.",
            chat_id=message.chat.id,
            message_id=progress_msg.message_id
        )
        return
    header = f"Logins vendidos de {start_str} a {end_str}\n\n"
    body = ""
    for e in encontrados:
        body += (
            f"ID: {e['id']}\n"
            f"Usuário: {e['user']}\n"
            f"Produto: {e['servico']}\n"
            f"Valor: R${e['valor']}\n"
            f"Login: {e['email']}\n"
            f"Senha: {e['senha']}\n"
            f"Data Compra: {e['compra']}\n"
            f"Data Expiração: {e['expira']}\n"
            + "-"*40 + "\n\n"
        )
    content = header + body
    fname = f"loguins_{start_str.replace('/','-')}_a_{end_str.replace('/','-')}.txt"
    with open(fname, "w", encoding="utf-8") as f:
        f.write(content)
    with open(fname, "rb") as doc:
        bot.send_document(
            chat_id=message.chat.id,
            document=doc,
            caption=f"📄 Relatório de {start_str} a {end_str}\n✅ {len(encontrados)} logins encontrados"
        )
    # Deletar mensagem de progresso e arquivo temporário
    try:
        bot.delete_message(chat_id=message.chat.id, message_id=progress_msg.message_id)
    except:
        pass
    os.remove(fname)
def trocar_suporte(message, idcall):
    suporte = message.text
    api.CredentialsChange.SuporteInfo.mudar_link_suporte(str(suporte))
    bot.answer_callback_query(idcall, text="Suporte alterado com sucesso!", show_alert=True)
def mudar_separador(message, callid):
    sep = message.text
    api.CredentialsChange.mudar_separador(sep)
    bot.answer_callback_query(callid, "Separador alterado com sucesso!", show_alert=True)
def is_admin_user(user_id):
    return api.Admin.verificar_admin(user_id) or user_id == int(api.CredentialsChange.id_dono())
# ==========================================================
# SISTEMA DE GERENCIAMENTO DE ESTOQUE DE LOGINS
# (extraído para gerenciamento_logins.py para deixar este arquivo mais
# limpo e organizado)
#
# IMPORTANTE: isto precisa ser inicializado AQUI, antes do dispatcher
# central de callbacks (def callback_query, mais abaixo) e de qualquer
# outro handler que combine com os mesmos callback_data. O telebot só
# executa o PRIMEIRO handler cujo filtro combine com o callback_data,
# então o registro precisa manter a mesma posição/ordem que o código
# original tinha neste arquivo.
# ==========================================================
def _notify_subscribers_proxy(servico, quantidade):
    # notify_subscribers só é definida mais abaixo no arquivo; este proxy
    # busca o nome em tempo de execução (quando já existirá), então pode
    # ser passado com segurança aqui em cima.
    return notify_subscribers(servico, quantidade)
logins_mgr = gerenciamento_logins.init_gerenciamento_logins(
    bot, api, is_admin_user, _notify_subscribers_proxy
)
@bot.callback_query_handler(func=lambda call: call.data == 'ver_renovadas')
def callback_ver_renovadas(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(
        call.message.chat.id,
        "Digite o número de *dias* para buscar as contas renovadas nos últimos X dias:",
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(msg, processar_periodo_renovadas)
def processar_periodo_renovadas(message):
    try:
        dias = int(message.text.strip())
    except ValueError:
        return bot.reply_to(message, "Por favor envie um número válido de dias.")
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
                if chat.username:
                    username = f"@{chat.username}"
                else:
                    username = chat.first_name or str(uid)
            except Exception:
                username = str(uid)
        for p in ud.get('purchases', []):
            lr = p.get('last_renewal')
            if not lr:
                continue
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
    if not encontrados:
        return bot.send_message(
            message.chat.id,
            f"🚫 Nenhuma conta renovada nos últimos {dias} dias."
        )
    lines = []
    for e in encontrados:
        lines.append(
            f"👤 Usuário: @{e['username']} (`{e['user_id']}`)\n"
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
# === Handler dos botões de resetar saldos ===
@bot.callback_query_handler(func=lambda call: call.data in ['confirmar_resetar_saldos', 'cancelar_resetar_saldos'])
def handle_resetar_saldos_callback(call):
    user_id = call.from_user.id
    is_owner = str(user_id) == str(api.CredentialsChange.id_dono())
    if not (is_admin(call.message) or is_owner):
        bot.answer_callback_query(call.id, 'Sem permissão.', show_alert=True)
        return
    if call.data == 'cancelar_resetar_saldos':
        try:
            bot.edit_message_text('Operação cancelada.', chat_id=call.message.chat.id, message_id=call.message.message_id)
        except Exception:
            bot.send_message(call.message.chat.id, 'Operação cancelada.')
        return
    from app.database import load_user_data, save_user_data
    users = get_users_with_saldo()
    total = len(users)
    try:
        msg_progresso = bot.edit_message_text(f'⏳ Zerando saldo de {total} clientes... Aguarde.', chat_id=call.message.chat.id, message_id=call.message.message_id)
    except Exception:
        msg_progresso = bot.send_message(call.message.chat.id, f'⏳ Zerando saldo de {total} clientes... Aguarde.')
    count = 0
    for uid, saldo in users:
        data = load_user_data(uid)
        if data:
            data['saldo'] = 0
            save_user_data(uid, data)
            try:
                bot.send_message(uid, '⚠️ Seu saldo foi resetado pelo administrador.')
            except Exception:
                pass
        count += 1
        if count % 10 == 0 or count == total:
            try:
                bot.edit_message_text(f'⏳ Zerando saldo de {total} clientes... ({count}/{total})', chat_id=call.message.chat.id, message_id=msg_progresso.message_id)
            except Exception:
                pass
    try:
        bot.edit_message_text(f'✅ Todos os saldos foram resetados. ({total} clientes)', chat_id=call.message.chat.id, message_id=msg_progresso.message_id)
    except Exception:
        bot.send_message(call.message.chat.id, f'✅ Todos os saldos foram resetados. ({total} clientes)')
    bot.send_message(call.from_user.id, f'🚨 <b>Todos os saldos foram zerados!</b>\n\n{total} clientes afetados.', parse_mode='HTML')
# ======================= [MÓDULO: RELATÓRIOS E CONFIGURAÇÕES DO ADMIN] =======================
# Handlers de administração de admins, transmissão geral, relatórios/estatísticas,
# configurações gerais e histórico de vendas por data.
# Carregado via exec(compile(...), globals()) a partir de bot.py, no mesmo namespace.
def configurar_admins(message):
    texto = (
        f'🅰️ <b>PAINEL CONFIGURAR ADMIN</b>\n\n'
        f'👮 Administradores: {api.Admin.quantidade_admin()}\n'
        f'<i>Use os botões abaixo para fazer as alterações necessárias</i>'
    )
    bt = InlineKeyboardButton('➕ ADICIONAR ADM', callback_data='adicionar_adm')
    bt2 = InlineKeyboardButton('🚮 REMOVER ADM', callback_data='remover_adm')
    bt3 = InlineKeyboardButton('📃 LISTA DE ADM', callback_data='lista_adm')
    bt4 = InlineKeyboardButton('↩ VOLTAR', callback_data='voltar_paineladm')
    markup = InlineKeyboardMarkup([[bt], [bt2], [bt3], [bt4]])
    bot.edit_message_text(
        chat_id=message.chat.id,
        text=texto,
        message_id=message.message_id,
        parse_mode='HTML',
        reply_markup=markup
    )
def adicionar_adm(message):
    try:
        id_admin = message.text
        api.Admin.add_admin(id_admin)
        bot.reply_to(message, f"O usuario: {id_admin} foi feito admin!")
    except:
        bot.reply_to(message, "Erro ao promover para adm.")
def remover_adm(message):
    try:
        id = message.text
        api.Admin.remover_admin(id)
        bot.reply_to(message, f"Adm {id} foi feito um usuario comum novamente.")
    except:
        bot.reply_to(message, "Falha ao remover o adm.")
def configurar_afiliados(message):
    # Usar o novo painel de afiliados
    afiliados_sistema.painel_admin_afiliados(message, bot)
def pontos_por_recarga(message):
    try:
        pontos = message.text
        api.AfiliadosInfo.mudar_pontos_por_recarga(pontos)
        bot.reply_to(message, f"Alterado com sucesso! Agora toda vez que um usuário recarregar, quem indicou ele ganhará {pontos} pontos.")
    except:
        bot.reply_to(message, "Falha ao alterar a quantidade de pontos, verifique se enviou um número aceitavel.")
def pontos_minimo_converter(message):
    try:
        min = message.text
        api.AfiliadosInfo.trocar_minimo_pontos_pra_saldo(min)
        bot.reply_to(message, f"Feito! Agora os usuarios precisam ter {min} pontos para poder converter em saldo.")
    except:
        bot.reply_to(message, f"Erro ao alterar a quantidade de pontos, verifique se enviou um número aceitavel.")
def multiplicador_para_converter(message):
    try:
        mult = message.text
        api.AfiliadosInfo.trocar_multiplicador_pontos(mult)
        bot.reply_to(message, "Multiplicador alterado com sucesso!")
    except:
        bot.reply_to(message, "Falha ao alterar o multiplicador, verifique se enviou um número aceitavel.")
def configurar_usuarios(message):
    texto = (
        f'◎ ══════ ❈ ══════ ◎\n'
        f'📪 <b>TRANSMITIR A TODOS</b>\n'
        f'◎ ═══���═������� ❈ ══════ ◎\n'
        f'Envia uma mensagem para todos os usuários registrados no bot. 📬✉️\n'
        f'Após clicar, envie o texto que quer transmitir ou a foto. Para enviar uma foto com texto, basta colocar '
        f'o texto na legenda da imagem. 📷🖋️\n'
        f'┕━━━━╗✹╔━━━━┙\n\n'
        f'◎ ══════ ❈ ══════ ◎\n'
        f'🔎 <b>PESQUISAR USUÁRIO</b>\n'
        f'◎ ══════ ❈ ══════ ◎\n'
        f'Se este usuário estiver registrado no bot, vai abrir as configurações de edição desse usuário. 💼🔧\n'
        f'Você poderá editar o saldo, ver o histórico de compras, e todas as informações dele. 📈📋\n'
        f'┕━━━━╗✹╔━━━━┙'
    )
    bt = InlineKeyboardButton('📫 TRANSMITIR A TODOS', callback_data='transmitir_todos')
    bt2 = InlineKeyboardButton('🔎 PESQUISAR USUARIO', callback_data='pesquisar_usuario')
    bt3 = InlineKeyboardButton('↩ VOLTAR', callback_data='voltar_paineladm')
    markup = InlineKeyboardMarkup([[bt], [bt2], [bt3]])
    bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=message.message_id,
        text=texto,
        reply_markup=markup,
        parse_mode='HTML'
    )
enviando_transmissao = False
def atualizar_status_envio(bot, status_message_info, stats):
    """
    Atualiza (edita) a mensagem de status no chat do ADM,
    mostrando quantos foram enviados, bloqueados, etc.
    """
    status_message_id = status_message_info['message_id']
    chat_id = status_message_info['chat_id']
    # Monta texto de status
    status_texto = (
        f"📣 <b>Status da Transmissão...</b> 🚀\n\n"
        f"👥 <b>Total processados:</b> <code>{stats['total_users']}</code>\n"
        f"✅ <b>Receberam com sucesso:</b> <code>{stats['usuarios_recebidos']}</code>\n"
        f"🚫 <b>Bloquearam o bot:</b> <code>{stats['bloqueados']}</code>\n"
        f"❌ <b>Falha no envio:</b> <code>{stats['usuarios_nao_recebidos']}</code>"
    )
    try:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=status_message_id,
            text=status_texto,
            parse_mode='HTML'
        )
    except:
        pass
def processar_lote_usuarios(
    bot,
    lista_usuarios,
    texto: str or None,
    video_file_path: str or None,
    photo_file_path: str or None,
    markup,
    stats: dict,
    status_message_info: dict
):
    """
    Função que processa (envia) um "chunk" (lote) de usuários.
    Ela atualiza um dicionário stats compartilhado, incrementando
    a contagem de envios e bloqueios. Cada envio respeita 1s de delay.
    """
    for user_id in lista_usuarios:
        user_data = load_user_data(user_id)
        if not user_data:
            with stats['lock']:
                stats['total_users'] += 1
                stats['usuarios_nao_recebidos'] += 1
            continue
        with stats['lock']:
            stats['total_users'] += 1
        try:
            if video_file_path:
                with open(video_file_path, 'rb') as video_file:
                    bot.send_video(
                        user_data["id"],
                        video=video_file,
                        caption=texto,
                        parse_mode='HTML',
                        reply_markup=markup,
                        timeout=120
                    )
            elif photo_file_path:
                with open(photo_file_path, 'rb') as photo_file:
                    bot.send_photo(
                        user_data["id"],
                        photo=photo_file,
                        caption=texto,
                        parse_mode='HTML',
                        reply_markup=markup,
                        timeout=120
                    )
            else:
                bot.send_message(
                    user_data["id"],
                    texto,
                    parse_mode='HTML',
                    reply_markup=markup
                )
            with stats['lock']:
                stats['mensagens_enviadas'] += 1
                stats['usuarios_recebidos'] += 1
        except ApiTelegramException as e:
            if (
                "bot was blocked by the user" in str(e)
                or "user is deactivated" in str(e)
                or "chat not found" in str(e)
            ):
                with stats['lock']:
                    stats['bloqueados'] += 1
            elif "Too Many Requests" in str(e):
                time.sleep(5)
                pass
            else:
                print(f"[BROADCAST] Falha ao enviar para {user_data.get('id')}: {e}")
                with stats['lock']:
                    stats['usuarios_nao_recebidos'] += 1
        except Exception as e:
            print(f"[BROADCAST] Falha inesperada ao enviar para {user_data.get('id')}: {e}")
            with stats['lock']:
                stats['usuarios_nao_recebidos'] += 1
        time.sleep(1)
        with stats['lock']:
            total_enviados = (
                stats['mensagens_enviadas'] +
                stats['usuarios_nao_recebidos'] +
                stats['bloqueados']
            )
            if total_enviados % 50 == 0:
                atualizar_status_envio(bot, status_message_info, stats)
def addsaldo(message):
    """
    Exibe o novo menu de recarga interativo com valores rápidos e a opção de digitar um valor.
    """
    try:
        # Texto principal do menu de recarga
        texto = (
            f"✅ <b>RECARREGAR SALDO</b>\n\n"
            f"Escolha um dos valores rápidos abaixo ou digite um valor personalizado.\n\n"
            f"<b>Observações:</b>\n"
            f"- Pagamento apenas por PIX.\n"
            f"- Mínimo: R${api.CredentialsChange.InfoPix.deposito_minimo_pix():.2f} | Máximo: R${api.CredentialsChange.InfoPix.deposito_maximo_pix():.2f}.\n"
            f"- Você pode ganhar bônus dependendo do valor da recarga."
        )
        # Criação dos botões
        markup = InlineKeyboardMarkup()
        # Linha 1: Valores rápidos
        markup.row(
            InlineKeyboardButton("R$ 10", callback_data="pix_quick 10"),
            InlineKeyboardButton("R$ 20", callback_data="pix_quick 20")
        )
        # Linha 2: Mais valores rápidos
        markup.row(
            InlineKeyboardButton("R$ 50", callback_data="pix_quick 50"),
            InlineKeyboardButton("R$ 100", callback_data="pix_quick 100")
        )
        # Linha 3: Opção para digitar um valor personalizado
        markup.row(InlineKeyboardButton("⌨️ Digitar Outro Valor", callback_data="digitar_valor_pix"))
        # Adiciona o botão de PIX Manual se estiver ativado nas configura��ões
        if api.CredentialsChange.StatusPix.pix_manual():
            markup.row(InlineKeyboardButton('📄 PIX MANUAL (Enviar Comprovante)', callback_data='pix_manual'))
        # Linha 4: Botão para voltar ao menu principal
        markup.row(InlineKeyboardButton('↩️ Voltar', callback_data='menu_start'))
        # Se houver uma foto customizada para 'addsaldo' (definida via /setfotomenu),
        # exibe o menu com a foto em vez de só texto.
        from app import interface as fotos_menus
        if fotos_menus.exibir_com_foto_opcional(
            bot, message.chat.id, message.message_id, 'addsaldo', texto, reply_markup=markup, parse_mode='HTML'
        ):
            return
        # Edita a mensagem existente para exibir o novo menu (funciona tanto se a
        # mensagem atual for texto quanto se for a foto do menu principal)
        api.editar_menu_seguro(
            bot,
            chat_id=message.chat.id,
            message_id=message.message_id,
            texto=texto,
            reply_markup=markup,
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Erro ao gerar menu 'addsaldo': {e}")
        bot.send_message(message.chat.id, "Ocorreu um erro ao abrir o menu de recarga.")


# ==========================================================
# LISTA DE COMANDOS DO BOT (botão "📋 Lista de Comandos" no painel admin)
# ==========================================================
# Texto gerado manualmente a partir de uma varredura em todos os arquivos do
# bot por @bot.message_handler(commands=[...]). Se um comando novo for
# adicionado no futuro, é só incluir a linha correspondente aqui também.

_COMANDOS_ADMIN_TEXTO = (
    "👑 <b>COMANDOS DE ADMIN / DONO</b>\n"
    "➖➖➖➖➖➖➖➖➖➖➖\n\n"
    "<b>Painel e estoque</b>\n"
    "🔹 /admin — abre o painel de administração\n"
    "🔹 /estoque — igual ao comando do cliente, mas pra admin/dono também mostra email e senha de cada login, e libera o botão de baixar tudo em .txt\n"
    "🔹 /quantidadelogins — mostra a quantidade de logins em estoque por serviço\n"
    "🔹 /add — inicia o modo de adição de logins em massa\n"
    "🔹 /done — finaliza o modo de adição de logins\n"
    "🔹 /addservico NOME/VALOR/DESC/DIAS — cadastra um novo serviço/produto\n"
    "🔹 /servicos_salvos — lista os templates de serviço salvos\n"
    "🔹 /resetar_saldos — zera o saldo de todos os clientes\n"
    "🔹 /gift &lt;valor&gt; &lt;quantidade&gt; — gera gift card(s)\n\n"
    "<b>Financeiro e vendas</b>\n"
    "🔹 /renda — mostra o faturamento do bot\n"
    "🔹 /top_depositors — ranking de quem mais depositou\n"
    "🔹 /top_products — ranking dos produtos mais vendidos\n"
    "🔹 /top_recent_depositors — ranking dos depósitos mais recentes\n"
    "🔹 /setpixmin &lt;valor&gt; — define o depósito mínimo via PIX\n"
    "🔹 /setpixmax &lt;valor&gt; — define o depósito máximo via PIX\n"
    "🔹 /togglepixmanual — liga/desliga o PIX manual\n"
    "🔹 /setbonus — configura o bônus de depósito\n"
    "🔹 /setrecompensa — configura a recompensa de indicação\n\n"
    "<b>Usuários e trocas</b>\n"
    "🔹 /user &lt;id&gt; — abre o painel de gerenciamento daquele cliente\n"
    "🔹 /contasproblema — lista contas com problema relatadas por clientes\n"
    "🔹 /addalert &lt;serviço&gt; — cria alerta de reposição de estoque\n"
    "🔹 /removealert &lt;serviço&gt; — remove um alerta de reposição\n"
    "🔹 /listalerts — lista os alertas de reposição configurados\n"
    "🔹 /trocas_pendentes — lista trocas de conta pendentes\n"
    "🔹 /config_trocas — configura o sistema de trocas automáticas\n"
    "🔹 /trocas_relatorio — relatório de trocas realizadas\n\n"
    "<b>Manutenção e sistema</b>\n"
    "🔹 /backup — gera um backup manual do bot\n"
    "🔹 /manutencao_on — ativa o modo de manutenção\n"
    "🔹 /manutencao_off — desativa o modo de manutenção\n"
    "🔹 /status_manutencao — mostra o status da manutenção\n"
    "🔹 /limparcache — limpa o cache interno do bot\n"
    "🔹 /setemoji — define o emoji usado em um produto/menu\n"
    "🔹 /prefixar — adiciona um prefixo aos nomes dos produtos\n"
    "🔹 /format — ferramenta de formatação de mensagens\n"
    "🔹 /adicionar_texto — adiciona/edita um texto do bot\n"
    "🔹 /get_id e /getchatid — mostram o ID do usuário/chat atual\n"
    "🔹 /criador — painel exclusivo do desenvolvedor do bot"
)

_COMANDOS_CLIENTE_TEXTO = (
    "👤 <b>COMANDOS DE CLIENTE</b>\n"
    "➖➖➖➖➖➖➖➖➖➖➖\n\n"
    "🔹 /start — inicia o bot e mostra o menu principal\n"
    "🔹 /pix &lt;valor&gt; — gera um PIX para depositar saldo\n"
    "🔹 /saldo — mostra seu saldo atual\n"
    "🔹 /id — mostra seu ID de usuário no Telegram\n"
    "🔹 /estoque — mostra o estoque disponível (valor, descrição, duração e quantidade de cada login)\n"
    "🔹 /historico — mostra seu histórico de compras\n"
    "🔹 /cancelar — cancela a operação em andamento\n"
    "🔹 /termos — mostra os termos de uso da loja\n"
    "🔹 /resgatar &lt;código&gt; — resgata um gift card\n"
    "🔹 /meulink — mostra seu link de indicação\n"
    "🔹 /minhasindicacoes — mostra quantas indicações você já fez\n"
    "🔹 /rankingindicadores — ranking de quem mais indica\n"
    "🔹 /afiliados — informações do programa de afiliados\n"
    "🔹 /ranking — ranking de produtos/clientes\n"
    "🔹 /alertas — gerencia seus alertas de reposição de estoque\n"
    "🔹 /ping (ou /health) — verifica se o bot está online"
)


@bot.callback_query_handler(func=lambda call: call.data == "admin_lista_comandos")
def admin_lista_comandos(call):
    """Mostra a lista completa de comandos do bot (admin + cliente), em
    duas mensagens separadas para não estourar o limite de caracteres do
    Telegram numa mensagem só."""
    if not (is_admin_user(call.from_user.id) or int(call.message.chat.id) == int(api.CredentialsChange.id_dono())):
        return bot.answer_callback_query(call.id, "🚫 Sem permissão.", show_alert=True)
    bot.answer_callback_query(call.id)
    markup_voltar = InlineKeyboardMarkup()
    markup_voltar.row(InlineKeyboardButton('↩ Voltar ao Painel', callback_data='voltar_paineladm'))
    try:
        bot.send_message(call.message.chat.id, _COMANDOS_ADMIN_TEXTO, parse_mode='HTML')
        bot.send_message(call.message.chat.id, _COMANDOS_CLIENTE_TEXTO, parse_mode='HTML', reply_markup=markup_voltar)
    except Exception as e:
        print(f"[Lista de Comandos] Erro ao enviar: {e}")
        bot.send_message(call.message.chat.id, "❌ Erro ao gerar a lista de comandos.")


# ==================== PIX TRANSMISSAO CARRINHO ====================
@bot.callback_query_handler(func=lambda call: call.data == 'digitar_valor_pix')
def callback_digitar_valor(call):
    """
    Este handler é ativado quando o usuário clica em "Digitar Outro Valor".
    Ele solicita que o usuário envie o valor desejado.
    """
    try:
        bot.answer_callback_query(call.id)
        # Deleta o menu anterior para uma interface mais limpa
        bot.delete_message(call.message.chat.id, call.message.message_id)
        msg = bot.send_message(
            call.message.chat.id,
            "💰 *Por favor, digite o valor que deseja recarregar:*",
            parse_mode="Markdown",
            reply_markup=types.ForceReply()  # Força o usuário a responder
        )
        # A próxima mensagem do usuário será processada pela função 'processar_valor_recarga'
        bot.register_next_step_handler(msg, processar_valor_recarga)
    except Exception as e:
        print(f"Erro em callback_digitar_valor: {e}")
        bot.send_message(call.message.chat.id, "Ocorreu um erro. Tente novamente.")
@bot.callback_query_handler(func=lambda call: call.data == 'pix_manual')
def callback_pix_manual(call):
    """
    Inicia o novo fluxo de PIX Manual, solicitando o valor ao usuário.
    """
    if not api.CredentialsChange.StatusPix.pix_manual():
        return bot.answer_callback_query(call.id, 'Pix manual desativado.', show_alert=True)
    try:
        bot.answer_callback_query(call.id)
        # Limpa o menu anterior
        bot.delete_message(call.message.chat.id, call.message.message_id)
        # Pede o valor
        msg = bot.send_message(
            call.message.chat.id,
            "💰 *Qual o valor que você vai depositar manualmente?*\n\n"
            "Envie o valor exato (ex: `1` ou `10.50`).",
            parse_mode="Markdown",
            reply_markup=types.ForceReply()
        )
        # Registra o próximo passo
        bot.register_next_step_handler(msg, processar_valor_pix_manual)
    except Exception as e:
        print(f"[ERRO] callback_pix_manual: {e}")
        bot.send_message(call.message.chat.id, "Ocorreu um erro. Tente novamente.")
def processar_valor_pix_manual(message):
    """
    Processa o valor enviado pelo usuário para o PIX Manual.
    """
    try:
        valor_str = message.text.replace("R$", "").replace(",", ".").strip()
        valor = float(valor_str)
        # O limite mínimo e máximo do painel foi removido
        # Mantemos apenas a trava para impedir depósitos negativos ou zerados
        if valor <= 0:
            msg = bot.reply_to(
                message,
                f"❌ Valor inválido! O depósito deve ser maior que R$ 0.00.\n\n"
                f"Por favor, digite o valor correto:",
                reply_markup=types.ForceReply()
            )
            # Tenta de novo
            bot.register_next_step_handler(msg, processar_valor_pix_manual)
            return
    except ValueError:
        # Não é um número
        msg = bot.reply_to(
            message,
            "❌ Valor inválido. Envie apenas números (ex: `10` ou `15.50`).\n\n"
            "Qual o valor que você vai depositar?",
            parse_mode="Markdown",
            reply_markup=types.ForceReply()
        )
        # Tenta de novo
        bot.register_next_step_handler(msg, processar_valor_pix_manual)
        return
    # Se o valor é válido:
    try:
        user_id = message.from_user.id
        user = message.from_user
        user_display_name = user.first_name or "Usuário"
        username = f"@{user.username}" if user.username else "Não definido"
        # 1. Pega o texto configurável (que contém a chave PIX, etc.)
        # Este texto deve ser configurado no painel admin (Editar Textos -> PIX Manual)
        texto_instrucoes = api.Textos.pix_manual(message)
        # 2. Pega o link de suporte
        link_suporte = api.CredentialsChange.SuporteInfo.link_suporte()
        # 3. Monta a mensagem para o usuário
        # Definindo as instruções fixas com sua chave
        texto_instrucoes = (
            f"✨ <b>PIX MANUAL</b>\n\n"
            f"🔑 <b>CHAVE PIX:</b> <code>4ead52fb-e19e-4a09-afab-4f24da94426c</code>\n"
            f"👤 <b>Nome:</b> Francisco Rafael Lopes\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✨ <b>ENVIE O COMPROVANTE PARA:</b> @Mobixsuporte"
        )
        texto_usuario = (
            f"✅ <b>Solicitação Registrada!</b>\n\n"
            f"Você informou um depósito de: <b>R$ {valor:.2f}</b>\n\n"
            f"{texto_instrucoes}\n\n"
            f"⚠️ <b>IMPORTANTE:</b>\n"
            f"Após realizar o pagamento, envie o <b>COMPROVANTE</b> para o nosso suporte.\n"
            f"🆔 <b>Seu ID:</b> <code>{user_id}</code>\n\n"
            f"<i>Clique na chave acima para copiar!</i>"
        )
        markup_usuario = InlineKeyboardMarkup()
        markup_usuario.row(InlineKeyboardButton("➡️ Enviar Comprovante ao Suporte", url=link_suporte))
        markup_usuario.row(InlineKeyboardButton("🏠 Voltar ao Menu Principal", callback_data="menu_start"))
        bot.send_message(
            user_id,
            texto_usuario,
            parse_mode='HTML',
            reply_markup=markup_usuario,
            disable_web_page_preview=True
        )
        # 4. Monta a notificação para o Admin
        texto_admin = (
            f"🔔 <b>Solicitação de PIX Manual</b>\n\n"
            f"O usuário <b>{escape(user_display_name)}</b> ({username}) iniciou uma recarga manual.\n\n"
            f"👤 <b>Usuário:</b> <code>{user_id}</code>\n"
            f"💰 <b>Valor Informado:</b> R$ {valor:.2f}\n\n"
            f"<i>Aguardando o envio do comprovante pelo suporte...</i>"
        )
        bot.send_message(
            ADMIN_ID,
            texto_admin,
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"[ERRO] processar_valor_pix_manual (etapa final): {e}")
        bot.reply_to(message, "Ocorreu um erro ao processar sua solicitação. Por favor, contate o suporte.")
def enviar_para_todos_thread(message, texto=None, video_file_path=None, photo_file_path=None, markup=None):
    status_inicial = f"🚀 Iniciando envio...\nHá {api.Admin.total_users()} usuários registrados.\nIsto pode demorar alguns minutos... Por favor, aguarde."
    sent_status_message = bot.send_message(
        chat_id=message.chat.id,
        text=status_inicial,
        parse_mode='HTML'
    )
    status_message_info = {
        'message_id': sent_status_message.message_id,
        'chat_id': message.chat.id
    }
    user_files = database.get_all_user_ids()
    stats = {
        'total_users': 0,
        'mensagens_enviadas': 0,
        'bloqueados': 0,
        'usuarios_recebidos': 0,
        'usuarios_nao_recebidos': 0,
        'lock': threading.Lock()
    }
    tamanho = len(user_files)
    if tamanho == 0:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=sent_status_message.message_id,
            text="Nenhum usuário para enviar a mensagem.",
            parse_mode='HTML'
        )
        return
    parte = tamanho // 3 if tamanho >= 3 else tamanho
    chunk1 = user_files[:parte]
    chunk2 = user_files[parte:2*parte]
    chunk3 = user_files[2*parte:]
    t1 = threading.Thread(
        target=processar_lote_usuarios,
        args=(bot, chunk1, texto, video_file_path, photo_file_path, markup, stats, status_message_info)
    )
    t2 = threading.Thread(
        target=processar_lote_usuarios,
        args=(bot, chunk2, texto, video_file_path, photo_file_path, markup, stats, status_message_info)
    )
    t3 = threading.Thread(
        target=processar_lote_usuarios,
        args=(bot, chunk3, texto, video_file_path, photo_file_path, markup, stats, status_message_info)
    )
    t1.start()
    t2.start()
    t3.start()
    t1.join()
    t2.join()
    t3.join()
    status_final = (
        f"✅ <b>Transmissão Concluída!</b> 🚀\n\n"
        f"👥 <b>Total processados:</b> <code>{stats['total_users']}</code>\n"
        f"✅ <b>Receberam com sucesso:</b> <code>{stats['usuarios_recebidos']}</code>\n"
        f"🚫 <b>Bloquearam o bot:</b> <code>{stats['bloqueados']}</code>\n"
        f"❌ <b>Falha no envio:</b> <code>{stats['usuarios_nao_recebidos']}</code>"
    )
    bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=sent_status_message.message_id,
        text=status_final,
        parse_mode='HTML'
    )
    if photo_file_path and os.path.exists(photo_file_path):
        os.remove(photo_file_path)
    if video_file_path and os.path.exists(video_file_path):
        os.remove(video_file_path)
def transmitir_todos(message):
    processando_msg = bot.send_message(message.chat.id, "Processando mídia... Por favor, aguarde.")
    if getattr(message, "forward_date", None) is not None:
        user_ids = database.get_all_user_ids()
        for user_id in user_ids:
            try:
                bot.forward_message(
                    chat_id=user_id,
                    from_chat_id=message.chat.id,
                    message_id=message.message_id
                )
            except Exception as e:
                print(f"Erro ao encaminhar mensagem para {user_id}: {e}")
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=processando_msg.message_id,
            text="Transmissão concluída!"
        )
        return  
    api.FuncaoTransmitir.zerar_infos()
    bt1 = InlineKeyboardButton('➕ ADICIONAR BOTÃO/LINK', callback_data='add_botao')
    bt2 = InlineKeyboardButton('✅ CONFIRMAR ENVIO', callback_data='confirmar_envio')
    markup = InlineKeyboardMarkup([[bt1], [bt2]])
    if message.content_type == 'video':
        video = message.video.file_id
        video_info = bot.get_file(video)
        video_path = bot.download_file(video_info.file_path)
        video_file_path = os.path.join(os.getcwd(), 'video.mp4')
        with open(video_file_path, 'wb') as new_file:
            new_file.write(video_path)
        api.FuncaoTransmitir.adicionar_video(video_file_path)
        api.FuncaoTransmitir.adicionar_texto(message.caption)
        bot.delete_message(message.chat.id, processando_msg.message_id)
        with open(video_file_path, 'rb') as video_file:
            bot.send_video(
                message.chat.id,
                video=video_file,
                caption=message.caption,
                reply_markup=markup,
                parse_mode='HTML',
                timeout=60
            )
    elif message.content_type == 'photo':
        photo = message.photo[-1].file_id
        photo_info = bot.get_file(photo)
        photo_path = bot.download_file(photo_info.file_path)
        photo_file_path = os.path.join(os.getcwd(), 'image.jpg')
        with open(photo_file_path, 'wb') as new_file:
            new_file.write(photo_path)
        api.FuncaoTransmitir.adicionar_foto(photo_file_path)
        api.FuncaoTransmitir.adicionar_texto(message.caption)
        bot.delete_message(message.chat.id, processando_msg.message_id)
        with open(photo_file_path, 'rb') as photo_file:
            bot.send_photo(
                message.chat.id,
                photo=photo_file,
                caption=message.caption,
                reply_markup=markup,
                parse_mode='HTML'
            )
    elif message.content_type == 'animation':
        animation = message.animation.file_id
        animation_info = bot.get_file(animation)
        animation_path = bot.download_file(animation_info.file_path)
        animation_file_path = os.path.join(os.getcwd(), 'animation.gif')
        with open(animation_file_path, 'wb') as new_file:
            new_file.write(animation_path)
        api.FuncaoTransmitir.adicionar_video(animation_file_path)
        api.FuncaoTransmitir.adicionar_texto(message.caption)
        bot.delete_message(message.chat.id, processando_msg.message_id)
        with open(animation_file_path, 'rb') as animation_file:
            bot.send_animation(
                message.chat.id,
                animation=animation_file,
                caption=message.caption,
                reply_markup=markup,
                parse_mode='HTML'
            )
    elif message.content_type == 'text':
        api.FuncaoTransmitir.adicionar_texto(message.text)
        bot.delete_message(message.chat.id, processando_msg.message_id)
        bot.send_message(
            message.chat.id,
            text=message.text,
            parse_mode='HTML',
            reply_markup=markup
        )
    else:
        bot.reply_to(message, "Este tipo de mensagem ainda não está disponível para transmitir.")
ITEMS_PER_PAGE = 50
def cart_show_products(user_id: int, page: int, msg):
    ITEMS_PER_PAGE = 10 # Força a variável a existir
    servicos = api.ControleLogins.pegar_servicos()
    vistos, produtos = set(), []
    for s in servicos:
        n = s["nome"]
        if n not in vistos:
            vistos.add(n)
            preco_original = float(s["valor"])
            # --- VERIFICAÇÃO DE OFERTA RELÂMPAGO NO MENU ---
            try:
                from app import Oferta_relampago
                preco_final = Oferta_relampago.verificar_preco(n, preco_original)
            except Exception:
                preco_final = preco_original
            # -----------------------------------------------
            produtos.append((n, preco_final))
    total_pages = max(1, math.ceil(len(produtos) / ITEMS_PER_PAGE))
    page = max(0, min(page, total_pages - 1))
    ini = page * ITEMS_PER_PAGE
    fim = (page + 1) * ITEMS_PER_PAGE
    slice_ = sorted(produtos)[ini:fim]
    txt = f"🛒 <b>Carrinho</b> — escolha itens (pág. {page+1}/{total_pages})"
    kb = InlineKeyboardMarkup(row_width=1)
    for nome, preco in slice_:
        cb_data = f'cart_add|{nome}'
        # PROTEÇÃO CONTRA NOME LONGO: O Telegram bloqueia botões com mais de 64 caracteres de sinal
        if len(cb_data.encode('utf-8')) > 64:
             # Corta de forma segura apenas o sinal interno para o botão não quebrar a tela
             cb_data = cb_data.encode('utf-8')[:64].decode('utf-8', 'ignore')
        kb.add(InlineKeyboardButton(
            f"{nome}  •  R${preco:.2f}",
            callback_data=cb_data
        ))
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton('⬅️ Anterior', callback_data=f'cart_show_{page-1}'))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton('Próxima ➡️', callback_data=f'cart_show_{page+1}'))
    nav.append(InlineKeyboardButton('🏠 Voltar', callback_data='servicos'))
    kb.row(*nav)
    # Se houver uma foto customizada para 'carrinho' (definida via /setfotomenu),
    # exibe o carrinho com a foto em vez de só texto.
    from app import interface as fotos_menus
    if fotos_menus.exibir_com_foto_opcional(
        bot, msg.chat.id, msg.message_id, 'carrinho', txt, reply_markup=kb
    ):
        return
    # Usa formatação segura e protege de queda caso a edição falhe
    try:
        safe_edit_message(msg, txt, reply_markup=kb)
    except Exception:
        bot.send_message(user_id, txt, reply_markup=kb, parse_mode="HTML")
def cart_render_summary(user_id: int):
    carrinho = user_carts.get(user_id, {})
    if not carrinho:
        return "🛒 Seu carrinho está vazio."
    try:
        chat  = bot.get_chat(user_id)
        if chat.username:                     
            nome_visivel = f"@{chat.username}"
        else:                                 
            nome_visivel = f"{chat.first_name or ''} {chat.last_name or ''}".strip() or "Usuário"
    except Exception:
        nome_visivel = "Usuário"
    total  = 0.0
    linhas = []
    for serv, qtd in carrinho.items():
        info = api.ControleLogins.peek_primeiro_disponivel(serv)
        if not info:        
            continue
        _, preco_original, *_ = info
        # --- VERIFICAÇÃO DE OFERTA RELÂMPAGO ---
        try:
            from app import Oferta_relampago
            preco_final = Oferta_relampago.verificar_preco(serv, float(preco_original))
        except Exception:
            preco_final = float(preco_original)
        # ---------------------------------------
        subtotal = preco_final * qtd
        total   += subtotal
        linhas.append(f"{serv} ×{qtd} — R${subtotal:.2f}")
    saldo = get_user_balance(user_id)
    return (
        f"👤 <b>{nome_visivel}</b> <code>({user_id})</code>\n"
        f"{chr(10).join(linhas)}\n"
        f"📦 <b>Total:</b> R${total:.2f}\n"
        f"💰 <b>Saldo:</b> R${saldo:.2f}"
    )
def cart_update_or_send_summary(user_id: int):
    txt = cart_render_summary(user_id)
    kb  = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton('✅ Comprar',  callback_data='cart_buy'),
        InlineKeyboardButton('❌ Cancelar', callback_data='cart_cancel')
    )
    if user_id in user_cart_msgs:                
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=user_cart_msgs[user_id],
                text=txt,
                parse_mode='HTML',
                reply_markup=kb
            )
            return
        except Exception:
            pass
    sent = bot.send_message(user_id, txt, parse_mode='HTML', reply_markup=kb)
    user_cart_msgs[user_id] = sent.message_id
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
# ───────────────────────────────────────────────────────────────
#  AVISO DE VENDA – 2 formatos (VERSÃO MODIFICADA)
#     • grupo de vendas  → mensagem bonita e detalhada (NOVO)
#     • ADM              → mensagem completa com imagem + WHATSAPP
# ───────────────────────────────────────────────────────────────
def avisar_venda(user_id: int,
                 servico: str,
                 email: str,
                 senha: str,
                 valor: float,
                 data_compra: str,
                 data_venc: str,
                 saldo_atual: float):
    import html
    import re
    tz = pytz_timezone('America/Sao_Paulo')
    # Obter informações do usuário para as notificações
    try:
        chat = bot.get_chat(user_id)
        user_info_username = f"@{chat.username}" if chat.username else "Não definido"
        user_info_name = (f"{chat.first_name or ''} {chat.last_name or ''}").strip() or "Não definido"
    except Exception:
        user_info_username = "N/A"
        user_info_name = "N/A"
    # Pega o estoque restante
    try:
        estoque_restante = api.ControleLogins.pegar_estoque(servico)
    except Exception as e:
        print(f"[avisar_venda] Falha ao obter estoque restante: {e}")
        estoque_restante = "N/A"
    # --- Carrega dados do usuário para pegar Whatsapp e Compras ---
    compras_hoje = 0
    whatsapp_user = "Não informado"
    try:
        user_data = load_user_data(user_id)
        if user_data:
            # Pega WhatsApp
            whatsapp_user = user_data.get('whatsapp', 'Não informado')
            # Calcula compras
            if 'compras' in user_data:
                hoje = datetime.now(tz).date()
                for compra in user_data['compras']:
                    try:
                        # Extrai a data da string 'dd/mm/aaaa às hh:mm:ss'
                        data_compra_obj = datetime.strptime(compra['data'].split(' ')[0], "%d/%m/%Y").date()
                        if data_compra_obj == hoje:
                            compras_hoje += 1
                    except (ValueError, KeyError):
                        continue
    except Exception as e:
        print(f"[avisar_venda] Erro ao carregar dados do usuário: {e}")
        compras_hoje = "N/A"
    # -----------------------------------------------------------
    #  LÓGICA DO LINK DO WHATSAPP
    # -----------------------------------------------------------
    whatsapp_display = whatsapp_user
    if whatsapp_user and whatsapp_user != "Não informado":
        # Remove tudo que não for número (ex: +, -, parênteses, espaços)
        numeros_limpos = re.sub(r'\D', '', str(whatsapp_user))
        if numeros_limpos:
            # Cria o link HTML
            whatsapp_display = f'<a href="https://wa.me/{numeros_limpos}">{whatsapp_user}</a>'
    # -----------------------------------------------------------
    #  AVISO PARA GRUPO DE VENDAS
    # -----------------------------------------------------------
    sale_msg_grp = (
        f"🚀✨ <b>NOVA VENDA REGISTRADA</b>🚀\n\n"
        f"<i>Um novo pedido foi confirmado com sucesso!</i>\n\n"
        f"➖➖➖➖➖➖➖➖➖➖\n\n"
        f"🛒 <b>Total de Compras Hoje:</b> {compras_hoje}ª\n\n"
        f"🛍️ <b>Produto:</b> {html.escape(servico)}\n"
        f"💰 <b>Valor:</b> R$ {float(valor):.2f}\n\n"
        f"➖➖➖➖➖➖➖➖➖➖\n\n"
        f"🕒 <b>Data e Hora:</b> {data_compra}"
    )
    try:
        # Envia apenas o texto sem revelar a foto e os dados do usuário
        bot.send_message(SALES_GROUP_ID, sale_msg_grp, parse_mode='HTML')
    except Exception as e:
        print(f"[avisar_venda] falha ao notificar grupo: {e}")
    # -----------------------------------------------------------
    #  AVISO PARA O ADMIN (Com WhatsApp Linkado)
    # -----------------------------------------------------------
    sale_msg_adm = (
        "🎉 <b>Nova venda!</b>\n\n"
        f"👤 <b>Usuário:</b> {user_info_username}\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
        f"👤 <b>Nome:</b> {user_info_name}\n"
        f"📞 <b>WhatsApp:</b> {whatsapp_display}\n"
        f"🎟️ <b>Serviço:</b> <b>{servico}</b>\n"
        f"🔢 <b>Estoque Restante:</b> {estoque_restante}\n"
        f"💰 <b>Valor:</b> R${float(valor):.2f}\n"
        f"🏦 <b>Saldo usuário:</b> R${saldo_atual:.2f}\n\n"
        f"🗓️ <b>Data da Compra:</b> {data_compra}\n"
        f"🗓 <b>Vencimento:</b> {data_venc}\n"
        f"📧 <b>Email:</b> <code>{email}</code>\n"
        f"🔑 <b>Senha:</b> <code>{senha}</code>"
    )
    # --- LÓGICA DE ENVIO COM IMAGEM PARA O ADMIN ---
    try:
        icone_url = obter_icone_servico(servico)
        if icone_url:
            bot.send_photo(
                chat_id=ADMIN_ID,
                photo=icone_url,
                caption=sale_msg_adm,
                parse_mode='HTML'
            )
        else:
            raise ValueError("Não foi possível obter uma URL de ícone.")
    except Exception as e:
        print(f"[avisar_venda] Falha ao enviar foto, enviando texto: {e}")
        try:
            bot.send_message(
                ADMIN_ID,
                sale_msg_adm,
                parse_mode='HTML'
            )
        except Exception as e_text:
            print(f"[avisar_venda] Falha CRÍTICA ao notificar admin: {e_text}")
def add_botao(message):
    try:
        text = message.text
        s = text.split('\n')
        markup = InlineKeyboardMarkup()
        for elemento in s:
            botoes = []
            separar = elemento.split('&&')
            for botao in separar:
                sep = botao.split('-')
                nome = sep[0].strip()
                url = sep[1].strip()
                botoes.append(InlineKeyboardButton(f'{nome}', url=f'{url}'))
            markup.row(*botoes)
        api.FuncaoTransmitir.adicionar_markup(markup)
        bt2 = InlineKeyboardButton('✅ CONFIRMAR ENVIO', callback_data='confirmar_envio')
        markup.row(bt2)
        if markup != None:
            texto = api.FuncaoTransmitir.pegar_texto()
            photo = api.FuncaoTransmitir.pegar_foto()
            video = api.FuncaoTransmitir.pegar_video()
            if video != None and os.path.exists(video):
                with open(video, 'rb') as video_file:
                    bot.send_video(message.chat.id, video=video_file, caption=texto, reply_markup=markup, parse_mode='HTML', timeout=60)
            elif photo != None and os.path.exists(photo) and texto == None:
                with open(photo, 'rb') as photo_file:
                    bot.send_photo(message.chat.id, photo_file, reply_markup=markup, parse_mode='HTML')
            elif photo != None and os.path.exists(photo) and texto != None:
                with open(photo, 'rb') as photo_file:
                    bot.send_photo(message.chat.id, photo_file, caption=texto, reply_markup=markup, parse_mode='HTML')
            elif texto != None:
                bot.send_message(message.chat.id, texto, reply_markup=markup, parse_mode='HTML')
            else:
                bot.reply_to(message, "Error!")
    except Exception as e:
        bot.reply_to(message, "Ocorreu um erro ao processar, verifique se enviou o nome e a URL no formato correto.")
        print(e)
def confirmar_envio(message):
    texto = api.FuncaoTransmitir.pegar_texto()
    video_file_path = api.FuncaoTransmitir.pegar_video()
    photo_file_path = api.FuncaoTransmitir.pegar_foto()
    markup = api.FuncaoTransmitir.pegar_markup()
    envio_thread = threading.Thread(
        target=enviar_para_todos_thread,
        args=(message, texto, video_file_path, photo_file_path, markup)
    )
    envio_thread.start()
def pesquisar_usuario(message):
    id = message.text.strip()
    if api.InfoUser.verificar_usuario(id):
        status_ban = "🧑‍⚖️ DESBANIR" if api.InfoUser.verificar_ban(id) else "🧑‍⚖️ BANIR"
        callback_ban = "desbanir" if api.InfoUser.verificar_ban(id) else "banir"
        texto = (
            f'🔎 <b>Usuário Encontrado</b> ✅\n\n'
            f'🕵️ <b>Informações</b>\n'
            f'📛 <b>ID:</b> <code>{id}</code>\n'
            f'💰 <b>Saldo:</b> <code>R${api.InfoUser.saldo(id):.2f}</code>\n'
            f'🛒 <b>Acessos Comprados:</b> <code>{api.InfoUser.total_compras(id)}</code>\n'
            f'💠 <b>PIX Inseridos:</b> <code>R${api.InfoUser.pix_inseridos(id):.2f}</code>\n'
            f'👥 <b>Indicados:</b> <code>{api.InfoUser.quantidade_afiliados(id)}</code>\n'
            f'🎁 <b>Gift Resgatado:</b> <code>R${api.InfoUser.gifts_resgatados(id):.2f}</code>'
        )
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton(status_ban, callback_data=f'{callback_ban} {id}'))
        markup.row(InlineKeyboardButton('💰 Alterar Saldo', callback_data=f'mudar_saldo {id}'),
                   InlineKeyboardButton('📥 Baixar Histórico', callback_data=f'baixar_historico {id}'))
        bot.send_message(chat_id=message.chat.id, text=texto, parse_mode='HTML', reply_markup=markup)
    else:
        bot.reply_to(message, "❌ Usuário não encontrado.")
def mudar_saldo(message, id):
    saldo = message.text
    try:
        api.InfoUser.mudar_saldo(id, saldo)
        bot.reply_to(message, "Saldo alterado com sucesso!")
    except:
        bot.reply_to(message, "Falha ao alterar, verifique se enviou um valor valido.")
# NOVO BLOCO DE CÓDIGO PARA GERENCIAMENTO DE USUÁRIO
from html import escape
# Esta função exibe o painel de gerenciamento do usuário
def display_user_management_panel(admin_chat_id, target_user_id, message_id=None):
    # Check if user exists
    if not api.InfoUser.verificar_usuario(target_user_id):
        error_text = f"❌ Usuário com ID <code>{target_user_id}</code> não encontrado no banco de dados."
        if message_id:
            try:
                bot.edit_message_text(error_text, chat_id=admin_chat_id, message_id=message_id, parse_mode='HTML')
            except ApiTelegramException:
                bot.send_message(admin_chat_id, error_text, parse_mode='HTML')
        else:
            bot.send_message(admin_chat_id, error_text, parse_mode='HTML')
        return
    # --- Fetch User Data ---
    try:
        chat_info = bot.get_chat(target_user_id)
        user_display = f"{chat_info.first_name}"
        if chat_info.last_name:
            user_display += f" {chat_info.last_name}"
        if chat_info.username:
            user_display += f" (@{chat_info.username})"
    except Exception:
        user_display = f"ID {target_user_id}"
    saldo = api.InfoUser.saldo(target_user_id)
    total_compras = api.InfoUser.total_compras(target_user_id)
    pix_inseridos = api.InfoUser.pix_inseridos(target_user_id)
    afiliados = api.InfoUser.quantidade_afiliados(target_user_id)
    gifts_resgatados = api.InfoUser.gifts_resgatados(target_user_id)
    is_banned = api.InfoUser.verificar_ban(target_user_id)
    # --- Format the message ---
    texto = (
        f"⚙️ <b>Painel de Gerenciamento de Usuário</b>\n\n"
        f"👤 <b>Usuário:</b> {escape(user_display)}\n"
        f"🆔 <b>ID:</b> <code>{target_user_id}</code>\n"
        f"<b>STATUS:</b> {'🚫 BANIDO' if is_banned else '✅ ATIVO'}\n"
        f"━━━━━━━━━━━━━━\n"
        f"💰 <b>Saldo:</b> R$ {saldo:.2f}\n"
        f"🛒 <b>Compras:</b> {total_compras}\n"
        f"💵 <b>Total Recarregado:</b> R$ {pix_inseridos:.2f}\n"
        f"👥 <b>Afiliados:</b> {afiliados}\n"
        f"🎁 <b>Gifts Resgatados:</b> R$ {gifts_resgatados:.2f}"
    )
    # --- Create Markup Buttons ---
    markup = InlineKeyboardMarkup()
    ban_button_text = "✅ Desbanir Usuário" if is_banned else "🚫 Banir Usuário"
    markup.row(InlineKeyboardButton(ban_button_text, callback_data=f'userpanel_ban_{target_user_id}'))
    markup.row(
        InlineKeyboardButton("💰 Alterar Saldo", callback_data=f'userpanel_saldo_{target_user_id}'),
        InlineKeyboardButton("✉️ Enviar Mensagem", callback_data=f'userpanel_msg_{target_user_id}')
    )
    markup.row(
         InlineKeyboardButton("📥 Baixar Histórico", callback_data=f'baixar_historico {target_user_id}')
    )
    markup.row(
        InlineKeyboardButton("🔄 Atualizar", callback_data=f'userpanel_refresh_{target_user_id}'),
        InlineKeyboardButton("↩️ Voltar", callback_data='voltar_paineladm')
    )
    # --- Send or Edit the message ---
    if message_id:
        try:
            bot.edit_message_text(
                chat_id=admin_chat_id,
                message_id=message_id,
                text=texto,
                parse_mode='HTML',
                reply_markup=markup
            )
        except ApiTelegramException as e:
            if "message is not modified" not in str(e):
                 bot.send_message(admin_chat_id, texto, parse_mode='HTML', reply_markup=markup)
    else:
        bot.send_message(admin_chat_id, texto, parse_mode='HTML', reply_markup=markup)
# Command handler for /user <ID>
@bot.message_handler(commands=['user'])
def command_user_panel(message):
    if not (api.Admin.verificar_admin(message.chat.id) or int(message.chat.id) == int(api.CredentialsChange.id_dono())):
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "ℹ️ Use o comando assim: <code>/user ID_DO_USUARIO</code>", parse_mode='HTML')
        return
    target_user_id = parts[1]
    if not target_user_id.isdigit():
        bot.reply_to(message, "❌ O ID do usuário deve ser um número.")
        return
    display_user_management_panel(message.chat.id, int(target_user_id))
# Callback handler for the user panel buttons
@bot.callback_query_handler(func=lambda call: call.data.startswith('userpanel_'))
def callback_user_panel(call):
    admin_chat_id = call.message.chat.id
    message_id = call.message.message_id
    try:
        parts = call.data.split('_')
        action = parts[1]
        target_user_id = int(parts[2])
        if action == 'refresh':
            bot.answer_callback_query(call.id, text="🔄 Atualizando dados...")
            display_user_management_panel(admin_chat_id, target_user_id, message_id)
        elif action == 'ban':
            is_banned = api.InfoUser.verificar_ban(target_user_id)
            if is_banned:
                api.InfoUser.tirar_ban(target_user_id)
                bot.answer_callback_query(call.id, text="✅ Usu��rio desbanido!")
            else:
                api.InfoUser.dar_ban(target_user_id)
                bot.answer_callback_query(call.id, text="🚫 Usuário banido!")
            display_user_management_panel(admin_chat_id, target_user_id, message_id)
        elif action == 'saldo':
            bot.answer_callback_query(call.id)
            msg = bot.send_message(
                admin_chat_id,
                f"Digite o <b>novo saldo</b> para o usuário <code>{target_user_id}</code>.\nUse <code>+valor</code> para adicionar ou <code>-valor</code> para remover.",
                parse_mode='HTML',
                reply_markup=types.ForceReply()
            )
            bot.register_next_step_handler(msg, process_saldo_change, target_user_id, message_id)
        elif action == 'msg':
            bot.answer_callback_query(call.id)
            msg = bot.send_message(
                admin_chat_id,
                f"Digite a mensagem que deseja enviar para o usuário <code>{target_user_id}</code>.",
                parse_mode='HTML',
                reply_markup=types.ForceReply()
            )
            bot.register_next_step_handler(msg, process_send_message, target_user_id)
    except Exception as e:
        print(f"Erro no callback do painel de usuário: {e}")
        bot.answer_callback_query(call.id, text="Ocorreu um erro.")
# next_step_handler to change balance
def process_saldo_change(message, target_user_id, panel_message_id):
    admin_chat_id = message.chat.id
    valor_str = message.text.replace(',', '.').strip()
    try:
        if valor_str.startswith('+'):
            valor = float(valor_str[1:])
            api.InfoUser.add_saldo(target_user_id, valor)
            bot.reply_to(message, f"✅ Adicionado R$ {valor:.2f} ao saldo do usuário.")
        elif valor_str.startswith('-'):
            valor = float(valor_str[1:])
            api.InfoUser.tirar_saldo(target_user_id, valor)
            bot.reply_to(message, f"✅ Removido R$ {valor:.2f} do saldo do usuário.")
        else:
            valor = float(valor_str)
            api.InfoUser.mudar_saldo(target_user_id, valor)
            bot.reply_to(message, f"✅ Saldo do usu��rio definido para R$ {valor:.2f}.")
    except ValueError:
        bot.reply_to(message, "❌ Valor inválido. Envie um número (ex: 50.50, +10, -20).")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Erro ao alterar o saldo: {e}")
    # Refresh the panel
    display_user_management_panel(admin_chat_id, target_user_id, panel_message_id)
# next_step_handler to send a message
def process_send_message(message, target_user_id):
    admin_chat_id = message.chat.id
    try:
        texto_a_enviar = "🔔 <b>Mensagem do Administrador</b> 🔔\n\n" + message.text
        bot.send_message(target_user_id, texto_a_enviar, parse_mode='HTML')
        bot.reply_to(message, "✅ Mensagem enviada com sucesso!")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Falha ao enviar a mensagem: {e}")
# FIM DO NOVO BLOCO DE CÓDIGO
def configurar_pix(message):
    texto = (
        f'🔑 <b>TOKEN PROMISSEPAY:</b> <code>{api.CredentialsChange.InfoPix.token_promissepay()}</code>\n'
        f'🔻 <b>DEPÓSITO MÍNIMO:</b> <code>R${api.CredentialsChange.InfoPix.deposito_minimo_pix():.2f}</code>\n'
        f'❗️ <b>DEPÓSITO MÁXIMO:</b> <code>R${api.CredentialsChange.InfoPix.deposito_maximo_pix():.2f}</code>\n'
        # Linhas de bônus removidas da exibição
    )
    bt = InlineKeyboardButton('🔴 PIX MANUAL', callback_data='trocar_pix_manual')
    bt2 = InlineKeyboardButton('🔴 PIX AUTOMATICO', callback_data='trocar_pix_automatico')
    if api.CredentialsChange.StatusPix.pix_manual() == True:
        bt = InlineKeyboardButton('🟢 PIX MANUAL', callback_data='trocar_pix_manual')
    if api.CredentialsChange.StatusPix.pix_auto() == True:
        bt2 = InlineKeyboardButton('🟢 PIX AUTOMATICO', callback_data='trocar_pix_automatico')
    bt3 = InlineKeyboardButton('🔑 MUDAR TOKEN', callback_data='mudar_token')
    bt4 = InlineKeyboardButton('🔻 MUDAR DEPOSITO MIN', callback_data='mudar_deposito_minimo')
    bt5 = InlineKeyboardButton('❗️ MUDAR DEPOSITO MAX', callback_data='mudar_deposito_maximo')
    # bt6 e bt7 (botões de bônus) foram removidos daqui
    bt8 = InlineKeyboardButton('↩ VOLTAR', callback_data='voltar_paineladm')
    # Markup atualizado sem bt6 e bt7
    markup = InlineKeyboardMarkup([[bt, bt2], [bt3], [bt4], [bt5], [bt8]])
    bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=message.message_id,
        text=texto,
        parse_mode='HTML',
        reply_markup=markup
    )
def mudar_token(message):
    try:
        token = message.text
        api.CredentialsChange.InfoPix.mudar_tokenmp(token)
        bot.reply_to(message, "Alterado com sucesso")
    except Exception as e:
        print(e)
        bot.reply_to(message, "Falha ao alterar")
def mudar_deposito_minimo(message):
    try:
        min = message.text
        api.CredentialsChange.InfoPix.trocar_deposito_minimo_pix(min)
        bot.reply_to(message, "Alterado com sucesso!")
    except Exception as e:
        print(e)
        bot.reply_to(message, "Falha ao alterar")
def mudar_deposito_maximo(message):
    try:
        max = message.text
        api.CredentialsChange.InfoPix.trocar_deposito_maximo_pix(max)
        bot.reply_to(message, "Alterado com sucesso")
    except Exception as e:
        print(e)
        bot.reply_to(message, "Falha ao alterar")
def mudar_expiracao(message):
    if message.text.isdigit() == True:
        expiracao = int(message.text)
        if expiracao < 15:
            bot.reply_to(message, "O tempo de expiracao deve ser maior do que 15 minutos!")
            return
        api.CredentialsChange.InfoPix.mudar_expiracao(expiracao)
        bot.reply_to(message, "Alterado com sucesso!")
    else:
        bot.reply_to(message, "Envie apenas digitos!")
def mudar_bonus(message):
    try:
        p = message.text
        p = p.replace('%', '')
        p = p.strip()
        api.CredentialsChange.BonusPix.mudar_quantidade_bonus(p)
        bot.reply_to(message, "Alterado com sucesso!")
    except Exception as e:
        print(e)
        bot.reply_to(message, "Falha ao alterar")
def mudar_min_bonus(message):
    try:
        valor_min = message.text.strip()
        api.CredentialsChange.BonusPix.mudar_valor_minimo_para_bonus(valor_min)
        bot.reply_to(message, "Alterado com sucesso!")
    except Exception as e:
        print("Erro em mudar_min_bonus:", e)
        bot.reply_to(message, "Falha ao alterar.")
# A SER ADICIONADO ✨
# ======================= [NOVO SISTEMA DE EDIÇÃO DE BOTÕES - LIGHT] =======================
# Mapeamento dos botões para nomes amigáveis
# ======================================================================================
# Handler específico para o botão, garante que ele responda ao clique
@bot.callback_query_handler(func=lambda call: call.data == 'gift_card')
def handler_gift_card_click(call):
    try:
        bot.answer_callback_query(call.id)
    except: pass
    gift_card(call.message)
def gift_card(message):
    bt = InlineKeyboardButton('🎁 GERAR 1 GIFT', switch_inline_query_current_chat='CREATEGIFT 1')
    bt2 = InlineKeyboardButton('🎁 GERAR 10 GIFTS', switch_inline_query_current_chat='CREATEGIFT 1 10')
    bt4 = InlineKeyboardButton('↩ VOLTAR', callback_data='voltar_paineladm')
    markup = InlineKeyboardMarkup([[bt], [bt2], [bt4]])
    texto = '<b>🎁 MENU GIFT CARDS</b>\n\nSelecione abaixo se deseja gerar apenas 1 ou um lote de 10 de uma vez.'
    try:
        # Tenta editar a mensagem atual
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=texto,
            parse_mode='HTML',
            reply_markup=markup
        )
    except Exception:
        # Se der erro (mensagem antiga), envia uma nova para não travar
        bot.send_message(
            chat_id=message.chat.id,
            text=texto,
            parse_mode='HTML',
            reply_markup=markup
        )
SUPORTA_COPY_TEXT = hasattr(telebot.types, 'CopyTextButton')
if not SUPORTA_COPY_TEXT:
    print("[AVISO] pyTelegramBotAPI instalado não tem CopyTextButton (lib desatualizada). "
          "Botão 'Copiar código' do gift card será ocultado até atualizar a lib (pip install -U pyTelegramBotAPI).")


# ==================== GIFTCARD PIX START ====================

@bot.inline_handler(lambda query: query.query.startswith('CREATEGIFT '))
def create_gift_card(inline_query):
    if api.Admin.verificar_admin(inline_query.from_user.id) == False and int(api.CredentialsChange.id_dono()) != int(inline_query.from_user.id):
        return
    if len(inline_query.query.split()) == 2:
        value = inline_query.query.split(' ')[1]
        valor, codigo = gerar_gift_card(value)
        txt = api.TextoInline.giftcard(None, codigo, 1, valor)
        title = f"Criar gift card de {value}"
        description = f"Clique aqui para criar um gift card de {value}."
        reply_markup = telebot.types.InlineKeyboardMarkup()
        button_text = "📝 Resgatar agora"
        button = telebot.types.InlineKeyboardButton(button_text, callback_data=f'resgatar {codigo}')
        reply_markup.row(button)
        if SUPORTA_COPY_TEXT:
            button_copiar = telebot.types.InlineKeyboardButton(
                "📋 Copiar código",
                copy_text=telebot.types.CopyTextButton(text=f'/resgatar {codigo}')
            )
            reply_markup.row(button_copiar)
        result_id = '1'
        try:
            result = telebot.types.InlineQueryResultArticle(
                id=result_id,
                title=title,
                description=description,
                input_message_content=telebot.types.InputTextMessageContent(txt, parse_mode='HTML'),
                reply_markup=reply_markup,
                thumbnail_url='https://cdn-icons-png.flaticon.com/512/612/612886.png'
            )
        except:
            result = telebot.types.InlineQueryResultArticle(
                id=result_id,
                title=title,
                description=description,
                input_message_content=telebot.types.InputTextMessageContent(txt, parse_mode='HTML'),
                reply_markup=reply_markup,
                thumb_url='https://cdn-icons-png.flaticon.com/512/612/612886.png'
            )
        bot.answer_inline_query(inline_query.id, [result], cache_time=0)
    else:
        value = inline_query.query.split(' ')[1]
        quantidade = inline_query.query.split(' ')[2]
        codigo = gerar_muito_gift(quantidade, value)
        txt = api.TextoInline.giftcard(None, codigo, quantidade, value)
        title = f"Criar {quantidade} gifts cards de R${float(value):.2f}"
        description = f"Clique aqui para criar {quantidade} gift card de R${float(value):.2f}."
        result_id = '3'
        reply_markup = None
        if SUPORTA_COPY_TEXT:
            codigos_lista = [c for c in codigo.strip().split('\n') if c]
            texto_copia = '\n'.join(f'/resgatar {c}' for c in codigos_lista)[:256]
            reply_markup = telebot.types.InlineKeyboardMarkup()
            button_copiar_lote = telebot.types.InlineKeyboardButton(
                "📋 Copiar todos os códigos",
                copy_text=telebot.types.CopyTextButton(text=texto_copia)
            )
            reply_markup.row(button_copiar_lote)
        try:
            result = telebot.types.InlineQueryResultArticle(
                id=result_id,
                title=title,
                description=description,
                input_message_content=telebot.types.InputTextMessageContent(txt, parse_mode='HTML'),
                reply_markup=reply_markup,
                thumbnail_url='https://cdn-icons-png.flaticon.com/512/1261/1261149.png'
            )
        except:
            result = telebot.types.InlineQueryResultArticle(
                id=result_id,
                title=title,
                description=description,
                input_message_content=telebot.types.InputTextMessageContent(txt, parse_mode='HTML'),
                reply_markup=reply_markup,
                thumb_url='https://cdn-icons-png.flaticon.com/512/1261/1261149.png'
            )
        bot.answer_inline_query(inline_query.id, [result])
def gerar_muito_gift(quantidade, valor):
    codigos = ''
    for i in range(int(quantidade)):
        while True:
            codigo = random.choices(string.ascii_uppercase + string.digits, k=9)
            codigo = ''.join(codigo)
            if api.GiftCard.validar_gift(codigo)[0] == False:
                api.GiftCard.create_gift(codigo, float(valor))
                codigos += f'\n{codigo}'
                break
            else:
                continue
    return codigos
def gerar_gift_card(valor):
    while True:
        codigo = random.choices(string.ascii_uppercase + string.digits, k=9)
        codigo = ''.join(codigo)
        if api.GiftCard.validar_gift(codigo)[0] == False:
            api.GiftCard.create_gift(codigo, float(valor))
            break
        else:
            continue
    return f'R${int(valor)},00', codigo
@bot.inline_handler(lambda query: query.query.startswith('CREATEPIX '))
def create_pix(query):
    if api.Admin.verificar_admin(query.from_user.id) == False and int(api.CredentialsChange.id_dono()) != int(query.from_user.id):
        return
    valor = query.query.split(' ')[1]
    payment = api.CriarPixPromissePay.gerar(valor, "inline")
    id_pag = payment['id']
    pix_copia_cola = payment['qr_code']
    txt = api.TextoInline.pix_gerado_inline(valor, pix_copia_cola, id_pag)
    title = f'Criar um pix de R${float(valor):.2f}'
    descricao = f'Clique aqui para gerar um pix de R${float(valor):.2f}'
    markup = InlineKeyboardMarkup([[InlineKeyboardButton('⏰ Aguardando Pagamento...', callback_data='aguardando')]])
    try:
        result = types.InlineQueryResultArticle(id='9', title=title, description=descricao, input_message_content=types.InputTextMessageContent(txt, parse_mode='HTML'), thumbnail_url='https://devtools.com.br/img/pix/logo-pix-png-icone-520x520.png', reply_markup=markup)
    except:
        result = types.InlineQueryResultArticle(id='9', title=title, description=descricao, input_message_content=types.InputTextMessageContent(txt, parse_mode='HTML'), thumb_url='https://devtools.com.br/img/pix/logo-pix-png-icone-520x520.png', reply_markup=markup)
    bot.answer_inline_query(query.id, [result], cache_time=0)
    verificar_inline_payment(id_pag, valor, query.from_user.id)
def verificar_inline_payment(id_pag: str, valor: float, user_id: int):
    import time
    from app.database import get_user_balance, add_saldo, add_pagamento
    from pytz import timezone as pytz_timezone
    from datetime import datetime
    admin_id = int(api.CredentialsChange.id_dono())
    tz = pytz_timezone('America/Sao_Paulo')
    start_time = time.time()
    timeout = 15 * 60   
    while True:
        if time.time() - start_time >= timeout:
            aviso = (
                f"⏰ *Timeout de Pagamento* ⏰\n\n"
                f" Usuário: `{user_id}`\n"
                f"💵 Valor gerado: `R${valor:.2f}`\n"
                f"🆔 Pagamento ID: `{id_pag}`\n\n"
                "O pagamento não foi concluído em 15 minutos."
            )
            bot.send_message(chat_id=admin_id, text=aviso, parse_mode='Markdown')
            # ALERTA DETALHADO AO ADM
            alertar_adm_pix_nao_pago(bot, user_id, valor)
            break
        time.sleep(5)
        try:
            result = api.CriarPixPromissePay.consultar(id_pag)
            status = str(result.get("status", "")).upper()
        except Exception as e:
            print(f"[verificar_inline_payment] erro ao consultar {id_pag}: {e}")
            continue
        if status == "PAID":
            try:
                min_bonus = float(api.CredentialsChange.BonusPix.valor_minimo_para_bonus())
                bonus_pct = float(api.CredentialsChange.BonusPix.quantidade_bonus())
            except:
                min_bonus, bonus_pct = float("inf"), 0.0
            if valor >= min_bonus:
                bonus_amt = valor * bonus_pct / 100
                saldo_deposito = valor + bonus_amt
            else:
                saldo_deposito = valor
            before = get_user_balance(user_id)
            add_saldo(user_id, saldo_deposito)
            add_pagamento(user_id, valor, id_pag)
            after = get_user_balance(user_id)
            print(f"[verificar_inline_payment] saldo de {user_id}: {before} -> {after}")
            texto_user = api.TextoInline.pagamento_aprovado(None, valor, id_pag)
            bot.send_message(chat_id=user_id, text=texto_user, parse_mode='HTML')
            now = datetime.now(tz).strftime("%d/%m/%Y %H:%M:%S")
            try:
                chat_info = bot.get_chat(user_id)
                if chat_info.username:
                    usuario_tag = f"@{chat_info.username} ({user_id})"
                elif chat_info.first_name:
                    usuario_tag = f"{chat_info.first_name} ({user_id})"
                else:
                    usuario_tag = f"{user_id}"
            except Exception:
                usuario_tag = f"{user_id}"
            texto_adm = (
                f"💰 *Depósito Aprovado*\n\n"
                f"👤 Usuário: `{usuario_tag}`\n"
                f"💵 Valor: `R${valor:.2f}`\n"
                f"➕ Bônus: `R${(saldo_deposito - valor):.2f}`\n"
                f"��� Saldo antes: `R${before:.2f}`\n"
                f"🏦 Saldo depois: `R${after:.2f}`\n"
                f"🕒 Data/Hora: `{now}`"
            )
            bot.send_message(chat_id=admin_id, text=texto_adm, parse_mode='Markdown')
            break
        elif status in ("CANCELLED", "CANCELED", "EXPIRED", "FAILED"):
            texto_cancel = api.TextoInline.pagamento_expirado(None, id_pag, f"{valor:.2f}")
            bot.send_message(chat_id=user_id, text=texto_cancel, parse_mode='HTML')
            try:
                chat = bot.get_chat(user_id)
                nome = f"@{chat.username}" if chat.username else chat.first_name or str(user_id)
            except:
                nome = str(user_id)
            aviso = (
                f"⚠️ *PIX Não Pago / Expirado*\n\n"
                f"👤 Usuário: `{nome}` (`{user_id}`)\n"
                f"💵 Valor gerado: `R${valor:.2f}`\n"
                f"🆔 Pagamento ID: `{id_pag}`"
            )
            bot.send_message(chat_id=admin_id, text=aviso, parse_mode='Markdown')
            # ALERTA DETALHADO AO ADM
            alertar_adm_pix_nao_pago(bot, user_id, valor)
            break
@bot.message_handler(commands=['resgatar'])
def redeem_gift(message):
    if api.Admin.verificar_vencimento() == True:
        ver_se_expirou()
        return
    msg = message.text.strip().split()
    if len(msg) != 2:
        bot.reply_to(message, "Erro, envie no formato correto.\nex: /resgatar 1isjue")
        return
    codigo = msg[1]
    processar_resgate(message.chat.id, codigo)
def processar_resgate(id, codigo):
    verif, valor = api.GiftCard.validar_gift(codigo)
    if verif == True:
        # 1. TRATAMENTO DE ERRO DO VALOR
        # Garante que o valor do gift vire número sem quebrar o bot
        try:
            if isinstance(valor, str):
                valor_float = float(valor.upper().replace('R$', '').replace(' ', '').replace(',', '.'))
            else:
                valor_float = float(valor)
        except Exception:
            # Se não conseguir converter o valor, para o resgate para não dar crash
            return
        # 2. CARREGA OS DADOS DO USUÁRIO
        user_data = load_user_data(id)
        if user_data is None:
            user_data = {
                "id": id,
                "status": "approved",
                "saldo": 0.0,
                "compras": [],
                "pagamentos": [],
                "whatsapp": "Não informado"
            }
        if 'saldo' not in user_data:
            user_data['saldo'] = 0.0
        # 3. SALVA O SALDO ANTES DE DELETAR O GIFT
        user_data['saldo'] += valor_float
        # --- NOVA LÓGICA: SALVAR DATA DO GIFT PARA O RELATÓRIO ---
        from datetime import datetime
        import pytz
        tz_brasil = pytz.timezone('America/Sao_Paulo')
        data_hora_resgate_historico = datetime.now(tz_brasil).strftime("%d/%m/%Y às %H:%M:%S")
        if 'historico_gifts' not in user_data:
            user_data['historico_gifts'] = []
        user_data['historico_gifts'].append({
            'valor': valor_float,
            'data': data_hora_resgate_historico,
            'codigo': codigo
        })
        # --- CORREÇÃO: soma no total histórico usado no relatório ---
        # (campo lido por api.InfoUser.gifts_resgatados / "Total Histórico")
        user_data['gift_redeemed'] = user_data.get('gift_redeemed', 0.0) + valor_float
        # ---------------------------------------------------------
        try:
            save_user_data(id, user_data)
        except Exception:
            return # Se falhar ao salvar, para tudo e o gift fica intacto.
        # 4. DELETA O GIFT SOMENTE SE CHEGOU ATÉ AQUI COM SUCESSO
        api.GiftCard.del_gift(codigo)
        # Obtém o nome do usuário e o novo saldo para a mensagem
        try:
            chat_info = bot.get_chat(id)
            user_first_name = chat_info.first_name
        except Exception:
            user_first_name = "Cliente"
        novo_saldo = user_data.get('saldo', 0.0)
        # Monta o texto detalhado
        texto_usuario = (
            f"✅ <b>Gift Card Resgatado com Sucesso!</b>\n\n"
            f"Olá, {user_first_name}!\n\n"
            f"Seu saldo foi atualizado com os créditos do Gift Card.\n\n"
            f"🧾 <b>Detalhes do Resgate:</b>\n"
            f" • <b>Valor Adicionado:</b> R$ {valor_float:.2f}\n"
            f" • <b>Código Utilizado:</b> <code>{codigo}</code>\n\n"
            f"💰 <b>Seu Novo Saldo é: R$ {novo_saldo:.2f}</b>\n\n"
            f"Agora você já pode explorar nossos produtos e fazer suas compras!"
        )
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🛍️ Ver Produtos", callback_data="servicos"))
        # Envia a mensagem pro usuário (com try para não dar crash se tiver em grupo)
        try:
            bot.send_message(
                int(id),
                texto_usuario,
                parse_mode='HTML',
                reply_markup=markup
            )
        except Exception:
            pass
        # Prepara os dados para a notificação do admin
        saldo_anterior = novo_saldo - valor_float
        try:
            chat_info = bot.get_chat(id)
            user_display_name = chat_info.first_name or ""
            user_username = f"@{chat_info.username}" if chat_info.username else "Não definido"
        except Exception:
            user_display_name = "Não encontrado"
            user_username = "Não encontrado"
        from datetime import datetime
        import pytz
        tz_brasil = pytz.timezone('America/Sao_Paulo')
        data_hora_resgate = datetime.now(tz_brasil).strftime("%d/%m/%Y às %H:%M:%S")
        # Monta o texto detalhado para o admin
        texto_admin = (
            f"<b>🎁 Gift Card Resgatado</b>\n\n"
            f"���� <b>Detalhes do Usuário:</b>\n"
            f" • <b>Nome:</b> {user_display_name}\n"
            f" • <b>Username:</b> {user_username}\n"
            f" • <b>ID:</b> <code>{id}</code>\n\n"
            f"🎟️ <b>Detalhes do Gift Card:</b>\n"
            f" • <b>Valor do Gift:</b> R$ {valor_float:.2f}\n"
            f" • <b>Código:</b> <code>{codigo}</code>\n\n"
            f"📊 <b>Atualização de Saldo:</b>\n"
            f" • <b>Saldo Anterior:</b> R$ {saldo_anterior:.2f}\n"
            f" • <b>Saldo Atual:</b> R$ {novo_saldo:.2f}\n\n"
            f"🕐 <b>Data/Hora:</b> {data_hora_resgate}"
        )
        # --- NOTIFICAÇÃO PARA ADMIN ---
        try:
            dono_id = api.CredentialsChange.id_dono()
            try:
                fotos_user = bot.get_user_profile_photos(id)
                foto_id = fotos_user.photos[0][-1].file_id if fotos_user.total_count > 0 else None
            except:
                foto_id = None
            try:
                if foto_id: 
                    bot.send_photo(dono_id, foto_id, caption=texto_admin, parse_mode='HTML')
                else: 
                    bot.send_message(dono_id, texto_admin, parse_mode='HTML')
            except Exception: 
                pass
        except Exception:
            pass
    else:
        try:
            bot.send_message(id, "Gift card inválido ou já resgatado!")
        except:
            pass
        return
@bot.message_handler(commands=['format'])
def formatar_msg(message):
    if api.Admin.verificar_vencimento() == True:
        ver_se_expirou()
        return
    txt = message.text
    txt = txt.replace('\n', '\n').split()[1:]
    txt = ' '.join(txt)
    print(txt)
    bot.send_message(message.chat.id, txt)
@bot.message_handler(commands=['adicionar_texto'])
def handle_adicionar_texto(message):
    msg = message.text
    msg = msg.replace('/adicionar_texto', '')
    if len(msg.split(f'{api.CredentialsChange.separador()}')) != 3:
        bot.reply_to(
            message,
            f'Formato incorreto! A mensagem deve estar no formato:\nTEXTO{api.CredentialsChange.separador()}NOME DO BOTÃO{api.CredentialsChange.separador()}URL DO BOTÃO'
        )
        return
    with open('mensagem_transmissora.txt', 'w') as f:
        f.write(msg)
    bot.reply_to(message, "Alterado com sucesso!")
@bot.inline_handler(lambda query: query.query.startswith('MENSAGEM'))
def inline_message(query):
    if api.Admin.verificar_admin(query.from_user.id) == False and int(api.CredentialsChange.id_dono()) != int(query.from_user.id):
        return
    try:
        with open('mensagem_transmissora.txt',  'r') as f:
            data = f.read()
    except:
        with open('mensagem_transmissora.txt',  'w') as f:
            f.write('')
        with open('mensagem_transmissora.txt',  'r') as f:
            data = f.read()
    if len(data) <= 1:
        try:
            result = types.InlineQueryResultArticle(
                id='110',
                title='Defina uma mensagem!',
                description='tem nenhuma mensagem registrada, clique aqui e veja as instruções.',
                input_message_content=types.InputTextMessageContent(
                    f"Para definir uma mensagem você deve usar o seguinte comando neste formato:\n\n"
                    f"<code>/adicionar_texto TEXTO{api.CredentialsChange.separador()}NOME BOTÃO{api.CredentialsChange.separador()}URL BOTÃO</code>\n\n"
                    f"Você pode usar <a href=\"http://telegram.me/MDtoHTMLbot?start=html\">HTML.</a> "
                    f"Após definir o seu texto, basta dar o mesmo comando inline <code>@{api.CredentialsChange.user_bot()} MENSAGEM</code> - "
                    f"Isso você pode utilizar em qualquer chat, para enviar uma mensagem com botão a partir do seu perfil. "
                    f"E para redefinir a mensagem, basta dar o mesmo comando",
                    parse_mode='HTML'
                ),
                thumbnail_url='https://compras.wiki.ufsc.br/images/5/56/Erro.png'
            )
        except:
            result = types.InlineQueryResultArticle(
                id='110',
                title='Defina uma mensagem!',
                description='Você não tem nenhuma mensagem registrada, clique aqui e veja as instruções.',
                input_message_content=types.InputTextMessageContent(
                    f"Para definir uma mensagem você deve usar o seguinte comando neste formato:\n\n"
                    f"<code>/adicionar_texto TEXTO{api.CredentialsChange.separador()}NOME BOTÃO{api.CredentialsChange.separador()}URL BOTÃO</code>\n\n"
                    f"Você pode usar <a href=\"http://telegram.me/MDtoHTMLbot?start=html\">HTML.</a> "
                    f"Após definir o seu texto, basta dar o mesmo comando inline <code>@{api.CredentialsChange.user_bot()} MENSAGEM</code> - "
                    f"Isso você pode utilizar em qualquer chat, para enviar uma mensagem com botão a partir do seu perfil. "
                    f"E para redefinir a mensagem, basta dar o mesmo comando",
                    parse_mode='HTML'
                ),
                thumb_url='https://compras.wiki.ufsc.br/images/5/56/Erro.png'
            )
    else:
        p = data.replace('/adicionar_texto', '')
        p = p.split(f'{api.CredentialsChange.separador()}')
        text = p[0]
        nome_botao = p[1]
        url_botao = p[2]
        markup = InlineKeyboardMarkup([[InlineKeyboardButton(f'{nome_botao}', url=f'{url_botao}')]])
        title = 'Enviar mensagem'
        description = 'Clique aqui para enviar uma mensagem com botão!'
        try:
            result = types.InlineQueryResultArticle(
                id=str(random.randint(1, 99999)),
                title=title,
                description=description,
                input_message_content=types.InputTextMessageContent(f'{text}', parse_mode='HTML'),
                reply_markup=markup,
                thumbnail_url='https://png.pngtree.com/png-vector/20190217/ourlarge/pngtree-vector-send-message-icon-png-image_558846.jpg'
            )
        except:
            result = types.InlineQueryResultArticle(
                id=str(random.randint(1, 99999)),
                title=title,
                description=description,
                input_message_content=types.InputTextMessageContent(f'{text}', parse_mode='HTML'),
                reply_markup=markup,
                thumb_url='https://png.pngtree.com/png-vector/20190217/ourlarge/pngtree-vector-send-message-icon-png-image_558846.jpg'
            )
    bot.answer_inline_query(query.id, [result], cache_time=0)
# ==========================================================
@bot.callback_query_handler(func=lambda call: call.data == 'check_subscription')
def callback_check_subscription(call):
    """Botão para o usuário confirmar que entrou no canal."""
    try:
        if verificar_inscricao_canal(call.from_user.id):
            bot.answer_callback_query(call.id, "✅ Inscrição confirmada!")
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except: pass
            # Simula o comando /start novamente para ir para a próxima etapa (telefone ou menu)
            call.message.from_user = call.from_user
            handle_start(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ Você ainda não entrou no canal!", show_alert=True)
    except Exception as e:
        print(f"Erro no check_subscription: {e}")
@bot.message_handler(commands=['start', f'start@{api.CredentialsChange.user_bot()}'])
def handle_start(message):
    # Sistema anti-flood centralizado
    if anti_flood.verificar_flood_start(message.from_user.id):
        anti_flood.enviar_aviso_flood_start(bot, message, ADMIN_ID)
        return
    if api.Admin.verificar_vencimento():
        ver_se_expirou()
        return
    user_id = message.from_user.id
    # Tenta limpar mensagem anterior
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception:
        pass
    # Verificações de Segurança (Ban e Manutenção)
    if api.InfoUser.verificar_ban(message.from_user.id):
        bot.send_message(message.chat.id, "🚫 Você está banido deste bot e não pode utilizá-lo!")
        return
    if is_on():
        if not (api.Admin.verificar_admin(message.from_user.id) or int(message.from_user.id) == int(api.CredentialsChange.id_dono())):
            maintenance_msg = get_maintenance_message()
            bot.send_message(chat_id=message.chat.id, text=maintenance_msg, allow_sending_without_reply=True)
            return
        bot.send_message(chat_id=message.chat.id, text="🔧 O bot está em manutenção, mas você foi identificado como administrador!", allow_sending_without_reply=True)
    elif api.CredentialsChange.status_manutencao():
        if not api.Admin.verificar_admin(message.from_user.id) and api.CredentialsChange.id_dono() != int(message.from_user.id):
            bot.send_message(chat_id=message.chat.id, text="🔧 O bot está em manutenção, voltaremos em breve!", allow_sending_without_reply=True)
            return
        bot.send_message(chat_id=message.chat.id, text="🔧 O bot está em manutenção, mas você foi identificado como administrador!", allow_sending_without_reply=True)
    # ==================================================================
    # LÓGICA 1: VERIFICAÇÃO DE CANAL (NOVO - PRIORIDADE ALTA)
    # ==================================================================
    if not canal_manager.verificar_inscricao_canal(user_id):
        texto_canal = (
            "👋 <b>Olá! Bem-vindo(a).</b>\n\n"
            "🔒 Para acessar nossa loja e usar o bot, você precisa entrar em nosso <b>Canal Oficial</b>.\n\n"
            "Clique no botão abaixo para entrar e depois confirme."
        )
        markup_canal = canal_manager.obter_markup_canal()
        bot.send_message(message.chat.id, texto_canal, parse_mode='HTML', reply_markup=markup_canal)
        return # PARA AQUI SE NÃO TIVER NO CANAL
    # Carrega dados do usuário (necessário para checar telefone e termos)
    user_data = load_user_data(user_id)
    # ==================================================================
    # LÓGICA 2: VERIFICAÇÃO DE WHATSAPP (EXISTENTE - PRIORIDADE MÉDIA)
    # ==================================================================
    # Se o usuário não existe ou não tem o campo 'whatsapp' salvo
    if not user_data or not user_data.get('whatsapp'):
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        button_phone = types.KeyboardButton(text="📲 Enviar WhatsApp (Obrigatório)", request_contact=True)
        markup.add(button_phone)
        bot.send_message(
            message.chat.id, 
            "✅ <b>Canal verificado!</b>\n\n"
            "Agora, para finalizar seu acesso e garantir a segurança, precisamos validar seu cadastro.\n\n"
            "👇 <b>Clique no botão abaixo para compartilhar seu WhatsApp.</b>", 
            parse_mode='HTML', 
            reply_markup=markup
        )
        # Processar referência de afiliado se presente
        if not user_data:
            afiliados_sistema.processar_comando_start_com_referencia(message, bot)
        return # PARA AQUI SE NÃO TIVER TELEFONE
    # Checa Termos de Uso (V2)
    try:
        if _th_pending(user_id) or _th_need_after_inc(user_id):
            _th_show(message.chat.id)
            return
    except Exception as e:
        print("[TERMS] Erro no /start:", e)
    # Notifica admin de acesso usando o novo módulo (Autoexclusão em 5s)
    try:
        notificacao_acesso.notificar_admin_acesso(bot, message, ADMIN_ID)
    except Exception as e:
        print(f"Erro ao chamar notificação de acesso: {e}")
    # Exibe Menu Principal
    markup = gerar_menu_principal(message)
    texto = api.Textos.start(message)
    from app import interface as fotos_menus
    bot.send_photo(
        chat_id=message.chat.id,
        photo=fotos_menus.obter_foto_menu('start') or api.FOTO_MENU_PRINCIPAL,
        caption=texto,
        parse_mode='HTML',
        reply_markup=markup
    )
    # --- LÓGICA DE LEMBRETE MELHORADA (MENOS FREQUENTE) ---
    # 1. Cancela timer anterior se já existir (evita mensagens acumuladas)
    if message.chat.id in pending_reminders:
        try:
            pending_reminders[message.chat.id].cancel()
        except:
            pass
    # 2. Tempo aumentado para 30 minutos (1800 segundos)
    # Isso fará a mensagem aparecer MUITO menos
    timer = Timer(600, remind_no_purchase, args=(message.chat.id,))
    timer.daemon = True
    timer.start()
    pending_reminders[message.chat.id] = timer
@bot.message_handler(content_types=['contact'])
def receber_contato(message):
    if not message.contact:
        return
    user_id = message.from_user.id
    # Verifica se o contato enviado pertence ao próprio usuário (anti-fraude básico)
    if message.contact.user_id != user_id:
        bot.reply_to(message, "❌ Por favor, envie o <b>seu próprio</b> contato usando o botão abaixo.", parse_mode='HTML')
        return
    phone_number = message.contact.phone_number
    user_data = load_user_data(user_id)
    eh_novo_usuario = False
    # Remove o teclado de pedir contato
    remove_kb = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "✅ Contato recebido com sucesso!", reply_markup=remove_kb)
    if not user_data:
        eh_novo_usuario = True
        # Cria o usuário
        user_data = {
            "id": user_id,
            "status": "approved",
            "saldo": 0.0,
            "compras": [],
            "pagamentos": [],
            "data_registro": time.strftime("%d/%m/%Y %H:%M:%S"),
            "whatsapp": phone_number 
        }
        # Aplica bônus
        try:
            bonus_registro = float(api.CredentialsChange.BonusRegistro.bonus())
            if bonus_registro > 0:
                user_data['saldo'] = bonus_registro
                bot.send_message(user_id, f"🎉 Bem-vindo! Você ganhou um bônus inicial de R${bonus_registro:.2f}!")
        except Exception:
            pass
        # --- NOTIFICAÇÃO (NOVO USUÁRIO) ---
        try:
            dono_id = api.CredentialsChange.id_dono()
            canal_id = -1002787400901
            u_tag = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
            # 1. DONO (Completo)
            msg_dono = (
                f"👤 <b>NOVO USUÁRIO REGISTRADO!</b>\n\n"
                f"<b>Nome:</b> {message.from_user.first_name}\n"
                f"<b>User:</b> {u_tag}\n"
                f"<b>ID:</b> <code>{user_id}</code>\n"
                f"<b>Zap:</b> <code>{phone_number}</code>"
            )
            # 2. CANAL (Simples com Foto)
            msg_canal = f"👤 Novo usuário cadastrado: {u_tag}"
            fotos = bot.get_user_profile_photos(user_id)
            foto_id = fotos.photos[0][-1].file_id if fotos.total_count > 0 else None
            # Envia Dono
            try:
                if foto_id: bot.send_photo(dono_id, foto_id, caption=msg_dono, parse_mode='HTML')
                else: bot.send_message(dono_id, msg_dono, parse_mode='HTML')
            except: pass
            # Envia Canal (Com foto se tiver)
            try:
                if foto_id: bot.send_photo(canal_id, foto_id, caption=msg_canal)
                else: bot.send_message(canal_id, msg_canal)
            except Exception as e: print(f"Erro canal user: {e}")
        except Exception as e:
            print(f"Erro ao notificar novo usuario: {e}")
        # ------------------------------------------
    else:
        # Usuário já existia mas não tinha zap salvo, apenas atualiza
        user_data['whatsapp'] = phone_number
    save_user_data(user_id, user_data)
    # ==================================================================
    # NOTIFICAÇÃO DETALHADA PARA O DONO (Novo WhatsApp)
    # ==================================================================
    try:
        id_dono = api.CredentialsChange.id_dono()
        # Coleta dados para exibição
        first_name = message.from_user.first_name or "Sem Nome"
        username = f"@{message.from_user.username}" if message.from_user.username else "Sem User"
        data_atual = time.strftime('%d/%m/%Y %H:%M:%S')
        texto_notificacao = (
            f"📲 <b>NOVO WHATSAPP CADASTRADO!</b>\n\n"
            f"👤 <b>Nome:</b> {first_name}\n"
            f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
            f"�� <b>Username:</b> {username}\n"
            f"📞 <b>WhatsApp:</b> <code>{phone_number}</code>\n"
            f"📅 <b>Data:</b> {data_atual}"
        )
        bot.send_message(id_dono, texto_notificacao, parse_mode='HTML')
    except Exception as e:
        print(f"Erro ao notificar dono sobre novo whatsapp: {e}")
    # ==================================================================
    # Segue o fluxo de mostrar o menu
    try:
        # Verifica se precisa mostrar os termos (se a função existir no contexto)
        if '_th_pending' in globals() and (_th_pending(user_id) or _th_need_after_inc(user_id)):
            _th_show(message.chat.id)
            return
    except: pass
    convidar_se_primeira_vez(user_id)
    markup = gerar_menu_principal(message)
    texto = api.Textos.start(message)
    from app import interface as fotos_menus
    bot.send_photo(
        chat_id=message.chat.id,
        photo=fotos_menus.obter_foto_menu('start') or api.FOTO_MENU_PRINCIPAL,
        caption=texto,
        parse_mode='HTML',
        reply_markup=markup
    )
def convidar_se_primeira_vez(user_id: int):
    ud = load_user_data(user_id)
    if ud is None:
        try:
            api.InfoUser.novo_usuario(user_id)    
        except AttributeError:
            from app import central                      
            central.novo_usuario(user_id)
        ud = load_user_data(user_id)           
    if not ud.get("invite_sent", False):
        bot.send_message(
            user_id,
            "⚠️ Para ficar por dentro das novidades, entre no nosso grupo!\n"
            "Depois é só continuar usando o bot normalmente 😉",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔗 Entrar no Grupo", url=JOIN_GROUP_LINK)
            )
        )
        ud["invite_sent"] = True
        save_user_data(user_id, ud)               
# COLE ESTE NOVO BLOCO DE CÓDIGO NO LUGAR DO ANTIGO
from app import interface as perfil_manager
def perfil(message):
    perfil_manager.exibir_perfil(message, bot, api, load_user_data)
ultimo_menu = {}
def enviar_menu_inicial(message):
    texto = api.Textos.start(message)
    markup = gerar_menu_principal(message)  
    if message.chat.id in ultimo_menu:
        try:
            bot.delete_message(message.chat.id, ultimo_menu[message.chat.id])
        except Exception as e:
            print(f"Erro ao deletar mensagem anterior: {e}")
    from app import interface as fotos_menus
    nova_msg = bot.send_photo(
        chat_id=message.chat.id,
        photo=fotos_menus.obter_foto_menu('start') or api.FOTO_MENU_PRINCIPAL,
        caption=texto,
        parse_mode='HTML',
        reply_markup=markup
    )
    ultimo_menu[message.chat.id] = nova_msg.message_id
@bot.callback_query_handler(func=lambda c: c.data == 'menu_start')
def callback_menu_start(call):
    abrir_menu_principal(call.message)    
    bot.answer_callback_query(call.id)
@bot.callback_query_handler(func=lambda call: call.data == 'menu_premios')
def callback_menu_premios(call):
    from app.interface import gerar_menu_premios 
    bot.answer_callback_query(call.id)
    texto = (
        "🎁 <b>Central de Prêmios e Vantagens!</b>\n\n"
        "Use o bot ao seu favor e ganhe recompensas incríveis. "
        "Escolha uma das opções abaixo para aproveitar:"
    )
    from app import interface as fotos_menus
    if fotos_menus.exibir_com_foto_opcional(
        bot, call.message.chat.id, call.message.message_id, 'menu_premios', texto,
        reply_markup=gerar_menu_premios()
    ):
        return
    try:
        api.editar_menu_seguro(
            bot,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            texto=texto,
            reply_markup=gerar_menu_premios(),
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Erro ao abrir menu de prêmios: {e}")
# ADICIONE ESTE NOVO HANDLER JUNTO COM OS OUTROS @bot.callback_query_handler:
@bot.callback_query_handler(func=lambda call: call.data == 'mostrar_menu_vendas')
def callback_mostrar_menu_vendas(call):
    """
    Como os menus foram unificados, este handler agora age como um redirecionamento seguro 
    para o Menu Principal toda vez que alguém clicar na seta "Voltar" nas telas de produtos.
    """
    try:
        abrir_menu_principal(call.message)
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"Erro ao voltar para o menu principal: {e}")
        bot.answer_callback_query(call.id, "Erro ao abrir o menu.", show_alert=True)
@bot.callback_query_handler(func=lambda call: call.data == 'mostrar_carrinho')
def callback_mostrar_carrinho(call):
    """
    Handler para o botão 'Carrinho' do menu de vendas.
    """
    user_id = call.from_user.id
    # 1. Responde à Callback Query IMEDIATAMENTE para tirar o reloginho do botão
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass
    # 2. Tenta processar o carrinho e atualizar a UI.
    try:
        cart_show_products(user_id, 0, call.message)
        _schedule_cart_expire(user_id)
    except telebot.apihelper.ApiTelegramException as e:
        error_str = str(e).lower()
        # IGNORA o erro se o Telegram avisar que a mensagem já é idêntica
        if "message is not modified" in error_str:
            pass 
        # Tenta enviar nova mensagem se o ID da mensagem sumiu
        elif "invalid message key/id" in error_str or "message to edit not found" in error_str:
            print("Fallback: Mensagem original não encontrada, enviando alerta.")
            try:
                bot.send_message(call.message.chat.id, "🛒 <b>Seu Carrinho:</b>\n\n(Digite /menu para voltar se não carregou os itens)", parse_mode="HTML")
            except Exception:
                pass
        else:
            print(f"Erro da API do Telegram ao abrir carrinho: {e}")
            bot.send_message(call.message.chat.id, "⚠️ Erro ao tentar abrir o carrinho. Digite /menu e tente novamente.")
    except Exception as e:
        print(f"Erro genérico ao mostrar carrinho/produtos: {e}")
        bot.send_message(call.message.chat.id, "⚠️ Ocorreu um erro inesperado. Digite /menu e tente novamente.")
def menu_categorias_servicos(message):
    servicos = api.ControleLogins.pegar_servicos()
    count_conta = count_tela = count_outros = 0
    ja_foram = []
    for servico in servicos:
        nome = servico["nome"]
        if nome not in ja_foram:
            nome_lower = nome.lower()
            if "conta" in nome_lower:
                count_conta += 1
            elif "tela" in nome_lower:
                count_tela += 1
            else:
                count_outros += 1
            ja_foram.append(nome)
    markup = InlineKeyboardMarkup()
    bt_conta = InlineKeyboardButton(
        f'🛒 CONTAS COMPLETAS ({count_conta})',
        callback_data='servicos_categoria conta'
    )
    bt_tela = InlineKeyboardButton(
        f'📲 TELAS ({count_tela})',
        callback_data='servicos_categoria tela'
    )
    bt_outros = InlineKeyboardButton(
        f'🛒 OUTROS ({count_outros})',
        callback_data='servicos_categoria outros'
    )
    bt_alertas = InlineKeyboardButton('🔔 MEUS ALERTAS', callback_data='alertas_user')
    bt_logins = InlineKeyboardButton('📦 MEU ESTOQUE', callback_data='mostrar_logins')
    bt_voltar = InlineKeyboardButton("⟨⟨", callback_data='menu_start')
    markup.add(bt_conta)
    markup.row(bt_tela, bt_outros)
    markup.add(bt_logins) 
    markup.add(bt_alertas)
    markup.add(bt_voltar)
    # Novo Código para Substituir (dentro da função menu_categorias_servicos):
# =====================================================================
    # ... (código para pegar counts e criar markup permanece o mesmo) ...
    gif_url, texto = ler_texto_e_gif("categoriasservicos") # Pega a URL e o texto/caption
    try:
        # Tenta editar a mídia e a legenda da mensagem existente
        # Nota: Editar de texto para animação ou vice-versa pode falhar.
        #       Se a mensagem anterior era texto, editamos o texto.
        #       Se era mídia (foto/animação), editamos a legenda.
        media_changed = False
        if getattr(message, 'animation', None) or getattr(message, 'photo', None):
             # Se a mensagem atual já tem mídia, tentamos editar a legenda e o markup
             try:
                 bot.edit_message_caption(
                     caption=texto,
                     chat_id=message.chat.id,
                     message_id=message.message_id,
                     reply_markup=markup,
                     parse_mode="HTML"
                 )
                 media_changed = True # Sinaliza que a legenda foi editada
             except Exception as edit_caption_error:
                 if 'message is not modified' in str(edit_caption_error).lower():
                     return # Se não mudou nada, ok.
                 print(f"Falha ao editar legenda, tentando editar texto: {edit_caption_error}")
                 # Continua para tentar editar o texto se a edição da legenda falhar
        if not media_changed:
            # Se não havia mídia antes, ou se editar legenda falhou, tenta editar o texto
            bot.edit_message_text(
                text=texto,
                chat_id=message.chat.id,
                message_id=message.message_id,
                reply_markup=markup,
                parse_mode="HTML"
            )
    except Exception as e:
        # Se qualquer edição falhar (exceto "não modificado"), envia uma nova mensagem como fallback
        if 'message is not modified' not in str(e).lower():
            print(f"Erro ao editar para menu de categorias, enviando nova mensagem/animação: {e}")
            try:
                # Tenta enviar a animação primeiro
                bot.send_animation(
                    chat_id=message.chat.id,
                    animation=gif_url,
                    caption=texto,
                    parse_mode="HTML",
                    reply_markup=markup
                )
            except Exception as send_anim_error:
                # Se enviar animação falhar, envia só o texto
                print(f"Erro ao enviar animação no fallback, enviando texto: {send_anim_error}")
                bot.send_message(
                    chat_id=message.chat.id,
                    text=texto,
                    parse_mode="HTML",
                    reply_markup=markup
                )
# =====================================================================
# NOVO HANDLER PARA PAGINAÇÃO DE CATEGORIAS
@bot.callback_query_handler(func=lambda c: c.data.startswith('servicos_cat_page_'))
def callback_servicos_cat_page(call):
    """
    Este handler captura os cliques nos botões 'Anterior' e 'Próximo' das listas de CATEGORIA.
    Formato esperado: servicos_cat_page_CATEGORIA_PAGINA
    """
    try:
        parts = call.data.split('_')
        categoria = parts[3] # Pega a categoria (ex: 'conta' ou 'tela')
        page = int(parts[4]) # Pega o número da página
        bot.answer_callback_query(call.id)
        # Chama a função servicos_por_categoria() novamente, passando a categoria e a nova página
        servicos_por_categoria(call.message, categoria, page=page)
    except Exception as e:
        print(f"Erro no callback_servicos_cat_page: {e}")
        bot.answer_callback_query(call.id, "Erro ao mudar de página.", show_alert=True)


# ==================== SERVICOS ESTOQUE ====================
def ler_texto_e_gif(nome_arquivo):
    caminho = os.path.join("textos", f"{nome_arquivo}.txt")
    gif_url = None
    caption = ""
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if lines:
            gif_url = lines[0].strip()
            caption = "".join(lines[1:]).strip()
    if not gif_url:
        gif_url = ""
    if not caption:
        caption = (
            "✨ <b>Selecione a categoria de serviços:</b> ✨\n\n"
            "👉 Escolha uma opção abaixo para visualizar os logins disponíveis!"
        )
    return gif_url, caption
def safe_edit_message(message, new_content, reply_markup=None):
    """
    Edita a mensagem do menu. A foto de boas-vindas (menu principal) é exclusiva
    dela mesma: se a mensagem atual tiver foto (ex: veio do menu principal),
    apaga e reenvia como texto puro, sem foto, ao navegar para outro menu.
    """
    try:
        if getattr(message, 'caption', None) is not None:
            raise ValueError("mensagem atual é foto; recriando como texto puro")
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=new_content,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    except Exception as e:
        error_str = str(e).lower()
        if "message is not modified" in error_str:
            return
        if "mensagem atual é foto" not in error_str:
            print("safe_edit_message error:", e)
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except Exception:
            pass
        bot.send_message(
            chat_id=message.chat.id,
            text=new_content,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
def voltar_menu_servicos(message):
    texto = api.Textos.menu_comprar(message)   
    markup = gerar_menu_principal()            
    safe_edit_message(message, texto, reply_markup=markup)
@bot.callback_query_handler(func=lambda c: c.data == 'voltar')
def callback_voltar(call):
    voltar_menu_servicos(call.message)
def servicos_por_categoria(message, categoria, page=1):
    """
    Filtra os serviços com a NOVA LÓGICA:
    - 'tela': Mostra apenas produtos com "tela" no nome.
    - 'conta': Mostra todos os produtos que NÃO têm "tela" no nome.
    - 'outros': (Se ainda for chamado) Não mostrará nada, pois 'conta' agora é o padrão.
    """
    servicos = api.ControleLogins.pegar_servicos()
    filtered_raw = []
    ja_foram = set() # Usar um set é mais eficiente
    for servico in servicos:
        nome = servico.get("nome") # Usar .get() para segurança
        if nome and nome not in ja_foram:
            nome_lower = nome.lower()
            # Lógica para "Telas"
            if categoria == "tela" and "tela" in nome_lower:
                filtered_raw.append((nome, servico))
                ja_foram.add(nome)
            # Lógica para "Contas"
            elif categoria == "conta" and "tela" not in nome_lower:
                filtered_raw.append((nome, servico))
                ja_foram.add(nome)
            # Lógica para "Outros"
            elif categoria == "outros" and "tela" not in nome_lower and "conta" not in nome_lower:
                pass 
    filtered_raw.sort(key=lambda x: x[0])
    # --- INÍCIO DA NOVA LÓGICA DE PAGINAÇÃO ---
    ITEMS_PER_PAGE = 10
    total_items = len(filtered_raw)
    if total_items == 0:
        total_pages = 1
    else:
        total_pages = math.ceil(total_items / ITEMS_PER_PAGE)
    page = max(1, min(page, total_pages))
    start_index = (page - 1) * ITEMS_PER_PAGE
    end_index = start_index + ITEMS_PER_PAGE
    produtos_da_pagina = filtered_raw[start_index:end_index]
    # --- FIM DA NOVA LÓGICA DE PAGINAÇÃO ---
    markup = InlineKeyboardMarkup()
    if not produtos_da_pagina:
        # Mensagem de "Sem Serviços"
        bt = InlineKeyboardButton("❌ SEM SERVIÇOS NESTA CATEGORIA", callback_data="noop")
        markup.add(bt)
    else:
        # Lista os serviços encontrados
        for nome, servico in produtos_da_pagina:
            valor = servico["valor"]
            # --- LINHA MODIFICADA ---
            try:
                # Busca o estoque atual para este serviço
                estoque = sum(1 for item in servicos if item.get("nome") == nome)
            except Exception:
                estoque = 0 # Define 0 em caso de erro
            # Monta o novo texto do botão com a quantidade
            nome_botao = f"{nome} R${float(valor):.2f} (Qnt: {estoque})"
            # --- FIM DA MODIFICAÇÃO ---
            markup.add(InlineKeyboardButton(nome_botao, callback_data=f"exibir_servico_cat {categoria} {nome}"))
    # --- INÍCIO DOS NOVOS BOTÕES DE NAVEGAÇÃO ---
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton("⬅️ Anterior", callback_data=f"servicos_cat_page_{categoria}_{page - 1}"))
    if total_pages > 1:
        nav_row.append(InlineKeyboardButton(f"Pág {page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton("Próxima ➡️", callback_data=f"servicos_cat_page_{categoria}_{page + 1}"))
    if nav_row:
        markup.row(*nav_row)
    # --- FIM DOS NOVOS BOTÕES DE NAVEGAÇÃO ---
    # --- INÍCIO DA MODIFICAÇÃO ---
    bt_pesq = InlineKeyboardButton('🔎 pesquisar logins', switch_inline_query_current_chat="buscar_loguin ")
    markup.row(bt_pesq)
    # --- FIM DA MODIFICAÇÃO ---
    # Botão de Voltar
    markup.add(InlineKeyboardButton('↩️ Voltar', callback_data='mostrar_menu_vendas'))
    # Define o título da categoria
    titulo_categoria = "Contas" if categoria == "conta" else categoria.capitalize()
    texto = f"<b>Serviços na categoria {titulo_categoria}:</b>"
    if total_pages > 1:
        texto += f"\n\n<b>Página {page} de {total_pages}</b>"
    from app import interface as fotos_menus
    if fotos_menus.exibir_com_foto_opcional(
        bot, message.chat.id, message.message_id, 'servicos_categoria', texto, reply_markup=markup
    ):
        return
    try:
        # A foto de boas-vindas é exclusiva do menu principal: se a mensagem atual
        # tiver foto (legenda), força o fallback abaixo para apagar e reenviar como texto puro.
        if hasattr(message, 'caption') and message.caption:
            raise ValueError("mensagem atual é foto; recriando como texto puro")
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=texto,
            parse_mode='HTML',
            reply_markup=markup
        )
    except Exception as e:
        # Fallback se a edição falhar (ou se vier da foto do menu principal)
        if 'message is not modified' not in str(e).lower():
            if 'mensagem atual é foto' not in str(e).lower():
                print(f"Erro ao editar para servicos_por_categoria, enviando nova: {e}")
            try:
                bot.delete_message(message.chat.id, message.message_id)
            except Exception:
                pass
            bot.send_message(
                chat_id=message.chat.id,
                text=texto,
                parse_mode='HTML',
                reply_markup=markup
            )
# Dicionário de emojis exclusivos para cada serviço
EMOJIS_SERVICOS = {
    "APPLE TV": "🍏",
    "CRUNCHYROLL": "🍥",
    "DISNEY": "🦄",
    "GLOBO ": "🌎",
    "GLOBO PREMIUM+3 ADICIONAIS": "➕",
    "GLOBO PREMIUM+COMBATE": "🥊",
    "GLOBO PREMIUM+PREMIERE": "⚽",
    "GLOBO PREMIUM+TELECINE": "🎬",
    "GLOBO PREMIUM 2 MESES": "⏳",
    "GLOBO PREMIUM": "💎",
    "GLOBO+PREMIERE": "🏆",
    "HBO MAX": "🟣",
    "PARAMOUNT PREMIUM": "🎥",
    "PRIME VIDEO": "🔵",
    "SPOTIFY 1 MES": "🎵",
    "TELECINE": "📽️",
    "YOUTUBE FAMÍLIA": "👨‍👩‍👧‍👦",
    "GLOBO": "🌎",
}
def get_emoji_servico(nome):
    nome_upper = nome.upper()
    for chave, emoji in EMOJIS_SERVICOS.items():
        if chave in nome_upper:
            return emoji
    return "✨"  # Padrão se não encontrar
# CÓDIGO PARA SUBSTITUIR (Linhas 7020-7096)
def servicos(message, page=1):
    """
    Exibe a lista de serviços paginada, com agrupamento ULTRA-AGRESSIVO.
    """
    import math
    import re # Biblioteca para arrancar caracteres invisíveis
    try:
        servicos_normais = api.ControleLogins.pegar_servicos() or []
    except Exception:
        servicos_normais = []
    produtos_agrupados = {}
    ja_processados = set()
    # 1. Agrupamento Implacável
    for servico in servicos_normais:
        nome_original = str(servico.get("nome", ""))
        # A MÁGICA AQUI: Arranca tudo que não for letra ou número.
        # "NETFLIX PREMIUM  " vira "NETFLIXPREMIUM" e "Netflix Premium" também vira "NETFLIXPREMIUM"
        chave_grupo = re.sub(r'[^a-zA-Z0-9]', '', nome_original).upper()
        if not chave_grupo:
            continue
        # Puxa o estoque real dessa variação diretamente da sua API
        if nome_original not in ja_processados:
            ja_processados.add(nome_original)
            try:
                estoque_deste_lote = sum(1 for item in servicos_normais if item.get("nome") == nome_original)
            except Exception:
                estoque_deste_lote = 0
            if chave_grupo in produtos_agrupados:
                # SE AS LETRAS FOREM IGUAIS, SOMA O ESTOQUE! (6 + 11 = 17)
                produtos_agrupados[chave_grupo]["estoque"] += estoque_deste_lote
            else:
                # Se for o primeiro, cria a base
                produtos_agrupados[chave_grupo] = {
                    "nome_exibicao": nome_original.strip(), # Mantém o nome bonito com os espaços na hora de exibir
                    "nome_original": nome_original, # Guarda o original pro sistema de compra não quebrar
                    "valor": servico.get("valor", 0),
                    "estoque": estoque_deste_lote
                }
    # Transforma o dicionário em lista
    produtos_unicos = list(produtos_agrupados.values())
    produtos_unicos = sorted(produtos_unicos, key=lambda x: x["nome_exibicao"])
    # --- Lógica de Paginação ---
    ITEMS_PER_PAGE = 50
    total_items = len(produtos_unicos)
    total_pages = 1 if total_items == 0 else math.ceil(total_items / ITEMS_PER_PAGE)
    page = max(1, min(page, total_pages))
    start_index = (page - 1) * ITEMS_PER_PAGE
    end_index = start_index + ITEMS_PER_PAGE
    produtos_da_pagina = produtos_unicos[start_index:end_index]
    # --- Fim da Lógica de Paginação ---
    markup = InlineKeyboardMarkup()
    # 2. Criação dos botões na tela
    if not produtos_da_pagina:
        markup.add(InlineKeyboardButton('❌ ESTOQUE VAZIO ❌', callback_data='noop'))
    else:
        for servico in produtos_da_pagina:
            nome_exibir = servico.get("nome_exibicao")
            nome_callback = servico.get("nome_original") 
            valor_original = float(servico.get("valor", 0))
            estoque_total = servico.get("estoque", 0)
            # --- Verifica se há Oferta Relâmpago ativa para este serviço ---
            try:
                valor_final = Oferta_relampago.verificar_preco(nome_callback, valor_original)
            except Exception:
                valor_final = valor_original
            # Se o preço mudou, adiciona um ícone de raio para destacar a promoção
            if valor_final < valor_original:
                nome_botao = f'⚡ {nome_exibir} R${valor_final:.2f} [Qnt: {estoque_total}]'
            else:
                nome_botao = f'{nome_exibir} R${valor_final:.2f} [Qnt: {estoque_total}]'
            # -------------------------------------------------------------
            callback_data = f"exibir_servico {nome_callback}"
            markup.add(InlineKeyboardButton(text=nome_botao, callback_data=callback_data))
    # 3. Botões de navegação
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton("⬅️ Anterior", callback_data=f"servicos_page_{page - 1}"))
    if total_pages > 1:
        nav_row.append(InlineKeyboardButton(f"Pág {page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton("Próxima ➡️", callback_data=f"servicos_page_{page + 1}"))
    if nav_row:
        markup.row(*nav_row)
    # 4. Botões finais
    markup.row(InlineKeyboardButton('🔎 pesquisar logins', switch_inline_query_current_chat="buscar_loguin "))
    markup.add(InlineKeyboardButton('↩️ Voltar', callback_data='mostrar_menu_vendas'))
    texto_estoque = "📊 <b>ESTOQUE ATUAL DO BOT</b> 📊\n"
    texto_estoque += f"📦 <b>Total disponível: {len(servicos_normais)} logins</b>\n"
    texto = api.Textos.menu_comprar(message) + f"\n\n{texto_estoque}"
    if total_pages > 1:
        texto += f"\n<b>Página {page} de {total_pages}</b>\n"
    # 5. Envia ou atualiza a tela
    from app import interface as fotos_menus
    if fotos_menus.exibir_com_foto_opcional(
        bot, message.chat.id, message.message_id, 'servicos', texto, reply_markup=markup
    ):
        return
    try:
        bot.edit_message_text(
            chat_id=message.chat.id, 
            message_id=message.message_id, 
            text=texto, 
            parse_mode='HTML', 
            reply_markup=markup
        )
    except Exception as e:
        if 'message is not modified' not in str(e).lower():
            try:
                bot.delete_message(message.chat.id, message.message_id)
            except Exception:
                pass
            bot.send_message(chat_id=message.chat.id, text=texto, parse_mode='HTML', reply_markup=markup)
# NOVO HANDLER PARA PAGINAÇÃO DE SERVIÇOS
@bot.callback_query_handler(func=lambda c: c.data.startswith('servicos_page_'))
def callback_servicos_page(call):
    """
    Este handler captura os cliques nos botões 'Anterior' e 'Próximo' da lista de serviços.
    """
    try:
        # Extrai o número da página do callback_data (ex: 'servicos_page_2')
        page = int(call.data.split('_')[-1])
        bot.answer_callback_query(call.id)
        # Chama a função servicos() novamente, passando a nova página
        servicos(call.message, page=page)
    except Exception as e:
        print(f"Erro no callback_servicos_page: {e}")
        bot.answer_callback_query(call.id, "Erro ao mudar de página.", show_alert=True)
# (Continuação do seu código original...)
def obter_icone_servico(nome_servico):
    """
    Busca o ícone correspondente ao serviço baseado no nome.
    SEMPRE retorna uma URL ou File ID - se não encontrar, retorna o padrão.
    """
    try:
        # --- NOVO: Verifica primeiro se existe foto salva no arquivo ---
        from app import interface as fotos_produtos
        foto_salva = fotos_produtos.obter_foto_customizada(nome_servico)
        if foto_salva:
            return foto_salva
        # -------------------------------------------------------------
        nome_lower = nome_servico.lower().strip()
        # Remove caracteres especiais e espaços extras
        nome_clean = nome_lower.replace('+', ' plus').replace('&', ' and ').strip()
        # Busca exata primeiro
        if nome_clean in icones:
            return icones[nome_clean]
        # Busca exata sem espaços
        nome_sem_espacos = nome_clean.replace(' ', '')
        for chave in icones.keys():
            if chave != 'padrao' and chave.replace(' ', '') == nome_sem_espacos:
                return icones[chave]
        # Lista de palavras-chave do nome do serviço
        palavras_servico = nome_clean.split()
        # Busca por correspondência de palavras-chave
        melhor_match = None
        maior_score = 0
        for chave, url in icones.items():
            if chave == 'padrao':
                continue
            palavras_chave = chave.lower().split()
            score = 0
            # Conta quantas palavras coincidem
            for palavra_servico in palavras_servico:
                for palavra_chave in palavras_chave:
                    if palavra_servico == palavra_chave:
                        score += 2  # Correspondência exata vale mais
                    elif palavra_servico in palavra_chave or palavra_chave in palavra_servico:
                        score += 1  # Correspondência parcial
            # Se encontrou correspondência melhor
            if score > maior_score:
                maior_score = score
                melhor_match = url
        # Se encontrou alguma correspondência, retorna
        if melhor_match and maior_score > 0:
            return melhor_match
        # Busca parcial - verifica se alguma chave do dicionário está contida no nome do serviço
        for chave, url in icones.items():
            if chave != 'padrao' and chave.lower() in nome_clean:
                return url
        # Busca parcial inversa - verifica se o nome do serviço está contido em alguma chave
        for chave, url in icones.items():
            if chave != 'padrao' and nome_clean in chave.lower():
                return url
        # Busca por palavras individuais
        for palavra in palavras_servico:
            if len(palavra) > 2:  # Ignora palavras muito pequenas
                for chave, url in icones.items():
                    if chave != 'padrao' and palavra in chave.lower():
                        return url
    except Exception as e:
        print(f"Erro na busca de ícone para {nome_servico}: {e}")
    # SEMPRE retorna o ícone padrão se não encontrar nada ou der erro
    return icones['padrao']
# (Importações no topo do arquivo já devem existir)
# ... (código anterior da função exibir_servico) ...
def exibir_servico(message, servico, return_callback='servicos'):
    import random
    import re
    # --- INÍCIO: GATILHO DE ABANDONO DE SERVIÇO ---
    lembrete_abandono.iniciar_contagem(bot, ADMIN_ID, message.chat.id, servico)
    # --- FIM: GATILHO DE ABANDONO DE SERVIÇO ---
    # 1. Puxa o texto original do seu bot
    texto, email = api.Textos.exibir_servico(message, servico)
    # --- [A MÁGICA: CÁLCULO INFALÍVEL DO ESTOQUE UNIFICADO] ---
    try:
        servicos_normais = api.ControleLogins.pegar_servicos() or []
        estoque_total = 0
        estoque_velho = 0
        # Transforma o nome clicado na chave matemática (ex: "NETFLIXPREMIUM")
        chave_busca = re.sub(r'[^a-zA-Z0-9]', '', str(servico)).upper()
        for item in servicos_normais:
            nome_original = str(item.get("nome", ""))
            chave_item = re.sub(r'[^a-zA-Z0-9]', '', nome_original).upper()
            # Se as chaves forem iguais, soma!
            if chave_item == chave_busca:
                # Usa a exata mesma forma de extrair a quantidade que funcionou no menu principal
                qtd = int(item.get("estoque", item.get("quantidade", 1)))
                estoque_total += qtd
                # Regista qual era a quantidade errada para a tentarmos apagar
                if nome_original == str(servico):
                    estoque_velho = qtd
        # Substitui a quantidade errada pela certa no texto gerado pela sua API
        if estoque_total > 0 and estoque_velho > 0:
            texto = re.sub(rf'(?i)(estoque|quantidade|disp[a-z]*|rest[a-z]*|logins|qnt|und)[\s\:\-\|\>]*{estoque_velho}', rf'\1: {estoque_total}', texto)
        # ⚠️ INJEÇÃO À FORÇA: Adiciona o total gigante no topo da mensagem
        texto = f"📦 <b>ESTOQUE TOTAL: {estoque_total} UNIDADES</b>\n\n" + texto
    except Exception as e:
        print(f"Erro ao unificar estoque na exibição: {e}")
    # ------------------------------------------------
    # --- [BUSCAR E ADICIONAR DESCRIÇÃO DO PRODUTO] ---
    try:
        info = api.ControleLogins.pegar_info(servico)
        descricao_servico = info[2] if (info and len(info) >= 3 and info[2]) else "Nenhuma descrição disponível."
        texto += f"\n\nℹ️ <b>Detalhes do Produto:</b>\n<i>{descricao_servico}</i>"
    except Exception as e:
        pass
    # -------------------------------------------------
    # --- PROVA SOCIAL (FOMO) ---
    try:
        qtd_pessoas = random.randint(12, 45)
        qtd_avaliacoes = random.randint(50, 250) 
        texto += f"\n\n⭐️⭐️⭐️⭐️⭐️ 4.6/5 ({qtd_avaliacoes} avaliações)"
        texto += f"\n👥 {qtd_pessoas} clientes visualizando este produto"
    except Exception:
        pass
      # --- BOTÕES EXISTENTES ---
    bt_comprar = InlineKeyboardButton('🛒 COMPRAR', callback_data=f'confirmar_compra_prompt {servico}')
    bt_comprar_qtd = InlineKeyboardButton('🔢 COMPRAR+1', callback_data=f'comprar_qtd {servico}')

    # --- BOTÃO VOLTAR, CARRINHO E FAVORITOS ---
    bt_voltar = InlineKeyboardButton('↩️ Voltar', callback_data=return_callback)
    bt_add_cart = InlineKeyboardButton('🛒 CARRINHO', callback_data=f'cart_add|{servico}')
    
    # Verifica se já é favorito para exibir o texto correto no botão
    from app import interface as sistema_favoritos
    meus_favs = sistema_favoritos.carregar_favoritos(message.chat.id)
    if servico in meus_favs:
        bt_fav = InlineKeyboardButton('💔 DESFAVORITAR', callback_data=f'fav_toggle|{servico}')
    else:
        bt_fav = InlineKeyboardButton('❤️ FAVORITAR', callback_data=f'fav_toggle|{servico}')
    
    # --- MONTAGEM DO MARKUP ---
    markup = InlineKeyboardMarkup()
    markup.row(bt_comprar, bt_comprar_qtd) 
    
    # Coloca Add Carrinho e Favoritar lado a lado
    markup.row(bt_add_cart, bt_fav) 
    markup.row(bt_voltar)
    # --- ENVIO / EDIÇÃO DA MENSAGEM FINAL ---
    try:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=texto,
            reply_markup=markup,
            parse_mode='HTML'
        )
    except Exception as e:
        if 'message is not modified' not in str(e).lower():
            try:
                bot.delete_message(message.chat.id, message.message_id)
            except Exception:
                pass
            bot.send_message(message.chat.id, texto, reply_markup=markup, parse_mode='HTML')
    # --- LÓGICA DE ENVIO/EDIÇÃO DA MENSAGEM (RESTANTE DA FUNÇÃO) ---
    # (O restante da sua função para editar ou enviar a mensagem com a foto continua aqui...)
# Novo Código para Substituir (dentro da função exibir_servico):
# ============================================================
    try:
        # Tenta editar a mensagem atual. Prioriza editar legenda se for mídia, senão edita texto.
        edited = False
        if getattr(message, 'caption', None) is not None:
            try:
                bot.edit_message_caption(
                    caption=texto,
                    chat_id=message.chat.id,
                    message_id=message.message_id,
                    parse_mode='HTML',
                    reply_markup=markup
                )
                edited = True
            except Exception as edit_caption_error:
                 if 'message is not modified' in str(edit_caption_error).lower():
                     return # Nada mudou, termina aqui.
                 print(f"Falha ao editar legenda, tentando editar texto: {edit_caption_error}")
                 # Continua para tentar editar texto
        if not edited:
            # Se não tinha legenda ou editar legenda falhou, tenta editar texto
             bot.edit_message_text(
                 text=texto,
                 chat_id=message.chat.id,
                 message_id=message.message_id,
                 parse_mode='HTML',
                 reply_markup=markup
             )
    except Exception as e:
        # Se qualquer edição falhar (exceto "não modificado"), executa o fallback de enviar nova mensagem com foto
        if 'message is not modified' not in str(e).lower():
            print(f"Não foi possível editar para exibir serviço '{servico}', enviando nova mensagem com foto: {e}")
            try:
                # Tenta deletar a mensagem antiga antes de enviar a nova (limpeza)
                bot.delete_message(message.chat.id, message.message_id)
            except Exception:
                pass # Ignora se não conseguir deletar
            # Obter ícone do serviço
            icone_url = obter_icone_servico(servico)
            if not icone_url:
                icone_url = icones['padrao']
            # Lista de URLs de fallback
            urls_fallback = [
                icone_url,
                icones['padrao'],
                'https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/No-Image-Placeholder.svg/512px-No-Image-Placeholder.svg.png',
                'https://via.placeholder.com/512x512/2C2F33/FFFFFF?text=SERVICO'
            ]
            foto_enviada = False
            for url in urls_fallback:
                try:
                    bot.send_photo(
                        chat_id=message.chat.id,
                        photo=url,
                        caption=texto,
                        parse_mode='HTML',
                        reply_markup=markup
                    )
                    foto_enviada = True
                    break # Sai do loop se conseguiu enviar
                except Exception as send_error:
                    print(f"Erro ao enviar imagem {url} para {servico}: {send_error}")
                    continue # Tenta a próxima URL
            # Se nenhuma foto funcionou, envia mensagem de texto como último recurso
            if not foto_enviada:
                print(f"Todas as URLs falharam para {servico}, enviando texto")
                bot.send_message(
                    chat_id=message.chat.id,
                    text=texto,
                    parse_mode='HTML',
                    reply_markup=markup
                )
_usuarios_aguardando_qtd = set()  # trava contra duplo clique em "COMPRAR+1"

@bot.callback_query_handler(func=lambda c: c.data.startswith("comprar_qtd"))
def callback_comprar_qtd(call):
    parts = call.data.split(maxsplit=1)
    if len(parts) < 2:
        bot.answer_callback_query(call.id, "Serviço não especificado.", show_alert=True)
        return
    servico = parts[1]
    user_id = call.from_user.id
    # Se o usuário já tem uma pergunta de quantidade pendente (ex: clicou 2x rápido),
    # ignora o clique repetido em vez de registrar um segundo next_step_handler
    # para o mesmo chat (isso causava compra em dobro e saldo negativo).
    if user_id in _usuarios_aguardando_qtd:
        bot.answer_callback_query(call.id, "Você já tem uma pergunta de quantidade pendente. Responda a ela antes de clicar de novo.", show_alert=True)
        return
    _usuarios_aguardando_qtd.add(user_id)
    bot.answer_callback_query(call.id)
    msg = bot.send_message(
        call.message.chat.id,
        f"Quantos logins de {servico} você deseja comprar?",
        reply_markup=types.ForceReply()
    )
    bot.register_next_step_handler(msg, processar_compra_quantidade, servico)
@estoque_api.serializar(bot)
def processar_compra_quantidade(message, servico):
    user_id = message.from_user.id
    # Libera a trava de duplo clique assim que a resposta do usuário chega.
    _usuarios_aguardando_qtd.discard(user_id)
    try:
        quantidade = int(message.text)
    except ValueError:
        bot.reply_to(message, "Por favor, envie um número válido.")
        return
    if quantidade < 1:
        bot.reply_to(message, "Informe uma quantidade maior que zero.")
        return
    # === INÍCIO DA TRAVA DE ESTOQUE ===
    # Puxa todos os serviços e conta quantos têm o mesmo nome do serviço que o cliente quer
    todos_servicos = api.ControleLogins.pegar_servicos()
    estoque_atual = sum(1 for s in todos_servicos if s.get("nome") == servico)
    if quantidade > estoque_atual:
        bot.send_message(
            message.chat.id, 
            f"⚠️ <b>Estoque insuficiente!</b>\n\nVocê pediu <b>{quantidade}</b>x, mas temos apenas <b>{estoque_atual}</b> contas de {servico} disponíveis no momento.",
            parse_mode="HTML"
        )
        return
    # === FIM DA TRAVA DE ESTOQUE ===
    resultado_peek = api.ControleLogins.peek_primeiro_disponivel(servico)
    if not resultado_peek:
        bot.send_message(message.chat.id, f"Acabaram os logins de {servico}.")
        return
    _, valor_str, _, _, _, _ = resultado_peek
    valor_original = float(valor_str)
    # Aplica a verificação da Oferta Relâmpago no preço unitário e o limite
    preco_unitario = valor_original
    try:
        from app import Oferta_relampago
        # CORREÇÃO: antes usava verificar_oferta_ativa(), que só retorna a
        # PRIMEIRA oferta relâmpago ativa da lista — se houvesse mais de uma
        # oferta simultânea, um produto que não fosse o primeiro da lista
        # nunca recebia o desconto no fluxo de quantidade (COMPRAR+1).
        # _achar_oferta(servico) procura a oferta certa para ESTE produto.
        oferta = Oferta_relampago._achar_oferta(servico)
        if oferta:
            preco_unitario = float(oferta["preco_promocional"])
            limite = int(oferta.get("limite_quantidade", 0))
            if limite > 0 and quantidade > limite:
                bot.send_message(
                    message.chat.id, 
                    f"⚠️ <b>Limite Excedido!</b>\n\nNesta Oferta Relâmpago, você pode comprar no máximo <b>{limite}</b> unidades por vez.", 
                    parse_mode="HTML"
                )
                return
    except Exception as e:
        print(f"Erro ao verificar oferta relâmpago na quantidade: {e}")
    saldo_user = float(api.InfoUser.saldo(user_id))
    total_necessario = quantidade * preco_unitario
    # CORREÇÃO: Arredondar para evitar erro
    saldo_user = round(saldo_user, 2)
    total_necessario = round(total_necessario, 2)
    if saldo_user < total_necessario:
        falta = total_necessario - saldo_user
        markup_pix = InlineKeyboardMarkup()
        markup_pix.row(InlineKeyboardButton(f"💳 Depositar R$ {falta:.2f} via PIX", callback_data=f"pix_quick {falta:.2f}"))
        markup_pix.row(InlineKeyboardButton("↩️ Voltar", callback_data=f"exibir_servico {servico}"))
        texto_erro = (
            f"❌ <b>Saldo Insuficiente</b>\n\n"
            f"Você precisa de <b>R$ {total_necessario:.2f}</b> para {quantidade}x {servico}.\n"
            f"Seu saldo atual: <b>R$ {saldo_user:.2f}</b>\n"
            f"Faltam: <b>R$ {falta:.2f}</b>\n\n"
            f"👇 Clique abaixo para gerar o PIX do valor que falta:"
        )
        bot.send_message(message.chat.id, texto_erro, parse_mode='HTML', reply_markup=markup_pix)
        return
    comprados = 0
    for i in range(quantidade):
        resultado = estoque_api.comprar(api, servico, user_id, f"quantidade:{user_id}:{message.message_id}:{i}", preco_unitario)
        if not resultado:
            bot.send_message(message.chat.id, f"Acabaram os logins de {servico} após comprar {comprados}.")
            break
        nome, _, email, senha, descricao, duracao = resultado
        # Utiliza o preco_unitario validado (com a oferta relâmpago, se houver)
        entregar(message, nome, preco_unitario, email, senha, descricao, duracao)
        comprados += 1
        time.sleep(1.0)
    bot.send_message(message.chat.id, f"Compra finalizada. Você comprou {comprados} logins de {servico}.")
@bot.message_handler(commands=['quantidadelogins'])
def mostrar_quantidade_logins(message):
    servicos = api.ControleLogins.pegar_servicos()
    total_logins = len(servicos)
    servico_counts = {}
    for servico in servicos:
        nome = servico["nome"]
        servico_counts[nome] = servico_counts.get(nome, 0) + 1
    texto = f"<b>Estoque de Logins: {total_logins}</b>\n\n"
    # Usando sorted() para ter uma ordem consistente
    for nome, count in sorted(servico_counts.items()):
        texto += f"{nome.upper()}: {count}\n"
    bot.send_message(message.chat.id, texto, parse_mode='HTML')
@bot.callback_query_handler(func=lambda c: c.data == 'mostrar_logins')
def callback_mostrar_logins(call):
    mostrar_quantidade_logins(call.message)
    bot.answer_callback_query(call.id)   
# ───────────────────────���─────────────────────�����─────────────────
# ──────────────────────────────────────────────────────────────
#  ENTREGA DE LOGIN + AVISO (formato modificado)
# ───────────────────────────────────────────────────────────────

# ==================== ENTREGA CARRINHO ALERTAS ====================
def _eh_servico_com_botoes_extras(nome_servico):
    """Retorna True apenas para Disney, Netflix e HBO MAX (case-insensitive)."""
    nome_lower = (nome_servico or "").lower()
    return any(termo in nome_lower for termo in ("disney", "netflix", "hbo"))


class _CopyTextButton:
    """Botão inline NATIVO de 'copiar para a área de transferência' (campo copy_text
    da Bot API, disponível desde a versão 7.5 do Telegram). A versão do
    pyTelegramBotAPI travada no projeto (4.12.0) não conhece esse campo, então
    não dá pra usar InlineKeyboardButton(copy_text=...) — em vez disso, construímos
    esse objeto simples que só precisa responder a to_dict(), que é o método que o
    telebot chama pra montar o JSON do teclado. Assim o clique copia o valor de
    verdade (o botão de alerta antigo só exibia o texto, sem copiar nada)."""
    def __init__(self, text, copy_text):
        self.text = text
        self.copy_text = (copy_text or "")[:256]  # limite da API: 1-256 caracteres

    def to_dict(self):
        return {"text": self.text, "copy_text": {"text": self.copy_text}}


def _montar_botoes_extras(markup, purchase_id, email, senha, nome_servico):
    """Adiciona os botões 'Copiar Email' e 'Copiar Senha' em TODOS os logins entregues.
    O botão 'Receber Código' (link do bot) só aparece para Disney, Netflix e HBO MAX."""
    from telebot.types import InlineKeyboardButton
    markup.row(
        _CopyTextButton("📋 Copiar Email", email),
        _CopyTextButton("📋 Copiar Senha", senha)
    )
    if _eh_servico_com_botoes_extras(nome_servico):
        markup.row(
            InlineKeyboardButton("📲 Receber Código", url="https://t.me/Recebercodigos_bot")
        )

def enviar_backup_estoque_adm():
    """
    Gera um TXT com o estoque atual e envia para o dono.
    Formato: NOME/VALOR/DESCRIÇÃO/EMAIL/SENHA/DURAÇÃO
    """
    try:
        # Pega os serviços restantes (o vendido já foi removido antes dessa chamada)
        logins = api.ControleLogins.pegar_servicos()
        if not logins:
            return # Se não tiver nada, não precisa mandar backup vazio
        conteudo = ""
        # Monta as linhas no formato solicitado
        for login in logins:
            # Garante que todos os campos existam para evitar erro
            nome = login.get('nome', 'N/A')
            valor_raw = login.get('valor', '0')
            # --- LÓGICA PARA REMOVER O .0 ---
            try:
                val_float = float(valor_raw)
                # Se for inteiro (ex: 10.0), vira int (10)
                if val_float.is_integer():
                    valor = str(int(val_float))
                else:
                    valor = str(val_float)
            except:
                valor = str(valor_raw)
            # --------------------------------
            descricao = login.get('descricao', '-')
            email = login.get('email', 'N/A')
            senha = login.get('senha', 'N/A')
            duracao = login.get('duracao', '0')
            # Formata a linha
            linha = f"{nome}/{valor}/{descricao}/{email}/{senha}/{duracao}"
            conteudo += f"{linha}\n\n" # Adiciona quebra de linha dupla para ficar legível como no seu exemplo
        # Salva num arquivo temporário
        filename = "backup_estoque_atual.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        # Envia para o dono
        dono_id = api.CredentialsChange.id_dono()
        with open(filename, 'rb') as f:
            bot.send_document(
                dono_id, 
                f, 
                caption="📦 <b>Backup de Segurança:</b> Estoque atualizado pós-venda.",
                parse_mode='HTML'
            )
        # Remove o arquivo temporário
        os.remove(filename)
    except Exception as e:
        print(f"[BACKUP ESTOQUE] Erro ao enviar backup: {e}")
def entregar(message, nome, valor, email, senha, descricao, duracao):
    """
    Envia a mensagem de confirmação de compra otimizada para o usuário,
    adiciona a compra ao histórico e notifica o administrador.
    """
    from datetime import datetime, timedelta
    import pytz
    from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
    user_id = message.chat.id
    t = pending_reminders.pop(user_id, None)
    if t:
        t.cancel()
    # --- INÍCIO: CANCELA O AVISO DE ABANDONO SE ELE COMPRAR ---
    from app import notificacoes as lembrete_abandono
    lembrete_abandono.cancelar_contagem(user_id)
    # --- FIM: CANCELA O AVISO ---
    tz = pytz.timezone('America/Sao_Paulo')
    now_sp = datetime.now(tz)
    exp_sp = now_sp + timedelta(days=int(duracao))
    data_cmp = now_sp.strftime("%d/%m/%Y %H:%M:%S")
    data_exp = exp_sp.strftime("%d/%m/%Y %H:%M:%S")
    saldo_atl = get_user_balance(user_id)
    descricao_fmt = descricao.replace('\n', '\n')
    # Pega o nome do usuário
    # Pega o nome do cliente diretamente do chat da entrega
    nome_usuario = message.chat.first_name if message.chat.first_name else "Cliente"
    # Formata a descrição e limpa as datas
    descricao_curta = descricao.replace('\n', ' ')
    data_compra_simples = data_cmp.split(' ')[0]
    data_venc_simples = data_exp.split(' ')[0]
    # Formata a descrição e limpa as datas para mostrar apenas o dia (remove o horário se houver)
    descricao_curta = descricao.replace('\n', ' ')
    data_compra_simples = data_cmp.split(' ')[0]
    data_venc_simples = data_exp.split(' ')[0]
    texto_user = (
        f"✅ <b>Compra Confirmada!</b>\n\n"
        f"Olá,<b>{nome_usuario}</b>! 👋\n\n"
        f" <b>{nome}</b>\n"
        f"├ 📧 <code>{email}</code>\n"
        f"└ 🔑 <code>{senha}</code>\n\n"
        f"📅 <b>Compra:</b> {data_compra_simples}\n"
        f"⚠️ <b>Vence:</b> {data_venc_simples}\n\n"
        f"💰 <b>R$ {float(valor):.2f}</b> | ℹ️ <i>{descricao_curta}</i>"
    )
    # --- ALTERAÇÃO PRINCIPAL AQUI ---
    # Adiciona a compra ao histórico e pega o ID único dela
    purchase_info = add_purchase(user_id, nome, email, senha, valor, int(duracao))
    purchase_id = purchase_info['id']
    markup = InlineKeyboardMarkup()
    # Adiciona o novo botão de reportar problema
    # --- MODIFICATION START ---
    # Only add the button if the feature is enabled in settings
    if is_reportar_problema_enabled():
        markup.row(InlineKeyboardButton("❗ Reportar Problema na Conta", callback_data=f"reportar_problema_{purchase_id}"))
    # --- MODIFICATION END ---
    markup.row(
        InlineKeyboardButton("🆘 Preciso de Ajuda", url=api.CredentialsChange.SuporteInfo.link_suporte())
    )
    _montar_botoes_extras(markup, purchase_id, email, senha, nome)
    # --- Bloco do botão Netflix REMOVIDO daqui ---
    # --- NOVO: Tenta enviar a mensagem de entrega com a foto do produto ---
    try:
        from app import interface as fotos_produtos
        foto_produto = fotos_produtos.obter_foto_customizada(nome)
        if foto_produto:
            bot.send_photo(
                user_id, 
                photo=foto_produto, 
                caption=texto_user, 
                parse_mode='HTML', 
                reply_markup=markup
            )
        else:
            bot.send_message(user_id, texto_user, parse_mode='HTML', reply_markup=markup, disable_web_page_preview=True)
    except Exception as e:
        print(f"[entregar] Erro ao enviar mensagem para o usuário {user_id}: {e}")
        # Fallback de segurança
        try:
            bot.send_message(user_id, texto_user, parse_mode='HTML', reply_markup=markup, disable_web_page_preview=True)
        except:
            pass
    # ----------------------------------------------------------------------
    avisar_venda(
        user_id=user_id,
        servico=nome,
        email=email,
        senha=senha,
        valor=valor,
        data_compra=data_cmp,
        data_venc=data_exp,
        saldo_atual=saldo_atl
    )
    # Envia backup do estoque restante para o ADM
    enviar_backup_estoque_adm()
# ======================= [INÍCIO] LÓGICA DE CONFIRMAÇÃO DE COMPRA =======================
@bot.callback_query_handler(lambda call: call.data == 'adicionar_login')
def on_adicionar_login(call):
    if not is_admin_user(call.from_user.id):
        bot.answer_callback_query(
            call.id,
            "🚫 Apenas administradores podem abastecer o estoque!",
            show_alert=True
        )
        return
    sep = api.CredentialsChange.separador()
    msg = bot.send_message(
        call.message.chat.id,
        f"Envie os acessos que deseja adicionar, no formato:\n"
        f"NOME{sep}VALOR{sep}DESCRICAO{sep}EMAIL{sep}SENHA{sep}DURACAO",
        parse_mode='HTML',
        reply_markup=types.ForceReply()
    )
    bot.register_next_step_handler(msg, logins_mgr.adicionar_login)
@bot.message_handler(commands=['get_id'])
def get_id(message):
    if api.Admin.verificar_vencimento() == True:
        ver_se_expirou()
        return
    bot.reply_to(message, f'{message.chat.id}')
# ======================= [UPGRADE] PAINEL DO CRIADOR =======================
@bot.message_handler(commands=['criador'])
def handle_criador(message):
    # MANTÉM O ID DO CRIADOR HARDCODED, pois este painel é para o DEV, não para o DONO.
    if str(message.from_user.id) == '7619679574':
        # --- [UPGRADE] Texto do Painel Reestruturado ---
        try:
            # Tenta buscar os dados de vencimento de forma segura
            vencimento_data = api.Admin.data_vencimento()
            vencimento_dias = api.Admin.tempo_ate_o_vencimento()
            vencimento_status = f"{vencimento_data} ({vencimento_dias} dias restantes)"
        except Exception:
            vencimento_status = "Erro ao carregar vencimento"
        try:
            bot_username = api.CredentialsChange.user_bot()
        except Exception:
            bot_username = "N/A"
        txt = (
            f'🧑‍💻 <b>PAINEL DO CRIADOR</b>\n'
            f'<i>Acesso de superusuário para @{bot_username}</i>\n'
            f'➖➖➖➖➖➖➖➖➖➖➖\n'
            f'🟢 <b>STATUS:</b> ONLINE\n'
            f'🎫 <b>Tipo de bot:</b> <i>Acessos e logins</i>\n\n'
            f'🤖 <b>INFORMAÇÕES DO BOT</b>\n'
            f'├─ <b>Versão:</b> <code>{api.CredentialsChange.versao_bot()}</code>\n'
            f'├ <b>Username:</b> @{bot_username}\n'
            f'└─ <b>Token:</b> <code>{api.CredentialsChange.token_bot()}</code>\n\n'
            f'👤 <b>INFORMAÇÕES DO CLIENTE (DONO)</b>\n'
            f'├─ <b>ID Dono:</b> <code>{api.CredentialsChange.id_dono()}</code>\n'
            f'└─ <b>Vencimento:</b> {vencimento_status}\n'
            f'➖➖➖➖➖➖➖➖➖➖➖'
        )
        # --- [UPGRADE] Botões Reorganizados ---
        markup = InlineKeyboardMarkup()
        # Linha 1: Identidade do Bot
        markup.row(
            InlineKeyboardButton('🔑 Mudar Token', callback_data='mudar_token_bot'),
            InlineKeyboardButton('🤖 Mudar User', callback_data='mudar_user_bot')
        )
        # Linha 2: Cliente e Versão
        markup.row(
            InlineKeyboardButton('💼 Mudar Dono', callback_data='mudar_dono_bot'),
            InlineKeyboardButton('✅ Mudar Versão', callback_data='mudar_versao_bot')
        )
        # Linha 3: Gerenciamento de Acesso e Ciclo de Vida
        markup.row(
            InlineKeyboardButton('👮‍♀️ Pegar Admin (Dono)', callback_data='pegar_admin_creator'),
            InlineKeyboardButton('⏰ Config. Vencimento', callback_data='configurar_vencimento')
        )
        # Linha 4: Ações e Atalhos
        markup.row(
            InlineKeyboardButton('🔃 Reiniciar Bot', callback_data='reiniciar_bot'),
            # Novo atalho para o painel do cliente (dono)
            InlineKeyboardButton('⚙️ Ver Painel Admin (Dono)', callback_data='voltar_paineladm')
        )
        # Linha 5: Estatísticas
        markup.row(
            InlineKeyboardButton('📊 Estatísticas Globais', callback_data='stats_criador')
        )
        # Linha 6: Adicionar a Grupo
        markup.row(
            InlineKeyboardButton('➕ Add em Grupo', url=f'https://t.me/{bot_username}?startgroup=start')
        )
        # L��gica para enviar ou editar a mensagem (mantida e melhorada)
        if message.text == '/criador':
            bot.send_message(chat_id=message.chat.id, text=txt, parse_mode='HTML', reply_markup=markup)
        else:
            try:
                # Tenta editar a mensagem
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=txt, parse_mode='HTML', reply_markup=markup)
            except Exception as e:
                # Se falhar (ex: msg não modificada ou muito antiga), envia uma nova
                if 'message is not modified' not in str(e).lower():
                    bot.send_message(chat_id=message.chat.id, text=txt, parse_mode='HTML', reply_markup=markup)
def _fmt_valor(valor):
    try:
        return f"R$ {float(valor):.2f}"
    except Exception:
        return "R$ 0.00"

def exibir_stats_criador(message):
    """Painel de estatísticas globais do /criador: total de usuários e
    tops de compradores/depositantes/gifts (hoje, semana, mês)."""
    try:
        total_users = api.Admin.total_users()
    except Exception:
        total_users = "N/A"
    try:
        s = relatorio_avancado.calcular_top_stats(api=api)
    except Exception as e:
        txt = f"📊 <b>ESTATÍSTICAS GLOBAIS</b>\n➖➖➖➖➖➖➖➖➖➖➖\n⚠️ Erro ao calcular estatísticas: {e}"
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton('↩ Voltar', callback_data='voltar_painel_creator'))
        try:
            bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=txt, parse_mode='HTML', reply_markup=markup)
        except Exception:
            bot.send_message(chat_id=message.chat.id, text=txt, parse_mode='HTML', reply_markup=markup)
        return

    txt = (
        f'📊 <b>ESTATÍSTICAS GLOBAIS</b>\n'
        f'➖➖➖➖➖➖➖➖➖➖➖\n'
        f'👥 <b>Total de usuários:</b> <code>{total_users}</code>\n\n'
        f'🛒 <b>TOP COMPRADOR</b>\n'
        f"├─ Hoje: {s['top_comp_hoje']['nome']} ({_fmt_valor(s['top_comp_hoje']['valor'])})\n"
        f"├─ Semana: {s['top_comp_semana']['nome']} ({_fmt_valor(s['top_comp_semana']['valor'])})\n"
        f"└─ Mês: {s['top_comp_mes']['nome']} ({_fmt_valor(s['top_comp_mes']['valor'])})\n\n"
        f'💰 <b>TOP DEPOSITANTE (PIX)</b>\n'
        f"├─ Hoje: {s['top_dep_hoje']['nome']} ({_fmt_valor(s['top_dep_hoje']['valor'])})\n"
        f"├─ Semana: {s['top_dep_semana']['nome']} ({_fmt_valor(s['top_dep_semana']['valor'])})\n"
        f"└─ Mês: {s['top_dep_mes']['nome']} ({_fmt_valor(s['top_dep_mes']['valor'])})\n\n"
        f'🎁 <b>TOP GIFTS RESGATADOS</b>\n'
        f"├─ Hoje: {s['top_gift_hoje']['nome']} ({_fmt_valor(s['top_gift_hoje']['valor'])})\n"
        f"├─ Semana: {s['top_gift_semana']['nome']} ({_fmt_valor(s['top_gift_semana']['valor'])})\n"
        f"└─ Mês: {s['top_gift_mes']['nome']} ({_fmt_valor(s['top_gift_mes']['valor'])})\n\n"
        f'🎁 <b>TOTAL DE GIFTS (soma de todos)</b>\n'
        f"├─ Hoje: {_fmt_valor(s['total_gifts_hoje'])}\n"
        f"├─ Semana: {_fmt_valor(s['total_gifts_semana'])}\n"
        f"├─ Mês: {_fmt_valor(s['total_gifts_mes'])}\n"
        f"└─ Total histórico: {_fmt_valor(s['total_gifts_all'])}\n"
        f'➖➖➖➖➖➖➖➖➖➖➖'
    )
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton('↩ Voltar', callback_data='voltar_painel_creator'))
    try:
        bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=txt, parse_mode='HTML', reply_markup=markup)
    except Exception as e:
        if 'message is not modified' not in str(e).lower():
            bot.send_message(chat_id=message.chat.id, text=txt, parse_mode='HTML', reply_markup=markup)
# ======================= [FIM DO UPGRADE] =======================
def trocar_token(message):
    api.CredentialsChange.mudar_token_bot(message.text)
    bot.reply_to(message, "Alterado com sucesso! Reiniciando...")
    safe_exit("acao do bot")
def trocar_user(message):
    api.CredentialsChange.mudar_user_bot(message.text)
    bot.reply_to(message, "Alterado!")
    message.text = '/criador'
    handle_criador(message)
def mudar_dono_bot(message):
    api.CredentialsChange.mudar_dono(message.text)
    bot.reply_to(message, "Alterado!")
    message.text = '/criador'
    handle_criador(message)
def mudar_dias_vencimento(message, tipo):
    if tipo == 'mais':
        api.Admin.aumentar_vencimento(message.text)
    else:
        api.Admin.diminuir_vencimento(message.text)
    bot.reply_to(message, 'Alterado!')
    message.text = '/criador'
    handle_criador(message)
def mudar_versao_bot(message):
    versao = message.text
    api.CredentialsChange.mudar_versao_bot(versao)
    bot.reply_to(message, "Alterado com sucesso!")
icones = {
    # Streamings principais
    'netflix': 'https://cdn.icon-icons.com/icons2/3053/PNG/512/netflix_macos_bigsur_icon_189917.png',
    'globo play': 'https://m.media-amazon.com/images/I/71bch7gUsqL.png',
    'globo': 'https://m.media-amazon.com/images/I/71bch7gUsqL.png',
    'prime': 'https://cdn.icon-icons.com/icons2/3914/PNG/512/prime_logo_icon_248780.png',
    'amazon prime': 'https://cdn.icon-icons.com/icons2/3914/PNG/512/prime_logo_icon_248780.png',
    'hbo': 'https://cdn.icon-icons.com/icons2/183/PNG/256/HBO_22554.png',
    'max': 'https://cdn.icon-icons.com/icons2/183/PNG/256/HBO_22554.png',
    'hbo max': 'https://cdn.icon-icons.com/icons2/183/PNG/256/HBO_22554.png',
    'disney': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/disney_logo_icon_168516.png',
    'disney+': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/disney_logo_icon_168516.png',
    'disney plus': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/disney_logo_icon_168516.png',
    'paramount': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Paramount_Plus_logo.svg/512px-Paramount_Plus_logo.svg.png',
    'paramount+': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Paramount_Plus_logo.svg/512px-Paramount_Plus_logo.svg.png',
    'paramount plus': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Paramount_Plus_logo.svg/512px-Paramount_Plus_logo.svg.png',
    'apple tv': 'https://cdn.icon-icons.com/icons2/3053/PNG/512/apple_tv_macos_bigsur_icon_189918.png',
    'appletv': 'https://cdn.icon-icons.com/icons2/3053/PNG/512/apple_tv_macos_bigsur_icon_189918.png',
    'youtube': 'https://cdn.icon-icons.com/icons2/195/PNG/256/YouTube_23392.png',
    'youtube premium': 'https://cdn.icon-icons.com/icons2/195/PNG/256/YouTube_23392.png',
    'crunchyroll': 'https://cdn.icon-icons.com/icons2/3132/PNG/512/crunchyroll_social_network_network_connection_communication_icon_192251.png',
    'crunchyrool': 'https://cdn.icon-icons.com/icons2/3132/PNG/512/crunchyroll_social_network_network_connection_communication_icon_192251.png',
    'telecine': 'https://pop.proddigital.com.br/wp-content/uploads/sites/8/elementor/thumbs/telecine-1-pr09zcpscitsxnsglhxs9fgak9j8yqld1snhs0od54.png',
    'telecine play': 'https://pop.proddigital.com.br/wp-content/uploads/sites/8/elementor/thumbs/telecine-1-pr09zcpscitsxnsglhxs9fgak9j8yqld1snhs0od54.png',
    'pluto tv': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/pluto_tv_logo_icon_168514.png',
    'pluto': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/pluto_tv_logo_icon_168514.png',
    'tubi': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/tubi_logo_icon_168513.png',
    'funimation': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/funimation_logo_icon_168512.png',
    'viki': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/viki_logo_icon_168511.png',
    'viki rakuten': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/viki_logo_icon_168511.png',
    'peacock': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/peacock_logo_icon_168510.png',
    'discovery': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/discovery_logo_icon_168509.png',
    'discovery+': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/discovery_logo_icon_168509.png',
    'discovery plus': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/discovery_logo_icon_168509.png',
    'starz': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/starz_logo_icon_168508.png',
    'showtime': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/showtime_logo_icon_168507.png',
    'espn': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/espn_logo_icon_168506.png',
    'espn+': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/espn_logo_icon_168506.png',
    'espn plus': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/espn_logo_icon_168506.png',
    'dazn': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/dazn_logo_icon_168505.png',
    'hulu': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/hulu_logo_icon_168504.png',
    # Canais de TV
    'claro tv': 'https://t2.tudocdn.net/601002?w=646&h=284',
    'claro': 'https://t2.tudocdn.net/601002?w=646&h=284',
    'sky': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/sky_logo_icon_168503.png',
    'directv': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/directv_logo_icon_168502.png',
    'directv go': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/directv_logo_icon_168502.png',
    'oi tv': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/oi_logo_icon_168501.png',
    'vivo tv': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/vivo_logo_icon_168500.png',
    'premiere': 'https://melhorescolha.com/blog/wp-content/uploads/2024/01/preco-do-premiere.jpg',
    'premiere fc': 'https://melhorescolha.com/blog/wp-content/uploads/2024/01/preco-do-premiere.jpg',
    'sportv': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/sportv_logo_icon_168499.png',
    'combate': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/combate_logo_icon_168498.png',
    # Ferramentas e apps
    'canva': 'https://cdn.icon-icons.com/icons2/3504/PNG/512/canva_icon_220714.png',
    'cap cut': 'https://www.moneytimes.com.br/uploads/2024/01/mt-capcut-2-1024x576.jpg',
    'capcut': 'https://www.moneytimes.com.br/uploads/2024/01/mt-capcut-2-1024x576.jpg',
    'adobe': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/adobe_logo_icon_168497.png',
    'photoshop': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/photoshop_logo_icon_168496.png',
    'premiere pro': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/premiere_pro_logo_icon_168495.png',
    'after effects': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/after_effects_logo_icon_168494.png',
    'illustrator': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/illustrator_logo_icon_168493.png',
    'lightroom': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/lightroom_logo_icon_168492.png',
    'indesign': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/indesign_logo_icon_168491.png',
    'audition': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/audition_logo_icon_168490.png',
    'animate': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/animate_logo_icon_168489.png',
    'dreamweaver': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/dreamweaver_logo_icon_168488.png',
    'xd': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/xd_logo_icon_168487.png',
    'acrobat': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/acrobat_logo_icon_168486.png',
    'bridge': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/bridge_logo_icon_168485.png',
    'dimension': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/dimension_logo_icon_168484.png',
    'character animator': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/character_animator_logo_icon_168483.png',
    'media encoder': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/media_encoder_logo_icon_168482.png',
    'rush': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/rush_logo_icon_168481.png',
    'spark': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/spark_logo_icon_168480.png',
    'fresco': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/fresco_logo_icon_168479.png',
    'aero': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/aero_logo_icon_168478.png',
    'substance': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/substance_logo_icon_168477.png',
    'mixamo': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/mixamo_logo_icon_168476.png',
    'fuse': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/fuse_logo_icon_168475.png',
    'stock': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/stock_logo_icon_168474.png',
    'behance': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/behance_logo_icon_168473.png',
    'portfolio': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/portfolio_logo_icon_168472.png',
    'fonts': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/fonts_logo_icon_168471.png',
    'color': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/color_logo_icon_168470.png',
    'capture': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/capture_logo_icon_168469.png',
    'comp': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/comp_logo_icon_168468.png',
    'preview': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/preview_logo_icon_168467.png',
    'scan': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/scan_logo_icon_168466.png',
    'fill': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/fill_logo_icon_168465.png',
    'draw': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/draw_logo_icon_168464.png',
    'sketch': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/sketch_logo_icon_168463.png',
    'photoshop camera': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/photoshop_camera_logo_icon_168462.png',
    'photoshop express': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/photoshop_express_logo_icon_168461.png',
    'lightroom mobile': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/lightroom_mobile_logo_icon_168460.png',
    'premiere rush': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/premiere_rush_logo_icon_168459.png',
    'premiere clip': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/premiere_clip_logo_icon_168458.png',
    'spark video': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/spark_video_logo_icon_168457.png',
    'spark page': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/spark_page_logo_icon_168456.png',
    'spark post': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/spark_post_logo_icon_168455.png',
    # Música
    'spotify': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Spotify_logo_without_text.svg/512px-Spotify_logo_without_text.svg.png',
    'apple music': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/apple_music_logo_icon_168454.png',
    'deezer': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/deezer_logo_icon_168453.png',
    'tidal': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/tidal_logo_icon_168452.png',
    'amazon music': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/amazon_music_logo_icon_168451.png',
    'youtube music': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/youtube_music_logo_icon_168450.png',
    'pandora': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/pandora_logo_icon_168449.png',
    'soundcloud': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/soundcloud_logo_icon_168448.png',
    # Jogos
    'xbox': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/xbox_logo_icon_168447.png',
    'xbox game pass': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/xbox_game_pass_logo_icon_168446.png',
    'playstation': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/playstation_logo_icon_168445.png',
    'playstation plus': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/playstation_plus_logo_icon_168444.png',
    'nintendo': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/nintendo_logo_icon_168443.png',
    'nintendo switch': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/nintendo_switch_logo_icon_168442.png',
    'steam': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/steam_logo_icon_168441.png',
    'epic games': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/epic_games_logo_icon_168440.png',
    'origin': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/origin_logo_icon_168439.png',
    'uplay': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/uplay_logo_icon_168438.png',
    'battle.net': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/battle_net_logo_icon_168437.png',
    'gog': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/gog_logo_icon_168436.png',
    'twitch': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/twitch_logo_icon_168435.png',
    'discord': 'https://cdn.icon-icons.com/icons2/2699/PNG/512/discord_logo_icon_168434.png',
    'padrao': 'https://i.i081d461f99d53128c8d408c86.png'  # Caso não encontre nada
}
# MUDANÇA: A função inline_search_logins foi modificada para ser mais completa.
@bot.inline_handler(lambda query: query.query.lower().startswith('buscar_loguin '))
def inline_search_logins(inline_query):
    termo = inline_query.query[13:].strip().lower()
    servicos = api.ControleLogins.pegar_servicos()
    dicionario = {}
    for s in servicos:
        nome_lower = s["nome"].lower()
        if termo in nome_lower:
            nome_plataforma = s["nome"]
            if nome_plataforma not in dicionario:
                # Obter todos os detalhes do primeiro item encontrado para este serviço
                dicionario[nome_plataforma] = {
                    "nome": s["nome"],
                    "valor": s["valor"],
                    "descricao": s.get("descricao", "Sem descrição."), # Adicionado para pegar a descrição
                    "duracao": s.get("duracao"), # Adicionado para pegar a duração
                    "lista": []
                }
            dicionario[nome_plataforma]["lista"].append(s)
    results = []
    count_id = 1
    for nome_serv, info in dicionario.items():
        nome = info["nome"]
        valor = info["valor"]
        descricao = info["descricao"]
        duracao = info.get("duracao")
        qtd_estoque = len(info["lista"])
        # O texto enviado quando o usuário clica no resultado
        linha_duracao_conteudo = f"\n<b>Validade:</b> {duracao} dias" if duracao else ""
        texto = (
            f"<b>🏦 Tipo:</b> {nome}\n"
            f"<b>💳 Valor:</b> R${float(valor):.2f}\n"
            f"<b>📦 Quantia em estoque:</b> {qtd_estoque}"
            f"{linha_duracao_conteudo}\n\n"
            f"<i>🔄Use os botões abaixo para comprar ou cancelar. 🔄</i>\n"
            f"<i>⚠️Precisa de Ajuda ? @Mobixsuporte</i>"
        )
        # Botões
        buy_btn = types.InlineKeyboardButton("Comprar", callback_data=f"comprarInline {nome}")
        cancel_btn = types.InlineKeyboardButton("Cancelar", callback_data="cancelarInline")
        kb = types.InlineKeyboardMarkup([[buy_btn, cancel_btn]])
        # Ícone
        icon_url = icones.get(nome.lower(), icones['padrao'])
        for chave, link_icon in icones.items():
            if chave in nome.lower():
                icon_url = link_icon
                break
        # Título do resultado (permanece o mesmo, limpo e direto)
        title = f"{nome}"
        # Descrição do resultado (agora mais completa)
        desc_parts = [
            f"Valor: R${float(valor):.2f}",
            f"Estoque: {qtd_estoque}"
        ]
        if duracao:
            desc_parts.append(f"Duração: {duracao} dias")
        description_line1 = " | ".join(desc_parts)
        # Adiciona um snippet da descrição, se houver e for útil
        desc_snippet = ""
        if descricao and descricao.strip() not in ['-', 'Sem descrição.']:
             # Trunca a descrição para não exceder o limite
            desc_snippet = (descricao[:60] + '...') if len(descricao) > 60 else descricao
            description_line1 += f"\n{desc_snippet.strip()}"
        result = types.InlineQueryResultArticle(
            id=str(count_id),
            title=title,
            description=description_line1, # Usando a nova descrição completa
            input_message_content=types.InputTextMessageContent(texto, parse_mode='HTML'),
            reply_markup=kb,
            thumbnail_url=icon_url
        )
        results.append(result)
        count_id += 1
    if not results:
        result_none = types.InlineQueryResultArticle(
            id='99999',
            title="Nenhum resultado encontrado",
            description="Não há nenhum login compatível com sua busca.",
            input_message_content=types.InputTextMessageContent("Não encontrei nada. Tente outro termo.")
        )
        results.append(result_none)
    bot.answer_inline_query(inline_query.id, results, cache_time=1)
@bot.message_handler(commands=['addalert'])
def cmd_addalert(message):
    if not is_admin(message): 
        return bot.reply_to(message, "❌ Sem permissão.")
    parts = message.text.split(maxsplit=1)
    if len(parts) != 2:
        return bot.reply_to(message, "Uso: /addalert NOME_DA_PALAVRA")
    key = parts[1].strip().lower()
    if key in alerts:
        return bot.reply_to(message, f"🔔 `{key}` já existe.", parse_mode='Markdown')
    alerts[key] = []
    save_alerts(alerts)
    bot.reply_to(message, f"✅ Alerta `{key}` adicionado.", parse_mode='Markdown')
@bot.message_handler(commands=['removealert'])
def cmd_removealert(message):
    if not is_admin(message):
        return bot.reply_to(message, "❌ Sem permissão.")
    parts = message.text.split(maxsplit=1)
    if len(parts) != 2:
        return bot.reply_to(message, "Uso: /removealert NOME_DA_PALAVRA")
    key = parts[1].strip().lower()
    if key not in alerts:
        return bot.reply_to(message, f"🔕 `{key}` não encontrado.", parse_mode='Markdown')
    del alerts[key]
    save_alerts(alerts)
    bot.reply_to(message, f"✅ Alerta `{key}` removido.", parse_mode='Markdown')
@bot.message_handler(commands=['listalerts'])
def cmd_listalerts(message):
    if not is_admin(message):
        return bot.reply_to(message, "❌ Sem permissão.")
    if not alerts:
        return bot.reply_to(message, "⚠️ Não há alertas cadastrados.")
    texto = "🔔 *Palavras-chave de alerta:*\n\n" + "\n".join(f"- `{k}` ({len(v)} assinantes)" for k, v in alerts.items())
    bot.reply_to(message, texto, parse_mode='Markdown')
@bot.message_handler(commands=['alertas'])
def cmd_alertas(message):
    uid = message.from_user.id
    if not alerts:
        return bot.reply_to(message, "🚫 Nenhum alerta disponível no momento.")
    texto = "🔔 *Gerencie seus alertas:*"
    markup = gerar_menu_alertas_para(uid)
    bot.reply_to(message, texto, parse_mode='Markdown', reply_markup=markup)
@bot.callback_query_handler(func=lambda c: c.data.startswith('alert_toggle|'))
def callback_alert_toggle(call):
    _, chave = call.data.split('|', 1)
    uid = call.from_user.id
    sub = alerts.setdefault(chave, [])
    if uid in sub:
        sub.remove(uid)
        bot.answer_callback_query(call.id, f"❌ Você desativou `{chave}`", show_alert=False)
    else:
        sub.append(uid)
        bot.answer_callback_query(call.id, f"✅ Você ativou `{chave}`", show_alert=False)
    save_alerts(alerts)   
    new_markup = gerar_menu_alertas_para(uid)
    bot.edit_message_reply_markup(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=new_markup
    )
@bot.callback_query_handler(func=lambda c: c.data.startswith("comprarInline "))
@estoque_api.serializar(bot)
def callback_comprar_inline(call):
    nome_servico = call.data.replace("comprarInline ", "").strip()
    user_id = call.from_user.id
    resultado_peek = api.ControleLogins.peek_primeiro_disponivel(nome_servico)
    if not resultado_peek:
        bot.answer_callback_query(
            call.id,
            "Serviço esgotado ou não encontrado!",
            show_alert=True
        )
        return
    _, valor, _, _, _, _ = resultado_peek
    saldo_user = float(api.InfoUser.saldo(user_id))
    # CORREÇÃO: Arredondar para evitar erro
    saldo_user = round(saldo_user, 2)
    valor_float = round(float(valor), 2)
    if saldo_user < valor_float:
        falta = valor_float - saldo_user
        bot.answer_callback_query(call.id, f"Saldo insuficiente! Faltam R${falta:.2f}", show_alert=True)
        return
    resultado = estoque_api.comprar(api, nome_servico, user_id, f"inline:{user_id}:{getattr(call, 'inline_message_id', None) or call.message.message_id}", valor_float)
    if not resultado:
        bot.answer_callback_query(
            call.id,
            "Serviço esgotado ou não encontrado!",
            show_alert=True
        )
        return
    nome, valor, email, senha, descricao, duracao = resultado
    entregar_inline_mesmo_formato(user_id, nome, valor, email, senha, descricao, duracao)
    bot.answer_callback_query(call.id, "Compra realizada com sucesso!", show_alert=True)
def entregar_inline_mesmo_formato(user_id, nome, valor, email, senha, descricao, duracao):
    import datetime, pytz
    data_atual = datetime.datetime.now(pytz.timezone('America/Sao_Paulo'))
    data_atual_formatada = data_atual.strftime("%d/%m/%Y %H:%M:%S")
    data_venc = data_atual + datetime.timedelta(days=int(duracao))
    data_venc_formatada = data_venc.strftime("%d/%m/%Y %H:%M:%S")
    texto = api.Textos.mensagem_comprou_inline(
        user_id, nome, valor, email, senha, descricao, duracao
    )
    texto = texto.replace('{data_sem_horario}', data_atual_formatada)
    texto = texto.replace('{data_vencimento}',  data_venc_formatada)
    from telebot.types import InlineKeyboardMarkup
    purchase_info = add_purchase(
        user_id,
        nome,
        email,
        senha,
        valor,
        int(duracao)
    )
    purchase_id = purchase_info['id']
    markup = InlineKeyboardMarkup()
    _montar_botoes_extras(markup, purchase_id, email, senha, nome)
    bot.send_message(
        chat_id=user_id,
        text=texto,
        parse_mode='HTML',
        reply_markup=markup if markup.keyboard else None
    )
    api.MudancaHistorico.add_compra(user_id, nome, valor, email, senha)
    SALES_GROUP_ID = -1002697063035
    user_data = api.load_user_data(user_id) or {}
    username = user_data.get('username', f"{user_id}")
    horario_brasil = datetime.datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M:%S")
    sale_message = (
        f"🛍️ Nova venda realizada!\n\n"
        f"🔑 Login: {nome}\n"
        f"🕒 Horário: {horario_brasil}"
    )
    try:
        bot.send_message(SALES_GROUP_ID, sale_message, parse_mode='HTML')
    except Exception as e:
        print(f"Erro ao enviar mensagem de venda: {e}")
    try:
        dono_id = api.CredentialsChange.id_dono()
        import html # Importa a biblioteca para formatação segura
        # --- Bloco Adicionado: Busca de detalhes do usuário ---
        try:
            chat_info = bot.get_chat(user_id)
            # Usa html.escape para evitar erros de formatação
            user_display_name = html.escape(chat_info.first_name or f"ID {user_id}")
            user_username = f"@{chat_info.username}" if chat_info.username else "Não possui"
        except Exception:
            user_display_name = f"ID {user_id}"
            user_username = "Não foi possível obter"
        # --- Fim do Bloco Adicionado ---
        # Construindo o log manualmente com os novos detalhes
        log_text = (
            f"<b>LOG DE COMPRA (Inline)</b>\n\n"
            f"<b>Nome:</b> {user_display_name}\n"
            f"<b>Username:</b> {user_username}\n"
            f"<b>ID user:</b> <code>{user_id}</code>\n\n"
            f"<b>Serviço:</b> {html.escape(nome)}\n"
            f"<b>Valor:</b> R${valor}\n"
            f"<b>Email:</b> <code>{html.escape(email)}</code>\n"
            f"<b>Senha:</b> <code>{html.escape(senha)}</code>\n"
            f"<b>Descrição:</b> {html.escape(descricao)}\n"
            f"<b>Validade:</b> {duracao} dias\n"
            f"<b>Data:</b> {data_atual_formatada}\n"
            f"<b>Vencimento:</b> {data_venc_formatada}" # <-- LINHA ADICIONADA
        )
        bot.send_message(dono_id, log_text, parse_mode='HTML')
    except Exception as e:
        # Mensagem de erro caso a nova lógica falhe
        bot.send_message(api.CredentialsChange.id_dono(), f'Falha ao enviar o log (construção manual)!\nMotivo: {e}')
def pegar_primeiro_disponivel(servico, buyer_id, sale_id):
    return api.ControleLogins.pegar_primeiro_disponivel(servico, buyer_id, sale_id)

def entregar_inline(user_id, nome, valor, email, senha, descricao, duracao, login_mostrado):
    import datetime, pytz
    data_atual = datetime.datetime.now(pytz.timezone("America/Sao_Paulo"))
    data_atual_formatada = data_atual.strftime("%d/%m/%Y %H:%M:%S")
    data_venc = data_atual + datetime.timedelta(days=int(duracao))
    data_venc_formatada = data_venc.strftime("%d/%m/%Y")
    descricao = descricao.replace('\n', '\n')
    texto_entrega = (
        f"✅ <b>Login Entregue!</b>\n\n"
        f"<b>Tipo:</b> {nome}\n"
        f"👤 <b>Usuário:</b> {email}\n"
        f"🔑 <b>Senha:</b> {senha}\n"
        f"🕒 <b>Validade:</b> {duracao} dia(s)\n"
        f"(de {data_atual_formatada} até {data_venc_formatada})\n\n"
        f"<i>{descricao}</i>"
    )
    from telebot.types import InlineKeyboardMarkup
    purchase_info = add_purchase(
        user_id,
        nome,
        email,
        senha,
        valor,
        int(duracao)
    )
    purchase_id = purchase_info['id']
    markup = InlineKeyboardMarkup()
    _montar_botoes_extras(markup, purchase_id, email, senha, nome)
    bot.send_message(
        chat_id=user_id,
        text=texto_entrega,
        parse_mode='HTML',
        reply_markup=markup if markup.keyboard else None
    )
    api.MudancaHistorico.add_compra(user_id, nome, valor, email, senha)
    SALES_GROUP_ID = -1002697063035   
    user_data = api.load_user_data(user_id) or {}
    username = user_data.get('username', None)
    if not username:
        username = f"{user_id}"
    horario_brasil = datetime.datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M:%S")
    sale_msg = (
        f"🛍️ Nova venda realizada!\n\n"
        f"🔑 Login: {nome}\n"
        f"🕒 Horário: {horario_brasil}"
    )
    try:
        bot.send_message(SALES_GROUP_ID, sale_msg, parse_mode='HTML')
    except Exception as e:
        print(f"Erro ao enviar mensagem de venda no grupo: {e}")
    dono_id = api.CredentialsChange.id_dono()
    try:
        log_text = (
            f"<b>LOG DE COMPRA (Inline)</b>\n\n"
            f"ID user: {user_id}\n"
            f"Serviço: {nome}\n"
            f"Valor: R${valor}\n"
            f"Email: {email}\n"
            f"Senha: {senha}\n"
            f"Descrição: {descricao}\n"
            f"Validade: {duracao} dias\n"
            f"Data: {data_atual_formatada}"
        )
        bot.send_message(dono_id, log_text, parse_mode='HTML')
    except Exception as e:
        print(f"Erro ao enviar log pro dono: {e}")
@bot.callback_query_handler(func=lambda call: call.data == "cancelarInline")
def cancelar_inline(call):
    if call.inline_message_id: 
        bot.edit_message_text(
            inline_message_id=call.inline_message_id,
            text="Operação cancelada."
        )
        bot.send_message(call.from_user.id, "Começar novamente ? /start")
    else:
        chat_id = call.message.chat.id
        message_id = call.message.message_id  
        bot.delete_message(chat_id, message_id)
        enviar_menu_inicial(call.message)
@bot.callback_query_handler(func=lambda c: c.data == 'config_alertas')
def callback_config_alertas(call):
    bot.answer_callback_query(call.id)   # <-- adiciona esta linha
    texto = "🔔 *Configuração de Alertas*\nEscolha o que deseja fazer:"
    markup = InlineKeyboardMarkup(row_width=2)
    markup.row(
        InlineKeyboardButton('➕ Adicionar Palavra', callback_data='admin_addalert_prompt'),
        InlineKeyboardButton('➖ Remover Palavra',   callback_data='admin_removealert_prompt')
    )
    markup.row(InlineKeyboardButton('↩ Voltar', callback_data='voltar_paineladm'))
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=texto,
        parse_mode='Markdown',
        reply_markup=markup
    )
@bot.callback_query_handler(func=lambda c: c.data == 'editar_link_canal')
def callback_editar_link_canal(call):
    """Handler para editar o link do canal"""
    bot.answer_callback_query(call.id)
    msg = bot.send_message(
        call.message.chat.id,
        "📝 <b>Digite o novo link do canal:</b>\n\n"
        "<i>Exemplo: https://t.me/+z06ZYa4CplVlMWMx</i>",
        parse_mode='HTML',
        reply_markup=types.ForceReply(selective=True)
    )
    bot.register_next_step_handler(msg, handle_editar_link_canal)
def handle_editar_link_canal(message):
    """Processa a edição do link do canal"""
    novo_link = message.text.strip()
    try:
        # Salva o novo link
        api.CanalObrigatorio.set_link_canal(novo_link)
        bot.reply_to(message, f"✅ Link do canal atualizado!", parse_mode='HTML')
    except Exception as e:
        bot.reply_to(message, f"❌ Erro ao atualizar link: {e}")
    # Volta ao painel admin
    painel_admin(message)
# ========================================================
@bot.callback_query_handler(func=lambda call: call.data == 'admin_addalert_prompt')
def callback_admin_addalert_prompt(call):
    bot.answer_callback_query(call.id)   # confirma o callback pro Telegram
    msg = bot.send_message(
        call.message.chat.id,
        "Digite o *nome* da nova palavra-chave de alerta:",
        parse_mode='Markdown',
        reply_markup=types.ForceReply(selective=True)
    )
    bot.register_next_step_handler(msg, handle_admin_addalert)
def handle_admin_addalert(message):
    key = message.text.strip().lower()
    if key in alerts:
        bot.reply_to(message, f"🔔 `{key}` já existe.", parse_mode='Markdown')
    else:
        alerts[key] = []
        save_alerts(alerts)
        bot.reply_to(message, f"✅ Alerta `{key}` adicionado.", parse_mode='Markdown')
    painel_admin(message)   
@bot.callback_query_handler(func=lambda call: call.data == 'admin_removealert_prompt')
def callback_admin_removealert_prompt(call):
    if not alerts:
        return bot.answer_callback_query(call.id, "⚠️ Não há alertas para remover.", show_alert=True)
    lista = "\n".join(f"- {k}" for k in alerts)
    msg = bot.send_message(
        call.message.chat.id,
        f"*Alertas atuais:*\n{lista}\n\nDigite o *nome* da palavra a remover:",
        parse_mode='Markdown',
        reply_markup=types.ForceReply()
    )
    bot.register_next_step_handler(msg, handle_admin_removealert)
def handle_admin_removealert(message):
    key = message.text.strip().lower()
    if key not in alerts:
        bot.reply_to(message, f"🔕 `{key}` não encontrado.", parse_mode='Markdown')
    else:
        del alerts[key]
        save_alerts(alerts)
        bot.reply_to(message, f"✅ Alerta `{key}` removido.", parse_mode='Markdown')
    painel_admin(message)
@bot.callback_query_handler(func=lambda c: c.data == 'menu_categorias_servicos')
def callback_voltar_categorias(call):
    bot.answer_callback_query(call.id)   
    try:
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    except Exception as e:
        print(f"Não foi possível deletar a mensagem de logins: {e}")
    menu_categorias_servicos(call.message)
@bot.callback_query_handler(func=lambda c: c.data == 'alertas_user')
def callback_alertas_user(call):
    bot.answer_callback_query(call.id)
    try:
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    except Exception as e:
        print(f"Não foi possível deletar a mensagem de alertas: {e}")
    texto = "🔔 *Gerencie seus alertas:*"
    markup = gerar_menu_alertas_para(call.from_user.id)
    bot.send_message(
        chat_id=call.message.chat.id,
        text=texto,
        parse_mode='Markdown',
        reply_markup=markup
    )
def gerar_menu_alertas_para(uid):
    markup = InlineKeyboardMarkup(row_width=2)
    for chave in alerts:
        inscrito = uid in alerts[chave]
        emoji    = '✅' if inscrito else '🔘'
        btn      = InlineKeyboardButton(
            f"{emoji} {chave.upper()}",
            callback_data=f"alert_toggle|{chave}"
        )
        markup.add(btn)
    # opcional: botão para voltar ao menu principal
    markup.add(InlineKeyboardButton("↩ Voltar ao menu", callback_data="menu_start"))
    return markup
@bot.callback_query_handler(func=lambda c: c.data.startswith("cart_show_"))
def cb_cart_show(call):
    page = int(call.data.split("_")[2])
    cart_show_products(call.from_user.id, page, call.message)
    bot.answer_callback_query(call.id)
    _schedule_cart_expire(call.from_user.id)        
@bot.callback_query_handler(func=lambda c: c.data.startswith("cart_add|"))
def cb_cart_add(call):
    serv = call.data.split("|", 1)[1]
    uid = call.from_user.id
    carr = user_carts.setdefault(uid, {})
    # --- VERIFICAÇÃO DE ESTOQUE ANTES DE ADICIONAR ---
    try:
        # Pega a quantidade real disponível no banco de dados
        estoque_real = api.ControleLogins.pegar_estoque(serv)
    except Exception:
        estoque_real = 0
    # Pega quantos o usuário JÁ colocou no carrinho
    qtd_no_carrinho = carr.get(serv, 0)
    # Se tentar adicionar mais do que existe, bloqueia
    if qtd_no_carrinho + 1 > estoque_real:
        bot.answer_callback_query(
            call.id, 
            f"⚠️ Estoque insuficiente! Apenas {estoque_real} disponíveis.", 
            show_alert=True
        )
        return
    # --- VERIFICAÇÃO DE LIMITE DA OFERTA RELÂMPAGO ---
    try:
        from app import Oferta_relampago
        # Mesma correção da seção de serviços e estoque: usa a oferta
        # específica deste produto, não apenas a primeira oferta ativa da lista.
        oferta = Oferta_relampago._achar_oferta(serv)
        if oferta:
            limite = int(oferta.get("limite_quantidade", 0))
            if limite > 0 and (qtd_no_carrinho + 1) > limite:
                bot.answer_callback_query(
                    call.id, 
                    f"⚠️ Limite excedido! Na Oferta Relâmpago o máximo é {limite} unidade(s).", 
                    show_alert=True
                )
                return
    except Exception as e:
        pass
    # -------------------------------------------------
    carr[serv] = carr.get(serv, 0) + 1
    bot.answer_callback_query(call.id, "✅ Adicionado ao carrinho")
    cart_update_or_send_summary(uid)
    _schedule_cart_expire(uid)
@bot.callback_query_handler(func=lambda c: c.data == "cart_cancel")
def cb_cart_cancel(call):
    uid = call.from_user.id
    user_carts.pop(uid, None)
    user_cart_msgs.pop(uid, None)
    _cancel_cart_timer(uid)                          
    bot.answer_callback_query(call.id, "Carrinho cancelado!")
    bot.delete_message(call.message.chat.id, call.message.message_id)
@bot.callback_query_handler(func=lambda c: c.data == "cart_buy")
@estoque_api.serializar(bot)
def cb_cart_buy(call):
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    uid  = call.from_user.id
    carr = user_carts.get(uid, {})
    if not carr:
        return bot.answer_callback_query(call.id, "Carrinho vazio.", show_alert=True)
    # --- Calcula o total ---
    total = 0
    for serv, qtd in carr.items():
        info = api.ControleLogins.peek_primeiro_disponivel(serv)
        if info:
            # --- VERIFICAÇÃO DE OFERTA RELÂMPAGO ---
            try:
                from app import Oferta_relampago
                preco_final = Oferta_relampago.verificar_preco(serv, float(info[1]))
            except Exception:
                preco_final = float(info[1])
            # ---------------------------------------
            total += preco_final * qtd
    # --- Verifica Saldo ---
    saldo_atual = get_user_balance(uid)
    # CORREÇÃO: Arredondar para evitar erro
    saldo_atual = round(saldo_atual, 2)
    total = round(total, 2)
    if saldo_atual < total:
        falta = total - saldo_atual
        bot.answer_callback_query(call.id, "Saldo insuficiente!", show_alert=False)
        markup_pix = InlineKeyboardMarkup()
        markup_pix.row(InlineKeyboardButton(f"💳 Depositar R$ {falta:.2f} via PIX", callback_data=f"pix_quick {falta:.2f}"))
        markup_pix.row(InlineKeyboardButton("🛒 Voltar ao Carrinho", callback_data="mostrar_carrinho"))
        texto_falta = (
            f"❌ <b>Saldo Insuficiente</b>\n\n"
            f"Faltam <b>R$ {falta:.2f}</b> para você levar todos os itens do carrinho.\n\n"
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
    # Cada unidade só é cobrada se a API retornar seu acesso.
    adquiridos = {}
    total_pago = 0.0
    interrompido = False
    for serv, qtd in list(carr.items()):
        if interrompido:
            break
        info_preco = api.ControleLogins.peek_primeiro_disponivel(serv)
        if not info_preco:
            continue
        preco_entrega = Oferta_relampago.verificar_preco(serv, float(info_preco[1]))
        for indice in range(qtd):
            try:
                dados = estoque_api.comprar(api, serv, uid,
                    f"carrinho:{uid}:{call.message.message_id}:{serv}:{indice}", preco_entrega)
            except estoque_api.EstoqueAPIError as exc:
                bot.send_message(uid, str(exc))
                interrompido = True
                break
            if not dados:
                break
            nome, valor, email, senha, desc, dias = dados
            adquiridos[serv] = adquiridos.get(serv, 0) + 1
            total_pago += valor
            # Retira antes de enviar: uma falha do Telegram não deve comprar outra conta.
            carr[serv] -= 1
            try:
                entregar(call.message, nome, valor, email, senha, desc, dias)
            except Exception:
                bot.send_message(uid, "Acesso reservado e salvo. Contate o suporte para recuperar a entrega.")
                interrompido = True
                break
    restantes = {serv: qtd for serv, qtd in carr.items() if qtd > 0}
    if restantes:
        user_carts[uid] = restantes
        user_cart_msgs.pop(uid, None)
    else:
        user_carts.pop(uid, None)
        user_cart_msgs.pop(uid, None)
        _cancel_cart_timer(uid)
    if total_pago:
        sistema_cashback_vip.processar_compra_cashback(bot, uid, total_pago)
    resumo = "\n".join(f"• {nome} (x{qtd})" for nome, qtd in adquiridos.items()) or "Nenhum item comprado."
    bot.answer_callback_query(call.id, "Processamento finalizado.")
    bot.send_message(uid, f"🛒 Compras confirmadas:\n{resumo}\nTotal cobrado: R$ {total_pago:.2f}\n"
                     + ("Os itens restantes continuam no carrinho. Abra o carrinho novamente." if restantes else "Carrinho concluído."))
# ───────────────────────────────────────────────────────────────
#  utilidades para controlar expiração de carrinho
# ─────────────────────��─────────────────────────────────────────
CART_TTL = 1800                   # 30 min = 1 800 s
cart_timers: dict[int, threading.Timer] = {}
def _schedule_cart_expire(uid: int):
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    t_old = cart_timers.pop(uid, None)
    if t_old:
        t_old.cancel()
    def _expire():
        user_carts.pop(uid, None)
        user_cart_msgs.pop(uid, None)
        bot.send_message(
            uid,
            "⏰ Seu carrinho foi descartado por inatividade (30 min).",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🏠 Menu inicial", callback_data="menu_start")
            )
        )
    t = threading.Timer(CART_TTL, _expire)
    t.daemon = True
    t.start()
    cart_timers[uid] = t
def _cancel_cart_timer(uid: int):
    t = cart_timers.pop(uid, None)
    if t:
        t.cancel()
# === HANDLERS DE AVISOS DE ESTOQUE ===
def salvar_novo_minimo_painel(message):
    try:
        valor_str = message.text.replace(',', '.').strip()
        valor = float(valor_str)
        api.CredentialsChange.InfoPix.trocar_deposito_minimo_pix(valor)
        bot.reply_to(message, f"✅ Depósito mínimo alterado para R$ {valor:.2f}")
        exibir_painel_pagamentos(message)
    except ValueError:
        bot.reply_to(message, "❌ Valor inválido. Use apenas números.")
    except Exception as e:
        bot.reply_to(message, f"❌ Erro ao salvar: {e}")
def salvar_novo_maximo_painel(message):
    try:
        valor_str = message.text.replace(',', '.').strip()
        valor = float(valor_str)
        api.CredentialsChange.InfoPix.trocar_deposito_maximo_pix(valor)
        bot.reply_to(message, f"✅ Depósito máximo alterado para R$ {valor:.2f}")
        exibir_painel_pagamentos(message)
    except ValueError:
        bot.reply_to(message, "❌ Valor inválido. Use apenas números.")
    except Exception as e:
        bot.reply_to(message, f"❌ Erro ao salvar: {e}")
def salvar_novo_valor_taxa_painel(message):
    from app.config_pagamentos import salvar_valor_taxa_intermediador
    try:
        valor_str = message.text.replace(',', '.').strip()
        valor = float(valor_str)
        if valor < 0:
            bot.reply_to(message, "❌ O valor da taxa não pode ser negativo.")
            return
        salvar_valor_taxa_intermediador(valor)
        bot.reply_to(message, f"✅ Valor da taxa do intermediador alterado para R$ {valor:.2f}")
        exibir_painel_pagamentos(message)
    except ValueError:
        bot.reply_to(message, "❌ Valor inválido. Use apenas números (ex: 0.50).")
    except Exception as e:
        bot.reply_to(message, f"❌ Erro ao salvar: {e}")
def salvar_novo_limite_isencao_painel(message):
    from app.config_pagamentos import salvar_limite_isencao_taxa
    try:
        valor_str = message.text.replace(',', '.').strip()
        valor = float(valor_str)
        if valor < 0:
            bot.reply_to(message, "❌ O valor do limite não pode ser negativo.")
            return
        salvar_limite_isencao_taxa(valor)
        bot.reply_to(message, f"✅ Limite de isenção da taxa alterado! Agora a taxa só é cobrada em PIX abaixo de R$ {valor:.2f}")
        exibir_painel_pagamentos(message)
    except ValueError:
        bot.reply_to(message, "❌ Valor inválido. Use apenas números (ex: 30.00, 50.00, 100.00).")
    except Exception as e:
        bot.reply_to(message, f"❌ Erro ao salvar: {e}")
@bot.callback_query_handler(func=lambda call: call.data == "voltar_admin")
def handle_voltar_admin(call):
    """Volta para o painel admin principal"""
    # Simular comando /admin para recriar o painel
    message = call.message
    message.text = '/admin'
    painel_admin(message)
# CÓDIGO CORRIGIDO
# ==========================================================
# CORREÇÃO: Handler Exclusivo para Resgatar Gift Card
# ==========================================================
@bot.callback_query_handler(func=lambda c: c.data.startswith('resgatar '))
def callback_resgatar_gift_prioridade(call):
    try:
        bot.answer_callback_query(call.id, "Processando...")
        # Pega o código após o espaço
        codigo = call.data.split()[1]
        # Chama sua função de processamento existente
        processar_resgate(call.from_user.id, codigo)
    except Exception as e:
        print(f"Erro ao resgatar: {e}")

# ----------------------------------------------------------

# ==================== CALLBACK GERAL ====================
@bot.callback_query_handler(func=lambda call: not call.data.startswith('stock_api_')
                                       and call.data != 'relatorio_trocas'
                                       and not call.data.startswith('gerar_relatorio_trocas_')
                                       and not call.data.startswith('exibir_promocao ')
                                       and not call.data.startswith('comprar_promocao ')
                                       and call.data != 'mostrar_promocoes'
                                       and call.data != 'configurar_promocoes'
                                       # ADIÇÃO: ignorar callbacks de aprovação/recusa de usuários
                                       and not call.data.startswith('approve_user_')
                                       and not call.data.startswith('deny_user_')
                                       and call.data not in ('admin_maintenance_message', 'admin_maintenance_message_default', 'admin_maintenance_cancel')
                                       # ADIÇÃO: ignorar callbacks do sistema de afiliados
                                       and call.data not in ('ver_indicacoes', 'ranking_indicadores', 'meu_link', 'admin_toggle_afiliados', 'admin_refresh_afiliados', 'admin_alterar_valor_indicacao', 'admin_stats_afiliados')
                                       # ADIÇÃO: ignorar callback de baixar histórico
                                       and not call.data.startswith('baixar_historico ')
 and not call.data.startswith('baixar_historico_30 ')
                                       # ADIÇÃO: ignorar callbacks dos botões "Ver Todas" / "Apenas Ativas" do /historico
                                       and not call.data.startswith('historico_ativas ')
                                       and not call.data.startswith('historico_todas ')
                                       # ADIÇÃO: ignorar callbacks da prévia/confirmação de abastecimento (/add)
                                       and not call.data.startswith('abast_confirmar_todos ')
                                       and not call.data.startswith('abast_confirmar_novos ')
                                       and not call.data.startswith('abast_cancelar ')
                                       # ================== CORREÇÃO ADICIONADA AQUI ==================
                                       and call.data != 'editar_textos_bot'
                                       and not call.data.startswith('edit_text_')
                                       # --- ADICIONAR ESTA LINHA ---
                                       and call.data != 'toggle_report_problem'
                                       # --- [ADICIONE ESTA NOVA EXCLUSÃO AQUI] ---
                                       and call.data != 'toggle_menu_categorias'
                                       # --- [ADICIONE ESTA NOVA EXCLUSÃO AQUI] ---
                                       and call.data != 'admin_gerenciar_bonus'
                                       # === CORREÇÕES DA CAIXA MISTERIOSA ===
                                       and call.data != 'comprar_caixa_misteriosa'
                                       and call.data != 'confirmar_compra_caixa'
                                       and call.data != 'admin_menu_caixa'
                                       and not call.data.startswith('admin_caixa_')
                                       # === VENCIMENTOS ===
                                       and call.data != 'menu_vencimentos'
                                       and call.data not in ['venc_hoje', 'venc_amanha']
                                       and call.data != 'menu_renovacao'
                                       and not call.data.startswith('renovar_conta_')
                                       and call.data != 'adm_renov_apps'
                                       and not call.data.startswith('tgl_renov_')
                                       and call.data != 'menu_ver_renovadas'
                                       and not call.data.startswith('rel_renov_')
                                       and call.data not in ['renovar_1', 'renovar_2', 'renovar_3', 'renovar_bot', 'voltar_vencido']
                                       # === CORREÇÃO: botão HISTÓRICO do perfil não respondia ===
                                       and call.data != 'ver_historico_perfil'
                                       # === GERENCIAR SALDOS (novo submenu do painel admin) ===
                                       and call.data != 'admin_gerenciar_saldos'
                                       and not call.data.startswith('saldos_')
                                       )
def callback_query(call):
    # Ignorar callbacks que são tratados por handlers específicos
    if call.data.startswith('cancel_notif_') or call.data.startswith('reativar_notif_'):
        return  # Deixa os handlers específicos tratarem
    # Configurar botões
    if call.data == 'config_alertas':
        bot.answer_callback_query(call.id)
        texto = "🔔 *Configuração de Alertas*\nEscolha o que deseja fazer:"
        markup = InlineKeyboardMarkup(row_width=2)
        markup.row(
            InlineKeyboardButton('➕ Adicionar Palavra', callback_data='admin_addalert_prompt'),
            InlineKeyboardButton('➖ Remover Palavra',   callback_data='admin_removealert_prompt')
        )
        markup.row(InlineKeyboardButton('↩ Voltar', callback_data='voltar_paineladm'))
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=texto,
                parse_mode='Markdown',
                reply_markup=markup
            )
        except Exception as e:
            print("Erro ao editar Configurar Alertas:", e)
        return
    if call.data == 'servicos':
        # Esta é a ação do botão "Ver Todos os Produtos".
        # Ele deve SEMPRE mostrar a lista completa de serviços, paginada.
        servicos(call.message, page=1)
        return
    if call.data.startswith("servicos_categoria"):
        parts = call.data.split()
        if len(parts) >= 2:
            categoria = parts[1]
            servicos_por_categoria(call.message, categoria, page=1) # Adicionado page=1
        return
    if call.data == 'menu_categorias_servicos':
        servicos(call.message)
        return
    # ... (dentro da função callback_query)
    tipos_rankings = [
        'rank_products', 'rank_depositors', 'rank_top_spenders', 
        'rank_gifts', 'rank_balance', 'rank_indicacoes'
    ]
    if call.data in tipos_rankings:
        atualizar_mensagem_rank(call, call.data)
        return
    if call.data == 'menu_start':
        texto = api.Textos.start(call.message)
        markup = gerar_menu_principal()
        from app import interface as fotos_menus
        foto = fotos_menus.obter_foto_menu('start') or api.FOTO_MENU_PRINCIPAL
        resultado = fotos_menus.exibir_com_foto(bot, call.message.chat.id, call.message.message_id, foto, texto, reply_markup=markup)
        if resultado is None:
            try:
                bot.send_message(call.message.chat.id, texto, parse_mode='HTML', reply_markup=markup)
            except Exception as e:
                print(f"Erro crítico ao abrir menu principal (callback_geral): {e}")
        return
    if call.data == 'ver_termos':
        bot.send_message(call.message.chat.id, termos_texto, parse_mode='HTML')
    if call.data == 'ver_rank':
      handle_rank(call.message)
    if call.data == 'mudar_token_bot':
        bot.send_message(call.message.chat.id, "Envie o novo token do bot:", reply_markup=types.ForceReply())
        bot.register_next_step_handler(call.message, trocar_token)
        return
    if call.data == 'pegar_admin_creator':
        if api.Admin.verificar_admin(call.message.chat.id) == False:
            api.Admin.add_admin(call.message.chat.id)
            bot.answer_callback_query(call.id, "Feito!", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "Você já é um admin!", show_alert=True)
    if call.data == 'mudar_user_bot':
        bot.send_message(call.message.chat.id, "Me envie o novo @ do bot:", reply_markup=types.ForceReply())
        bot.register_next_step_handler(call.message, trocar_user)
        return
    if call.data == 'mudar_dono_bot':
        bot.send_message(call.message.chat.id, "Digite o id do novo dono:", reply_markup=types.ForceReply())
        bot.register_next_step_handler(call.message, mudar_dono_bot)
        return
    if call.data == 'configurar_vencimento':
        txt = '<i>Selecione abaixo a opção desejada:</i>'
        bt = InlineKeyboardButton('➕ AUMENTAR DIAS', callback_data='modificar_dias mais')
        bs = InlineKeyboardButton('➖ DIMINUIR DIAS', callback_data='modificar_dias menos')
        bp = InlineKeyboardButton('⭕ ZERAR DIAS', callback_data='parar_dias_creator')
        vo = InlineKeyboardButton('↩ VOLTAR', callback_data='voltar_painel_creator')
        markup = InlineKeyboardMarkup([[bt], [bs], [bp], [vo]])
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=txt,
            parse_mode='HTML',
            reply_markup=markup
        )
        return
    if call.data == 'parar_dias_creator':
        api.Admin.zerar_vencimento()
        bot.reply_to(call.message, "Os dias foram zerados!")
        return
    if call.data.split()[0] == 'modificar_dias':
        tipo = call.data.split()[1]
        bot.send_message(call.message.chat.id, "Digite a quantidade de dias:", reply_markup=types.ForceReply())
        bot.register_next_step_handler(call.message, mudar_dias_vencimento, tipo)
        return
    if call.data == 'mudar_versao_bot':
        bot.send_message(call.message.chat.id, "Digite a nova versão do bot:", reply_markup=types.ForceReply())
        bot.register_next_step_handler(call.message, mudar_versao_bot)
    if call.data == 'configurar_pagamentos':
        bot.answer_callback_query(call.id)
        exibir_painel_pagamentos(call.message)
        return
    # --- LÓGICA DOS BOTÕES DE PAGAMENTO (COLADO AQUI PARA FUNCIONAR) ---
    if call.data == 'trocar_pix_manual':
        api.CredentialsChange.ChangeStatusPix.change_pix_manual()
        bot.answer_callback_query(call.id, "Status alterado!", show_alert=True)
        exibir_painel_pagamentos(call.message)
        return
    if call.data == 'mudar_deposito_minimo':
        bot.answer_callback_query(call.id)
        msg = bot.send_message(
            call.message.chat.id,
            "📉 <b>Alterar Depósito Mínimo</b>\n\nDigite o novo valor mínimo (ex: 5.00):",
            parse_mode='HTML',
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, salvar_novo_minimo_painel)
        return
    if call.data == 'mudar_deposito_maximo':
        bot.answer_callback_query(call.id)
        msg = bot.send_message(
            call.message.chat.id,
            "📈 <b>Alterar Depósito Máximo</b>\n\nDigite o novo valor máximo (ex: 500.00):",
            parse_mode='HTML',
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, salvar_novo_maximo_painel)
        return
    # -------------------------------------------------------------------
    if call.data == 'alterar_token_promissepay':
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "Envie o novo token (API key) do PromissePay:", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, salvar_novo_token_promissepay)
        return
    if call.data == 'configurar_misticpay':
        bot.answer_callback_query(call.id)
        msg = bot.send_message(
            call.message.chat.id,
            "🔑 <b>Configurar MisticPay</b>\n\nEnvie o <b>Client ID</b> e <b>Client Secret</b> separados por espaço.\n\nExemplo:\n<code>seu_client_id seu_client_secret</code>",
            parse_mode='HTML',
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, processar_credenciais_misticpay)
        return
    if call.data == 'alterar_token_mercadopago':
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "Envie o novo Access Token do Mercado Pago:", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, salvar_novo_token_mercadopago)
        return
    if call.data == 'trocar_gateway':
        trocar_gateway_ativo(call)
        return
    if call.data == 'trocar_auto_gateway':
        alternar_troca_automatica_gateway(call)
        return
    if call.data == 'trocar_taxa_intermediador':
        alternar_taxa_intermediador_pix(call)
        return
    if call.data == 'mudar_valor_taxa':
        bot.answer_callback_query(call.id)
        msg = bot.send_message(
            call.message.chat.id,
            "💰 <b>Alterar Valor da Taxa do Intermediador</b>\n\nDigite o novo valor fixo da taxa (ex: 0.30, 0.50, 1.00):",
            parse_mode='HTML',
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, salvar_novo_valor_taxa_painel)
        return
    if call.data == 'mudar_limite_isencao_taxa':
        bot.answer_callback_query(call.id)
        msg = bot.send_message(
            call.message.chat.id,
            "🎯 <b>Alterar Limite de Isenção da Taxa</b>\n\nDigite a partir de qual valor de PIX a taxa do intermediador deixa de ser cobrada (ex: 30.00, 50.00, 100.00):",
            parse_mode='HTML',
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, salvar_novo_limite_isencao_painel)
        return
    if call.data == 'voltar_painel_creator':
        # call.message.from_user é o BOT (dono da mensagem editada), não quem clicou.
        # handle_criador() valida a identidade do criador olhando from_user.id, então
        # sem essa correção a checagem falha sempre e o botão parece "não responder".
        call.message.from_user = call.from_user
        handle_criador(call.message)
        return
    if call.data == 'stats_criador':
        exibir_stats_criador(call.message)
        return
    try:
        if api.InfoUser.verificar_ban(call.message.chat.id) == True:
            bot.reply_to(call.message, "Você está banido neste bot e não pode utiliza-lo!")
            return
    except:
        if api.InfoUser.verificar_ban(call.from_user.id) == True:
            bot.reply_to(call.message, "Você está banido neste bot e não pode utiliza-lo!")
            return
    # Verificar manutenção (sistema novo tem prioridade)
    if is_on():
        if not (api.Admin.verificar_admin(call.message.chat.id) or int(call.message.chat.id) == int(api.CredentialsChange.id_dono())):
            maintenance_msg = get_maintenance_message()
            bot.answer_callback_query(call.id, maintenance_msg, show_alert=True)
            return
    elif api.CredentialsChange.status_manutencao() == True:
        if api.Admin.verificar_admin(call.message.chat.id) == False:
            if api.CredentialsChange.id_dono() != int(call.message.chat.id):
                bot.answer_callback_query(call.id, "O bot esta em manutenção, voltaremos em breve!", show_alert=True)
                return
        bot.answer_callback_query(call.id, "O bot está em manutenção, mas você foi identificado como administrador!", show_alert=True)
    if api.Admin.verificar_vencimento() == True:
        ver_se_expirou()
        return
    # =============== Voltar painel adm
    if call.data == 'voltar_paineladm':
        painel_admin(call.message)
    # =============== Menu inicial
    if call.data == 'perfil':
        perfil(call.message)
    if call.data == 'servicos':
        servicos(call.message)
    if call.data == 'addsaldo':
        addsaldo(call.message)
    # =============== Menu Pix
    if call.data == 'pix_manu':
        if api.CredentialsChange.StatusPix.pix_manual() == True:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f'{api.Textos.pix_manual(call.message)}',
                parse_mode='HTML'
            )
  # ... (próximo à linha 6176)
    if call.data == 'pix_auto':
        if api.CredentialsChange.StatusPix.pix_auto() == True:
            bot.send_message(
                chat_id=call.message.chat.id,
                text=(
                    f"Digite o valor que deseja recarregar!\n"
                    f"mínimo: R${api.CredentialsChange.InfoPix.deposito_minimo_pix():.2f}\n"
                    f"máximo: R${api.CredentialsChange.InfoPix.deposito_maximo_pix():.2f}"
                ),
                reply_markup=types.ForceReply()
            )
            # A função agora é a mesma do Passo 1, que está corretamente definida
            bot.register_next_step_handler(call.message, processar_valor_recarga) # <--- LINHA CORRIGIDA
    # =============== Menu serviços (from category)
    if call.data.startswith('exibir_servico_cat '):
        try:
            parts = call.data.split(maxsplit=2)
            categoria = parts[1]
            nome = parts[2]
            # O callback de retorno deve reabrir a lista da categoria
            return_cb = f"servicos_categoria {categoria}"
            exibir_servico(call.message, nome, return_callback=return_cb)
        except Exception as e:
            print(f"Erro no handler exibir_servico_cat: {e}")
            # Fallback para o handler genérico
            exibir_servico(call.message, call.data.split(maxsplit=1)[-1])
        return # Importante para parar a execução
    # =============== Menu serviços (generic)
    if call.data.split()[0] == 'exibir_servico':
        nome = call.data.split()[1:]
        nome = ' '.join(nome)
        exibir_servico(call.message, nome) # Isso usará o 'servicos' padrão como retorno
    # =============== Menu perfil
    # Bloco de código "trocar_pontos" foi removido. Não cole nada aqui.
    if call.data == 'menu_start':
        handle_start(call.message)
    # =============== Configurações gerais
    if call.data == 'reiniciar_bot':
        bot.answer_callback_query(call.id, "Reiniciando...", show_alert=True)
        safe_exit("acao do bot")
    if call.data == 'configuracoes_geral':
        configuracoes_geral(call.message)
    if call.data == 'manutencao':
        api.CredentialsChange.mudar_status_manutencao()
        bot.answer_callback_query(call.id, "Status de manutenção atualizado com sucesso!", show_alert=True)
        configuracoes_geral(call.message)
    if call.data == 'toggle_menu_categorias':
        if not is_admin_user(call.from_user.id):
            return bot.answer_callback_query(call.id, "🚫 Acesso Negado!", show_alert=True)
        novo_estado = alternar_menu_categorias()
        status_str = "ativado 🟢" if novo_estado else "desativado 🔴"
        bot.answer_callback_query(call.id, f"Menu de Categorias {status_str} com sucesso!", show_alert=True)
        configuracoes_geral(call.message)
    if call.data == 'suporte':
        bot.send_message(
            chat_id=call.message.chat.id,
            text="Me envie o novo link do suporte:",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(call.message, trocar_suporte, call.id)
    if call.data == 'mudar_separador':
        bot.send_message(
            call.message.chat.id,
            "Digite o novo separador:",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(call.message, mudar_separador, call.id)
    # =============== Configurações de login (ver gerenciamento_logins.py)
    if call.data == 'configurar_logins':
        logins_mgr.configurar_logins(call.message)
    if call.data == 'adicionar_login':
        separador = api.CredentialsChange.separador()
        bot.send_message(
            call.message.chat.id,
            f"Envie os acessos que deseja adicionar, no formato:\nNOME{separador}VALOR{separador}DESCRICAO{separador}EMAIL{separador}SENHA{separador}DURACAO",
            parse_mode='HTML',
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(call.message, logins_mgr.adicionar_login)
    if call.data == 'adicionar_login_massa':
        msg = bot.send_message(
            call.message.chat.id,
            "📦 <b>Abastecimento em Massa</b>\n\n"
            "Envie os detalhes do serviço no formato:\n"
            "<code>Nome / Valor / Descrição / Duração (dias)</code>\n\n"
            "<b>Exemplo:</b> <code>Claro TV / 15.00 / Conta Premium / 30</code>",
            parse_mode='HTML',
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, logins_mgr.receber_detalhes_massa)
    if call.data == 'remover_login':
        # Exibe o novo menu principal de remoção
        logins_mgr.menu_remover_login(call)
        return
    if call.data == 'remover_listar_servicos':
        # Chama a função que lista os serviços (fluxo antigo)
        logins_mgr.listar_servicos_para_remover(call)
        return
    if call.data == 'remover_por_plataforma':
        logins_mgr.remover_por_plataforma(call.message)
    if call.data == 'zerar_estoque':
        try:
            api.ControleLogins.zerar_estoque()
            bot.answer_callback_query(call.id, text="Estoque zerado com sucesso!", show_alert=True)
        except:
            bot.answer_callback_query(call.id, text="Falha ao zerar o estoque.", show_alert=True)
    if call.data == 'mudar_valor_servico':
        bot.send_message(
            call.message.chat.id,
            f"Digite o serviço e o novo valor, separados por {api.CredentialsChange.separador()}\nEx: NETFLIX{api.CredentialsChange.separador()}10",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(call.message, logins_mgr.mudar_valor_servico)
    if call.data == 'mudar_valor_todos':
        bot.send_message(
            call.message.chat.id,
            "Me envie o novo valor dos acessos:",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(call.message, logins_mgr.mudar_valor_todos)
    # =============== Configurações de adms
    if call.data == 'configurar_admins':
        configurar_admins(call.message)
    if call.data == 'adicionar_adm':
        bot.send_message(
            call.message.chat.id,
            "Digite o id do novo adm:",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(call.message, adicionar_adm)
    if call.data == 'remover_adm':
        bot.send_message(
            call.message.chat.id,
            "Digite o id do admin que será removido:",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(call.message, remover_adm)
    if call.data == 'lista_adm':
        try:
            lista = api.Admin.listar_admins()
            bot.send_message(call.message.chat.id, text=lista, parse_mode='HTML')
        except:
            bot.send_message(call.message.chat.id, "Erro ao buscar lista de admin")
    # =============== Configurações dos afiliados
    if call.data == 'configurar_afiliados':
        configurar_afiliados(call.message)
    if call.data == 'mudar_status_afiliados':
        try:
            api.AfiliadosInfo.mudar_status_afiliado()
            bot.answer_callback_query(call.id, "Status alterado com sucesso!", show_alert=True)
            configurar_afiliados(call.message)
        except:
            bot.answer_callback_query(call.id, "Falha ao mudar o status.", show_alert=True)
    if call.data == 'pontos_por_recarga':
        bot.send_message(
            call.message.chat.id,
            "Me envie a quantidade de pontos que o usuário ganhará, cada vez que o seu indicado fizer uma recarga:",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(call.message, pontos_por_recarga)
    if call.data == 'pontos_minimo_converter':
        bot.send_message(
            call.message.chat.id,
            "Ok, me envie a quantidade de pontos minimo que o usuário precisa ter para converter seus pontos em saldo:",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(call.message, pontos_minimo_converter)
    if call.data == 'multiplicador_para_converter':
        bot.send_message(
            call.message.chat.id,
            "Me envie o novo multiplicador:",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(call.message, multiplicador_para_converter)
    # =============== Configurações de usuarios
    if call.data == 'configurar_usuarios':
        configurar_usuarios(call.message)
    if call.data == 'transmitir_todos':
        if api.Admin.verificar_admin(call.message.chat.id) == True or int(call.message.chat.id) == int(api.CredentialsChange.id_dono()):
            api.FuncaoTransmitir.zerar_infos()
            bot.send_message(
                call.message.chat.id,
                "Me envie a mensagem que deseja transmitir:",
                reply_markup=types.ForceReply(),
                parse_mode='HTML'
            )
            bot.register_next_step_handler(call.message, transmitir_todos)
    if call.data == 'add_botao':
        if api.Admin.verificar_admin(call.message.chat.id) == True or int(call.message.chat.id) == int(api.CredentialsChange.id_dono()):
            bot.send_message(
                call.message.chat.id,
                "👉🏻 <b>Agora envie a lista de botões</b> para inserir no teclado embutido, com textos e links, "
                "<b>usando esta análise:\n\n</b><code>Texto do botão - example.com\nTexto do botão - example.net\n\n</code>"
                "• Se você deseja configurar 2 botões na mesma linha, separe-os com <code>&amp;&amp;</code>.\n\n"
                "<b>Exemplo:\n</b><code>Grupo - t.me/username &amp;&amp; Canal - t.me/username\nWhatsapp - wa.link/lo1oy6</code>",
                disable_web_page_preview=True,
                reply_markup=types.ForceReply(),
                parse_mode='HTML'
            )
            bot.register_next_step_handler(call.message, add_botao)
    if call.data == 'confirmar_envio':
        if api.Admin.verificar_admin(call.message.chat.id) == True or int(call.message.chat.id) == int(api.CredentialsChange.id_dono()):
            confirmar_envio(call.message)
    if call.data == 'pesquisar_usuario':
        bot.send_message(
            call.message.chat.id,
            "Digite o id do usuario:",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(call.message, pesquisar_usuario)
    if call.data.split()[0] == 'banir':
        id = call.data.split()[1]
        if api.InfoUser.verificar_ban(id) == True:
            api.InfoUser.tirar_ban(id)
            bot.answer_callback_query(call.id, "Usuario desbanido!", show_alert=True)
            return
        else:
            api.InfoUser.dar_ban(id)
            bot.answer_callback_query(call.id, "Usuario banido!", show_alert=True)
            return
    if call.data.split()[0] == 'mudar_saldo':
        id = call.data.split()[1]
        bot.send_message(
            call.message.chat.id,
            f"Digite o novo saldo do usuario {id}:",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(call.message, mudar_saldo, id)# COLE ESTE NOVO BLOCO DE CÓDIGO
# COLE ESTE NOVO BLOCO DE CÓDIGO NO LUGAR DO ANTIGO
# COLE ESTE NOVO BLOCO DE CÓDIGO NO LUGAR
@bot.callback_query_handler(func=lambda call: call.data.startswith('baixar_historico_30 '))
def callback_baixar_historico_30_dias(call):
    bot.answer_callback_query(call.id, "Gerando seu histórico dos últimos 30 dias...")
    user_id = call.data.split(' ')[1]
    try:
        import os
        from datetime import datetime, timedelta
        user_data = load_user_data(user_id)
        if not user_data or not user_data.get("compras"):
            bot.send_message(call.message.chat.id, "❌ Você ainda não possui compras registradas.")
            return
        compras = user_data.get("compras", [])
        compras_30_dias = []
        # Filtra as compras dos últimos 30 dias
        data_limite = datetime.now() - timedelta(days=30)
        for compra in compras:
            try:
                # Pega a data ignorando a parte do horário " às HH:MM:SS" caso exista
                data_str = compra.get('data', '').split(' ')[0] 
                data_compra_obj = datetime.strptime(data_str, "%d/%m/%Y")
                if data_compra_obj >= data_limite:
                    compras_30_dias.append(compra)
            except ValueError:
                continue # Pula se a data estiver em um formato inválido
        if not compras_30_dias:
            bot.send_message(call.message.chat.id, "⚠️ Você não possui nenhuma compra nos últimos 30 dias.")
            return
        # Garante que o diretório exista
        pasta_historicos = 'historicos'
        if not os.path.exists(pasta_historicos):
            os.makedirs(pasta_historicos)
        caminho_arquivo = os.path.join(pasta_historicos, f'historico_30dias_{user_id}.txt')
        # Monta o TXT
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            f.write(f"--- HISTÓRICO DE COMPRAS (ÚLTIMOS 30 DIAS) ---\n")
            f.write(f"Usuário ID: {user_id}\n")
            f.write(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"----------------------------------------------\n\n")
            for c in compras_30_dias:
                f.write(f"Serviço: {c.get('servico', 'N/A')}\n")
                f.write(f"Valor: R$ {float(c.get('valor', 0)):.2f}\n")
                f.write(f"Data: {c.get('data', 'N/A')}\n")
                f.write(f"Email: {c.get('email', 'N/A')}\n")
                f.write(f"Senha: {c.get('senha', 'N/A')}\n")
                f.write(f"------------------------\n")
        # Envia o arquivo
        with open(caminho_arquivo, 'rb') as doc:
            bot.send_document(
                call.message.chat.id, 
                doc, 
                caption="📅 Aqui está o seu histórico de compras dos últimos 30 dias."
            )
        # Apaga o arquivo temporário por segurança
        os.remove(caminho_arquivo)
    except Exception as e:
        print(f"Erro ao gerar histórico de 30 dias: {e}")
        bot.send_message(call.message.chat.id, "❌ Ocorreu um erro ao gerar seu histórico.")
@bot.callback_query_handler(func=lambda call: call.data.startswith('baixar_historico '))
def callback_baixar_historico(call):
    # Resposta imediata para o usuário
    bot.answer_callback_query(call.id, "Gerando seu histórico, por favor aguarde...")
    user_id = call.data.split(' ')[1]
    print(f"--- GERAÇÃO DE HISTÓRICO PARA USUÁRIO {user_id} ---")
    try:
        # Verifica se o usuário tem compras antes de prosseguir
        user_data = load_user_data(user_id)
        if not user_data or not user_data.get("compras"):
            print(f" -> Usuário {user_id} não possui histórico de compras.")
            bot.send_message(call.message.chat.id, "❌ Você ainda não possui compras para gerar um histórico.")
            return
        # Garante que o diretório 'historicos' exista
        pasta_historicos = 'historicos'
        print(f" -> Verificando/Criando a pasta '{pasta_historicos}'...")
        os.makedirs(pasta_historicos, exist_ok=True)
        # Chama a função para gerar o arquivo de texto
        print(" -> Chamando 'api.InfoUser.fazer_txt_do_historico'...")
        sucesso_criacao = api.InfoUser.fazer_txt_do_historico(user_id)
        if not sucesso_criacao:
            print(" -> A função da API retornou 'False'. Usu��rio provavelmente não encontrado na base de dados.")
            bot.send_message(call.message.chat.id, "❌ Não foi possível encontrar seus dados para gerar o hist��rico.")
            return
        # Verifica se o arquivo foi realmente criado
        file_path = os.path.join(pasta_historicos, f'{user_id}.txt')
        print(f" -> Verificando se o arquivo '{file_path}' existe...")
        if not os.path.exists(file_path):
            print(f" -> ERRO CRÍTICO: A função da API deveria ter criado o arquivo, mas ele não foi encontrado!")
            raise FileNotFoundError("O arquivo de histórico não foi criado pela função da API.")
        # Envia o arquivo para o usuário
        print(" -> Arquivo encontrado. Enviando para o usuário...")
        with open(file_path, 'rb') as file:
            bot.send_document(
                call.message.chat.id,
                document=file,
                caption="📜 Aqui está seu histórico completo de compras."
            )
        print(" -> Histórico enviado com sucesso!")
    except PermissionError:
        print(f"[ERRO DE PERMISSÃO] O bot não tem permissão para criar a pasta '{pasta_historicos}' ou escrever arquivos nela.")
        bot.send_message(call.message.chat.id, "❌ Ocorreu um erro de permissão no servidor. Contate o administrador.")
    except FileNotFoundError:
        print(f"[ERRO] Arquivo não encontrado. A função da API provavelmente não criou o arquivo.")
        bot.send_message(call.message.chat.id, "❌ Não foi possível gerar seu histórico, pois você ainda não possui compras registradas.")
    except Exception as e:
        print(f"[ERRO INESPERADO] Falha ao gerar histórico para {user_id}: {e}")
        import traceback
        traceback.print_exc()
        bot.send_message(call.message.chat.id, "❌ Ocorreu um erro inesperado ao processar sua solicitação. Tente novamente.")
    # =============== Configurações pix
    if call.data == 'configurar_pix':
        configurar_pix(call.message)
    if call.data == 'trocar_pix_manual':
        api.CredentialsChange.ChangeStatusPix.change_pix_manual()
        bot.answer_callback_query(call.id, "Status do PIX Manual alterado!", show_alert=True)
        exibir_painel_pagamentos(call.message)
        return
    if call.data == 'mudar_deposito_minimo':
        bot.answer_callback_query(call.id)
        msg = bot.send_message(
            call.message.chat.id,
            "📉 <b>Alterar Depósito Mínimo</b>\n\nDigite o novo valor mínimo (ex: 5.00):",
            parse_mode='HTML',
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, salvar_novo_minimo_painel)
        return
    if call.data == 'mudar_deposito_maximo':
        bot.answer_callback_query(call.id)
        msg = bot.send_message(
            call.message.chat.id,
            "📈 <b>Alterar Depósito Máximo</b>\n\nDigite o novo valor máximo (ex: 500.00):",
            parse_mode='HTML',
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, salvar_novo_maximo_painel)
        return
    if call.data == 'mudar_bonus':
        bot.send_message(
            call.message.chat.id,
            'Me envie a porcentagem de bonus que o usuario ganhará por cada depósito:\n\nPor favor, envie sem o caractér (%)',
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(call.message, mudar_bonus)
    if call.data == 'mudar_min_bonus':
        msg = bot.send_message(
            call.message.chat.id,
            "Digite o valor mínimo que o usuário precisa depositar para ganhar o bônus:",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, mudar_min_bonus)
    # =============== Configurações gift card
    if call.data == 'gift_card':
        gift_card(call.message)

    # (Código antigo de resgate removido - agora usamos o handler exclusivo no topo)
    # Bloco 'toggle_menu_categorias' removido (agora é uma função @handler separada)
    # ======================= [NOVO SISTEMA DE EDIÇÃO DE TEXTOS - MODULARIZADO] =======================
from app import textos_manager
textos_manager.registrar_handlers(bot, api)
# =====================================================================================================
from telebot.types import Message
# Função utilitária para reexibir o painel de pagamentos

# ==================== FAILOVER PAGAMENTOS ====================
"""
=============================================================================
FAILOVER_PAGAMENTOS.PY
=============================================================================
Failover automático entre os gateways de PIX configurados (PromissePay,
MisticPay, MercadoPago).

Regra: se o gateway ativo falhar ao gerar o PIX (erro de conexão, timeout,
erro da API, etc.), o bot tenta automaticamente o próximo gateway
configurado e estável, sem precisar de intervenção manual.

Como funciona a "estabilidade":
- Cada gateway tem um contador de falhas consecutivas em
  settings/gateway_status.json.
- Ao atingir FALHAS_PARA_INSTAVEL falhas seguidas, o gateway é marcado como
  instável e fica de castigo por COOLDOWN_SEGUNDOS — nesse período ele só é
  tentado por último (não é excluído: se todos estiverem instáveis, ainda
  assim tentamos gerar por ele em vez de falhar de vez).
- Qualquer sucesso zera o contador e reabilita o gateway na hora.
=============================================================================
"""

import json
import os
import time
import base64
import threading
import concurrent.futures

ARQUIVO_STATUS_GATEWAYS = 'settings/gateway_status.json'
ORDEM_PADRAO = ['promissepay', 'misticpay', 'mercadopago']

FALHAS_PARA_INSTAVEL = 2          # falhas seguidas até marcar como instável
COOLDOWN_SEGUNDOS = 5 * 60        # tempo que o gateway fica "de lado"

# Tempo máximo que esperamos por UM gateway antes de considerá-lo instável e
# partir pro próximo. Protege contra APIs que ficam "penduradas" retentando
# internamente (ex: MisticPay com Read Timeout + retry automático do urllib3),
# o que sem isso podia travar o cliente por 40-60s+ num gateway já fora do ar.
TIMEOUT_POR_GATEWAY_SEGUNDOS = 12

_executor_gateways = concurrent.futures.ThreadPoolExecutor(max_workers=6, thread_name_prefix="pix_gw")

_status_lock = threading.Lock()

# ===== PROTEÇÃO CONTRA GERAÇÃO DUPLICADA (mesmo chat + mesmo valor em sequência) =====
# Existem casos (instância duplicada, reprocessamento do Telegram, duplo clique) em
# que o handler de /pix é chamado mais de uma vez para o mesmo pedido do usuário.
# Essa trava evita gerar 2 PIX idênticos em sequência rápida.
DEBOUNCE_SEGUNDOS = 8
_geracao_lock = threading.Lock()
_ultima_geracao_por_chat = {}  # chat_id -> (timestamp, valor)


class PixDuplicadoError(Exception):
    """Levantado quando um pedido idêntico (mesmo chat + valor) chega em sequência rápida demais."""
    pass


def _requisicao_duplicada(chat_id, valor) -> bool:
    agora = time.time()
    chave = int(chat_id)
    with _geracao_lock:
        info = _ultima_geracao_por_chat.get(chave)
        if info and info[1] == valor and (agora - info[0]) < DEBOUNCE_SEGUNDOS:
            return True
        _ultima_geracao_por_chat[chave] = (agora, valor)
        return False


# ===== PERSISTÊNCIA DO STATUS =====

def _carregar_status() -> dict:
    try:
        with open(ARQUIVO_STATUS_GATEWAYS, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _salvar_status(status: dict) -> None:
    try:
        os.makedirs(os.path.dirname(ARQUIVO_STATUS_GATEWAYS), exist_ok=True)
        with open(ARQUIVO_STATUS_GATEWAYS, 'w', encoding='utf-8') as f:
            json.dump(status, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"[FAILOVER] Erro ao salvar status dos gateways: {e}")


def registrar_falha(gateway: str, motivo: str = "") -> None:
    """Registra uma falha do gateway. Marca como instável após N falhas seguidas."""
    with _status_lock:
        status = _carregar_status()
        info = status.get(gateway, {"falhas": 0, "bloqueado_ate": 0})
        info["falhas"] = int(info.get("falhas", 0)) + 1
        info["ultima_falha"] = int(time.time())
        info["ultimo_motivo"] = str(motivo)[:200]
        if info["falhas"] >= FALHAS_PARA_INSTAVEL:
            info["bloqueado_ate"] = int(time.time()) + COOLDOWN_SEGUNDOS
            print(f"[FAILOVER] ⚠️ Gateway '{gateway}' marcado como INSTÁVEL por {COOLDOWN_SEGUNDOS // 60} min (falhas: {info['falhas']})")
        status[gateway] = info
        _salvar_status(status)


def registrar_sucesso(gateway: str) -> None:
    """Zera o contador de falhas e desbloqueia o gateway."""
    with _status_lock:
        status = _carregar_status()
        status[gateway] = {"falhas": 0, "bloqueado_ate": 0, "ultima_falha": 0, "ultimo_motivo": ""}
        _salvar_status(status)


def esta_instavel(gateway: str) -> bool:
    status = _carregar_status()
    info = status.get(gateway, {})
    return int(info.get("bloqueado_ate", 0)) > int(time.time())


def status_gateways() -> dict:
    """Retorna um resumo legível do status de cada gateway (usado em painéis/admin)."""
    status = _carregar_status()
    resumo = {}
    for gw in ORDEM_PADRAO:
        info = status.get(gw, {})
        resumo[gw] = {
            "estavel": not esta_instavel(gw),
            "falhas_consecutivas": int(info.get("falhas", 0)),
            "instavel_ate": info.get("bloqueado_ate", 0),
        }
    return resumo


# ===== ORDEM DE TENTATIVA =====

def _gateways_configurados() -> list:
    from app.config_pagamentos import ConfigPromissePay, ConfigMisticPay, ConfigMercadoPago
    configurados = []
    if ConfigPromissePay.esta_configurado():
        configurados.append('promissepay')
    if ConfigMisticPay.esta_configurado():
        configurados.append('misticpay')
    if ConfigMercadoPago.esta_configurado():
        configurados.append('mercadopago')
    return configurados


def ordem_de_tentativa() -> list:
    """
    Monta a ordem de gateways a tentar:
    1. Gateway ativo (selecionado no painel) primeiro, se estiver configurado e estável.
    2. Demais gateways configurados e estáveis.
    3. Por fim, gateways configurados mas instáveis (melhor tentar do que não ter opção).

    Se a troca automática estiver desligada no painel, nenhum failover ocorre:
    só o gateway ativo é tentado (se falhar, a geração do PIX falha mesmo).
    """
    from app.config_pagamentos import obter_gateway_ativo, troca_automatica_ativa
    configurados = _gateways_configurados()
    if not configurados:
        return []

    ativo = obter_gateway_ativo()

    if not troca_automatica_ativa():
        return [ativo] if ativo in configurados else []

    candidatos = [ativo] + [g for g in ORDEM_PADRAO if g != ativo]
    candidatos = [g for g in candidatos if g in configurados]

    estaveis = [g for g in candidatos if not esta_instavel(g)]
    instaveis = [g for g in candidatos if esta_instavel(g)]
    return estaveis + instaveis


# ===== GERAÇÃO NORMALIZADA POR GATEWAY =====

def _gerar_promissepay(valor, message):
    payment = api.CriarPixPromissePay.gerar(valor, message.chat.id)
    id_pag = payment['id']
    pix_copia_cola = payment['qr_code']
    qr_bytes = base64.b64decode(payment['qr_code_base64'])
    return id_pag, pix_copia_cola, qr_bytes


def _gerar_misticpay(valor, message):
    chat_info = bot.get_chat(message.chat.id)
    nome = chat_info.first_name or "Cliente"
    payment = api.CriarPixMisticPay.gerar(valor, message.chat.id, nome=nome)
    id_pag = payment['id']
    pix_copia_cola = payment['qr_code']
    qr_bytes = base64.b64decode(payment['qr_code_base64'])
    return id_pag, pix_copia_cola, qr_bytes


def _gerar_mercadopago(valor, message):
    payment = api.CriarPixMercadoPago.gerar(valor, message.chat.id)
    id_pag = payment['id']
    pix_copia_cola = payment['qr_code']
    qr_bytes = base64.b64decode(payment['qr_code_base64'])
    return id_pag, pix_copia_cola, qr_bytes


_GERADORES = {
    'promissepay': _gerar_promissepay,
    'misticpay': _gerar_misticpay,
    'mercadopago': _gerar_mercadopago,
}


def gerar_pix_com_failover(valor, message):
    """
    Tenta gerar o PIX percorrendo os gateways configurados na ordem definida
    por ordem_de_tentativa(). Retorna no primeiro que funcionar.

    Retorno (sucesso): dict com gateway, id_pag, pix_copia_cola, qr_bytes
    Levanta Exception apenas se TODOS os gateways configurados falharem.
    Levanta PixDuplicadoError se o mesmo chat pedir o mesmo valor em menos de
    DEBOUNCE_SEGUNDOS (proteção contra processamento duplicado do mesmo pedido).
    """
    if _requisicao_duplicada(message.chat.id, valor):
        print(f"[FAILOVER] ⛔ Pedido duplicado ignorado: chat={message.chat.id} valor={valor} (dentro de {DEBOUNCE_SEGUNDOS}s)")
        raise PixDuplicadoError(f"Pedido duplicado para chat {message.chat.id} no valor de R$ {valor:.2f}")

    ordem = ordem_de_tentativa()
    if not ordem:
        raise Exception("Nenhum gateway de pagamento está configurado.")

    erros = []
    for gateway in ordem:
        gerador = _GERADORES.get(gateway)
        if not gerador:
            continue
        try:
            print(f"[FAILOVER] Tentando gerar PIX via '{gateway}' (timeout: {TIMEOUT_POR_GATEWAY_SEGUNDOS}s)...")
            future = _executor_gateways.submit(gerador, valor, message)
            try:
                id_pag, pix_copia_cola, qr_bytes = future.result(timeout=TIMEOUT_POR_GATEWAY_SEGUNDOS)
            except concurrent.futures.TimeoutError:
                raise TimeoutError(
                    f"Gateway '{gateway}' não respondeu em {TIMEOUT_POR_GATEWAY_SEGUNDOS}s (considerado instável)"
                )
            registrar_sucesso(gateway)
            print(f"[FAILOVER] ✅ PIX gerado com sucesso via '{gateway}' (ID: {id_pag})")
            return {
                "gateway": gateway,
                "id_pag": id_pag,
                "pix_copia_cola": pix_copia_cola,
                "qr_bytes": qr_bytes,
            }
        except Exception as e:
            erro_str = str(e)
            print(f"[FAILOVER] ❌ Falha no gateway '{gateway}': {erro_str}")
            registrar_falha(gateway, erro_str)
            erros.append(f"{gateway}: {erro_str[:150]}")
            continue

    raise Exception(
        "Falha ao gerar PIX em todos os gateways configurados. Detalhes: " + " | ".join(erros)
    )


# ==================== PAGAMENTOS PIX ====================
def exibir_painel_pagamentos(message):
    try:
        with open('settings/credenciais.json', 'r', encoding='utf-8') as f:
            cred = json.load(f)
    except Exception:
        cred = {}
    token_promissepay = cred.get('gateway_pagamento', {}).get('promissepay', {}).get('token', 'Não configurado')
    mistic_ci = cred.get('gateway_pagamento', {}).get('misticpay', {}).get('client_id', 'Não configurado')
    token_mercadopago = cred.get('gateway_pagamento', {}).get('mercadopago', {}).get('token', 'Não configurado')
    gateway_selecionada = cred.get('gateway_pagamento', {}).get('selecionada', 'promissepay')
    min_pix = api.CredentialsChange.InfoPix.deposito_minimo_pix()
    max_pix = api.CredentialsChange.InfoPix.deposito_maximo_pix()
    status_manual = api.CredentialsChange.StatusPix.pix_manual()
    txt_btn_manual = "Desativar Manual 🔴" if status_manual else "Ativar Manual 🟢"
    gateway_emoji = '✅' if gateway_selecionada == 'promissepay' else '⚪'
    mistic_emoji = '✅' if gateway_selecionada == 'misticpay' else '⚪'
    mercadopago_emoji = '✅' if gateway_selecionada == 'mercadopago' else '⚪'
    if token_promissepay and token_promissepay != 'Não configurado' and len(token_promissepay) > 12:
        token_promissepay_exibido = f"{token_promissepay[:10]}...{token_promissepay[-4:]}"
    else:
        token_promissepay_exibido = token_promissepay
    if token_mercadopago and token_mercadopago != 'Não configurado' and len(token_mercadopago) > 12:
        token_mercadopago_exibido = f"{token_mercadopago[:10]}...{token_mercadopago[-4:]}"
    else:
        token_mercadopago_exibido = token_mercadopago
    from app.config_pagamentos import troca_automatica_ativa, taxa_intermediador_ativa, obter_valor_taxa_intermediador, obter_limite_isencao_taxa
    auto_gateway_ligada = troca_automatica_ativa()
    txt_btn_auto_gateway = "🔁 Troca Automática: LIGADA ✅" if auto_gateway_ligada else "🔁 Troca Automática: DESLIGADA ⛔"
    taxa_ligada = taxa_intermediador_ativa()
    valor_taxa = obter_valor_taxa_intermediador()
    limite_isencao = obter_limite_isencao_taxa()
    txt_btn_taxa_status = "💰 Taxa: LIGADA ✅" if taxa_ligada else "💰 Taxa: DESLIGADA ⛔"
    texto = (
        f'<b>💳 CONFIGURAÇÃO DE PAGAMENTOS</b>\n\n'
        f'🔔 <b>Gateway Ativa:</b> {gateway_selecionada.upper()} ✅\n'
        f'🔁 <b>Troca Automática:</b> {"Ligada" if auto_gateway_ligada else "Desligada"}\n'
        f'➖➖➖➖➖➖➖➖➖➖\n'
        f'<b>⚙️ LIMITES E REGRAS:</b>\n'
        f'🔻 <b>Mínimo:</b> R$ {min_pix:.2f}\n'
        f'🔺 <b>Máximo:</b> R$ {max_pix:.2f}\n'
        f'✋ <b>Pix Manual:</b> {"Ligado" if status_manual else "Desligado"}\n'
        f'➖➖➖➖➖➖➖➖➖➖\n'
        f'<b>💰 TAXA DO INTERMEDIADOR:</b>\n'
        f'Status: {"Ligada ✅" if taxa_ligada else "Desligada ⛔"}\n'
        f'Valor: R$ {valor_taxa:.2f} <i>(cobrada só abaixo de R$ {limite_isencao:.2f})</i>\n'
        f'➖➖➖➖➖➖➖➖➖➖\n'
        f'<b>🏦 GATEWAYS:</b>\n\n'
        f'<b>PromissePay</b> {gateway_emoji}\nToken: <code>{token_promissepay_exibido}</code>\n\n'
        f'<b>MisticPay</b> {mistic_emoji}\nClient ID: <code>{mistic_ci}</code>\n\n'
        f'<b>Mercado Pago</b> {mercadopago_emoji}\nToken: <code>{token_mercadopago_exibido}</code>\n'
    )
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton(f'{txt_btn_manual}', callback_data='trocar_pix_manual'))
    markup.row(
        InlineKeyboardButton(f'🔻 Mín: {min_pix:.0f}', callback_data='mudar_deposito_minimo'),
        InlineKeyboardButton(f'🔺 Máx: {max_pix:.0f}', callback_data='mudar_deposito_maximo')
    )
    markup.row(
        InlineKeyboardButton('✏️ Token PromissePay', callback_data='alterar_token_promissepay'),
        InlineKeyboardButton('🔑 MisticPay', callback_data='configurar_misticpay')
    )
    markup.row(InlineKeyboardButton('✏️ Token Mercado Pago', callback_data='alterar_token_mercadopago'))
    markup.row(InlineKeyboardButton('🔄 Trocar Gateway', callback_data='trocar_gateway'))
    markup.row(InlineKeyboardButton(txt_btn_auto_gateway, callback_data='trocar_auto_gateway'))
    markup.row(
        InlineKeyboardButton(txt_btn_taxa_status, callback_data='trocar_taxa_intermediador'),
        InlineKeyboardButton(f'✏️ Valor: R$ {valor_taxa:.2f}', callback_data='mudar_valor_taxa')
    )
    markup.row(InlineKeyboardButton(f'✏️ Isenção acima de: R$ {limite_isencao:.2f}', callback_data='mudar_limite_isencao_taxa'))
    markup.row(InlineKeyboardButton('↩ Voltar', callback_data='voltar_paineladm'))
    try:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=texto,
            parse_mode='HTML',
            reply_markup=markup
        )
    except Exception:
        bot.send_message(message.chat.id, texto, parse_mode='HTML', reply_markup=markup)
# Função para trocar o gateway ativo entre PromissePay e MisticPay
def trocar_gateway_ativo(call):
    """Alterna entre PromissePay e MisticPay"""
    try:
        with open('settings/credenciais.json', 'r', encoding='utf-8') as f:
            cred = json.load(f)
    except Exception:
        cred = {}
    # Inicializar estrutura se nao existir
    if 'gateway_pagamento' not in cred:
        cred['gateway_pagamento'] = {'selecionada': 'promissepay', 'promissepay': {}}
    # Alternar gateway (ciclo: promissepay -> misticpay -> mercadopago -> promissepay)
    ordem_gateways = ['promissepay', 'misticpay', 'mercadopago']
    gateway_atual = cred['gateway_pagamento'].get('selecionada', 'promissepay')
    try:
        idx_atual = ordem_gateways.index(gateway_atual)
    except ValueError:
        idx_atual = 0
    novo_gateway = ordem_gateways[(idx_atual + 1) % len(ordem_gateways)]
    cred['gateway_pagamento']['selecionada'] = novo_gateway
    # Salvar credenciais
    try:
        with open('settings/credenciais.json', 'w', encoding='utf-8') as f:
            json.dump(cred, f, ensure_ascii=False, indent=4)
        bot.answer_callback_query(call.id, f"Gateway alterado para {novo_gateway.upper()}!", show_alert=True)
        exibir_painel_pagamentos(call.message)
    except Exception as e:
        bot.answer_callback_query(call.id, f"Erro ao trocar gateway: {e}", show_alert=True)
# Função para ligar/desligar a troca automática (failover) entre gateways
def alternar_troca_automatica_gateway(call):
    """Liga ou desliga o failover automático entre PromissePay e MisticPay."""
    from app.config_pagamentos import alternar_troca_automatica
    try:
        novo_status = alternar_troca_automatica()
        texto_status = "LIGADA ✅" if novo_status else "DESLIGADA ⛔"
        bot.answer_callback_query(call.id, f"Troca automática de gateway: {texto_status}", show_alert=True)
        exibir_painel_pagamentos(call.message)
    except Exception as e:
        bot.answer_callback_query(call.id, f"Erro ao alterar troca automática: {e}", show_alert=True)
# Função para ligar/desligar a taxa fixa do intermediador
def alternar_taxa_intermediador_pix(call):
    """Liga ou desliga a cobrança da taxa fixa do intermediador em PIX abaixo de R$ 50."""
    from app.config_pagamentos import alternar_taxa_intermediador
    try:
        novo_status = alternar_taxa_intermediador()
        texto_status = "LIGADA ✅" if novo_status else "DESLIGADA ⛔"
        bot.answer_callback_query(call.id, f"Taxa do intermediador: {texto_status}", show_alert=True)
        exibir_painel_pagamentos(call.message)
    except Exception as e:
        bot.answer_callback_query(call.id, f"Erro ao alterar taxa: {e}", show_alert=True)
# Função utilitária para salvar novo token PromissePay
def salvar_novo_token_promissepay(message):
    novo_token = message.text.strip()
    try:
        with open('settings/credenciais.json', 'r', encoding='utf-8') as f:
            cred = json.load(f)
    except Exception:
        cred = {}
    if 'gateway_pagamento' not in cred:
        cred['gateway_pagamento'] = {'selecionada': 'promissepay', 'promissepay': {}}
    if 'promissepay' not in cred['gateway_pagamento']:
        cred['gateway_pagamento']['promissepay'] = {}
    cred['gateway_pagamento']['promissepay']['token'] = novo_token
    try:
        with open('settings/credenciais.json', 'w', encoding='utf-8') as f:
            json.dump(cred, f, ensure_ascii=False, indent=4)
        bot.reply_to(message, '✅ Token PromissePay atualizado com sucesso!')
        # Reexibe o painel de pagamentos após atualizar
        exibir_painel_pagamentos(message)
    except Exception as e:
        bot.reply_to(message, f'❌ Erro ao salvar token: {e}')
# Função utilitária para salvar novo token Mercado Pago
def salvar_novo_token_mercadopago(message):
    novo_token = message.text.strip()
    try:
        with open('settings/credenciais.json', 'r', encoding='utf-8') as f:
            cred = json.load(f)
    except Exception:
        cred = {}
    if 'gateway_pagamento' not in cred:
        cred['gateway_pagamento'] = {'selecionada': 'promissepay', 'promissepay': {}}
    if 'mercadopago' not in cred['gateway_pagamento']:
        cred['gateway_pagamento']['mercadopago'] = {}
    cred['gateway_pagamento']['mercadopago']['token'] = novo_token
    try:
        with open('settings/credenciais.json', 'w', encoding='utf-8') as f:
            json.dump(cred, f, ensure_ascii=False, indent=4)
        bot.reply_to(message, '✅ Token Mercado Pago atualizado com sucesso!')
        # Reexibe o painel de pagamentos após atualizar
        exibir_painel_pagamentos(message)
    except Exception as e:
        bot.reply_to(message, f'❌ Erro ao salvar token: {e}')
# Função utilitária para salvar credenciais MisticPay
def processar_credenciais_misticpay(message):
    try:
        partes = message.text.strip().split()
        if len(partes) != 2:
            bot.reply_to(message, "❌ Formato inválido. Envie o Client ID e Client Secret separados por um espaço.")
            return
        client_id, client_secret = partes[0], partes[1]
        try:
            with open('settings/credenciais.json', 'r', encoding='utf-8') as f:
                cred = json.load(f)
        except Exception:
            cred = {}
        if 'gateway_pagamento' not in cred:
            cred['gateway_pagamento'] = {'selecionada': 'promissepay', 'promissepay': {}}
        if 'misticpay' not in cred['gateway_pagamento']:
            cred['gateway_pagamento']['misticpay'] = {}
        cred['gateway_pagamento']['misticpay']['client_id'] = client_id
        cred['gateway_pagamento']['misticpay']['client_secret'] = client_secret
        try:
            with open('settings/credenciais.json', 'w', encoding='utf-8') as f:
                json.dump(cred, f, ensure_ascii=False, indent=4)
            bot.reply_to(message, '✅ Credenciais do MisticPay atualizadas com sucesso!')
            exibir_painel_pagamentos(message)
        except Exception as e:
            bot.reply_to(message, f'❌ Erro ao salvar credenciais: {e}')
    except Exception as e:
        bot.reply_to(message, f'❌ Erro ao processar credenciais: {e}')
def gerar_pix_por_comando(message: Message):
    if api.Admin.verificar_vencimento():
        ver_se_expirou()
        return
    if api.InfoUser.verificar_ban(message.from_user.id):
        bot.reply_to(message, "Você está banido e não pode usar o bot!")
        return
    partes = message.text.strip().split()
    if len(partes) != 2:
        return
    valor_str = partes[1].replace("R$", "").replace(",", ".").strip()
    try:
        valor = float(valor_str)
    except ValueError:
        bot.reply_to(message, "Valor inválido! Digite algo como /pix 10 ou /pix 10.00")
        return
    minimo = float(api.CredentialsChange.InfoPix.deposito_minimo_pix())
    maximo = float(api.CredentialsChange.InfoPix.deposito_maximo_pix())
    if not (minimo <= valor <= maximo):
        bot.reply_to(
            message,
            f"Valor inválido! Digite um valor entre R${minimo:.2f} e R${maximo:.2f}"
        )
        return
    # Iniciando fluxo único: PromissePay
    payment = api.CriarPixPromissePay.gerar(valor, message.chat.id)
    id_pag = payment['id']
    pix_copia_cola = payment['qr_code']
    qr_code_base64 = payment['qr_code_base64']
    import base64
    qr_image = base64.b64decode(qr_code_base64 + "=" * (-len(qr_code_base64) % 4))
    with open('qrcode.png', 'wb') as f:
        f.write(qr_image)
    caption = api.Textos.pix_automatico(message, pix_copia_cola, 15, id_pag, f"{valor:.2f}")
    sent = bot.send_photo(
        chat_id=message.chat.id,
        photo=open('qrcode.png', 'rb'),
        caption=caption,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton('⏰ Aguardando Pagamento...', callback_data='aguardando')]
        ])
    )
    # --- NOTIFICAÇÃO (PIX GERADO) ---
    try:
        dono_id = api.CredentialsChange.id_dono()
        canal_id = -1002787400901
        u_tag = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
        msg_dono = (
            f"💸 <b>PIX GERADO!</b>\n\n"
            f"👤 <b>Cliente:</b> {message.from_user.first_name}\n"
            f"🆔 <b>ID:</b> <code>{message.chat.id}</code>\n"
            f"💰 <b>Valor:</b> R$ {valor:.2f}\n"
            f"🧾 <b>Pagamento ID:</b> <code>{id_pag}</code>"
        )
        # Mensagem do canal: sem foto e sem valor exato (privacidade do cliente)
        msg_canal = "💸 Um usuário gerou um Pix."
        fotos_pix = bot.get_user_profile_photos(message.chat.id)
        foto_id = fotos_pix.photos[0][-1].file_id if fotos_pix.total_count > 0 else None
        try:
            if foto_id: bot.send_photo(dono_id, foto_id, caption=msg_dono, parse_mode='HTML')
            else: bot.send_message(dono_id, msg_dono, parse_mode='HTML')
        except: pass
        try:
            # Canal recebe só o texto genérico (nunca a foto do cliente nem o valor)
            bot.send_message(canal_id, msg_canal)
        except Exception as e: print(f"Erro canal pix: {e}")
    except Exception as e:
        print(f"Erro ao avisar pix: {e}")
    import threading
    threading.Thread(
        target=verificar_pagamento_promissepay,
        args=(message.chat.id, id_pag, valor, sent.message_id),
        daemon=True
    ).start()
@bot.message_handler(regexp=rf'^/pix(?:@{api.CredentialsChange.user_bot()})?\s*$')
def pix_help(message: Message):
    bot.reply_to(
        message,
        "✨ Para gerar um Pix, digite o comando e o valor desejado.\n\n"
        "💳 Exemplo: `/pix 10.00`\n"
        "  _Isso gerará um Pix no valor de R$ 10,00._\n\n"
        "Lembre-se de verificar o valor mínimo e máximo no menu de recarga!",
        parse_mode='Markdown'
    )
import threading, time
@bot.message_handler(commands=['pix', f'pix@{api.CredentialsChange.user_bot()}'])
# === Ponte do PIX Automático -> /pix <valor> ===
def processar_valor_recarga(message):
    """Recebe o valor digitado após clicar no botão de recarga
    e reusa a lógica do /pix existente. Ex.: "5" -> "/pix 5"""
    try:
        txt = (getattr(message, "text", "") or "").strip()
        if not txt:
            try:
                from telebot.types import ForceReply
                message_bot = globals().get("bot")
                if message_bot:
                    message_bot.send_message(message.chat.id, "Digite um valor válido para recarga.", reply_markup=ForceReply())
            except Exception:
                pass
            return
        message.text = f"/pix {txt}"
        # chama a função principal já existente
        gerar_pix_por_comando(message)
    except Exception as e:
        try:
            globals().get("bot").reply_to(message, f"❌ Erro ao processar valor: {e}")
        except Exception:
            pass
# === Verificação assíncrona de pagamento (PromissePay) ===
def verificar_pagamento_promissepay(chat_id, id_pag, valor, message_id):
    """Consulta periodicamente o status no PromissePay (GET /transactions/:id) e,
    quando aprovado (status PAID), credita o saldo e atualiza a mensagem."""
    import time
    from app.database import load_user_data, save_user_data, check_pagamento_ja_processado
    from pytz import timezone as pytz_timezone
    from datetime import datetime
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    tentativas = 90  # ~15 minutos (90 iterações de 10s)
    admin_id = int(api.CredentialsChange.id_dono())
    tz = pytz_timezone('America/Sao_Paulo')
    for _ in range(tentativas):
        try:
            result = api.CriarPixPromissePay.consultar(id_pag)
            status = str(result.get("status", "")).upper()
        except Exception as e:
            print(f"[PROMISSEPAY-VERIFY] Erro ao consultar status do pag. {id_pag}: {e}")
            status = "ERROR"
        if status == "PAID":
            try:
                if check_pagamento_ja_processado(id_pag):
                    return
                min_bonus = float(api.CredentialsChange.BonusPix.valor_minimo_para_bonus())
                bonus_pct = float(api.CredentialsChange.BonusPix.quantidade_bonus())
                bonus_amt = float(valor) * bonus_pct / 100 if float(valor) >= min_bonus else 0.0
                saldo_deposito = float(valor) + bonus_amt
                user_data = load_user_data(chat_id) or {}
                before = float(user_data.get('saldo', 0.0))
                after = before + saldo_deposito
                user_data['saldo'] = after
                pagamentos = user_data.get('pagamentos', [])
                pagamentos.append({
                    'id': id_pag,
                    'valor': valor,
                    'data': datetime.now(tz).strftime("%d/%m/%Y às %H:%M:%S")
                })
                user_data['pagamentos'] = pagamentos
                save_user_data(chat_id, user_data)
                bot.send_message(chat_id, f"✅ Pagamento confirmado! Saldo adicionado: R${valor:.2f}" + (f' (+ Bônus R${bonus_amt:.2f})' if bonus_amt else ''))
                try:
                    texto_final = (
                        "✅ <b>Pagamento Aprovado!</b>\n\n"
                        "Seu saldo foi creditado com sucesso.\n\n"
                        "<i>O QR Code e a chave PIX foram removidos por segurança.</i>"
                    )
                    bot.edit_message_caption(
                        caption=texto_final,
                        chat_id=chat_id,
                        message_id=message_id,
                        parse_mode='HTML',
                        reply_markup=None
                    )
                except Exception as e:
                    print(f"[PromissePay] Falha ao editar a mensagem final do PIX: {e}")
                try:
                    chat_info = bot.get_chat(chat_id)
                    user_display_name = chat_info.first_name or f"ID {chat_id}"
                    user_username = f"@{chat_info.username}" if chat_info.username else "Não possui"
                except Exception:
                    user_display_name = f"ID {chat_id}"
                    user_username = "Não foi possível obter"
                texto_adm = (
                    f"<b>💰 PAGAMENTO APROVADO - PromissePay</b>\n\n"
                    f"<b>Detalhes do Cliente:</b>\n"
                    f"👤 <b>Nome:</b> {user_display_name}\n"
                    f"📱 <b>Username:</b> {user_username}\n"
                    f"🆔 <b>ID:</b> <code>{chat_id}</code>\n\n"
                    f"<b>Detalhes da Transação:</b>\n"
                    f"💵 <b>Valor Recebido:</b> R${valor:.2f}\n"
                    f"🎁 <b>Bônus Aplicado:</b> R${bonus_amt:.2f}\n"
                    f"➕ <b>Total Creditado:</b> R${saldo_deposito:.2f}\n\n"
                    f"<b>Atualização de Saldo:</b>\n"
                    f"  - <b>Anterior:</b> R${before:.2f}\n"
                    f"  - <b>Atual:</b> R${after:.2f}\n\n"
                    f"<b>Referência do Pagamento:</b>\n"
                    f"<code>{id_pag}</code>\n\n"
                    f"🕐 <b>Data:</b> {datetime.now(tz).strftime('%d/%m/%Y às %H:%M:%S')}"
                )
                bot.send_message(chat_id=admin_id, text=texto_adm, parse_mode='HTML')
            except Exception as e:
                print(f"[PromissePay] Falha CRÍTICA ao processar pagamento aprovado para {chat_id}: {e}")
                bot.send_message(chat_id=admin_id, text=f"⚠️ <b>ERRO CRÍTICO</b> ⚠️\nPagamento PromissePay de R${valor:.2f} para o usuário <code>{chat_id}</code> foi aprovado, mas falhou ao creditar o saldo.\n\n<b>Erro:</b> {e}", parse_mode='HTML')
            return
        elif status in ["CANCELLED", "EXPIRED", "CANCELED", "FAILED"]:
            try:
                bot.edit_message_caption(chat_id=chat_id, message_id=message_id, caption=f"❌ Este PIX foi cancelado ou expirou.", parse_mode="HTML")
            except:
                bot.send_message(chat_id, "❌ O PIX gerado anteriormente foi cancelado ou expirou.")
            # ALERTAR O ADM SOBRE O NÃO PAGAMENTO
            alertar_adm_pix_nao_pago(bot, chat_id, valor)
            return
        time.sleep(10)
    try:
        bot.edit_message_caption(chat_id=chat_id, message_id=message_id, caption="⏱️ O tempo para pagamento deste PIX expirou. Gere um novo se desejar.", parse_mode="HTML")
    except:
        bot.send_message(chat_id, "⏱️ O tempo de verificação do pagamento expirou.")
    # ALERTAR O ADM SOBRE O NÃO PAGAMENTO (TIMEOUT)
    alertar_adm_pix_nao_pago(bot, chat_id, valor)
# === Verificação assíncrona de pagamento (Mercado Pago) ===
def verificar_pagamento_mercadopago(chat_id, id_pag, valor, message_id):
    """Consulta periodicamente o status no Mercado Pago (GET /v1/payments/:id) e,
    quando aprovado (status PAID), credita o saldo e atualiza a mensagem."""
    import time
    from app.database import load_user_data, save_user_data, check_pagamento_ja_processado
    from pytz import timezone as pytz_timezone
    from datetime import datetime
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    tentativas = 90  # ~15 minutos (90 iterações de 10s)
    admin_id = int(api.CredentialsChange.id_dono())
    tz = pytz_timezone('America/Sao_Paulo')
    for _ in range(tentativas):
        try:
            result = api.CriarPixMercadoPago.consultar(id_pag)
            status = str(result.get("status", "")).upper()
        except Exception as e:
            print(f"[MERCADOPAGO-VERIFY] Erro ao consultar status do pag. {id_pag}: {e}")
            status = "ERROR"
        if status == "PAID":
            try:
                if check_pagamento_ja_processado(id_pag):
                    return
                min_bonus = float(api.CredentialsChange.BonusPix.valor_minimo_para_bonus())
                bonus_pct = float(api.CredentialsChange.BonusPix.quantidade_bonus())
                bonus_amt = float(valor) * bonus_pct / 100 if float(valor) >= min_bonus else 0.0
                saldo_deposito = float(valor) + bonus_amt
                user_data = load_user_data(chat_id) or {}
                before = float(user_data.get('saldo', 0.0))
                after = before + saldo_deposito
                user_data['saldo'] = after
                pagamentos = user_data.get('pagamentos', [])
                pagamentos.append({
                    'id': id_pag,
                    'valor': valor,
                    'data': datetime.now(tz).strftime("%d/%m/%Y às %H:%M:%S")
                })
                user_data['pagamentos'] = pagamentos
                save_user_data(chat_id, user_data)
                bot.send_message(chat_id, f"✅ Pagamento confirmado! Saldo adicionado: R${valor:.2f}" + (f' (+ Bônus R${bonus_amt:.2f})' if bonus_amt else ''))
                try:
                    texto_final = (
                        "✅ <b>Pagamento Aprovado!</b>\n\n"
                        "Seu saldo foi creditado com sucesso.\n\n"
                        "<i>O QR Code e a chave PIX foram removidos por segurança.</i>"
                    )
                    bot.edit_message_caption(
                        caption=texto_final,
                        chat_id=chat_id,
                        message_id=message_id,
                        parse_mode='HTML',
                        reply_markup=None
                    )
                except Exception as e:
                    print(f"[MercadoPago] Falha ao editar a mensagem final do PIX: {e}")
                try:
                    chat_info = bot.get_chat(chat_id)
                    user_display_name = chat_info.first_name or f"ID {chat_id}"
                    user_username = f"@{chat_info.username}" if chat_info.username else "Não possui"
                except Exception:
                    user_display_name = f"ID {chat_id}"
                    user_username = "Não foi possível obter"
                texto_adm = (
                    f"<b>💰 PAGAMENTO APROVADO - Mercado Pago</b>\n\n"
                    f"<b>Detalhes do Cliente:</b>\n"
                    f"👤 <b>Nome:</b> {user_display_name}\n"
                    f"📱 <b>Username:</b> {user_username}\n"
                    f"🆔 <b>ID:</b> <code>{chat_id}</code>\n\n"
                    f"<b>Detalhes da Transação:</b>\n"
                    f"💵 <b>Valor Recebido:</b> R${valor:.2f}\n"
                    f"🎁 <b>Bônus Aplicado:</b> R${bonus_amt:.2f}\n"
                    f"➕ <b>Total Creditado:</b> R${saldo_deposito:.2f}\n\n"
                    f"<b>Atualização de Saldo:</b>\n"
                    f"  - <b>Anterior:</b> R${before:.2f}\n"
                    f"  - <b>Atual:</b> R${after:.2f}\n\n"
                    f"<b>Referência do Pagamento:</b>\n"
                    f"<code>{id_pag}</code>\n\n"
                    f"🕐 <b>Data:</b> {datetime.now(tz).strftime('%d/%m/%Y às %H:%M:%S')}"
                )
                bot.send_message(chat_id=admin_id, text=texto_adm, parse_mode='HTML')
            except Exception as e:
                print(f"[MercadoPago] Falha CRÍTICA ao processar pagamento aprovado para {chat_id}: {e}")
                bot.send_message(chat_id=admin_id, text=f"⚠️ <b>ERRO CRÍTICO</b> ⚠️\nPagamento Mercado Pago de R${valor:.2f} para o usuário <code>{chat_id}</code> foi aprovado, mas falhou ao creditar o saldo.\n\n<b>Erro:</b> {e}", parse_mode='HTML')
            return
        elif status in ["CANCELLED", "EXPIRED", "CANCELED", "FAILED"]:
            try:
                bot.edit_message_caption(chat_id=chat_id, message_id=message_id, caption=f"❌ Este PIX foi cancelado ou expirou.", parse_mode="HTML")
            except:
                bot.send_message(chat_id, "❌ O PIX gerado anteriormente foi cancelado ou expirou.")
            # ALERTAR O ADM SOBRE O NÃO PAGAMENTO
            alertar_adm_pix_nao_pago(bot, chat_id, valor)
            return
        time.sleep(10)
    try:
        bot.edit_message_caption(chat_id=chat_id, message_id=message_id, caption="⏱️ O tempo para pagamento deste PIX expirou. Gere um novo se desejar.", parse_mode="HTML")
    except:
        bot.send_message(chat_id, "⏱️ O tempo de verificação do pagamento expirou.")
    # ALERTAR O ADM SOBRE O NÃO PAGAMENTO (TIMEOUT)
    alertar_adm_pix_nao_pago(bot, chat_id, valor)
def gerar_pix_por_comando(message: Message):
    if api.Admin.verificar_vencimento():
        ver_se_expirou()
        return
    if api.InfoUser.verificar_ban(message.from_user.id):
        bot.reply_to(message, "Você está banido e não pode usar o bot!")
        return
    partes = message.text.strip().split()
    if len(partes) != 2:
        return
    valor_str = partes[1].replace("R$", "").replace(",", ".").strip()
    try:
        valor = float(valor_str)
    except ValueError:
        bot.reply_to(message, "Valor inválido! Digite algo como /pix 10 ou /pix 10.00")
        return
    minimo = float(api.CredentialsChange.InfoPix.deposito_minimo_pix())
    maximo = float(api.CredentialsChange.InfoPix.deposito_maximo_pix())
    if not (minimo <= valor <= maximo):
        bot.reply_to(
            message,
            f"Valor inválido! Digite um valor entre R${minimo:.2f} e R${maximo:.2f}"
        )
        return
    import threading
    from io import BytesIO

    # ===== GERAÇÃO COM FAILOVER AUTOMÁTICO ENTRE OS 3 GATEWAYS =====
    try:
        resultado = gerar_pix_com_failover(valor, message)
    except PixDuplicadoError as e:
        # Pedido repetido (mesmo chat + valor) chegou em sequência rápida demais.
        # Provavelmente processamento duplicado do mesmo clique/comando — ignora
        # silenciosamente para não gerar 2 PIX nem incomodar o cliente/admin.
        print(f"[PIX_DUPLICADO] {e}")
        return
    except Exception as e:
        error_msg = str(e)
        print(f"[PIX_FAILOVER_ERROR] User: {message.chat.id} | Valor: {valor} | Erro: {error_msg}")
        try:
            bot.send_message(
                message.chat.id,
                "❌ Todos os métodos de pagamento estão indisponíveis no momento. Tente novamente em alguns minutos."
            )
        except:
            pass
        try:
            dono_id = api.CredentialsChange.id_dono()
            bot.send_message(dono_id, f"🚨 <b>TODOS OS GATEWAYS FALHARAM!</b>\n\nUsuário: <code>{message.chat.id}</code>\nValor: R$ {valor:.2f}\n\n{error_msg[:500]}", parse_mode='HTML')
        except:
            pass
        return

    gateway_usado = resultado['gateway']
    id_pag = resultado['id_pag']
    pix_copia_cola = resultado['pix_copia_cola']
    image_stream = BytesIO(resultado['qr_bytes'])

    from app.config_pagamentos import calcular_taxa_pix, obter_valor_taxa_intermediador, obter_limite_isencao_taxa
    expiracao = api.CredentialsChange.InfoPix.expiracao() if gateway_usado == 'misticpay' else 15
    taxa_fixa = calcular_taxa_pix(valor)
    valor_taxa_config = obter_valor_taxa_intermediador()
    limite_isencao = obter_limite_isencao_taxa()
    valor_com_taxa = float(valor) + taxa_fixa
    caption = api.Textos.pix_automatico(message, pix_copia_cola, expiracao, id_pag, f"{valor:.2f}")
    if taxa_fixa > 0:
        caption += f"\n\n⚠️ <b>Atenção:</b> O valor total do PIX gerado é de <b>R$ {valor_com_taxa:.2f}</b> devido à taxa do intermediador (R$ {taxa_fixa:.2f}).\n\nℹ️ <i>Pagamentos a partir de R$ {limite_isencao:.2f} não possuem taxa.</i>"
    elif valor_taxa_config > 0:
        caption += f"\n\nℹ️ <i>Pagamentos abaixo de R$ {limite_isencao:.2f} possuem taxa fixa de R$ {valor_taxa_config:.2f} do intermediador. Este PIX não possui taxa.</i>"

    sent = bot.send_photo(
        chat_id=message.chat.id,
        photo=image_stream,
        caption=caption,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton('⏰ Aguardando Pagamento...', callback_data='aguardando')]
        ])
    )

    # Armazena dados do pagamento para verificação via webhook (misticpay)
    if gateway_usado in ('misticpay',):
        try:
            with open('settings/pagamentos_pendentes.json', 'r', encoding='utf-8') as f:
                pagamentos_pendentes = json.load(f)
        except:
            pagamentos_pendentes = {}
        pagamentos_pendentes[str(id_pag)] = {
            'chat_id': message.chat.id,
            'valor': valor,
            'message_id': sent.message_id,
            'timestamp': int(time.time())
        }
        with open('settings/pagamentos_pendentes.json', 'w', encoding='utf-8') as f:
            json.dump(pagamentos_pendentes, f, indent=4)

    # --- NOTIFICAÇÃO (PIX GERADO) ---
    try:
        dono_id = api.CredentialsChange.id_dono()
        canal_id = -1002787400901
        u_tag = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
        msg_dono = (
            f"💸 <b>PIX GERADO!</b> ({gateway_usado})\n\n"
            f"👤 <b>Cliente:</b> {message.from_user.first_name}\n"
            f"🆔 <b>ID:</b> <code>{message.chat.id}</code>\n"
            f"💰 <b>Valor:</b> R$ {valor:.2f}\n"
            f"🧾 <b>Pagamento ID:</b> <code>{id_pag}</code>"
        )
        # Mensagem do canal: sem valor exato (privacidade do cliente)
        msg_canal = "💸 Um usuário gerou um Pix."
        try:
            bot.send_message(dono_id, msg_dono, parse_mode='HTML')
        except: pass
        try:
            bot.send_message(canal_id, msg_canal)
        except Exception as e:
            print(f"Erro canal pix: {e}")
    except Exception as e:
        print(f"Erro ao avisar pix: {e}")
    # ----------------------------------------

    # Inicia verificação em background com a função correta do gateway usado
    if gateway_usado == 'promissepay':
        threading.Thread(
            target=verificar_pagamento_promissepay,
            args=(message.chat.id, id_pag, valor, sent.message_id),
            daemon=True
        ).start()
    elif gateway_usado == 'misticpay':
        threading.Thread(
            target=lambda: verificar_pagamento_misticpay(message.chat.id, id_pag, valor, sent.message_id),
            daemon=True
        ).start()
    elif gateway_usado == 'mercadopago':
        threading.Thread(
            target=verificar_pagamento_mercadopago,
            args=(message.chat.id, id_pag, valor, sent.message_id),
            daemon=True
        ).start()
@bot.message_handler(commands=['top_depositors'])
def handle_top_depositors(message):
    if not (api.Admin.verificar_admin(message.chat.id) or int(message.chat.id) == int(api.CredentialsChange.id_dono())):
        bot.reply_to(message, "❌ Você não tem permissão para usar este comando.")
        return
    top_depositors = rankings.get_top_depositors()
    if top_depositors:
        output = "<b>🏆 Top 10 Usuários com Mais Depósitos 🏆</b>\n\n"
        for idx, user in enumerate(top_depositors, start=1):
            username = user.get('username') or f"User{user.get('id')}"
            total_pagos = float(user.get('total_pagos', 0.0))
            output += f"{idx}. <b>{username}</b> (ID: <code>{user.get('id')}</code>) - <b>Total Depósitos:</b> R${total_pagos:.2f}\n"
        bot.send_message(chat_id=message.chat.id, text=output, parse_mode='HTML')
    else:
        bot.send_message(chat_id=message.chat.id, text='Não há depositadores para exibir no ranking.')
@bot.message_handler(commands=['top_products'])
def handle_top_products(message):
    if not (api.Admin.verificar_admin(message.chat.id) or int(message.chat.id) == int(api.CredentialsChange.id_dono())):
        bot.reply_to(message, "❌ Você não tem permissão para usar este comando.")
        return
    top_products = rankings.get_top_products_last_30_days()
    if top_products:
        output = "<b>🏆 Top 10 Produtos Mais Vendidos nos Últimos 30 Dias 🏆</b>\n\n"
        for idx, (produto, vendas) in enumerate(top_products, start=1):
            output += f"{idx}. <b>{produto}</b> - <b>Vendas:</b> {vendas}\n"
        bot.send_message(chat_id=message.chat.id, text=output, parse_mode='HTML')
    else:
        bot.send_message(chat_id=message.chat.id, text='Nenhum produto vendido nos últimos 30 dias.')
@bot.message_handler(commands=['top_recent_depositors'])
def handle_top_recent_depositors(message):
    if not (api.Admin.verificar_admin(message.chat.id) or int(message.chat.id) == int(api.CredentialsChange.id_dono())):
        bot.reply_to(message, "❌ Você não tem permissão para usar este comando.")
        return
    top_recent_depositors = rankings.get_top_recent_depositors()
    if top_recent_depositors:
        output = "<b>🏆 Top 10 Usuários com Mais Depósitos nos Últimos 30 Dias 🏆</b>\n\n"
        for idx, user in enumerate(top_recent_depositors, start=1):
            username = user.get('username') or f"User{user.get('id')}"
            total_recent_pagos = float(user.get('total_recent_pagos', 0.0))
            output += f"{idx}. <b>{username}</b> (ID: <code>{user.get('id')}</code>) - <b>Depósitos Recentes:</b> R${total_recent_pagos:.2f}\n"
        bot.send_message(chat_id=message.chat.id, text=output, parse_mode='HTML')
    else:
        bot.send_message(chat_id=message.chat.id, text='Nenhum depósito recente registrado nos últimos 30 dias.')
@bot.message_handler(commands=['rank'])
def handle_rank(message):
    top_users = get_top_users()
    if top_users:
        medals = ['🥇', '🥈', '🥉']
        output = "🏆 *Top 20 Usuários por Saldo* 🏆\n\n"
        for idx, user in enumerate(top_users):
            medal = medals[idx] if idx < 3 else f"{idx+1}º"
            output += f"{medal} @{user['username']} (ID: {user['id']}) - Saldo: R${user['saldo']:.2f}\n"
        bot.send_message(chat_id=message.chat.id, text=output, parse_mode='HTML')
    else:
        bot.send_message(chat_id=message.chat.id, text='Não há usuários para exibir no ranking.')

def is_admin(message):
    return api.Admin.verificar_admin(message.chat.id) == True or int(message.chat.id) == int(api.CredentialsChange.id_dono())

# ==================== LOGINS SALDOS ====================
import os, json, hashlib
# =========================================================================
# SISTEMA DE ABASTECIMENTO INTELIGENTE
# - Templates de serviço (modo rápido: só EMAIL/SENHA)
# - Importação em massa por arquivo (.txt/.csv)
# - Prévia com confirmação antes de gravar no estoque
# - Detecção de duplicados
# =========================================================================
modo_rapido = {}  # user_id -> dict do template em uso (ou None = modo completo)
pendentes_confirmacao = {}  # user_id -> {'logins': [...], 'duplicados': set(emails)}

def _templates_path():
    return os.path.join('database', 'templates_servicos.json')

def carregar_templates():
    caminho = _templates_path()
    if not os.path.exists(caminho):
        return {}
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[Abastecimento] Erro ao carregar templates: {e}")
        return {}

def salvar_template(nome, valor, descricao, duracao):
    templates = carregar_templates()
    templates[nome.strip()] = {'valor': valor.strip(), 'descricao': descricao.strip(), 'duracao': duracao.strip()}
    os.makedirs('database', exist_ok=True)
    with open(_templates_path(), 'w', encoding='utf-8') as f:
        json.dump(templates, f, indent=4, ensure_ascii=False)

def buscar_template(nome_busca):
    """Busca um template por nome, ignorando maiúsculas/minúsculas e espaços."""
    templates = carregar_templates()
    alvo = nome_busca.strip().upper()
    for nome_salvo, dados in templates.items():
        if nome_salvo.strip().upper() == alvo:
            return nome_salvo, dados
    return None, None

@bot.message_handler(commands=['addservico'])
def comando_addservico(message):
    return bot.reply_to(message, "Estoque gerenciado pela API. Faça a reposição no bot raiz.")

@bot.message_handler(commands=['servicos_salvos'])
def comando_listar_templates(message):
    if not is_admin(message):
        bot.reply_to(message, "❌ Você não tem permissão para usar este comando.")
        return
    templates = carregar_templates()
    if not templates:
        bot.reply_to(message, "📭 Nenhum modelo de serviço salvo ainda. Use /addservico para criar um.")
        return
    linhas = ["📋 <b>Modelos de Serviço Salvos:</b>\n"]
    for nome, dados in sorted(templates.items()):
        linhas.append(f"• <b>{nome}</b> — R${dados.get('valor')} — {dados.get('duracao')} dias")
    linhas.append("\n<i>Use /add NOME para abastecer rapidamente (só EMAIL/SENHA).</i>")
    bot.reply_to(message, "\n".join(linhas), parse_mode='HTML')

@bot.message_handler(commands=['add'])
def iniciar_adicao_logins(message):
    return bot.reply_to(message, "Estoque gerenciado pela API. Faça a reposição no bot raiz.")
def _historico_parse_data(data_str):
    """Tenta converter a data da compra em datetime, aceitando os formatos
    mais comuns usados no bot (com hora, só data BR, ou ISO)."""
    if not data_str:
        return None
    data_str = data_str.strip()
    try:
        return datetime.strptime(data_str, "%d/%m/%Y %H:%M:%S")
    except ValueError:
        pass
    try:
        return datetime.strptime(data_str.split(" ")[0], "%d/%m/%Y")
    except ValueError:
        pass
    try:
        return datetime.strptime(data_str.split(" ")[0], "%Y-%m-%d")
    except ValueError:
        pass
    return None


def _historico_filtrar_ativas(historico_total):
    """Retorna só as compras com 30 dias ou menos (contas 'ativas')."""
    agora = datetime.now()
    ativas = []
    for item in historico_total:
        try:
            data_str = item.get("data_compra") or item.get("data") or item.get("data_pagamento") or ""
            data_compra = _historico_parse_data(data_str)
            if data_compra:
                if (agora - data_compra).days <= 30:
                    ativas.append(item)
            else:
                print(f"[Aviso] Formato de data desconhecido no histórico: {data_str}")
        except Exception as e:
            print(f"Erro ao processar data no histórico: {e}")
            continue
    return ativas


_HISTORICO_ESTADO_PATH = 'historicos/_estado_envio.json'


def _historico_carregar_estado():
    if not os.path.exists(_HISTORICO_ESTADO_PATH):
        return {}
    try:
        with open(_HISTORICO_ESTADO_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _historico_salvar_estado(estado):
    caminho_dir = 'historicos'
    if not os.path.exists(caminho_dir): os.makedirs(caminho_dir)
    with open(_HISTORICO_ESTADO_PATH, 'w', encoding='utf-8') as f:
        json.dump(estado, f, ensure_ascii=False)


def _historico_item_hash(item):
    """Gera uma identidade estável pro item, pra saber se ele já foi
    mandado antes ou se é novo/alterado."""
    produto = item.get('produto') or item.get('servico') or item.get('nome') or ""
    acesso = item.get('email') or item.get('login') or item.get('usuario') or item.get('conta') or ""
    senha = item.get('senha') or item.get('pass') or ""
    data_compra = item.get('data_compra') or item.get('data') or item.get('data_pagamento') or ""
    chave = f"{produto}|{acesso}|{senha}|{data_compra}"
    return hashlib.sha1(chave.encode('utf-8')).hexdigest()


def _historico_filtrar_novos(user_id, itens):
    """Separa, dentre os itens que apareceriam no arquivo, só os que ainda
    não foram enviados pro usuário antes (novos ou com dado alterado)."""
    estado = _historico_carregar_estado()
    chave_usuario = str(user_id)
    ja_enviados = set(estado.get(chave_usuario, []))
    novos = []
    hashes_atuais = []
    for item in itens:
        h = _historico_item_hash(item)
        hashes_atuais.append(h)
        if h not in ja_enviados:
            novos.append(item)
    return novos, ja_enviados, hashes_atuais


def _historico_marcar_enviados(user_id, ja_enviados, hashes_atuais):
    estado = _historico_carregar_estado()
    chave_usuario = str(user_id)
    estado[chave_usuario] = list(ja_enviados.union(hashes_atuais))
    _historico_salvar_estado(estado)


def _historico_montar_teclado(user_id, apenas_ativas):
    markup = InlineKeyboardMarkup()
    # Sempre mostra os dois botões, um embaixo do outro
    markup.add(InlineKeyboardButton('🟢 Apenas Ativas (30 dias)', callback_data=f'historico_ativas {user_id}'))
    markup.add(InlineKeyboardButton('📋 Histórico Completo', callback_data=f'historico_todas {user_id}'))
    return markup


def _historico_gerar_arquivo(user_id, itens, apenas_ativas):
    caminho_dir = 'historicos'
    if not os.path.exists(caminho_dir): os.makedirs(caminho_dir)
    sufixo = 'ativas' if apenas_ativas else 'todas'
    caminho_txt = f'{caminho_dir}/{user_id}_{sufixo}.txt'
    titulo = "RELATÓRIO DE CONTAS ATIVAS (30 DIAS)" if apenas_ativas else "RELATÓRIO DE TODAS AS COMPRAS"
    with open(caminho_txt, "w", encoding="utf-8") as f:
        f.write(f"{titulo}\n")
        f.write(f"USUÁRIO ID: {user_id}\n")
        f.write("="*30 + "\n\n")
        for h in itens:
            produto = h.get('produto') or h.get('servico') or h.get('nome') or "Não especificado"
            data_mostrada = h.get('data_compra') or h.get('data') or "Data não encontrada"
            # Tenta pegar o acesso pelas chaves mais comuns (email, login, usuario, conta)
            acesso = h.get('email') or h.get('login') or h.get('usuario') or h.get('conta') or "Email/Login não encontrado"
            # Caso o bot salve a senha separada do email, você também pode mostrá-la
            senha = h.get('senha') or h.get('pass') or ""
            f.write(f"PRODUTO: {produto}\n")
            # Se houver senha e ela já não estiver colada junto com o acesso
            if senha and senha not in acesso:
                f.write(f"ACESSO: {acesso}\n")
                f.write(f"SENHA: {senha}\n")
            else:
                f.write(f"ACESSO: {acesso}\n")
            f.write(f"COMPRADO EM: {data_mostrada}\n")
            f.write("-" * 20 + "\n")
    return caminho_txt


def _historico_enviar(chat_id, user_id, apenas_ativas, enviar_arquivo=True):
    data = load_user_data(user_id) or {}
    historico_total = data.get("compras", []) or data.get("historico", [])
    itens = _historico_filtrar_ativas(historico_total) if apenas_ativas else historico_total
    teclado = _historico_montar_teclado(user_id, apenas_ativas)

    if not itens:
        if apenas_ativas:
            texto = (
                "📅 <b>Você não tem compras ativas (não vencidas) no bot.</b>\n\n"
                "<i>Use o botão abaixo para ver todas as compras.</i>"
            )
        else:
            texto = (
                "📂 <b>Você não tem compras no bot.</b> Quando comprar alguma conta, "
                "as informações dela ficarão exibidas aqui."
            )
        bot.send_message(chat_id, texto, parse_mode='HTML', reply_markup=teclado)
        return

    # Cálculos à prova de falhas: evita erros se o valor estiver vazio ou vier com formato estranho
    total_gasto = 0.0
    for r in itens:
        valor_bruto = str(r.get("valor") or r.get("preco") or "0")
        # Troca as vírgulas por pontos e tira qualquer R$ que possa ter ficado preso na string
        valor_limpo = valor_bruto.replace('R$', '').replace(' ', '').replace(',', '.')
        try:
            total_gasto += float(valor_limpo)
        except ValueError:
            pass

    titulo = "Suas Contas Ativas (30 dias)" if apenas_ativas else "Todas as Suas Compras"
    rodape = "<i>Use os botões abaixo para escolher e receber o arquivo com os dados de acesso.</i>"
    resumo = (
        f"📊 <b>{titulo}</b>\n\n"
        f"💸 Total investido: R${total_gasto:.2f}\n"
        f"📦 Quantidade: {len(itens)} itens\n\n"
        f"{rodape}"
    )
    bot.send_message(chat_id, resumo, parse_mode='HTML', reply_markup=teclado)


def _historico_enviar_arquivo(chat_id, message_id, user_id, apenas_ativas):
    """Chamado ao clicar em um dos botões: apaga a mensagem com os botões
    e manda só o arquivo TXT com os itens novos ou alterados desde o
    último envio (não repete o que o usuário já recebeu antes)."""
    data = load_user_data(user_id) or {}
    historico_total = data.get("compras", []) or data.get("historico", [])
    itens = _historico_filtrar_ativas(historico_total) if apenas_ativas else historico_total

    # Remove a mensagem com os botões para não deixar "lixo" na conversa
    try:
        bot.delete_message(chat_id, message_id)
    except Exception:
        # Se não conseguir apagar (ex: mensagem muito antiga), pelo menos remove os botões
        try:
            bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
        except Exception:
            pass

    if not itens:
        texto = (
            "📅 <b>Você não tem compras ativas (não vencidas) no bot.</b>"
            if apenas_ativas else
            "📂 <b>Você não tem compras no bot.</b>"
        )
        bot.send_message(chat_id, texto, parse_mode='HTML')
        return

    try:
        caminho_txt = _historico_gerar_arquivo(user_id, itens, apenas_ativas)
        with open(caminho_txt, 'rb') as f:
            bot.send_document(
                chat_id=chat_id,
                document=f,
                caption=(
                    f"📜 {len(itens)} item(ns) - Contas Ativas" if apenas_ativas
                    else f"📜 {len(itens)} item(ns) - Histórico de Compras"
                )
            )
        # Limpeza
        if os.path.exists(caminho_txt): os.remove(caminho_txt)
    except Exception as e:
        print(f"Erro ao gerar TXT: {e}")
        bot.send_message(chat_id, "❌ Erro ao gerar o arquivo de histórico.")


@bot.message_handler(commands=['historico'])
def comando_historico(message):
    user_id = message.from_user.id
    # Só mostra o resumo + os dois botões; o arquivo TXT só é enviado quando o usuário clicar em um deles
    _historico_enviar(message.chat.id, user_id, apenas_ativas=False, enviar_arquivo=False)


@bot.callback_query_handler(func=lambda call: call.data == 'ver_historico_perfil')
def callback_ver_historico_perfil(call):
    """Botão '📜 HISTÓRICO' dentro do menu de Perfil."""
    user_id = call.from_user.id
    bot.answer_callback_query(call.id)
    _historico_enviar(call.message.chat.id, user_id, apenas_ativas=False, enviar_arquivo=False)


@bot.callback_query_handler(func=lambda call: call.data.startswith('historico_ativas '))
def callback_historico_ativas(call):
    user_id = call.data.split(' ')[1]
    bot.answer_callback_query(call.id)
    _historico_enviar_arquivo(call.message.chat.id, call.message.message_id, user_id, apenas_ativas=True)


@bot.callback_query_handler(func=lambda call: call.data.startswith('historico_todas '))
def callback_historico_todas(call):
    user_id = call.data.split(' ')[1]
    bot.answer_callback_query(call.id)
    _historico_enviar_arquivo(call.message.chat.id, call.message.message_id, user_id, apenas_ativas=False)
@bot.message_handler(commands=['id'])
def comando_id(message):
    user = message.from_user
    user_id = user.id
    username = user.username or "—"
    saldo = get_user_balance(user_id)
    bot.reply_to(
        message,
        (
            f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
            f"👤 <b>Nome:</b> {user.first_name} {user.last_name or ''}\n"
            f"🔖 <b>@:</b> @{username}\n"
            f"💰 <b>Saldo:</b> R${float(saldo):.2f}"
        ),
        parse_mode='HTML'
    )
@bot.message_handler(commands=['saldo'])
def comando_saldo(message):
    user = message.from_user
    user_id = user.id
    username = user.username or "—"
    saldo = get_user_balance(user_id)
    bot.reply_to(
        message,
        (
            f"💰 <b>Saldo:</b> R${float(saldo):.2f}\n"
            f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
            f"🔖 <b>@:</b> @{username}"
        ),
        parse_mode='HTML'
    )
@bot.message_handler(commands=['done'])
def finalizar_comando(message):
    user_id = message.from_user.id
    if adding_logins.get(user_id, False):
        finalizar_adicao_logins(user_id)
    else:
        bot.reply_to(message, "❌ Você não está no modo de adição de logins.")
def _escapar_markdown_legado(texto):
    """Escapa caracteres especiais do Markdown legado do Telegram (_, *, `, [)
    para que emails/senhas com esses símbolos não quebrem a formatação da mensagem."""
    if texto is None:
        return ''
    for ch in ('_', '*', '`', '['):
        texto = texto.replace(ch, '\\' + ch)
    return texto


def _identificador_linha(linha):
    """Tenta identificar a linha inválida pelo e-mail (mais legível pro admin);
    se não achar '@', usa um trecho da própria linha."""
    for parte in linha.split('/'):
        parte = parte.strip()
        if '@' in parte:
            return parte
    trecho = linha.strip()
    return (trecho[:40] + '…') if len(trecho) > 40 else trecho


def _diagnosticar_linha(user_id, linha):
    """Explica exatamente por que uma linha foi rejeitada (campo vazio, barra
    dupla, valor/duração não numéricos, etc.), no mesmo estilo de um diff
    campo a campo."""
    template = modo_rapido.get(user_id)
    if template:
        esperado, campos = 2, ['EMAIL', 'SENHA']
    else:
        esperado, campos = 6, ['NOME', 'VALOR', 'DESCRIÇÃO', 'EMAIL', 'SENHA', 'DURAÇÃO']

    if '//' in linha:
        return "contém uma barra dupla '//' (ficou um campo vazio no meio) — remova a barra extra."

    partes = linha.split('/')
    if len(partes) < esperado:
        faltando = esperado - len(partes)
        return (f"faltam {faltando} campo(s) — esperado {esperado} "
                f"({'/'.join(campos)}), a linha só tem {len(partes)}.")
    if len(partes) > esperado:
        sobrando = len(partes) - esperado
        return (f"tem {sobrando} campo(s) a mais — esperado {esperado} "
                f"({'/'.join(campos)}), a linha tem {len(partes)}.")

    partes = [p.strip() for p in partes]
    if template:
        email, senha = partes
        if not email:
            return "o campo EMAIL está vazio."
        if not senha:
            return "o campo SENHA está vazio."
    else:
        _nome, valor, _descricao, email, _senha, duracao = partes
        if not email:
            return "o campo EMAIL está vazio."
        try:
            float(valor.replace(',', '.'))
        except ValueError:
            return f"o campo VALOR ('{valor}') não é um número válido."
        try:
            int(duracao)
        except ValueError:
            return f"o campo DURAÇÃO ('{duracao}') não é um número inteiro válido."
    return "formato inválido (não foi possível identificar o campo exato)."


def _linha_para_completa(user_id, linha):
    """Converte uma linha crua para o formato completo NOME/VALOR/DESCRICAO/EMAIL/SENHA/DURACAO.
    No modo rápido, a linha só precisa ter EMAIL/SENHA (o resto vem do template)."""
    template = modo_rapido.get(user_id)
    partes = linha.split('/')
    if template:
        if len(partes) != 2:
            return None
        email, senha = partes[0].strip(), partes[1].strip()
        if not email or not senha:
            return None
        return f"{template['nome']}/{template['valor']}/{template['descricao']}/{email}/{senha}/{template['duracao']}"
    else:
        if len(partes) != 6:
            return None
        # Valida que valor e duração são numéricos antes de aceitar a linha
        _nome, valor, _descricao, email, _senha, duracao = [p.strip() for p in partes]
        if not email:
            return None
        try:
            float(valor.replace(',', '.'))
            int(duracao)
        except ValueError:
            return None
        return '/'.join(p.strip() for p in partes)

def _processar_linhas(user_id, linhas):
    """Processa uma lista de linhas cruas (vindas de texto ou de arquivo), adicionando
    as válidas ao buffer temp_logins. Retorna (adicionados, invalidos, detalhes_erros),
    onde detalhes_erros é uma lista de strings "identificador — motivo exato"."""
    adicionados = 0
    invalidos = 0
    detalhes_erros = []
    for linha in linhas:
        linha = linha.strip()
        if not linha:
            continue
        completa = _linha_para_completa(user_id, linha)
        if completa is None:
            invalidos += 1
            motivo = _diagnosticar_linha(user_id, linha)
            identificador = _escapar_markdown_legado(_identificador_linha(linha))
            detalhes_erros.append(f"{identificador} — {motivo}")
            continue
        temp_logins.setdefault(user_id, []).append(completa)
        adicionados += 1
    return adicionados, invalidos, detalhes_erros

def _reiniciar_timer_abastecimento(user_id):
    if user_id in add_login_timers:
        add_login_timers[user_id].cancel()
    timer = Timer(300, finalizar_adicao_logins, args=[user_id])
    timer.start()
    add_login_timers[user_id] = timer

def _formato_esperado_texto(user_id):
    template = modo_rapido.get(user_id)
    if template:
        return "`EMAIL/SENHA`"
    return "`NOME/VALOR/DESCRIÇÃO/EMAIL/SENHA/DURAÇÃO`"

@bot.message_handler(func=lambda message: adding_logins.get(message.from_user.id, False) and message.text and not message.text.startswith('/'))
def receber_logins(message):
    user_id = message.from_user.id
    if not adding_logins.get(user_id, False):
        return
    linhas = message.text.strip().split('\n')
    adicionados, invalidos, detalhes_erros = _processar_linhas(user_id, linhas)
    quantidade_total = len(temp_logins.get(user_id, []))
    feedback = f"✅ Adicionados {adicionados} login(s) com sucesso! (total no lote: {quantidade_total})"
    if invalidos > 0:
        feedback += f"\n❌ {invalidos} linha(s) com formato inválido foram ignoradas:"
        for detalhe in detalhes_erros[:10]:
            feedback += f"\n   • {detalhe}"
        if len(detalhes_erros) > 10:
            feedback += f"\n   • ... e mais {len(detalhes_erros) - 10} linha(s)."
        feedback += f"\nFormato esperado: {_formato_esperado_texto(user_id)}"
    feedback += "\nEnvie mais logins, um arquivo .txt/.csv, ou envie `/done` para revisar e finalizar."
    bot.reply_to(message, feedback, parse_mode='Markdown')
    _reiniciar_timer_abastecimento(user_id)

@bot.message_handler(content_types=['document'], func=lambda message: adding_logins.get(message.from_user.id, False))
def receber_arquivo_logins(message):
    """Permite abastecer em massa enviando um arquivo .txt/.csv com um login por linha,
    em vez de digitar linha por linha no chat."""
    user_id = message.from_user.id
    nome_arquivo = (message.document.file_name or '').lower()
    if not (nome_arquivo.endswith('.txt') or nome_arquivo.endswith('.csv')):
        bot.reply_to(message, "⚠️ Envie um arquivo .txt ou .csv, com um login por linha no mesmo formato do modo em uso.")
        return
    try:
        file_info = bot.get_file(message.document.file_id)
        conteudo_bytes = bot.download_file(file_info.file_path)
        conteudo = conteudo_bytes.decode('utf-8', errors='replace')
    except Exception as e:
        bot.reply_to(message, f"❌ Erro ao ler o arquivo: {e}")
        return
    linhas = [l.strip().rstrip(',') for l in conteudo.splitlines()]
    adicionados, invalidos, detalhes_erros = _processar_linhas(user_id, linhas)
    quantidade_total = len(temp_logins.get(user_id, []))
    feedback = f"📎 Arquivo processado! {adicionados} login(s) válido(s) adicionados. (total no lote: {quantidade_total})"
    if invalidos > 0:
        feedback += f"\n❌ {invalidos} linha(s) inválida(s) foram ignoradas:"
        for detalhe in detalhes_erros[:10]:
            feedback += f"\n   • {detalhe}"
        if len(detalhes_erros) > 10:
            feedback += f"\n   • ... e mais {len(detalhes_erros) - 10} linha(s)."
        feedback += f"\nFormato esperado: {_formato_esperado_texto(user_id)}"
    feedback += "\nEnvie `/done` para revisar e confirmar o abastecimento."
    bot.reply_to(message, feedback, parse_mode='Markdown')
    _reiniciar_timer_abastecimento(user_id)

def _chaves_existentes_estoque():
    """Carrega o conjunto de (plataforma, email) já presentes no estoque gravado."""
    return set()

def _chave_login(linha):
    """Extrai (plataforma, email) normalizados de uma linha NOME/VALOR/DESCRICAO/EMAIL/SENHA/DURACAO."""
    partes = linha.split('/')
    return (partes[0].strip().lower(), partes[3].strip().lower())

def _emails_duplicados(logins):
    """Verifica quais (plataforma, email) já são duplicados: seja porque já existem no estoque
    atual, seja porque aparecem mais de uma vez dentro do próprio lote sendo enviado agora.
    Só conta como duplicidade se for da MESMA plataforma (campo 'nome')."""
    chaves_existentes = _chaves_existentes_estoque()
    duplicados = set()
    vistos_no_lote = set()
    for linha in logins:
        try:
            chave = _chave_login(linha)
        except IndexError:
            continue
        if chave in chaves_existentes or chave in vistos_no_lote:
            duplicados.add(chave)
        vistos_no_lote.add(chave)
    return duplicados

def _chaves_renovadas():
    """Carrega um dicionário {(plataforma, email): info} com os logins que já foram renovados
    dentro do bot, ou seja, que aparecem em 'purchases' de algum cliente com 'last_renewal'
    preenchido. 'info' traz o cliente, a senha, quando foi renovado e o vencimento atual —
    para avisar o admin com detalhes antes de abastecer, evitando recolocar em estoque um
    login que já foi entregue/renovado para um cliente."""
    from app.database import load_user_data, get_all_user_ids
    tz_br = pytz_timezone('America/Sao_Paulo')
    chaves = {}
    try:
        for uid in get_all_user_ids():
            user_data = load_user_data(uid) or {}
            username = user_data.get('username') or str(uid)
            for p in user_data.get('purchases', []):
                if not p.get('last_renewal'):
                    continue
                nome = str(p.get('servico', '')).strip().lower()
                email = str(p.get('email', '')).strip().lower()
                if not (nome and email):
                    continue
                try:
                    renovado_em = datetime.fromisoformat(p['last_renewal']).astimezone(tz_br).strftime('%d/%m/%Y %H:%M')
                except Exception:
                    renovado_em = p.get('last_renewal', '—')
                try:
                    vencimento = datetime.fromisoformat(p['expires_at']).astimezone(tz_br).strftime('%d/%m/%Y %H:%M')
                except Exception:
                    vencimento = p.get('expires_at', '—')
                chaves[(nome, email)] = {
                    'user_id': uid,
                    'username': username,
                    'senha': p.get('senha', '—'),
                    'renovado_em': renovado_em,
                    'vencimento': vencimento,
                }
    except Exception as e:
        print(f"[Abastecimento] Erro ao checar logins renovados: {e}")
    return chaves

def _logins_renovados(logins):
    """Verifica quais (plataforma, email) do lote sendo abastecido já foram renovados
    dentro do bot (já pertencem a um cliente que renovou aquele login). Retorna um
    dicionário {(plataforma, email): info} com os detalhes da renovação encontrada."""
    chaves_renovadas = _chaves_renovadas()
    renovados = {}
    for linha in logins:
        try:
            chave = _chave_login(linha)
        except IndexError:
            continue
        if chave in chaves_renovadas:
            renovados[chave] = chaves_renovadas[chave]
    return renovados

def finalizar_adicao_logins(user_id):
    """Chamado por /done ou por timeout. Não grava mais direto no estoque: monta uma
    prévia do lote (com aviso de duplicados) e pede confirmação por botão antes de gravar."""
    if not adding_logins.get(user_id, False):
        return
    logins = temp_logins.get(user_id, [])
    adding_logins[user_id] = False
    if user_id in add_login_timers:
        add_login_timers[user_id].cancel()
        del add_login_timers[user_id]
    if not logins:
        bot.send_message(user_id, "❌ Nenhum login foi adicionado.")
        modo_rapido.pop(user_id, None)
        return
    counts = Counter()
    for linha in logins:
        try:
            nome = linha.split('/')[0]
            counts[nome] += 1
        except Exception:
            continue
    duplicados = _emails_duplicados(logins)
    renovados = _logins_renovados(logins)
    pendentes_confirmacao[user_id] = {'logins': logins, 'duplicados': duplicados, 'renovados': renovados}
    total = len(logins)
    partes_msg = [
        "📝 <b>Prévia do Abastecimento</b>",
        f"Total de logins prontos para gravar: <b>{total}</b> em <b>{len(counts)}</b> serviço(s).",
        ""
    ]
    for servico, qtd in sorted(counts.items()):
        partes_msg.append(f"• <b>{servico}:</b> {qtd} login(s)")
    markup = InlineKeyboardMarkup()
    if renovados:
        partes_msg.append(f"\n🔁 <b>{len(renovados)} login(s) já foram renovados dentro do bot</b> (já entregue(s)/renovado(s) para um cliente — cuidado ao reabastecer):")
        for (nome, email), info in list(renovados.items())[:10]:
            partes_msg.append(
                f"  • <b>{nome}</b> - {email} / {info['senha']}\n"
                f"    👤 Cliente: {info['username']} (<code>{info['user_id']}</code>)\n"
                f"    🗓 Renovado em: {info['renovado_em']}\n"
                f"    ⏳ Vence em: {info['vencimento']}"
            )
        if len(renovados) > 10:
            partes_msg.append(f"  ...e mais {len(renovados) - 10}.")
    if duplicados:
        partes_msg.append(f"\n⚠️ <b>{len(duplicados)} login(s) já existem no estoque atual</b> (mesma plataforma + mesmo email):")
        for nome, email in list(duplicados)[:10]:
            partes_msg.append(f"  • {nome} - {email}")
        if len(duplicados) > 10:
            partes_msg.append(f"  ...e mais {len(duplicados) - 10}.")
    if duplicados or renovados:
        markup.add(InlineKeyboardButton('✅ Gravar Todos Mesmo Assim', callback_data=f'abast_confirmar_todos {user_id}'))
        markup.add(InlineKeyboardButton('🧹 Gravar Só os Novos (pular duplicados/renovados)', callback_data=f'abast_confirmar_novos {user_id}'))
    else:
        markup.add(InlineKeyboardButton('✅ Confirmar e Gravar', callback_data=f'abast_confirmar_todos {user_id}'))
    markup.add(InlineKeyboardButton('❌ Cancelar', callback_data=f'abast_cancelar {user_id}'))
    bot.send_message(user_id, "\n".join(partes_msg), parse_mode='HTML', reply_markup=markup)

def _gravar_logins_no_estoque(user_id, logins):
    """Grava de fato os logins no estoque via api.ControleLogins, atualiza data_adicao
    e dispara os alertas de novo estoque. Só é chamado após confirmação do admin."""
    return bot.send_message(user_id, "Estoque gerenciado pela API. Use o bot raiz.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('abast_confirmar_todos ') or call.data.startswith('abast_confirmar_novos '))
def cb_confirmar_abastecimento(call):
    modo_pular_duplicados = call.data.startswith('abast_confirmar_novos ')
    user_id = int(call.data.split(' ')[1])
    if call.from_user.id != user_id and not is_admin(call.message):
        bot.answer_callback_query(call.id, 'Sem permissão.', show_alert=True)
        return
    pendente = pendentes_confirmacao.pop(user_id, None)
    bot.answer_callback_query(call.id)
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except Exception:
        pass
    if not pendente:
        bot.send_message(user_id, "❌ Essa prévia expirou ou já foi processada.")
        return
    logins = pendente['logins']
    duplicados = pendente['duplicados']
    renovados = pendente.get('renovados', {})
    if modo_pular_duplicados and (duplicados or renovados):
        chaves_existentes = _chaves_existentes_estoque()
        vistos_no_lote = set()
        novos_logins = []
        for l in logins:
            try:
                chave = _chave_login(l)
            except IndexError:
                novos_logins.append(l)
                continue
            if chave in chaves_existentes:
                continue  # já existe no estoque: descarta
            if chave in renovados:
                continue  # login já renovado dentro do bot: descarta
            if chave in vistos_no_lote:
                continue  # repetido dentro do próprio lote: mantém só a 1ª ocorrência
            vistos_no_lote.add(chave)
            novos_logins.append(l)
        logins = novos_logins
    _gravar_logins_no_estoque(user_id, logins)
    temp_logins[user_id] = []
    modo_rapido.pop(user_id, None)

@bot.callback_query_handler(func=lambda call: call.data.startswith('abast_cancelar '))
def cb_cancelar_abastecimento(call):
    user_id = int(call.data.split(' ')[1])
    if call.from_user.id != user_id and not is_admin(call.message):
        bot.answer_callback_query(call.id, 'Sem permissão.', show_alert=True)
        return
    pendentes_confirmacao.pop(user_id, None)
    temp_logins[user_id] = []
    modo_rapido.pop(user_id, None)
    bot.answer_callback_query(call.id, 'Abastecimento cancelado.')
    try:
        bot.edit_message_text('❌ Abastecimento cancelado. Nenhum login foi gravado.', chat_id=call.message.chat.id, message_id=call.message.message_id)
    except Exception:
        bot.send_message(user_id, '❌ Abastecimento cancelado. Nenhum login foi gravado.')

adding_logins = {}
temp_logins = {}
add_login_timers = {}
ID_CANAL_NOTIFICACOES = "-1002787400901" # COLOQUE O ID DO SEU CANAL AQUI (Não esqueça do -100)
def notify_subscribers(servico: str, quantidade: int):
    """Alerta para Canal, ADM e usuários inscritos na PALAVRA do serviço."""
    from datetime import datetime
    import pytz
    import os
    import json
    try:
        # Pega estoque atual
        try:
            estoque_atual = int(api.ControleLogins.pegar_estoque(servico) or 0)
        except Exception:
            estoque_atual = 0
        tz_brasil = pytz.timezone('America/Sao_Paulo')
        agora = datetime.now(tz_brasil).strftime("%d/%m/%Y às %H:%M:%S")
        if int(quantidade) == 1:
            texto = f"""
📢 <b>NOVO ALERTA DE LOGIN</b> 📢
✅ Foi adicionado <b>{quantidade} novo login</b> ao estoque!
🔹 <b>Serviço:</b> {servico}
🔹 <b>Quantidade adicionada:</b> {quantidade}
📦 <b>Estoque atual:</b> {estoque_atual}
🕐 <b>Atualizado em:</b> {agora}
➡️ Acesse o bot e garanta o seu antes que acabe!
"""
        else:
            texto = f"""
📢 <b>NOVO ALERTA DE LOGIN</b> 📢
✅ Foram adicionados <b>{quantidade} novos logins</b>!
🔹 <b>Serviço:</b> {servico}
🔹 <b>Quantidade adicionada:</b> {quantidade}
📦 <b>Estoque atual:</b> {estoque_atual}
🕐 <b>Atualizado em:</b> {agora}
➡️ Entre agora no bot e aproveite!
"""
        # ==========================================
        # 1. TECLADO PARA O CANAL (Apenas Abrir o Bot)
        # ==========================================
        kb_canal = InlineKeyboardMarkup(row_width=1)
        try:
            bot_username = (api.CredentialsChange.user_bot() or "").lstrip("@")
            if bot_username:
                kb_canal.add(InlineKeyboardButton("🤖 Abrir o bot", url=f"https://t.me/{bot_username}"))
        except Exception:
            pass
        # ==========================================
        # 2. TECLADO PARA O BOT (Botão Removido)
        # ==========================================
        kb_bot = None
        # ==========================================
        # ENVIOS
        # ==========================================
        # 1. ENVIAR PARA O CANAL
        try:
            bot.send_message(ID_CANAL_NOTIFICACOES, texto, parse_mode="HTML", reply_markup=kb_canal)
        except Exception as e:
            print(f"[ALERTAS] Erro ao enviar para o CANAL: {e}")
        # 2. ENVIAR PARA O ADM (Dono do bot)
        id_dono = None
        try:
            id_dono = str(api.CredentialsChange.id_dono())
            bot.send_message(id_dono, texto, parse_mode="HTML", reply_markup=kb_bot)
        except Exception as e:
            print(f"[ALERTAS] Erro ao enviar para o ADM: {e}")
        # 3. ENVIAR PARA USUÁRIOS INSCRITOS
        try:
            alerts = {}
            # Tenta achar o arquivo de alertas na raiz do bot
            caminho_alerts = 'alerts.json'
            # Se não achar na raiz, tenta na pasta database (caso você tenha movido)
            if not os.path.exists(caminho_alerts):
                caminho_alerts = os.path.join('database', 'alerts.json')
            if os.path.exists(caminho_alerts):
                with open(caminho_alerts, 'r', encoding='utf-8') as f:
                    alerts = json.load(f)
            usuarios_para_notificar = set()
            # A lógica original do seu bot salva {"NOME_DO_SERVICO": [ID1, ID2]}
            chave_servico = str(servico).strip().upper()
            for palavra, usuarios in alerts.items():
                palavra_upper = str(palavra).strip().upper()
                # Verifica se a palavra bate com o serviço (Ex: "NETFLIX" bate com "NETFLIX 1 TELA")
                if palavra_upper in chave_servico or chave_servico in palavra_upper:
                    if isinstance(usuarios, list):
                        for uid in usuarios:
                            usuarios_para_notificar.add(str(uid))
                    else:
                        usuarios_para_notificar.add(str(usuarios))
            # Envia o alerta para cada usuário encontrado
            for u in usuarios_para_notificar:
                try:
                    if u != id_dono: # Evita mandar duplicado pro dono
                        bot.send_message(u, texto, parse_mode="HTML", reply_markup=kb_bot)
                except Exception as e:
                    print(f"[ALERTAS] Falha ao enviar alerta para usuário {u}: {e}")
        except Exception as e:
            print(f"[ALERTAS] Erro ao processar inscritos: {e}")
    except Exception as e:
        print(f"[ALERTAS] Erro fatal em notify_subscribers: {e}")
@bot.message_handler(commands=['getchatid'])
def get_chat_id(message):
    chat_id = message.chat.id
    bot.reply_to(message, f'O ID deste chat é: {chat_id}')
@bot.message_handler(commands=['gift'])
def handle_gift_command(message):
    if not (api.Admin.verificar_admin(message.from_user.id) or int(message.from_user.id) == int(api.CredentialsChange.id_dono())):
        bot.reply_to(message, "❌ Você não tem permissão para usar este comando.")
        return
    try:
        valor = float(message.text.split()[1])
    except (IndexError, ValueError):
        bot.reply_to(message, "⚠️ Use o comando corretamente:\n/gift <valor>\nExemplo: /gift 10")
        return
    while True:
        codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
        if not api.GiftCard.validar_gift(codigo)[0]:
            api.GiftCard.create_gift(codigo, valor)
            break
    texto_gift = (
        f"🏷 <b>GIFT CARD GERADO!</b>\n"
        f"📮 <b>GIFT CARD:</b> <code>/resgatar {codigo}</code>\n"
        f"💸 <b>VALOR:</b> R$ {valor:.2f}\n"
        f"📥 <b>RESGATE:</b> @{api.CredentialsChange.user_bot()}"
    )
    bot.reply_to(message, texto_gift, parse_mode='HTML')
def iniciar_verificacao():
    while True:
        time.sleep(240)
        ver_se_expirou()
        time.sleep(43200)
threading.Thread(target=iniciar_verificacao).start()
import time, threading, os, uuid
def add_purchase(user_id, servico, email, senha, valor, duracao):
    user_data = load_user_data(user_id) or {}
    purchases = user_data.get('purchases', [])
    now = datetime.now(pytz_timezone('America/Sao_Paulo'))
    # --- CORREÇÃO APLICADA ---
    # Agora, a expiração é calculada a partir da data e hora exatas da compra.
    expires_at = now + timedelta(days=int(duracao))
    # --- FIM DA CORREÇÃO ---
    purchase = {
        'id': str(uuid.uuid4()),
        'servico': servico,
        'email': email,
        'senha': senha,
        'valor': float(valor),
        'data_compra': now.isoformat(),
        'expires_at': expires_at.isoformat(),
        'notified_one_day_before': False,
        'notified_on_expiration': False
    }
    purchases.append(purchase)
    user_data['purchases'] = purchases
    # --- Adicionar também no campo 'compras' para estatísticas do painel ---
    compras = user_data.get('compras', [])
    compras.append({
        'servico': servico,
        'valor': float(valor),
        'email': email,
        'senha': senha,
        'data': now.strftime("%d/%m/%Y %H:%M:%S")
    })
    user_data['compras'] = compras
    user_data['total_compras'] = len(compras)
    save_user_data(user_id, user_data)
    return purchase
# threading.Thread(target=send_expiration_notifications, daemon=True).start()
print("[AVISO] O loop automático de renovação (send_expiration_notifications) foi desativado.")
from app.database import load_user_data, save_user_data, get_user_balance, add_saldo, add_pagamento
# Função para exibir o painel de avisos de expiração (sem loop)
# [REMOVIDO] Código legado do painel antigo removido. Toda lógica de painel de avisos agora está centralizada na função _create_paginated_admin_message e _get_all_current_avisos.
# Handlers removidos - agora estão no callback_query genérico
@bot.callback_query_handler(func=lambda call: call.data == 'noop')
def handle_noop(call):
    """Handler para botões que não fazem nada (como indicador de página)"""
    bot.answer_callback_query(call.id)
# === HANDLERS DOS NOVOS BOTÕES DO PAINEL DE AVISOS DO ADMIN ===
# CORREÇÃO: get_all_user_ids listava database/users/*.json, pasta que não
# existe mais após a migração para SQLite. Agora usa database.get_all_user_ids().
from app.database import get_all_user_ids
def get_users_with_saldo():
    from app.database import load_user_data
    user_ids = get_all_user_ids()
    users = []
    for uid in user_ids:
        data = load_user_data(uid)
        if data and data.get('saldo', 0) > 0:
            users.append((uid, data['saldo']))
    return users
@bot.message_handler(commands=['resetar_saldos'])
def resetar_saldos(message):
    if not (is_admin(message) or str(message.from_user.id) == str(api.CredentialsChange.id_dono())):
        bot.reply_to(message, 'Apenas administradores podem usar este comando.')
        return
    users = get_users_with_saldo()
    total = len(users)
    if total == 0:
        bot.reply_to(message, 'Nenhum cliente possui saldo para resetar.')
        return
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton('✅ Confirmar Reset', callback_data='confirmar_resetar_saldos'),
        InlineKeyboardButton('❌ Cancelar', callback_data='cancelar_resetar_saldos')
    )
    aviso = f'⚠️ <b>ATENÇÃO!</b>\n\nExistem <b>{total}</b> clientes com saldo.\nDeseja realmente ZERAR o saldo de todos?\n\nEsta ação NÃO pode ser desfeita.'
    bot.reply_to(message, aviso, parse_mode='HTML', reply_markup=markup)
@bot.callback_query_handler(func=lambda call: call.data in ['confirmar_resetar_saldos', 'cancelar_resetar_saldos'])
def handle_resetar_saldos_callback(call):
    user_id = call.from_user.id
    is_owner = str(user_id) == str(api.CredentialsChange.id_dono())
    if not (is_admin(call.message) or is_owner):
        bot.answer_callback_query(call.id, 'Sem permissão.', show_alert=True)
        return
    if call.data == 'cancelar_resetar_saldos':
        try:
            bot.edit_message_text('Operação cancelada.', chat_id=call.message.chat.id, message_id=call.message.message_id)
        except Exception:
            bot.send_message(call.message.chat.id, 'Operação cancelada.')
        return
    from app.database import load_user_data, save_user_data
    users = get_users_with_saldo()
    total = len(users)
    try:
        msg_progresso = bot.edit_message_text(f'⏳ Zerando saldo de {total} clientes... Aguarde.', chat_id=call.message.chat.id, message_id=call.message.message_id)
    except Exception:
        msg_progresso = bot.send_message(call.message.chat.id, f'⏳ Zerando saldo de {total} clientes... Aguarde.')
    count = 0
    for uid, saldo in users:
        data = load_user_data(uid)
        if data:
            data['saldo'] = 0
            save_user_data(uid, data)
            try:
                bot.send_message(uid, '⚠��� Seu saldo foi resetado pelo administrador.')
            except Exception:
                pass
        count += 1
        if count % 10 == 0 or count == total:
            try:
                bot.edit_message_text(f'⏳ Zerando saldo de {total} clientes... ({count}/{total})', chat_id=call.message.chat.id, message_id=msg_progresso.message_id)
            except Exception:
                pass
    try:
        bot.edit_message_text(f'✅ Todos os saldos foram resetados. ({total} clientes)', chat_id=call.message.chat.id, message_id=msg_progresso.message_id)
    except Exception:
        bot.send_message(call.message.chat.id, f'✅ Todos os saldos foram resetados. ({total} clientes)')
    bot.send_message(call.from_user.id, f'🚨 <b>Todos os saldos foram zerados!</b>\n\n{total} clientes afetados.', parse_mode='HTML')

# Função duplicada removida - usando a versão corrigida acima
# Handler: Voltar ao Painel de Avisos
# === HANDLERS CORRIGIDOS PARA REATIVAR/CANCELAR AVISOS DO PAINEL ADMIN ===

# ==================== MONITORAMENTO BACKUP ====================
from telebot.types import CallbackQuery
# === COMO USAR: handlers e comandos (registrados antes do polling) ===
# Início do loop de polling movido para o final do arquivo para que todos os handlers
# sejam registrados antes do bot começar a escutar eventos.
# 
# Garantir que não há webhook ativo quando usamos polling
# COLE ESTE BLOCO AQUI (Ele vai capturar os cliques nos botões de TXT)
try:
    bot.remove_webhook()
except Exception:
    pass
# removido: chamada direta de bot.infinity_polling()
# (Nada de handlers abaixo deste ponto)
@bot.message_handler(commands=['ping','health'])
def _health_ping(m):
    try:
        bot.reply_to(m, "✅ Estou online.")
    except Exception as e:
        print(f"[HEALTH] erro ao responder: {e}")
# ======= LOOP DE POLLING RESILIENTE =======
import time, logging
try:
    import faulthandler; faulthandler.enable()
except Exception:
    pass
try:
    from telebot import util, logger
    logger.setLevel(logging.INFO)
except Exception:
    util = None
# ===== DEBUG: loga qualquer mensagem recebida =====
@bot.message_handler(commands=['start'])
def _cmd_start(m):
    try:
        bot.send_message(m.chat.id, "🤖 Bot online! Use /ping para testar. (start mínimo de diagnóstico)")
    except Exception as e:
        print(f"[START] erro: {e}")
# [REMOVIDO] Handler de diagnóstico antigo que estava causando conflitos
# @bot.message_handler(commands=['admin'])
# def _cmd_admin(m):
#     pass
# Handler de diagnóstico de estoque removido
@bot.message_handler(commands=['id'])
def _cmd_id(m):
    try:
        bot.send_message(m.chat.id, f"🆔 Seu ID: {m.from_user.id}")
    except Exception as e:
        print(f"[ID] erro: {e}")
# ======================= [INÍCIO] GERENCIAMENTO DE EMOJIS =======================
@bot.message_handler(commands=['setemoji'])
def command_set_emoji(message):
    """
    Comando para admin: Altera o ID de um emoji premium no arquivo JSON.
    Uso: /setemoji 💰 5224257782013769471
    """
    import os
    import json
    try:
        # Verifica se o usuário é o dono do bot
        if str(message.from_user.id) != str(api.CredentialsChange.id_dono()):
            bot.reply_to(message, "🚫 Você não tem permissão para usar este comando.")
            return
        parts = (message.text or "").strip().split(maxsplit=2)
        if len(parts) < 3:
            bot.reply_to(
                message, 
                "ℹ️ <b>Uso correto:</b>\n<code>/setemoji [emoji] [id]</code>\n\nExemplo: <code>/setemoji 💰 5224257782013769471</code>", 
                parse_mode='HTML'
            )
            return
        emoji_target = parts[1]
        new_id = parts[2]
        # Garante que o ID contém apenas números
        if not new_id.isdigit() and new_id != "":
             bot.reply_to(message, "❌ O ID do emoji deve conter apenas números.")
             return
        caminho_arquivo = 'premium_emojis.json'
        # Carrega o JSON atual
        if os.path.exists(caminho_arquivo):
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            bot.reply_to(message, "❌ Arquivo premium_emojis.json não encontrado.")
            return
        # Atualiza ou cria a entrada para o emoji
        if "emojis" not in data:
            data["emojis"] = {}
        if emoji_target in data["emojis"]:
            data["emojis"][emoji_target]["custom_emoji_id"] = new_id
        else:
            # Se o emoji não existir no arquivo, adiciona um novo
            data["emojis"][emoji_target] = {
                "fallback": emoji_target,
                "custom_emoji_id": new_id,
                "descricao": "Adicionado pelo painel do bot",
                "ocorrencias_encontradas": 0
            }
        # Salva as alterações no arquivo
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        bot.reply_to(message, f"✅ O emoji {emoji_target} foi atualizado com o ID <code>{new_id}</code> com sucesso no sistema!", parse_mode='HTML')
    except Exception as e:
        bot.reply_to(message, f"⚠️ Erro ao salvar o emoji: {e}")
# ======================= [INÍCIO] ADICIONAR EMOJI EM MASSA =======================
@bot.message_handler(commands=['prefixar'])
def command_prefixar(message):
    """
    Adiciona um emoji (ou texto) na frente de todos os produtos que contenham uma palavra-chave.
    Uso: /prefixar Globo 🌷
    """
    return bot.reply_to(message, "Estoque gerenciado pela API. Use o bot raiz.")
# ======================= [FIM] ADICIONAR EMOJI EM MASSA =======================
# ===== DIAGNÓSTICO DE WEBHOOK / UPDATES =====
def _diag_webhook_and_updates():
    try:
        import requests, json as _json
        base = f"https://api.telegram.org/bot{bot.token}"
        # 1) getMe
        r = requests.get(f"{base}/getMe", timeout=10)
        print("[TG] getMe:", r.text)
        # 2) getWebhookInfo
        r = requests.get(f"{base}/getWebhookInfo", timeout=10)
        print("[TG] getWebhookInfo:", r.text)
        # 3) deleteWebhook (hard) com drop_pending_updates
        r = requests.get(f"{base}/deleteWebhook?drop_pending_updates=true", timeout=10)
        print("[TG] deleteWebhook:", r.text)
        # 4) getUpdates (se ainda houver webhook, deve dar 409)
        r = requests.get(f"{base}/getUpdates", timeout=10)
        print("[TG] getUpdates:", r.text)
    except Exception as e:
        print(f"[TG] diag erro: {e}")
# ===== DEBUG (seguro): loga apenas mensagens de texto que NÃO são comandos =====
# Safe global state for maintenance message capture used by multiple handlers
try:
    admin_setting_maintenance_message
except NameError:
    admin_setting_maintenance_message = {}
# @bot.message_handler(func=lambda m: getattr(m, "text", "") and not m.text.startswith("/") and not admin_setting_maintenance_message.get(m.from_user.id, False), content_types=['text'])
def _debug_any_msg(m):
    try:
        u = getattr(m.from_user, 'username', None)
        print(f"[MSG] {m.chat.id} @{u} -> {m.text}")
    except Exception as e:
        print(f"[MSG] erro para logar msg: {e}")
        print("[ERROR] Já existe uma instância do bot rodando! Removendo lockfile antigo...")
        try:
            os.remove(lockfile)
        except:
            pass
    # Criar lockfile para esta instância
    try:
        with open(lockfile, 'w') as f:
            f.write(str(os.getpid()))
        print(f"[BOOT] Instância única confirmada (PID: {os.getpid()})")
    except Exception as e:
        print(f"[ERROR] Falha ao criar lockfile: {e}")
    print("[BOOT] removendo webhook e iniciando polling…")
    try:
        info = bot.get_webhook_info()
        print(f"[TG] getWebhookInfo(pytelebot): url={getattr(info, 'url', None)}, pending={getattr(info, 'pending_update_count', None)}")
    except Exception as e:
        print(f"[TG] getWebhookInfo erro: {e}")
    try:
        bot.remove_webhook()
        print("[TG] remove_webhook() chamado com sucesso.")
    except Exception as e:
        print(f"[TG] remove_webhook() erro: {e}")
    # loop robusto com backoff exponencial
    reconnect_attempts = 0
    max_attempts = 20
    try:
        while True:
            try:
                print(f"[TG] Iniciando polling (tentativa {reconnect_attempts + 1})")
                bot.infinity_polling(timeout=20, long_polling_timeout=20)
                # Se chegou aqui, reset counter
                reconnect_attempts = 0
            except KeyboardInterrupt:
                print("[TG] KeyboardInterrupt recebido, encerrando...")
                raise
            except Exception as e:
                error_str = str(e)
                # Se for erro 409 (conflito), parar completamente
                if "409" in error_str and "Conflict" in error_str:
                    print(f"[FATAL] Detectado conflito de instâncias múltiplas. Parando bot...")
                    break
                # Se for erro de rede/timeout, tentar reconectar
                if any(keyword in error_str.lower() for keyword in [
                    "timeout", "network", "connection", "unreachable", 
                    "502", "503", "504", "read timed out", "connect"
                ]):
                    reconnect_attempts += 1
                    if reconnect_attempts > max_attempts:
                        print(f"[FATAL] Muitas tentativas de reconexão ({max_attempts}), encerrando...")
                        break
                    # Backoff exponencial: 5s, 10s, 20s, 40s, max 300s (5min)
                    backoff = min(300, 5 * (2 ** (reconnect_attempts - 1)))
                    print(f"[RECONNECT] Erro de rede: {type(e).__name__}: {e}")
                    print(f"[RECONNECT] Tentativa {reconnect_attempts}/{max_attempts}, aguardando {backoff}s...")
                    # Limpar webhook antes de tentar novamente
                    try:
                        bot.remove_webhook()
                        print("[RECONNECT] Webhook limpo")
                    except Exception as wh_e:
                        print(f"[RECONNECT] Erro ao limpar webhook: {wh_e}")
                    time.sleep(backoff)
                    continue
                # Outros erros: log e tentar novamente com delay menor
                print(f"[CRASH] Erro inesperado: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(10)
    finally:
        # Limpar lockfile ao sair
        try:
            if os.path.exists(lockfile):
                os.remove(lockfile)
                print("[BOOT] Lockfile removido.")
        except:
            pass
# === RL BACKUP ADMIN CALLBACKS ===
# --- Deduplicação simples de alertas para ADM (evita duplicidade imediata) ---
__dedup_alerts_adm = {}  # chave: str -> epoch
def _adm_dedup_key(servico: str, quantidade: int, estoque_atual: int) -> str:
    return f"{(servico or '').strip().upper()}|{int(quantidade)}|{int(estoque_atual)}"
@bot.callback_query_handler(func=lambda c: c.data in {"admin_backup_now", "admin_backup_path"})
def cb_admin_backup(c):
    if str(c.from_user.id) != str(ADMIN_ID):
        return bot.answer_callback_query(c.id, "Acesso negado.", show_alert=True)
    if c.data == "admin_backup_path":
        import os
        try:
            bp = os.path.abspath(backup_manager.BACKUP_DIR)
            bot.answer_callback_query(c.id, "Ok!")
            return bot.send_message(c.message.chat.id, f"📁 Pasta de backups:\n`{bp}`", parse_mode="Markdown")
        except Exception as e:
            bot.answer_callback_query(c.id, "Erro", show_alert=True)
            return bot.send_message(c.message.chat.id, f"⚠️ Erro ao obter pasta: {e}")
    if c.data == "admin_backup_now":
        bot.answer_callback_query(c.id, "Iniciando backup…")
        try:
            bot.send_message(c.message.chat.id, "⏳ Fazendo backup… (você receberá o arquivo/link ao concluir)")
            backup_manager.run_backup_async(bot=bot, admin_id=ADMIN_ID, label="manual")
        except Exception as e:
            bot.send_message(c.message.chat.id, f"⚠️ Erro ao iniciar backup: {e}")
@bot.message_handler(commands=['backup'])
def cmd_backup(message):
    if str(message.from_user.id) != str(ADMIN_ID):
        return bot.reply_to(message, "Acesso negado.")
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🧩 Backup (ZIP)", callback_data="admin_backup_now"),
        InlineKeyboardButton("📁 Pasta Backups", callback_data="admin_backup_path")
    )
    bot.send_message(message.chat.id, "Selecione uma opção de backup:", reply_markup=kb)
@bot.callback_query_handler(func=lambda c: c.data == "admin_backup_toggle")
def cb_admin_backup_toggle(c):
    if str(c.from_user.id) != str(ADMIN_ID):
        return bot.answer_callback_query(c.id, "Acesso negado.", show_alert=True)
    try:
        new_state = not backup_manager.is_enabled()
        backup_manager.set_enabled(new_state)
        status = "ligado 🟢" if new_state else "desligado 🔴"
        bot.answer_callback_query(c.id, f"Auto-Backup {status}!", show_alert=True)
        # Re-render painel admin se quiser atualizar o texto do botão
        try:
            painel_admin(c.message)  # se sua função aceita 'message'
        except Exception:
            pass
    except Exception as e:
        bot.answer_callback_query(c.id, f"Erro: {e}", show_alert=True)
# === Modo Manutenção: comandos de ADM ===
try:
    @bot.message_handler(commands=["manutencao_on"])
    def _adm_maint_on(message):
        try:
            if message.from_user.id == ADMIN_ID:
                maintenance_on()
                bot.reply_to(message, "🚧 Modo manutenção **ativado**. Usuários comuns serão temporariamente bloqueados.")
                try:
                    (
                notify_all_users_async(bot, exclude_ids=[ADMIN_ID])
                if 'notify_all_users_async' in globals() else notify_all_users(bot, exclude_ids=[ADMIN_ID])
            )
                except Exception as _e:
                    print(f"[maintenance] notify_all_users falhou: {_e}")
            else:
                bot.reply_to(message, "❌ Apenas administradores podem usar este comando.")
        except Exception as _e:
            print(f"[maintenance] erro manutencao_on: {_e}")
    @bot.message_handler(commands=["manutencao_off"])
    def _adm_maint_off(message):
        try:
            if message.from_user.id == ADMIN_ID:
                maintenance_off()
                bot.reply_to(message, "✅ Modo manutenção **desativado**. Tudo normalizado.")
            else:
                bot.reply_to(message, "❌ Apenas administradores podem usar este comando.")
        except Exception as _e:
            print(f"[maintenance] erro manutencao_off: {_e}")
except Exception as _e:
    print(f"[maintenance] falha ao registrar comandos: {_e}")
# ======================= [CALLBACKS MANUTENÇÃO PAINEL ADMIN] =======================
@bot.callback_query_handler(func=lambda c: c.data in ['admin_maintenance_on', 'admin_maintenance_off'])
def callback_admin_maintenance_toggle(call):
    """Handler para ativar/desativar manutenção via painel admin"""
    try:
        # Verificar se é admin usando a mesma lógica do painel
        if not (api.Admin.verificar_admin(call.from_user.id) or int(call.from_user.id) == int(api.CredentialsChange.id_dono())):
            return bot.answer_callback_query(call.id, "❌ Acesso negado.", show_alert=True)
        if call.data == 'admin_maintenance_on':
            maintenance_on()
            bot.answer_callback_query(call.id, "🚧 Manutenção ATIVADA!", show_alert=True)
            try:
                all_admin_ids = get_all_admin_ids()
                notify_all_users(bot, exclude_ids=all_admin_ids)
            except Exception as e:
                print(f"[MAINTENANCE] Erro ao notificar usuários: {e}")
        elif call.data == 'admin_maintenance_off':
            maintenance_off()
            bot.answer_callback_query(call.id, "✅ Manutenção DESATIVADA!", show_alert=True)
        # Atualizar o painel admin para refletir a mudança
        try:
            painel_admin(call.message)
        except Exception as e:
            print(f"[MAINTENANCE] Erro ao atualizar painel: {e}")
    except Exception as e:
        print(f"[MAINTENANCE] Erro no callback toggle: {e}")
        bot.answer_callback_query(call.id, "❌ Erro interno.", show_alert=True)
# Handlers de configura����o de mensagem removidos - causavam conflitos
# Todos os handlers de configuração de mensagem foram removidos
# Handler removido - funcionalidade simplificada
# ======================= [COMANDO DE STATUS MANUTENÇÃO] =======================
@bot.message_handler(commands=['status_manutencao'])
def cmd_status_manutencao(message):
    """Comando para verificar status detalhado da manutenção (apenas admin)"""
    try:
        if not (api.Admin.verificar_admin(message.from_user.id) or int(message.from_user.id) == int(api.CredentialsChange.id_dono())):
            return bot.reply_to(message, "❌ Apenas administradores podem usar este comando.")
        status = is_on()
        current_message = get_maintenance_message()
        texto = (
            f"🔧 <b>STATUS DO SISTEMA DE MANUTENÇÃO</b>\n\n"
            f"🚦 <b>Status:</b> {'🔴 ATIVADO' if status else '🟢 DESATIVADO'}\n\n"
            f"📝 <b>Mensagem atual:</b>\n<i>{current_message}</i>\n\n"
            f"💡 <b>Comandos disponíveis:</b>\n"
            f"• <code>/manutencao_on</code> - Ativar manutenção\n"
            f"• <code>/manutencao_off</code> - Desativar manutenção\n"
            f"• <code>/admin</code> - Painel completo com controles\n\n"
            f"⚙️ <i>Use o painel admin para configuração avançada</i>"
        )
        bot.reply_to(message, texto, parse_mode='HTML')
    except Exception as e:
        print(f"[MAINTENANCE] Erro no status: {e}")

# ======================= [SISTEMA DE AFILIADOS - CALLBACKS] =======================

# ==================== AFILIADOS BACKUP SCHEDULER ====================
@bot.callback_query_handler(func=lambda call: call.data in [
    'ver_indicacoes', 'ranking_indicadores', 'meu_link', 
    'admin_toggle_afiliados', 'admin_refresh_afiliados', 
    'admin_alterar_valor_indicacao', 'admin_stats_afiliados'
])
def handle_afiliados_callbacks(call):
    """Handler para callbacks do sistema de afiliados"""
    afiliados_sistema.handle_callback_afiliados(call, bot)
@bot.message_handler(func=lambda message: afiliados_sistema.admin_setting_valor_indicacao.get(message.from_user.id, False))
def handle_set_valor_indicacao(message):
    """Handler para capturar o novo valor de indicação"""
    user_id = message.from_user.id
    try:
        # Verificar se é admin
        if not (api.Admin.verificar_admin(user_id) or int(user_id) == int(api.CredentialsChange.id_dono())):
            afiliados_sistema.admin_setting_valor_indicacao[user_id] = False
            return bot.reply_to(message, "❌ Acesso negado.")
        # Tentar converter para float
        novo_valor = float(message.text.replace(',', '.'))
        if novo_valor < 0:
            return bot.reply_to(message, "❌ O valor deve ser positivo.")
        # Atualizar valor
        api.SistemaAfiliados.set_valor_indicacao(novo_valor)
        afiliados_sistema.admin_setting_valor_indicacao[user_id] = False
        bot.reply_to(message, f"✅ Valor por indicação alterado para R$ {novo_valor:.2f}")
    except ValueError:
        bot.reply_to(message, "❌ Valor inválido. Digite um número (exemplo: 10.50)")# ... (final da função handle_set_valor_indicacao) ...
    except Exception as e:
        afiliados_sistema.admin_setting_valor_indicacao[user_id] = False
        bot.reply_to(message, f"❌ Erro ao alterar valor: {e}")
# <<<---- COLOQUE SEU NOVO CÓDIGO A PARTIR DESTA LINHA ---->>>
# --- NEW CALLBACK HANDLER FOR REPORT PROBLEM TOGGLE ---
@bot.callback_query_handler(func=lambda call: call.data == 'toggle_report_problem')
def callback_toggle_report_problem(call):
    """Handles the button click in the admin panel to toggle the report problem feature."""
    if not is_admin_user(call.from_user.id):
        return bot.answer_callback_query(call.id, "🚫 Acesso Negado!", show_alert=True)
    try:
        new_state = toggle_reportar_problema()
        feedback_text = "✅ Sistema 'Reportar Problema' ATIVADO." if new_state else "❌ Sistema 'Reportar Problema' DESATIVADO."
        bot.answer_callback_query(call.id, feedback_text, show_alert=True)
        # Refresh the admin panel to show the updated button state
        try:
            # Simulate the /admin command to refresh the panel
            admin_message = call.message
            admin_message.text = '/admin' # Ensure the logic inside painel_admin knows it's an edit
            painel_admin(admin_message)
        except Exception as refresh_error:
            print(f"[ERROR] Failed to refresh admin panel after toggling report problem: {refresh_error}")
            # Send a simple confirmation if refresh fails
            bot.send_message(call.message.chat.id, feedback_text)
    except Exception as e:
        print(f"[ERROR] Failed to toggle report problem setting: {e}")
        bot.answer_callback_query(call.id, "❌ Erro ao alterar a configuração.", show_alert=True)
# --- END OF NEW CALLBACK HANDLER ---
# --- [NOVO] HANDLER PARA MENU CATEGORIAS ---
@bot.callback_query_handler(func=lambda c: c.data == 'toggle_menu_categorias')
def callback_toggle_menu_categorias(call):
    if not is_admin_user(call.from_user.id):
        return bot.answer_callback_query(call.id, "🚫 Acesso Negado!", show_alert=True)
    try:
        novo_estado = alternar_menu_categorias()
        txt = "Menu filtrado ativado!" if novo_estado else "Menu filtrado desativado!"
        bot.answer_callback_query(call.id, txt, show_alert=True)
        painel_admin(call.message)
    except Exception as e:
        print(f"[ERROR] Failed to toggle menu categorias: {e}")
        bot.answer_callback_query(call.id, "❌ Erro ao alterar a configuração.", show_alert=True)
# --- [FIM] NOVO HANDLER ---
@bot.message_handler(commands=['contasproblema'])
def command_contas_problema(message):
    """
    Comando para gerar o relatório de contas com problema.
    """
    if not (api.Admin.verificar_admin(message.from_user.id) or int(message.from_user.id) == int(api.CredentialsChange.id_dono())):
        return bot.reply_to(message, "🚫 Acesso Negado!")
    troca_automatica.gerar_relatorio_trocas(bot, message.chat.id)
@bot.callback_query_handler(func=lambda call: call.data == 'relatorio_trocas')
def callback_relatorio_trocas(call):
    """
    Mostra o menu de seleção de período para o relatório de trocas.
    """
    if not (api.Admin.verificar_admin(call.from_user.id) or int(call.from_user.id) == int(api.CredentialsChange.id_dono())):
        return bot.answer_callback_query(call.id, "🚫 Acesso Negado!", show_alert=True)
    bot.answer_callback_query(call.id)
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📅 Últimas 24 horas", callback_data="gerar_relatorio_trocas_1"))
    markup.row(InlineKeyboardButton("📅 Últimos 7 dias", callback_data="gerar_relatorio_trocas_7"))
    markup.row(InlineKeyboardButton("📅 Últimos 30 dias", callback_data="gerar_relatorio_trocas_30"))
    markup.row(InlineKeyboardButton("♾️ Todos os registros", callback_data="gerar_relatorio_trocas_todos"))
    markup.row(InlineKeyboardButton("❌ Cancelar", callback_data="voltar_paineladm")) # Volta para o painel admin
    bot.edit_message_text(
        "Selecione o período para o relatório de contas com problema:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup
    )
@bot.callback_query_handler(func=lambda call: call.data.startswith('gerar_relatorio_trocas_'))
def callback_gerar_relatorio_filtrado(call):
    """
    Pega a escolha do admin (1, 7, 30 dias ou todos) e gera o relatório.
    """
    if not (api.Admin.verificar_admin(call.from_user.id) or int(call.from_user.id) == int(api.CredentialsChange.id_dono())):
        return bot.answer_callback_query(call.id, "🚫 Acesso Negado!", show_alert=True)
    bot.answer_callback_query(call.id)
    try:
        # Deleta o menu de seleção
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    periodo = call.data.replace('gerar_relatorio_trocas_', '')
    dias = None
    if periodo.isdigit():
        dias = int(periodo)
    troca_automatica.gerar_relatorio_trocas(bot, call.message.chat.id, dias=dias)
# === INICIALIZAÇÃO DO BOT (depois de registrar TODOS os handlers) ===
# ADICIONE ESTE BLOCO ANTES de start_polling() ou if __name__ == '__main__':
# --- Novo Sistema de Agendamento de Backup ---
BACKUP_JOB_TAG = "auto_backup_job"
def run_scheduled_backup():
    """Função que será chamada pelo agendador para executar o backup."""
    if not backup_manager.is_enabled():
        print("[Scheduler] Backup automático desabilitado, pulando execução.")
        return
    print(f"[Scheduler] Iniciando backup automático agendado...")
    try:
        interval_minutes = backup_manager.get_backup_interval_minutes()
        label = backup_manager._humanize_minutes(interval_minutes)
        # Chama a função de backup assíncrona do backup_manager, passando o bot e ADMIN_ID
        # !! Certifique-se que ADMIN_ID está definido globalmente no seu bot.py !!
        # Se não estiver, você pode precisar obtê-lo aqui:
        # ADMIN_ID = int(api.CredentialsChange.id_dono()) # Descomente se necessário
        backup_manager.run_backup_async(bot=bot, admin_id=ADMIN_ID, label=f"auto_{label}")
        print(f"[Scheduler] Backup automático disparado com sucesso.")
    except Exception as e:
        print(f"[Scheduler] Erro ao disparar backup automático: {e}")
        try:
            # Tenta notificar o admin sobre a falha no agendamento
            # ADMIN_ID = int(api.CredentialsChange.id_dono()) # Descomente se necessário
            bot.send_message(ADMIN_ID, f"⚠️ Falha ao iniciar o backup agendado: {e}")
        except Exception as notify_err:
            print(f"[Scheduler] Falha ao notificar admin sobre erro no agendamento: {notify_err}")
def update_schedule():
    """Limpa o job antigo e agenda um novo com o intervalo atual."""
    schedule.clear(BACKUP_JOB_TAG)
    if not backup_manager.is_enabled(): # Adicionado: Não agendar se estiver desabilitado
        print("[Scheduler] Backup desabilitado, nenhum job agendado.")
        return
    interval = backup_manager.get_backup_interval_minutes()
    schedule.every(interval).minutes.do(run_scheduled_backup).tag(BACKUP_JOB_TAG)
    print(f"[Scheduler] Backup agendado para rodar a cada {interval} minutos.")
    next_run = schedule.next_run
    if next_run:
        print(f"[Scheduler] Próxima execução agendada para: {next_run}")
    else:
        print("[Scheduler] Não foi possível determinar a próxima execução.")
def schedule_checker():
    """Thread que executa continuamente os jobs agendados."""
    print("[Scheduler] Thread de verificação de agendamento iniciada.")
    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            print(f"[Scheduler] Erro durante run_pending: {e}")
        time.sleep(60) # Verifica a cada 60 segundos

# --- Inicialização do Agendamento ---

# ==================== VERIFICACAO GATEWAYS ====================
try:
    print("[Scheduler] Configurando o agendamento inicial do backup...")
    # !! Certifique-se que ADMIN_ID está definido globalmente ANTES daqui !!
    # Se não, defina-o aqui:
    if 'ADMIN_ID' not in globals():
         ADMIN_ID = int(api.CredentialsChange.id_dono())
         print(f"[Scheduler] ADMIN_ID definido como {ADMIN_ID}")
    update_schedule() # Agenda o backup com o intervalo atual ao iniciar
    # Inicia a thread que verifica os agendamentos
    scheduler_thread = threading.Thread(target=schedule_checker, daemon=True)
    scheduler_thread.start()
    print("[Scheduler] Thread de agendamento iniciada.")
except Exception as e:
    print(f"[Scheduler] Erro CRÍTICO ao iniciar o agendador de backup: {e}")
# --- Fim do Novo Sistema de Agendamento ---
# ==========================================================
# HANDLERS DO NOVO SISTEMA DE SUPORTE
# ==========================================================
# ===== INTEGRAÇÃO MISTICPAY =====
def verificar_pagamento_misticpay(chat_id, id_pag, valor, message_id):
    """Consulta periodicamente o status no MisticPay e credita o saldo."""
    import time
    import requests
    from app.database import load_user_data, save_user_data, check_pagamento_ja_processado
    from pytz import timezone as pytz_timezone
    from datetime import datetime
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    tz = pytz_timezone('America/Sao_Paulo')
    admin_id = int(api.CredentialsChange.id_dono())
    print(f"[MISTIC-VERIFY] Iniciando verificação de pagamento: ID={id_pag}, Chat={chat_id}, Valor={valor}")
    try:
        creds = api.CredentialsChange.InfoMisticPay.credenciais()
        import base64
        auth_str = base64.b64encode(f"{creds['ci']}:{creds['cs']}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_str}",
            "Content-Type": "application/json"
        }
        url = "https://api.misticpay.com/api/transactions/check"
        print(f"[MISTIC-VERIFY] Credenciais carregadas com sucesso")
    except Exception as e:
        print(f"[MISTIC-VERIFY] ❌ Erro ao obter credenciais: {e}")
        bot.send_message(chat_id, f"❌ Erro ao verificar pagamento: credenciais não configuradas")
        return
    expiracao_minutos = int(api.CredentialsChange.InfoPix.expiracao())
    tentativas = (expiracao_minutos * 60) // 10
    print(f"[MISTIC-VERIFY] Tentativas: {tentativas} (expiracao: {expiracao_minutos} min)")
    for tentativa_num in range(tentativas):
        try:
            payload = {"transactionId": str(id_pag)}
            print(f"[MISTIC-VERIFY] Tentativa {tentativa_num + 1}/{tentativas}: Consultando {id_pag}...")
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            result = response.json()
            print(f"[MISTIC-VERIFY] Status HTTP: {response.status_code}")
            print(f"[MISTIC-VERIFY] Resposta: {result}")
            if response.status_code == 200 and "transaction" in result:
                status = result["transaction"]["transactionState"]
                print(f"[MISTIC-VERIFY] Status da transação: {status}")
            else:
                status = "PENDENTE"
                print(f"[MISTIC-VERIFY] Resposta inválida, status=PENDENTE")
        except Exception as e:
            print(f"[MISTIC-VERIFY] ❌ Erro ao consultar status do pag. {id_pag}: {e}")
            time.sleep(10)
            continue
        if status == "COMPLETO":
            print(f"[MISTIC-VERIFY] Pagamento COMPLETO! Processando...")
            try:
                if check_pagamento_ja_processado(id_pag):
                    print(f"[MISTIC-VERIFY] Pagamento já foi processado")
                    return
                min_bonus = float(api.CredentialsChange.BonusPix.valor_minimo_para_bonus())
                pct_bonus = float(api.CredentialsChange.BonusPix.quantidade_bonus())
                bonus_amt = (valor * (pct_bonus / 100.0)) if valor >= min_bonus else 0.0
                saldo_deposito = valor + bonus_amt
                print(f"[MISTIC-VERIFY] Bonus: {bonus_amt}, Total: {saldo_deposito}")
                user_data = load_user_data(chat_id)
                if user_data is None:
                    from app.database import initialize_user
                    user_data = initialize_user(chat_id)
                    print(f"[MISTIC-VERIFY] Usuario inicializado")
                before = user_data.get('saldo', 0.0)
                after = before + saldo_deposito
                user_data['saldo'] = after
                print(f"[MISTIC-VERIFY] Saldo: {before} -> {after}")
                pagamentos = user_data.get('pagamentos', [])
                pagamentos.append({
                    'id': id_pag,
                    'valor': valor,
                    'data': datetime.now(tz).strftime("%d/%m/%Y às %H:%M:%S")
                })
                user_data['pagamentos'] = pagamentos
                save_user_data(chat_id, user_data)
                print(f"[MISTIC-VERIFY] Dados salvos")
                # Obter dados do usuário para a mensagem
                nome = "Cliente"
                username = "Sem username"
                try:
                    # Tenta obter do banco de dados
                    nome_db = user_data.get('nome', '')
                    username_db = user_data.get('username', '')
                    if nome_db:
                        nome = nome_db
                    if username_db:
                        username = username_db
                except Exception as e:
                    print(f"[MISTIC-VERIFY] Erro ao obter dados do usuário: {e}")
                    pass
                # Formatar mensagem para o usuário com saldo
                msg_usuario = (
                    f"🌟 <b>PAGAMENTO APROVADO!</b>\n\n"
                    f"💰 Valor creditado: <b>R$ {saldo_deposito:.2f}</b>\n\n"
                    f"<b>Atualização de Saldo:</b>\n"
                    f"- Anterior: R$ {before:.2f}\n"
                    f"+ Novo Saldo: R$ {after:.2f}\n\n"
                    f"📅 Data: {datetime.now(tz).strftime('%d/%m/%Y às %H:%M:%S')}"
                )
                print(f"[MISTIC-VERIFY] Enviando: {msg_usuario}")
                # Enviar mensagem ao usuário com retry
                tentativas_msg = 0
                while tentativas_msg < 3:
                    try:
                        bot.send_message(chat_id, msg_usuario, parse_mode='HTML')
                        print(f"[MISTIC-VERIFY] Mensagem enviada ao usuário com sucesso")
                        break
                    except Exception as e:
                        tentativas_msg += 1
                        print(f"[MISTIC-VERIFY] Tentativa {tentativas_msg}/3 falhou ao enviar msg ao usuário: {e}")
                        if tentativas_msg < 3:
                            time.sleep(2)
                # Editar caption da imagem
                try:
                    bot.edit_message_caption(chat_id=chat_id, message_id=message_id, caption=f"✅ <b>Pagamento de R${valor:.2f} Aprovado!</b>", parse_mode="HTML")
                    print(f"[MISTIC-VERIFY] Caption editada com sucesso")
                except Exception as e:
                    print(f"[MISTIC-VERIFY] Falha ao editar caption: {e}")
                # Notificar Admin com retry
                # nome e username ja foram definidos acima
                texto_adm = (
                    f"🌟 <b>PAGAMENTO APROVADO - MisticPay</b>\n\n"
                    f"<b>Detalhes do Cliente:</b>\n"
                    f"👤 <b>Nome:</b> {nome}\n"
                    f"💳 <b>Username:</b> {username}\n"
                    f"🆔 <b>ID:</b> <code>{chat_id}</code>\n\n"
                    f"<b>Detalhes da Transação:</b>\n"
                    f"💵 <b>Valor Recebido:</b> R$ {valor:.2f}\n"
                    f"🎁 <b>Bônus Aplicado:</b> R$ {bonus_amt:.2f}\n"
                    f"💰 <b>Total Creditado:</b> R$ {saldo_deposito:.2f}\n\n"
                    f"<b>Atualização de Saldo:</b>\n"
                    f"- <b>Anterior:</b> R$ {before:.2f}\n"
                    f"+ <b>Novo Saldo:</b> R$ {after:.2f}\n\n"
                    f"<b>Referência do Pagamento:</b>\n"
                    f"🔐 <code>{id_pag}</code>\n\n"
                    f"📅 <b>Data:</b> {datetime.now(tz).strftime('%d/%m/%Y às %H:%M:%S')}"
                )
                tentativas_adm = 0
                while tentativas_adm < 3:
                    try:
                        bot.send_message(chat_id=admin_id, text=texto_adm, parse_mode='HTML')
                        print(f"[MISTIC-VERIFY] Notificação enviada ao admin com sucesso")
                        break
                    except Exception as e:
                        tentativas_adm += 1
                        print(f"[MISTIC-VERIFY] Tentativa {tentativas_adm}/3 falhou ao enviar msg ao admin: {e}")
                        if tentativas_adm < 3:
                            time.sleep(2)
            except Exception as e:
                print(f"[MisticPay] Falha ao processar pagamento {chat_id}: {e}")
            return
        elif status in ["FALHA", "CANCELADO"]:
            try:
                bot.edit_message_caption(chat_id=chat_id, message_id=message_id, caption="❌ Este pagamento foi cancelado ou falhou.", parse_mode="HTML")
            except:
                pass
            return
        time.sleep(10)
    try:
        bot.edit_message_caption(chat_id=chat_id, message_id=message_id, caption="⏱️ O tempo para pagamento deste PIX expirou.", parse_mode="HTML")
    except:
        pass
    alertar_adm_pix_nao_pago(bot, chat_id, valor)

# =========================================================
# SISTEMA DE VENCIMENTOS (SUBMENU)
# =========================================================
@bot.callback_query_handler(func=lambda call: call.data == 'menu_vencimentos')
def menu_vencimentos_opcoes(call):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📅 Vencendo HOJE", callback_data="venc_hoje"))
    markup.row(InlineKeyboardButton("📅 Vencendo AMANHÃ", callback_data="venc_amanha"))
    markup.row(InlineKeyboardButton("📊 Vendas por Data", callback_data="ver_loguins_por_data"))
    markup.row(InlineKeyboardButton("⬅️ Voltar", callback_data="voltar_paineladm"))
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="<b>📅 Vencimentos e Vendas</b>\n\nEscolha a opção que deseja consultar:",
        reply_markup=markup,
        parse_mode="HTML"
    )
@bot.callback_query_handler(func=lambda call: call.data in ['venc_hoje', 'venc_amanha'])
def processar_vencimentos(call):
    deslocamento = 0 if call.data == 'venc_hoje' else 1
    periodo_txt = "Hoje" if deslocamento == 0 else "Amanhã"
    bot.answer_callback_query(call.id, "Buscando...")
    # 1. Dá um feedback visual IMEDIATO para o botão não parecer travado
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"⏳ <b>Aguarde...</b>\nFazendo uma varredura profunda nas contas para <b>{periodo_txt}</b>. Isso pode levar alguns segundos...",
            parse_mode="HTML"
        )
    except Exception:
        pass # Ignora se a mensagem já estiver com esse texto
    # 2. Faz a varredura pesada
    lista, data_formatada = vencimentos.listar_contas(deslocamento)
    # 3. Monta o resultado final
    if not lista:
        texto = f"✅ Nenhuma conta a completar 30 dias em <b>{data_formatada}</b>."
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("⬅️ Voltar", callback_data="menu_vencimentos"))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=texto, reply_markup=markup, parse_mode="HTML")
    else:
        # Gerar o arquivo TXT formatado
        nome_arquivo = f"vencimentos_{data_formatada.replace('/', '_')}.txt"
        conteudo_txt = ""
        for item in lista:
            # Garante que se o login for None ou vazio, apareça algo no TXT
            login_exibir = item['login'] if item['login'] else "Não informado"
            conteudo_txt += f"Produto: {item['produto']}\n"
            conteudo_txt += f"Login: {login_exibir}\n"
            conteudo_txt += f"Data Compra: {item['data_compra']}\n"
            conteudo_txt += f"Data Expiração: {item['data_exp']}\n\n"
        with open(nome_arquivo, "w", encoding="utf-8") as f:
            f.write(conteudo_txt)
        with open(nome_arquivo, "rb") as f:
            bot.send_document(
                call.message.chat.id, 
                f, 
                caption=f"📂 <b>Relatório de Vencimentos</b>\n📅 Data: {data_formatada}\n📌 Total: {len(lista)} contas",
                parse_mode="HTML"
            )
        # Remove o arquivo tempor��rio após enviar
        import os
        os.remove(nome_arquivo)
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("⬅️ Voltar", callback_data="menu_vencimentos"))
    # 4. Atualiza a tela com o resultado da varredura
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=texto,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Erro ao exibir resultado de vencimentos: {e}")


# ==================== GERENCIAR SALDOS ====================
# =============================================================================
# MÓDULO: GERENCIAR SALDOS (painel admin)
# -----------------------------------------------------------------------------
# Submenu completo de gestão de saldo dos clientes:
#   🔎 Buscar cliente            -> ver saldo/atividade de 1 cliente + ações
#   👥 Listar clientes com saldo -> lista paginada + exportar .txt
#   💰 Adicionar saldo           -> credita saldo (com motivo opcional)
#   ➖ Remover saldo             -> debita saldo
#   🔄 Ajustar saldo             -> define um valor exato de saldo
#   📜 Histórico de movimentações-> log de tudo que foi add/remover/ajustar
#   📊 Relatório geral           -> totais, médias, maior saldo, mov. do dia
#   🚨 Clientes com saldo parado -> saldo > 0 sem nenhuma atividade recente
#
# Esta seção usa os globais definidos neste arquivo:
# bot, api, database, InlineKeyboardButton, InlineKeyboardMarkup, types,
# ApiTelegramException, escape.
# =============================================================================

_SALDOS_PAGE_SIZE = 10


def _saldos_admin_ok(chat_id):
    try:
        return bool(api.Admin.verificar_admin(chat_id) or int(chat_id) == int(api.CredentialsChange.id_dono()))
    except Exception:
        return False


def _saldos_fmt_money(v):
    try:
        return f"R$ {float(v or 0):.2f}"
    except Exception:
        return "R$ 0.00"


def _saldos_fmt_data(iso_str):
    if not iso_str:
        return "nunca"
    try:
        from datetime import datetime as _dt
        dt = _dt.strptime(str(iso_str)[:19], "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(iso_str)


def _saldos_nome(uid, username=None):
    if username:
        return f"@{username}"
    return f"ID {uid}"


def _saldos_send_or_edit(chat_id, message_id, texto, markup):
    if message_id:
        try:
            bot.edit_message_text(
                chat_id=chat_id, message_id=message_id, text=texto,
                parse_mode='HTML', reply_markup=markup, disable_web_page_preview=True
            )
            return
        except ApiTelegramException as e:
            if "message is not modified" in str(e):
                return
    bot.send_message(chat_id, texto, parse_mode='HTML', reply_markup=markup, disable_web_page_preview=True)


# ----------------------------------------------------------------------------
# MENU PRINCIPAL
# ----------------------------------------------------------------------------
def render_menu_saldos(chat_id, message_id=None):
    texto = (
        "💳 <b>GERENCIAR SALDOS</b>\n"
        "➖➖➖➖➖➖➖➖➖➖➖\n"
        "🛠️ <i>Selecione uma opção abaixo:</i>"
    )
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton('🔎 Buscar cliente', callback_data='saldos_buscar'),
        InlineKeyboardButton('👥 Listar c/ saldo', callback_data='saldos_listar_0')
    )
    markup.row(
        InlineKeyboardButton('💰 Adicionar saldo', callback_data='saldos_add'),
        InlineKeyboardButton('➖ Remover saldo', callback_data='saldos_rem')
    )
    markup.row(
        InlineKeyboardButton('🔄 Ajustar saldo', callback_data='saldos_ajt'),
        InlineKeyboardButton('📜 Histórico', callback_data='saldos_hist_0')
    )
    markup.row(
        InlineKeyboardButton('📊 Relatório geral', callback_data='saldos_rel'),
        InlineKeyboardButton('🚨 Saldo parado', callback_data='saldos_parado_menu')
    )
    markup.row(InlineKeyboardButton('↩️ Voltar ao Painel Admin', callback_data='voltar_paineladm'))
    _saldos_send_or_edit(chat_id, message_id, texto, markup)


@bot.callback_query_handler(func=lambda call: call.data == 'admin_gerenciar_saldos')
def cb_admin_gerenciar_saldos(call):
    if not _saldos_admin_ok(call.message.chat.id):
        return bot.answer_callback_query(call.id, "🚫 Sem permissão.", show_alert=True)
    bot.answer_callback_query(call.id)
    render_menu_saldos(call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == 'saldos_menu')
def cb_saldos_menu(call):
    bot.answer_callback_query(call.id)
    render_menu_saldos(call.message.chat.id, call.message.message_id)


# ----------------------------------------------------------------------------
# 🔎 BUSCAR CLIENTE
# ----------------------------------------------------------------------------
def render_ficha_cliente(chat_id, target_id, message_id=None):
    if not api.InfoUser.verificar_usuario(target_id):
        texto = f"❌ Cliente com ID <code>{target_id}</code> não encontrado."
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton('↩️ Voltar', callback_data='saldos_menu'))
        return _saldos_send_or_edit(chat_id, message_id, texto, markup)
    target_id = int(target_id)
    saldo = api.InfoUser.saldo(target_id)
    pix_inseridos = api.InfoUser.pix_inseridos(target_id)
    total_compras = api.InfoUser.total_compras(target_id)
    u_data = database.load_user_data(target_id) or {}
    username = u_data.get('username')
    ultimas = database.get_movimentacoes_saldo(user_id=target_id, limit=1)
    ultima_mov = _saldos_fmt_data(ultimas[0]['data']) if ultimas else "nenhuma"
    texto = (
        f"🔎 <b>Ficha de Saldo do Cliente</b>\n\n"
        f"👤 <b>Cliente:</b> {_saldos_nome(target_id, username)}\n"
        f"🆔 <b>ID:</b> <code>{target_id}</code>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖\n"
        f"💰 <b>Saldo atual:</b> <code>{_saldos_fmt_money(saldo)}</code>\n"
        f"💵 <b>Total já recarregado:</b> <code>{_saldos_fmt_money(pix_inseridos)}</code>\n"
        f"🛒 <b>Compras realizadas:</b> <code>{total_compras}</code>\n"
        f"🕒 <b>Última movimentação de saldo (admin):</b> {ultima_mov}"
    )
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton('💰 Adicionar', callback_data=f'saldos_add_id_{target_id}'),
        InlineKeyboardButton('➖ Remover', callback_data=f'saldos_rem_id_{target_id}'),
        InlineKeyboardButton('🔄 Ajustar', callback_data=f'saldos_ajt_id_{target_id}')
    )
    markup.row(InlineKeyboardButton('📜 Ver histórico deste cliente', callback_data=f'saldos_hist_cli_{target_id}_0'))
    markup.row(InlineKeyboardButton('↩️ Voltar', callback_data='saldos_menu'))
    _saldos_send_or_edit(chat_id, message_id, texto, markup)


@bot.callback_query_handler(func=lambda call: call.data == 'saldos_buscar')
def cb_saldos_buscar(call):
    if not _saldos_admin_ok(call.message.chat.id):
        return bot.answer_callback_query(call.id, "🚫 Sem permissão.", show_alert=True)
    bot.answer_callback_query(call.id)
    msg = bot.send_message(
        call.message.chat.id,
        "🔎 Digite o <b>ID</b> do cliente que deseja buscar:",
        parse_mode='HTML', reply_markup=types.ForceReply()
    )
    bot.register_next_step_handler(msg, _saldos_proc_buscar)


def _saldos_proc_buscar(message):
    target_id = message.text.strip()
    if not target_id.isdigit():
        return bot.reply_to(message, "❌ O ID deve ser um número.")
    render_ficha_cliente(message.chat.id, target_id)


# ----------------------------------------------------------------------------
# 👥 LISTAR CLIENTES COM SALDO
# ----------------------------------------------------------------------------
def render_listar_saldos(chat_id, page, message_id=None):
    total = database.count_clientes_com_saldo()
    clientes = database.get_clientes_com_saldo(limit=_SALDOS_PAGE_SIZE, offset=page * _SALDOS_PAGE_SIZE)
    if not clientes and page == 0:
        texto = "👥 <b>Nenhum cliente com saldo encontrado.</b>"
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton('↩️ Voltar', callback_data='saldos_menu'))
        return _saldos_send_or_edit(chat_id, message_id, texto, markup)
    inicio = page * _SALDOS_PAGE_SIZE + 1
    linhas = []
    for i, c in enumerate(clientes, start=inicio):
        linhas.append(f"{i}. {_saldos_nome(c['id'], c['username'])} — <code>{_saldos_fmt_money(c['saldo'])}</code> (<code>{c['id']}</code>)")
    total_paginas = max(1, -(-total // _SALDOS_PAGE_SIZE))
    texto = (
        f"👥 <b>CLIENTES COM SALDO</b> ({total} no total)\n"
        f"📄 Página {page + 1}/{total_paginas}\n"
        f"➖➖➖➖➖➖➖➖➖➖➖\n" + "\n".join(linhas)
    )
    markup = InlineKeyboardMarkup()
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton('⬅️ Anterior', callback_data=f'saldos_listar_{page-1}'))
    if (page + 1) * _SALDOS_PAGE_SIZE < total:
        nav.append(InlineKeyboardButton('Próxima ➡️', callback_data=f'saldos_listar_{page+1}'))
    if nav:
        markup.row(*nav)
    markup.row(InlineKeyboardButton('📥 Baixar lista completa (.txt)', callback_data='saldos_listar_dl'))
    markup.row(InlineKeyboardButton('↩️ Voltar', callback_data='saldos_menu'))
    _saldos_send_or_edit(chat_id, message_id, texto, markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('saldos_listar_') and call.data != 'saldos_listar_dl')
def cb_saldos_listar(call):
    if not _saldos_admin_ok(call.message.chat.id):
        return bot.answer_callback_query(call.id, "🚫 Sem permissão.", show_alert=True)
    bot.answer_callback_query(call.id)
    try:
        page = int(call.data.rsplit('_', 1)[1])
    except Exception:
        page = 0
    render_listar_saldos(call.message.chat.id, page, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == 'saldos_listar_dl')
def cb_saldos_listar_dl(call):
    if not _saldos_admin_ok(call.message.chat.id):
        return bot.answer_callback_query(call.id, "🚫 Sem permissão.", show_alert=True)
    bot.answer_callback_query(call.id, "Gerando arquivo...")
    import io
    from datetime import datetime as _dt
    clientes = database.get_clientes_com_saldo(limit=None)
    conteudo = f"--- CLIENTES COM SALDO ({_dt.now().strftime('%d/%m/%Y %H:%M')}) ---\n"
    conteudo += f"Total de clientes: {len(clientes)}\n\n"
    for c in clientes:
        conteudo += f"ID: {c['id']} | @{c['username'] or '-'} | Saldo: {_saldos_fmt_money(c['saldo'])}\n"
    arq = io.BytesIO(conteudo.encode('utf-8'))
    arq.name = f"clientes_com_saldo_{_dt.now().strftime('%d-%m-%Y')}.txt"
    bot.send_document(call.message.chat.id, arq, caption=f"📁 {len(clientes)} clientes com saldo.")


# ----------------------------------------------------------------------------
# 💰 ADICIONAR / ➖ REMOVER / 🔄 AJUSTAR — fluxo por botão do menu (pede ID)
# ----------------------------------------------------------------------------
_SALDOS_ACOES = {
    'add': {'titulo': 'Adicionar Saldo', 'verbo': 'adicionar', 'tipo': 'adicao', 'emoji': '💰'},
    'rem': {'titulo': 'Remover Saldo', 'verbo': 'remover', 'tipo': 'remocao', 'emoji': '➖'},
    'ajt': {'titulo': 'Ajustar Saldo', 'verbo': 'definir como', 'tipo': 'ajuste', 'emoji': '🔄'},
}


@bot.callback_query_handler(func=lambda call: call.data in ('saldos_add', 'saldos_rem', 'saldos_ajt'))
def cb_saldos_acao_sem_id(call):
    if not _saldos_admin_ok(call.message.chat.id):
        return bot.answer_callback_query(call.id, "🚫 Sem permissão.", show_alert=True)
    acao = call.data.split('_')[1]
    info = _SALDOS_ACOES[acao]
    bot.answer_callback_query(call.id)
    msg = bot.send_message(
        call.message.chat.id,
        f"{info['emoji']} <b>{info['titulo']}</b>\n\nDigite o <b>ID</b> do cliente:",
        parse_mode='HTML', reply_markup=types.ForceReply()
    )
    bot.register_next_step_handler(msg, _saldos_proc_pedir_valor, acao)


@bot.callback_query_handler(func=lambda call: call.data.startswith(('saldos_add_id_', 'saldos_rem_id_', 'saldos_ajt_id_')))
def cb_saldos_acao_com_id(call):
    if not _saldos_admin_ok(call.message.chat.id):
        return bot.answer_callback_query(call.id, "🚫 Sem permissão.", show_alert=True)
    partes = call.data.split('_')
    acao = partes[1]
    target_id = partes[3]
    info = _SALDOS_ACOES[acao]
    bot.answer_callback_query(call.id)
    _saldos_pedir_valor(call.message.chat.id, target_id, acao)


def _saldos_proc_pedir_valor(message, acao):
    target_id = message.text.strip()
    if not target_id.isdigit():
        return bot.reply_to(message, "❌ O ID deve ser um número.")
    if not api.InfoUser.verificar_usuario(target_id):
        return bot.reply_to(message, f"❌ Cliente com ID <code>{target_id}</code> não encontrado.", parse_mode='HTML')
    _saldos_pedir_valor(message.chat.id, target_id, acao)


def _saldos_pedir_valor(chat_id, target_id, acao):
    info = _SALDOS_ACOES[acao]
    saldo_atual = api.InfoUser.saldo(target_id)
    if acao == 'ajt':
        texto = (f"{info['emoji']} <b>{info['titulo']}</b> — Cliente <code>{target_id}</code>\n"
                  f"Saldo atual: <code>{_saldos_fmt_money(saldo_atual)}</code>\n\n"
                  f"Digite o <b>novo valor</b> do saldo (ex: <code>50.00</code>):")
    else:
        texto = (f"{info['emoji']} <b>{info['titulo']}</b> — Cliente <code>{target_id}</code>\n"
                  f"Saldo atual: <code>{_saldos_fmt_money(saldo_atual)}</code>\n\n"
                  f"Digite o <b>valor</b> a {info['verbo']} (ex: <code>10.50</code>):")
    msg = bot.send_message(chat_id, texto, parse_mode='HTML', reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, _saldos_proc_confirmar_valor, acao, target_id)


def _saldos_proc_confirmar_valor(message, acao, target_id):
    valor_str = message.text.replace(',', '.').strip()
    try:
        valor = float(valor_str)
        if valor < 0:
            raise ValueError
    except ValueError:
        return bot.reply_to(message, "❌ Valor inválido. Envie um número positivo (ex: 25.50).")
    admin_id = message.chat.id
    saldo_anterior = api.InfoUser.saldo(target_id)
    info = _SALDOS_ACOES[acao]
    if acao == 'add':
        api.InfoUser.add_saldo(target_id, valor)
        saldo_novo = saldo_anterior + valor
        resultado = f"✅ Adicionado {_saldos_fmt_money(valor)} ao saldo do cliente <code>{target_id}</code>."
    elif acao == 'rem':
        ok = api.InfoUser.tirar_saldo(target_id, valor)
        if not ok:
            return bot.reply_to(
                message,
                f"❌ Saldo insuficiente. Saldo atual: {_saldos_fmt_money(saldo_anterior)}.",
                parse_mode='HTML'
            )
        saldo_novo = saldo_anterior - valor
        resultado = f"✅ Removido {_saldos_fmt_money(valor)} do saldo do cliente <code>{target_id}</code>."
    else:  # ajt
        api.InfoUser.mudar_saldo(target_id, valor)
        saldo_novo = valor
        resultado = f"✅ Saldo do cliente <code>{target_id}</code> ajustado para {_saldos_fmt_money(valor)}."
    try:
        database.registrar_movimentacao_saldo(
            user_id=target_id, tipo=info['tipo'], valor=valor,
            saldo_anterior=saldo_anterior, saldo_novo=saldo_novo, admin_id=admin_id
        )
    except Exception as e:
        print(f"[GerenciarSaldos] Falha ao registrar movimentação: {e}")
    resultado += f"\n💰 Novo saldo: <code>{_saldos_fmt_money(saldo_novo)}</code>"
    bot.reply_to(message, resultado, parse_mode='HTML')
    # Avisa o cliente
    try:
        if info['tipo'] == 'adicao':
            bot.send_message(int(target_id), f"💰 Seu saldo recebeu um crédito de {_saldos_fmt_money(valor)}.\nSaldo atual: {_saldos_fmt_money(saldo_novo)}")
        elif info['tipo'] == 'remocao':
            bot.send_message(int(target_id), f"⚠️ Foi debitado {_saldos_fmt_money(valor)} do seu saldo.\nSaldo atual: {_saldos_fmt_money(saldo_novo)}")
    except Exception:
        pass


# ----------------------------------------------------------------------------
# 📜 HISTÓRICO DE MOVIMENTAÇÕES
# ----------------------------------------------------------------------------
def _saldos_fmt_linha_mov(m):
    emoji = {'adicao': '💰', 'remocao': '➖', 'ajuste': '🔄'}.get(m['tipo'], '•')
    return (f"{emoji} <b>{_saldos_fmt_data(m['data'])}</b> | Cliente <code>{m['user_id']}</code>\n"
            f"   {m['tipo'].capitalize()}: {_saldos_fmt_money(m['valor'])} "
            f"(<code>{_saldos_fmt_money(m['saldo_anterior'])}</code> ➜ <code>{_saldos_fmt_money(m['saldo_novo'])}</code>)"
            f"{' | admin ' + str(m['admin_id']) if m.get('admin_id') else ''}")


def render_historico(chat_id, page, message_id=None, target_id=None):
    total = database.count_movimentacoes_saldo(user_id=target_id)
    movs = database.get_movimentacoes_saldo(user_id=target_id, limit=_SALDOS_PAGE_SIZE, offset=page * _SALDOS_PAGE_SIZE)
    titulo = f"📜 <b>HISTÓRICO DE MOVIMENTAÇÕES</b>"
    if target_id:
        titulo += f" — Cliente <code>{target_id}</code>"
    if not movs and page == 0:
        texto = f"{titulo}\n\nNenhuma movimentação registrada ainda."
        markup = InlineKeyboardMarkup()
        if target_id:
            markup.row(InlineKeyboardButton('↩️ Voltar à ficha', callback_data=f'saldos_buscar_direto_{target_id}'))
        markup.row(InlineKeyboardButton('↩️ Voltar', callback_data='saldos_menu'))
        return _saldos_send_or_edit(chat_id, message_id, texto, markup)
    total_paginas = max(1, -(-total // _SALDOS_PAGE_SIZE))
    texto = f"{titulo}\n📄 Página {page + 1}/{total_paginas}\n➖➖➖➖➖➖➖➖➖➖➖\n\n"
    texto += "\n\n".join(_saldos_fmt_linha_mov(m) for m in movs)
    prefixo = f"saldos_hist_cli_{target_id}" if target_id else "saldos_hist"
    markup = InlineKeyboardMarkup()
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton('⬅️ Anterior', callback_data=f'{prefixo}_{page-1}'))
    if (page + 1) * _SALDOS_PAGE_SIZE < total:
        nav.append(InlineKeyboardButton('Próxima ➡️', callback_data=f'{prefixo}_{page+1}'))
    if nav:
        markup.row(*nav)
    if not target_id:
        markup.row(InlineKeyboardButton('🔎 Filtrar por cliente', callback_data='saldos_hist_filtro'))
    markup.row(InlineKeyboardButton('📥 Baixar completo (.txt)', callback_data=f'saldos_hist_dl_{target_id or 0}'))
    markup.row(InlineKeyboardButton('↩️ Voltar', callback_data='saldos_menu'))
    _saldos_send_or_edit(chat_id, message_id, texto, markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('saldos_hist_') and not call.data.startswith(('saldos_hist_filtro', 'saldos_hist_dl', 'saldos_hist_cli')))
def cb_saldos_hist(call):
    if not _saldos_admin_ok(call.message.chat.id):
        return bot.answer_callback_query(call.id, "🚫 Sem permissão.", show_alert=True)
    bot.answer_callback_query(call.id)
    try:
        page = int(call.data.rsplit('_', 1)[1])
    except Exception:
        page = 0
    render_historico(call.message.chat.id, page, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('saldos_hist_cli_'))
def cb_saldos_hist_cli(call):
    if not _saldos_admin_ok(call.message.chat.id):
        return bot.answer_callback_query(call.id, "🚫 Sem permissão.", show_alert=True)
    bot.answer_callback_query(call.id)
    partes = call.data.split('_')
    target_id = partes[3]
    page = int(partes[4]) if len(partes) > 4 else 0
    render_historico(call.message.chat.id, page, call.message.message_id, target_id=target_id)


@bot.callback_query_handler(func=lambda call: call.data == 'saldos_hist_filtro')
def cb_saldos_hist_filtro(call):
    if not _saldos_admin_ok(call.message.chat.id):
        return bot.answer_callback_query(call.id, "🚫 Sem permissão.", show_alert=True)
    bot.answer_callback_query(call.id)
    msg = bot.send_message(
        call.message.chat.id, "🔎 Digite o <b>ID</b> do cliente para ver o histórico dele:",
        parse_mode='HTML', reply_markup=types.ForceReply()
    )
    bot.register_next_step_handler(msg, _saldos_proc_hist_filtro)


def _saldos_proc_hist_filtro(message):
    target_id = message.text.strip()
    if not target_id.isdigit():
        return bot.reply_to(message, "❌ O ID deve ser um número.")
    render_historico(message.chat.id, 0, target_id=target_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('saldos_hist_dl_'))
def cb_saldos_hist_dl(call):
    if not _saldos_admin_ok(call.message.chat.id):
        return bot.answer_callback_query(call.id, "🚫 Sem permissão.", show_alert=True)
    bot.answer_callback_query(call.id, "Gerando arquivo...")
    import io
    from datetime import datetime as _dt
    target_raw = call.data.rsplit('_', 1)[1]
    target_id = int(target_raw) if target_raw != '0' else None
    movs = database.get_movimentacoes_saldo(user_id=target_id, limit=100000)
    conteudo = f"--- HISTÓRICO DE MOVIMENTAÇÕES DE SALDO ({_dt.now().strftime('%d/%m/%Y %H:%M')}) ---\n"
    if target_id:
        conteudo += f"Cliente: {target_id}\n"
    conteudo += f"Total de registros: {len(movs)}\n\n"
    for m in movs:
        conteudo += (f"{_saldos_fmt_data(m['data'])} | Cliente {m['user_id']} | {m['tipo']} | "
                      f"Valor {_saldos_fmt_money(m['valor'])} | "
                      f"{_saldos_fmt_money(m['saldo_anterior'])} -> {_saldos_fmt_money(m['saldo_novo'])} | "
                      f"admin {m.get('admin_id') or '-'}\n")
    arq = io.BytesIO(conteudo.encode('utf-8'))
    arq.name = f"historico_saldos_{_dt.now().strftime('%d-%m-%Y')}.txt"
    bot.send_document(call.message.chat.id, arq, caption=f"📁 {len(movs)} movimentações.")


# ----------------------------------------------------------------------------
# 📊 RELATÓRIO GERAL
# ----------------------------------------------------------------------------
@bot.callback_query_handler(func=lambda call: call.data == 'saldos_rel')
def cb_saldos_rel(call):
    if not _saldos_admin_ok(call.message.chat.id):
        return bot.answer_callback_query(call.id, "🚫 Sem permissão.", show_alert=True)
    bot.answer_callback_query(call.id)
    r = database.get_relatorio_saldo_geral()
    maior_nome = _saldos_nome(r['maior_saldo_id'], r['maior_saldo_username']) if r['maior_saldo_id'] else '—'
    saldo_net_hoje = r['entradas_hoje'] - r['saidas_hoje']
    texto = (
        "📊 <b>RELATÓRIO GERAL DE SALDOS</b>\n"
        "➖➖➖➖➖➖➖➖➖➖➖\n"
        f"👥 <b>Clientes com saldo:</b> {r['qtd_clientes_com_saldo']}\n"
        f"💰 <b>Total em saldo circulando:</b> {_saldos_fmt_money(r['total_em_saldo'])}\n"
        f"📈 <b>Saldo médio por cliente:</b> {_saldos_fmt_money(r['saldo_medio'])}\n"
        f"👑 <b>Maior saldo individual:</b> {maior_nome} — {_saldos_fmt_money(r['maior_saldo_valor'])}\n"
        "➖➖➖➖➖➖➖➖➖➖➖\n"
        f"🗓️ <b>Movimentações hoje:</b> {r['movimentacoes_hoje']}\n"
        f"   💰 Entradas: {_saldos_fmt_money(r['entradas_hoje'])}\n"
        f"   ➖ Saídas: {_saldos_fmt_money(r['saidas_hoje'])}\n"
        f"   📐 Saldo líquido do dia: {_saldos_fmt_money(saldo_net_hoje)}\n"
        "➖➖➖➖➖➖➖➖➖➖➖\n"
        f"📚 <b>Total adicionado (histórico):</b> {_saldos_fmt_money(r['total_adicionado_historico'])}\n"
        f"📚 <b>Total removido (histórico):</b> {_saldos_fmt_money(r['total_removido_historico'])}"
    )
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton('🚨 Ver saldo parado', callback_data='saldos_parado_menu'))
    markup.row(InlineKeyboardButton('↩️ Voltar', callback_data='saldos_menu'))
    _saldos_send_or_edit(call.message.chat.id, call.message.message_id, texto, markup)


# ----------------------------------------------------------------------------
# 🚨 CLIENTES COM SALDO PARADO
# ----------------------------------------------------------------------------
@bot.callback_query_handler(func=lambda call: call.data == 'saldos_parado_menu')
def cb_saldos_parado_menu(call):
    if not _saldos_admin_ok(call.message.chat.id):
        return bot.answer_callback_query(call.id, "🚫 Sem permissão.", show_alert=True)
    bot.answer_callback_query(call.id)
    texto = (
        "🚨 <b>CLIENTES COM SALDO PARADO</b>\n\n"
        "Considera-se \"parado\" o saldo de um cliente que não teve nenhuma "
        "compra, recarga ou ajuste de admin no período escolhido.\n\n"
        "Escolha o período de inatividade:"
    )
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton('15 dias', callback_data='saldos_parado_15_0'),
        InlineKeyboardButton('30 dias', callback_data='saldos_parado_30_0'),
    )
    markup.row(
        InlineKeyboardButton('60 dias', callback_data='saldos_parado_60_0'),
        InlineKeyboardButton('90 dias', callback_data='saldos_parado_90_0'),
    )
    markup.row(InlineKeyboardButton('↩️ Voltar', callback_data='saldos_menu'))
    _saldos_send_or_edit(call.message.chat.id, call.message.message_id, texto, markup)


def render_saldo_parado(chat_id, dias, page, message_id=None):
    clientes = database.get_clientes_saldo_parado(dias=dias, limit=1000)
    total = len(clientes)
    pagina_itens = clientes[page * _SALDOS_PAGE_SIZE: (page + 1) * _SALDOS_PAGE_SIZE]
    if not pagina_itens and page == 0:
        texto = f"🚨 <b>SALDO PARADO (+{dias} dias)</b>\n\n✅ Nenhum cliente com saldo parado nesse período."
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton('↩️ Voltar', callback_data='saldos_parado_menu'))
        return _saldos_send_or_edit(chat_id, message_id, texto, markup)
    inicio = page * _SALDOS_PAGE_SIZE + 1
    linhas = []
    for i, c in enumerate(pagina_itens, start=inicio):
        linhas.append(
            f"{i}. {_saldos_nome(c['id'], c['username'])} — <code>{_saldos_fmt_money(c['saldo'])}</code>\n"
            f"    última atividade: {_saldos_fmt_data(c['ultima_atividade'])} | ID <code>{c['id']}</code>"
        )
    total_paginas = max(1, -(-total // _SALDOS_PAGE_SIZE))
    texto = (
        f"🚨 <b>SALDO PARADO (+{dias} dias)</b> — {total} clientes\n"
        f"📄 Página {page + 1}/{total_paginas}\n"
        f"➖➖➖➖➖➖➖➖➖➖➖\n" + "\n".join(linhas)
    )
    markup = InlineKeyboardMarkup()
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton('⬅️ Anterior', callback_data=f'saldos_parado_{dias}_{page-1}'))
    if (page + 1) * _SALDOS_PAGE_SIZE < total:
        nav.append(InlineKeyboardButton('Próxima ➡️', callback_data=f'saldos_parado_{dias}_{page+1}'))
    if nav:
        markup.row(*nav)
    markup.row(InlineKeyboardButton('📥 Baixar lista (.txt)', callback_data=f'saldos_parado_dl_{dias}'))
    markup.row(InlineKeyboardButton('↩️ Voltar', callback_data='saldos_parado_menu'))
    _saldos_send_or_edit(chat_id, message_id, texto, markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('saldos_parado_') and not call.data.startswith(('saldos_parado_menu', 'saldos_parado_dl_')))
def cb_saldos_parado(call):
    if not _saldos_admin_ok(call.message.chat.id):
        return bot.answer_callback_query(call.id, "🚫 Sem permissão.", show_alert=True)
    bot.answer_callback_query(call.id)
    partes = call.data.split('_')
    try:
        dias = int(partes[2])
        page = int(partes[3])
    except Exception:
        dias, page = 30, 0
    render_saldo_parado(call.message.chat.id, dias, page, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('saldos_parado_dl_'))
def cb_saldos_parado_dl(call):
    if not _saldos_admin_ok(call.message.chat.id):
        return bot.answer_callback_query(call.id, "🚫 Sem permissão.", show_alert=True)
    bot.answer_callback_query(call.id, "Gerando arquivo...")
    import io
    from datetime import datetime as _dt
    dias = int(call.data.rsplit('_', 1)[1])
    clientes = database.get_clientes_saldo_parado(dias=dias, limit=100000)
    conteudo = f"--- CLIENTES COM SALDO PARADO HÁ MAIS DE {dias} DIAS ({_dt.now().strftime('%d/%m/%Y %H:%M')}) ---\n"
    conteudo += f"Total: {len(clientes)}\n\n"
    for c in clientes:
        conteudo += (f"ID: {c['id']} | @{c['username'] or '-'} | Saldo: {_saldos_fmt_money(c['saldo'])} | "
                      f"Última atividade: {_saldos_fmt_data(c['ultima_atividade'])}\n")
    arq = io.BytesIO(conteudo.encode('utf-8'))
    arq.name = f"saldo_parado_{dias}dias_{_dt.now().strftime('%d-%m-%Y')}.txt"
    bot.send_document(call.message.chat.id, arq, caption=f"📁 {len(clientes)} clientes com saldo parado (+{dias} dias).")


# Atalho: voltar direto pra ficha de um cliente (usado após ver o histórico dele)
@bot.callback_query_handler(func=lambda call: call.data.startswith('saldos_buscar_direto_'))
def cb_saldos_buscar_direto(call):
    if not _saldos_admin_ok(call.message.chat.id):
        return bot.answer_callback_query(call.id, "🚫 Sem permissão.", show_alert=True)
    bot.answer_callback_query(call.id)
    target_id = call.data.rsplit('_', 1)[1]
    render_ficha_cliente(call.message.chat.id, target_id, call.message.message_id)

# =========================================================================================
# ===== WEBHOOK HANDLER PARA MISTICPAY =====
# Webhook removido - usando apenas polling para compatibilidade com SquareCloud
# Inicia e passa os handlers do Canal Obrigatório
canal_manager.init_canal(bot, api, painel_admin, handle_start)
if __name__ == "__main__":
    start_polling()
