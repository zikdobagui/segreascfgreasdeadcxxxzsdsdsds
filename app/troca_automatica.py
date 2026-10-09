# sistema_trocas.py
#
# Sistema de Trocas — versão robusta.
#
# Substitui o antigo troca_automatica.py mantendo 100% de compatibilidade
# com os pontos de integração existentes:
#   - mesma função pública: setup(bot)
#   - mesmos callback_data: 'reportar_problema_<id>', 'confirmar_troca_<id>', 'cancelar_troca'
#   - mesma função auxiliar usada por fora: nenhuma (tudo fica encapsulado aqui)
#
# NOVIDADES em relação à versão anterior:
#   1. Garantia por tempo:     só troca automática dentro de X horas da compra.
#   2. Limite anti-abuso:      no máximo N trocas por usuário a cada P dias.
#   3. Fora da garantia/limite: cai para revisão manual do admin (aprova/nega
#                               na hora, pelo próprio Telegram), em vez de
#                               recusar ou de liberar troca infinita.
#   4. Trava de concorrência:  lock por usuário (evita duplo clique / duplo
#                               processamento) + lock global na retirada do
#                               estoque (evita duas trocas simultâneas
#                               "roubarem" o mesmo login).
#   5. Expiração do pedido:    um "Confirmar Troca" esquecido expira sozinho.
#   6. Validação da descrição: texto vazio/curto ou mídia não é aceito.
#   7. Log em arquivo próprio (database/trocas_log.json): relatórios e
#      contagem de limite ficam instantâneos, sem varrer todo mundo.
#   8. Painel admin:           /config_trocas, /trocas_pendentes, /trocas_relatorio
#
# Nenhum outro arquivo do bot precisa mudar. Onde hoje existe:
#     import troca_automatica
#     ...
#     troca_automatica.setup(bot)
# troque para:
#     import sistema_trocas
#     ...
#     sistema_trocas.setup(bot)

import os
import json
import time
import uuid
import threading
from html import escape
from datetime import datetime, timedelta

import pytz
from telebot.types import ForceReply, InlineKeyboardMarkup, InlineKeyboardButton

from app import central as api
from app.database import load_user_data, save_user_data, get_all_user_ids

TZ = pytz.timezone('America/Sao_Paulo')

CONFIG_PATH = os.path.join('database', 'trocas_config.json')
LOG_PATH = os.path.join('database', 'trocas_log.json')
PENDENTES_PATH = os.path.join('database', 'trocas_pendentes_admin.json')

DEFAULT_CONFIG = {
    "garantia_horas": 72,       # janela de troca automática após a compra
    "max_trocas_periodo": 2,    # trocas automáticas permitidas por usuário
    "periodo_dias": 30,         # ...dentro desse período
    "pedido_expira_minutos": 15  # tempo para o cliente confirmar a troca
}

# --------------------------------------------------------------------------
# Infraestrutura de concorrência
# --------------------------------------------------------------------------
_arquivo_lock = threading.RLock()      # protege leitura/escrita dos JSONs deste módulo
_estoque_lock = threading.RLock()      # protege a retirada de login do estoque (acessos.json)
_locks_usuario = {}
_locks_usuario_guard = threading.Lock()


def _lock_do_usuario(user_id):
    """Retorna (criando se preciso) um Lock exclusivo para esse usuário, para
    impedir que dois cliques/threads processem a mesma troca ao mesmo tempo."""
    with _locks_usuario_guard:
        lock = _locks_usuario.get(user_id)
        if lock is None:
            lock = threading.RLock()
            _locks_usuario[user_id] = lock
        return lock


# --------------------------------------------------------------------------
# Persistência simples em JSON (config / log / pendências admin)
# --------------------------------------------------------------------------
def _read_json(path, default):
    with _arquivo_lock:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return default() if callable(default) else default


def _write_json(path, data):
    with _arquivo_lock:
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        tmp = f"{path}.tmp"
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)  # escrita atômica: nunca deixa o arquivo pela metade


def get_config():
    cfg = _read_json(CONFIG_PATH, dict(DEFAULT_CONFIG))
    changed = False
    for k, v in DEFAULT_CONFIG.items():
        if k not in cfg:
            cfg[k] = v
            changed = True
    if changed:
        _write_json(CONFIG_PATH, cfg)
    return cfg


def _save_config(cfg):
    _write_json(CONFIG_PATH, cfg)


def _log_evento(**kwargs):
    log = _read_json(LOG_PATH, list)
    entrada = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(TZ).isoformat(),
    }
    entrada.update(kwargs)
    log.append(entrada)
    _write_json(LOG_PATH, log)
    return entrada


def _contar_trocas_recentes(user_id, dias):
    """Conta quantas trocas AUTOMÁTICAS concluídas esse usuário já fez nos
    últimos `dias` dias (usado pro limite anti-abuso)."""
    cutoff = datetime.now(TZ) - timedelta(days=dias)
    log = _read_json(LOG_PATH, list)
    total = 0
    for entrada in log:
        if entrada.get("user_id") != user_id:
            continue
        if entrada.get("status") not in ("concluida", "concluida_manual"):
            continue
        try:
            ts = datetime.fromisoformat(entrada["timestamp"])
        except Exception:
            continue
        if ts >= cutoff:
            total += 1
    return total


def _pendentes_admin():
    return _read_json(PENDENTES_PATH, dict)


def _salvar_pendente_admin(req_id, registro):
    pend = _pendentes_admin()
    pend[req_id] = registro
    _write_json(PENDENTES_PATH, pend)


def _remover_pendente_admin(req_id):
    pend = _pendentes_admin()
    pend.pop(req_id, None)
    _write_json(PENDENTES_PATH, pend)


# --------------------------------------------------------------------------
# Helpers de estoque (com lock — impede duas trocas pegarem o mesmo login)
# --------------------------------------------------------------------------
def _retirar_login_do_estoque(servico, buyer_id, sale_id):
    with _estoque_lock:
        return api.ControleLogins.pegar_primeiro_disponivel(servico, buyer_id, sale_id)


def _tem_estoque(servico):
    with _estoque_lock:
        return api.ControleLogins.peek_primeiro_disponivel(servico) is not None


def _is_admin(user_id):
    try:
        return bool(api.Admin.verificar_admin(user_id)) or int(user_id) == int(api.CredentialsChange.id_dono())
    except Exception:
        return False


# --------------------------------------------------------------------------
# Módulo principal
# --------------------------------------------------------------------------
def setup(bot, montar_botoes_extras=None):

    # ---------------------------------------------------------------- util
    def _is_reportar_problema_enabled():
        try:
            from app import bot as bot_module
            return bot_module.is_reportar_problema_enabled()
        except Exception:
            return True

    def _achar_compra(user_data, purchase_id):
        for i, p in enumerate(user_data.get('purchases', [])):
            if p.get('id') == purchase_id:
                return i, p
        return -1, None

    def _dentro_da_garantia(compra, cfg):
        data_compra_str = compra.get('data_compra')
        if not data_compra_str:
            return True  # sem data registrada: não bloqueia por garantia
        try:
            data_compra = datetime.fromisoformat(data_compra_str)
            if data_compra.tzinfo is None:
                data_compra = TZ.localize(data_compra)
        except Exception:
            return True
        limite = data_compra + timedelta(hours=cfg.get("garantia_horas", 72))
        return datetime.now(TZ) <= limite

    def _reenviar_login_da_compra(user_id, compra):
        purchase_id = compra.get('id')
        nome = compra.get('servico', 'N/A')
        email = compra.get('email', 'N/A')
        senha = compra.get('senha', 'N/A')

        texto = (
            f"ℹ️ <b>Aqui está o login da sua conta novamente:</b>\n\n"
            f" <b>{escape(nome)}</b>\n"
            f"├ 📧 <code>{escape(email)}</code>\n"
            f"└ 🔑 <code>{escape(senha)}</code>\n\n"
            f"<i>(Toque para copiar)</i>"
        )
        markup = InlineKeyboardMarkup()
        if _is_reportar_problema_enabled():
            markup.row(InlineKeyboardButton("❗ Reportar Problema na Conta", callback_data=f"reportar_problema_{purchase_id}"))
        markup.row(InlineKeyboardButton("🆘 Preciso de Ajuda", url=api.CredentialsChange.SuporteInfo.link_suporte()))
        try:
            if montar_botoes_extras is not None:
                montar_botoes_extras(markup, purchase_id, email, senha, nome)
        except Exception:
            pass
        try:
            bot.send_message(user_id, texto, parse_mode='HTML', reply_markup=markup)
        except Exception as e:
            print(f"[sistema_trocas] Falha ao reenviar login: {e}")

    def _notificar_admin(texto, markup=None):
        try:
            admin_id = int(api.CredentialsChange.id_dono())
            bot.send_message(admin_id, texto, parse_mode='HTML', reply_markup=markup)
        except Exception as e:
            print(f"[sistema_trocas] Falha ao notificar admin: {e}")

    def _entregar_login_ao_cliente(user_id, novo_login_info, motivo_extra=""):
        nome, valor, email, senha, descricao, duracao = novo_login_info
        texto = (
            f"✅ <b>Troca Realizada com Sucesso!</b>\n\n"
            f"Aqui está sua nova conta de <b>{escape(nome)}</b>:\n\n"
            f"📧 <b>Login:</b> <code>{escape(email)}</code>\n"
            f"🔑 <b>Senha:</b> <code>{escape(senha)}</code>\n\n"
            f"<i>(Toque para copiar)</i>\n\n"
            f"Pedimos desculpas pelo inconveniente.{motivo_extra}"
        )
        markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton("🆘 Ainda com problemas? Fale com o Suporte", url=api.CredentialsChange.SuporteInfo.link_suporte())
        )
        bot.send_message(user_id, texto, parse_mode='HTML', reply_markup=markup)
        return email, senha

    # =====================================================================
    # PASSO 1 — cliente clica em "Reportar Problema"
    # =====================================================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith('reportar_problema_'))
    def handle_report_button(call):
        try:
            purchase_id = call.data.replace('reportar_problema_', '')
            user_id = call.from_user.id
            cfg = get_config()

            user_data = load_user_data(user_id) or {}
            _, compra = _achar_compra(user_data, purchase_id)
            if not compra:
                bot.answer_callback_query(call.id, "Compra não encontrada.", show_alert=True)
                return

            if compra.get('troca_realizada'):
                bot.answer_callback_query(call.id, "Esta conta já foi trocada anteriormente.", show_alert=True)
                return

            servico = compra.get('servico')
            dentro_garantia = _dentro_da_garantia(compra, cfg)
            excedeu_limite = _contar_trocas_recentes(user_id, cfg.get("periodo_dias", 30)) >= cfg.get("max_trocas_periodo", 2)
            modo = "auto" if (dentro_garantia and not excedeu_limite) else "manual"

            # Só checa estoque de antemão se for troca automática (a manual
            # não depende de estoque no momento do clique, o admin decide depois).
            if modo == "auto" and servico and not _tem_estoque(servico):
                bot.answer_callback_query(call.id, "Sem estoque disponível no momento.", show_alert=True)
                bot.send_message(
                    call.message.chat.id,
                    f"😔 Desculpe, não temos estoque de '{escape(servico)}' para realizar a troca agora. "
                    f"Por favor, contate o suporte."
                )
                _notificar_admin(
                    f"<b>⚠️ Cliente tentou reportar problema (sem estoque) ⚠️</b>\n\n"
                    f"O cliente <code>{user_id}</code> tentou reportar problema em <b>{escape(servico)}</b>, "
                    f"mas não há estoque para troca agora.\n\n"
                    f"‼️ <b>AÇÃO NECESSÁRIA:</b> Reponha o estoque assim que possível."
                )
                return

            bot.answer_callback_query(call.id, "📝 Por favor, leia as instruções com atenção.")
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass

            aviso_extra = ""
            if modo == "manual" and not dentro_garantia:
                aviso_extra = (
                    "\n\n⏰ <b>Atenção:</b> o prazo de troca automática dessa conta já passou. "
                    "Seu pedido será enviado para análise manual da nossa equipe."
                )
            elif modo == "manual" and excedeu_limite:
                aviso_extra = (
                    "\n\n🔎 <b>Atenção:</b> identificamos várias trocas recentes na sua conta. "
                    "Por segurança, este pedido será revisado manualmente pela nossa equipe."
                )

            texto_instrucoes = (
                "📝 <b>REPORTAR PROBLEMA NA CONTA</b>\n\n"
                "Para que nosso sistema possa realizar uma troca, por favor, leia com atenção.\n\n"
                "<b>Passo 1: Verifique se o problema é válido para troca.</b>\n"
                "✅ <b>Problemas Válidos:</b>\n"
                "  • Login ou senha incorretos.\n"
                "  • O plano da conta é diferente do que você comprou.\n"
                "  • A conta está com status de 'suspensa' ou 'cancelada'.\n\n"
                "❌ <b>NÃO é um problema válido para troca:</b>\n"
                "  • Mensagem de 'Muitas telas em uso simultâneo'.\n"
                "  • Lentidão ou travamentos (verifique sua internet).\n\n"
                "<b>AVISO:</b> O abuso desta função levará ao <b>banimento permanente</b>. Use com responsabilidade."
                f"{aviso_extra}"
            )
            bot.send_message(call.message.chat.id, texto_instrucoes, parse_mode='HTML')

            msg = bot.send_message(
                call.message.chat.id,
                "<b>Passo 2: Agora, descreva o problema detalhadamente abaixo.</b>",
                parse_mode='HTML',
                reply_markup=ForceReply(selective=True)
            )
            bot.register_next_step_handler(msg, pedir_confirmacao_troca, purchase_id, modo)
        except Exception as e:
            print(f"[ERRO] handle_report_button: {e}")
            try:
                bot.send_message(call.message.chat.id, "Ocorreu um erro ao iniciar o reporte. Tente novamente.")
            except Exception:
                pass

    # =====================================================================
    # PASSO 2 — cliente descreve o problema
    # =====================================================================
    def pedir_confirmacao_troca(message, purchase_id, modo):
        user_id = message.from_user.id

        if message.content_type != 'text' or not (message.text or "").strip():
            msg = bot.send_message(
                user_id,
                "⚠️ Por favor, descreva o problema em <b>texto</b> (não vale foto/áudio/figurinha). Tente novamente:",
                parse_mode='HTML',
                reply_markup=ForceReply(selective=True)
            )
            bot.register_next_step_handler(msg, pedir_confirmacao_troca, purchase_id, modo)
            return

        problema_descrito = message.text.strip()
        if len(problema_descrito) < 5:
            msg = bot.send_message(
                user_id,
                "⚠️ Descreva com um pouco mais de detalhe o que está acontecendo (mínimo 5 caracteres):",
                reply_markup=ForceReply(selective=True)
            )
            bot.register_next_step_handler(msg, pedir_confirmacao_troca, purchase_id, modo)
            return

        cfg = get_config()
        expira_em = datetime.now(TZ) + timedelta(minutes=cfg.get("pedido_expira_minutos", 15))

        with _lock_do_usuario(user_id):
            user_data = load_user_data(user_id) or {}
            user_data['pending_report'] = {
                'purchase_id': purchase_id,
                'description': problema_descrito,
                'modo': modo,
                'expira_em': expira_em.isoformat(),
            }
            save_user_data(user_id, user_data)

        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ Confirmar Troca", callback_data=f"confirmar_troca_{purchase_id}"),
            InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_troca")
        )
        bot.send_message(
            user_id,
            "❓ Você confirma que deseja realizar a troca desta conta?\n\n"
            "Esta ação não pode ser desfeita.",
            reply_markup=markup
        )

    # =====================================================================
    # PASSO 3 — cliente confirma
    # =====================================================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith('confirmar_troca_'))
    def realizar_troca_confirmada(call):
        user_id = call.from_user.id
        with _lock_do_usuario(user_id):
            try:
                bot.answer_callback_query(call.id, "Confirmado! Processando a troca...")
                bot.edit_message_text("🔄 Processando sua solicitação de troca... Por favor, aguarde.", call.message.chat.id, call.message.message_id)

                user_data = load_user_data(user_id) or {}
                pending_report = user_data.pop('pending_report', None)
                save_user_data(user_id, user_data)  # já consome o pedido — impede duplo processamento

                if not pending_report:
                    bot.send_message(user_id, "❌ Ocorreu um erro: a solicitação de troca expirou ou não foi encontrada. Por favor, tente novamente.")
                    return

                try:
                    expira_em = datetime.fromisoformat(pending_report['expira_em'])
                except Exception:
                    expira_em = None
                if expira_em and datetime.now(TZ) > expira_em:
                    bot.send_message(user_id, "⌛ Esse pedido de troca expirou. Por favor, clique em 'Reportar Problema' novamente.")
                    return

                purchase_id = pending_report['purchase_id']
                problema_descrito = pending_report['description']
                modo = pending_report.get('modo', 'auto')

                idx, compra_defeituosa = _achar_compra(user_data, purchase_id)
                if not compra_defeituosa:
                    bot.send_message(user_id, "❌ A compra original não foi encontrada. A troca não pode ser processada.")
                    return

                if compra_defeituosa.get('troca_realizada'):
                    bot.send_message(user_id, "⚠️ Esta conta já foi trocada anteriormente. Se o problema persistir, contate o suporte.")
                    return

                servico = compra_defeituosa['servico']

                # ---------------- MODO MANUAL: envia para revisão do admin ----------------
                if modo == "manual":
                    req_id = str(uuid.uuid4())
                    _salvar_pendente_admin(req_id, {
                        "user_id": user_id,
                        "purchase_id": purchase_id,
                        "servico": servico,
                        "problema": problema_descrito,
                        "login_antigo": {"email": compra_defeituosa.get('email'), "senha": compra_defeituosa.get('senha')},
                        "criado_em": datetime.now(TZ).isoformat(),
                    })
                    _log_evento(user_id=user_id, purchase_id=purchase_id, servico=servico,
                                status="pendente_admin", problema=problema_descrito, req_id=req_id)

                    bot.send_message(
                        user_id,
                        "📨 Seu pedido de troca foi enviado para análise da nossa equipe. "
                        "Você receberá uma resposta em breve. Obrigado pela paciência!"
                    )
                    admin_markup = InlineKeyboardMarkup()
                    admin_markup.row(
                        InlineKeyboardButton("✅ Aprovar e Trocar", callback_data=f"trocaadm_aprovar_{req_id}"),
                        InlineKeyboardButton("❌ Negar", callback_data=f"trocaadm_negar_{req_id}")
                    )
                    _notificar_admin(
                        f"<b>🕵️ TROCA PARA REVISÃO MANUAL</b>\n\n"
                        f"<b>Cliente:</b> <code>{user_id}</code>\n"
                        f"<b>Serviço:</b> {escape(servico)}\n"
                        f"<b>Motivo da revisão:</b> {'fora da garantia' if not _dentro_da_garantia(compra_defeituosa, get_config()) else 'limite de trocas atingido'}\n\n"
                        f"<b>Problema relatado:</b>\n<i>{escape(problema_descrito)}</i>\n\n"
                        f"<b>Login atual:</b>\n<code>{escape(compra_defeituosa.get('email',''))}:{escape(compra_defeituosa.get('senha',''))}</code>",
                        markup=admin_markup
                    )
                    return

                # ---------------- MODO AUTOMÁTICO ----------------
                novo_login_info = _retirar_login_do_estoque(servico, user_id, f"troca:{user_id}:{purchase_id}:{call.message.message_id}")

                if not novo_login_info:
                    _log_evento(user_id=user_id, purchase_id=purchase_id, servico=servico,
                                status="sem_estoque", problema=problema_descrito)
                    bot.send_message(user_id, f"😔 Desculpe, não temos mais estoque de '{escape(servico)}' para realizar a troca agora. Por favor, contate o suporte.")
                    _reenviar_login_da_compra(user_id, compra_defeituosa)
                    _notificar_admin(
                        f"<b>🚨 FALHA NA TROCA (SEM ESTOQUE) 🚨</b>\n\n"
                        f"O cliente <code>{user_id}</code> tentou trocar <b>{escape(servico)}</b>, mas o estoque acabou.\n\n"
                        f"<b>Problema:</b> <i>{escape(problema_descrito)}</i>\n\n"
                        f"<b>Login com defeito:</b> <code>{escape(compra_defeituosa['email'])}:{escape(compra_defeituosa['senha'])}</code>\n\n"
                        f"‼️ <b>AÇÃO NECESSÁRIA:</b> Contate o cliente e reponha o estoque!"
                    )
                    return

                email, senha = _entregar_login_ao_cliente(user_id, novo_login_info)

                user_data = load_user_data(user_id) or {}
                idx, _compra_atual = _achar_compra(user_data, purchase_id)
                if idx >= 0:
                    user_data['purchases'][idx]['troca_realizada'] = True
                    user_data['purchases'][idx]['relato_problema'] = problema_descrito
                    user_data['purchases'][idx]['substituida_por'] = {'email': email, 'senha': senha}
                    user_data['purchases'][idx]['data_troca'] = datetime.now(TZ).isoformat()
                    save_user_data(user_id, user_data)

                _log_evento(user_id=user_id, purchase_id=purchase_id, servico=servico,
                            status="concluida", problema=problema_descrito,
                            login_antigo={"email": compra_defeituosa.get('email'), "senha": compra_defeituosa.get('senha')},
                            login_novo={"email": email, "senha": senha})

                try:
                    user_info = bot.get_chat(user_id)
                    user_display_name = escape(user_info.first_name or "")
                except Exception:
                    user_display_name = "Não encontrado"
                _notificar_admin(
                    f"<b>🔄 TROCA AUTOMÁTICA REALIZADA 🔄</b>\n\n"
                    f"<b>Cliente:</b> {user_display_name} (<code>{user_id}</code>)\n"
                    f"<b>Serviço:</b> {escape(servico)}\n\n"
                    f"<b>Problema Relatado:</b>\n<i>{escape(problema_descrito)}</i>\n\n"
                    f"<b>Login Antigo (removido):</b>\n<code>{escape(compra_defeituosa['email'])}:{escape(compra_defeituosa['senha'])}</code>\n\n"
                    f"<b>Login Novo (entregue):</b>\n<code>{escape(email)}:{escape(senha)}</code>\n\n"
                    f"🕐 <b>Data/Hora:</b> {datetime.now(TZ).strftime('%d/%m/%Y às %H:%M:%S')}"
                )
            except Exception as e:
                print(f"[ERRO] realizar_troca_confirmada: {e}")
                try:
                    bot.send_message(user_id, "❌ Ocorreu um erro grave ao processar sua troca. Por favor, contate o suporte.")
                except Exception:
                    pass

    # =====================================================================
    # Cancelar
    # =====================================================================
    @bot.callback_query_handler(func=lambda call: call.data == 'cancelar_troca')
    def handle_cancelar_troca(call):
        user_id = call.from_user.id
        bot.answer_callback_query(call.id, "Operação cancelada.")
        bot.edit_message_text("✅ A solicitação de troca foi cancelada.", call.message.chat.id, call.message.message_id)

        with _lock_do_usuario(user_id):
            user_data = load_user_data(user_id) or {}
            pending_report = user_data.get('pending_report')
            purchase_id = pending_report.get('purchase_id') if pending_report else None
            if pending_report:
                del user_data['pending_report']
                save_user_data(user_id, user_data)

        if purchase_id:
            _, compra = _achar_compra(user_data, purchase_id)
            if compra:
                _reenviar_login_da_compra(user_id, compra)

    # =====================================================================
    # Admin — aprova/nega pedidos em revisão manual
    # =====================================================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith('trocaadm_'))
    def handle_admin_decisao(call):
        admin_id = call.from_user.id
        if not _is_admin(admin_id):
            bot.answer_callback_query(call.id, "🚫 Apenas administradores.", show_alert=True)
            return

        acao, req_id = call.data.replace('trocaadm_', '').split('_', 1)
        pend = _pendentes_admin()
        registro = pend.get(req_id)
        if not registro:
            bot.answer_callback_query(call.id, "Esse pedido já foi resolvido ou não existe mais.", show_alert=True)
            return

        user_id = registro['user_id']
        purchase_id = registro['purchase_id']
        servico = registro['servico']

        if acao == "negar":
            _remover_pendente_admin(req_id)
            _log_evento(user_id=user_id, purchase_id=purchase_id, servico=servico,
                        status="negada_admin", problema=registro.get('problema'), req_id=req_id)
            bot.answer_callback_query(call.id, "Pedido negado.")
            try:
                bot.edit_message_text(call.message.html_text + "\n\n❌ <b>NEGADO</b>", call.message.chat.id, call.message.message_id, parse_mode='HTML')
            except Exception:
                pass
            try:
                bot.send_message(user_id, "😕 Após análise, não foi possível autorizar a troca da sua conta. Fale com o suporte se quiser mais detalhes.")
            except Exception:
                pass
            return

        if acao == "aprovar":
            novo_login_info = _retirar_login_do_estoque(servico, user_id, f"troca-admin:{req_id}")
            if not novo_login_info:
                bot.answer_callback_query(call.id, "Sem estoque para essa aprovação.", show_alert=True)
                bot.send_message(call.message.chat.id, f"⚠️ Não há estoque de '{escape(servico)}' para aprovar essa troca agora. Reponha o estoque e tente de novo.")
                return

            email, senha = _entregar_login_ao_cliente(
                user_id, novo_login_info,
                motivo_extra="\n\n(Sua troca foi aprovada manualmente pela nossa equipe.)"
            )

            with _lock_do_usuario(user_id):
                user_data = load_user_data(user_id) or {}
                idx, compra = _achar_compra(user_data, purchase_id)
                if idx >= 0:
                    user_data['purchases'][idx]['troca_realizada'] = True
                    user_data['purchases'][idx]['relato_problema'] = registro.get('problema')
                    user_data['purchases'][idx]['substituida_por'] = {'email': email, 'senha': senha}
                    user_data['purchases'][idx]['data_troca'] = datetime.now(TZ).isoformat()
                    save_user_data(user_id, user_data)

            _remover_pendente_admin(req_id)
            _log_evento(user_id=user_id, purchase_id=purchase_id, servico=servico,
                        status="concluida_manual", problema=registro.get('problema'), req_id=req_id,
                        login_novo={"email": email, "senha": senha})

            bot.answer_callback_query(call.id, "Troca aprovada e entregue!")
            try:
                bot.edit_message_text(call.message.html_text + "\n\n✅ <b>APROVADO E ENTREGUE</b>", call.message.chat.id, call.message.message_id, parse_mode='HTML')
            except Exception:
                pass

    # =====================================================================
    # Admin — /trocas_pendentes
    # =====================================================================
    @bot.message_handler(commands=['trocas_pendentes'])
    def cmd_trocas_pendentes(message):
        if not _is_admin(message.from_user.id):
            return
        pend = _pendentes_admin()
        if not pend:
            bot.reply_to(message, "✅ Nenhum pedido de troca aguardando revisão.")
            return
        for req_id, registro in pend.items():
            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton("✅ Aprovar e Trocar", callback_data=f"trocaadm_aprovar_{req_id}"),
                InlineKeyboardButton("❌ Negar", callback_data=f"trocaadm_negar_{req_id}")
            )
            texto = (
                f"<b>🕵️ PEDIDO PENDENTE</b>\n\n"
                f"<b>Cliente:</b> <code>{registro['user_id']}</code>\n"
                f"<b>Serviço:</b> {escape(registro['servico'])}\n"
                f"<b>Problema:</b> <i>{escape(registro.get('problema',''))}</i>\n"
                f"<b>Login atual:</b> <code>{escape(registro['login_antigo'].get('email',''))}:{escape(registro['login_antigo'].get('senha',''))}</code>\n"
                f"<b>Aberto em:</b> {registro.get('criado_em','N/A')}"
            )
            bot.send_message(message.chat.id, texto, parse_mode='HTML', reply_markup=markup)

    # =====================================================================
    # Admin — /config_trocas (garantia, limite, período)
    # =====================================================================
    def _texto_config(cfg):
        return (
            "⚙️ <b>CONFIGURAÇÕES DO SISTEMA DE TROCAS</b>\n\n"
            f"⏰ <b>Garantia automática:</b> {cfg['garantia_horas']}h após a compra\n"
            f"🔁 <b>Limite de trocas automáticas:</b> {cfg['max_trocas_periodo']} a cada {cfg['periodo_dias']} dias\n"
            f"⌛ <b>Prazo pra confirmar o pedido:</b> {cfg['pedido_expira_minutos']} min\n\n"
            "Fora da garantia ou acima do limite, a troca não é recusada — "
            "ela vai para revisão manual (você aprova/nega pelo Telegram)."
        )

    def _markup_config(cfg):
        m = InlineKeyboardMarkup()
        m.row(
            InlineKeyboardButton("➖ 12h", callback_data="trocacfg_garantia_-12"),
            InlineKeyboardButton(f"Garantia: {cfg['garantia_horas']}h", callback_data="noop"),
            InlineKeyboardButton("➕ 12h", callback_data="trocacfg_garantia_+12"),
        )
        m.row(
            InlineKeyboardButton("➖ 1", callback_data="trocacfg_maxtrocas_-1"),
            InlineKeyboardButton(f"Limite: {cfg['max_trocas_periodo']}", callback_data="noop"),
            InlineKeyboardButton("➕ 1", callback_data="trocacfg_maxtrocas_+1"),
        )
        m.row(
            InlineKeyboardButton("➖ 5 dias", callback_data="trocacfg_periodo_-5"),
            InlineKeyboardButton(f"Período: {cfg['periodo_dias']}d", callback_data="noop"),
            InlineKeyboardButton("➕ 5 dias", callback_data="trocacfg_periodo_+5"),
        )
        m.row(InlineKeyboardButton("✅ Fechar", callback_data="trocacfg_fechar"))
        return m

    @bot.message_handler(commands=['config_trocas'])
    def cmd_config_trocas(message):
        if not _is_admin(message.from_user.id):
            return
        cfg = get_config()
        bot.send_message(message.chat.id, _texto_config(cfg), parse_mode='HTML', reply_markup=_markup_config(cfg))

    @bot.callback_query_handler(func=lambda call: call.data.startswith('trocacfg_'))
    def handle_config_trocas(call):
        if not _is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "🚫 Apenas administradores.", show_alert=True)
            return

        if call.data == "trocacfg_fechar":
            bot.answer_callback_query(call.id, "Configurações salvas.")
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            return

        cfg = get_config()
        campo, delta_str = call.data.replace('trocacfg_', '').rsplit('_', 1)
        delta = int(delta_str)

        if campo == "garantia":
            cfg["garantia_horas"] = max(1, cfg["garantia_horas"] + delta)
        elif campo == "maxtrocas":
            cfg["max_trocas_periodo"] = max(1, cfg["max_trocas_periodo"] + delta)
        elif campo == "periodo":
            cfg["periodo_dias"] = max(1, cfg["periodo_dias"] + delta)

        _save_config(cfg)
        bot.answer_callback_query(call.id, "Atualizado.")
        try:
            bot.edit_message_text(_texto_config(cfg), call.message.chat.id, call.message.message_id,
                                   parse_mode='HTML', reply_markup=_markup_config(cfg))
        except Exception:
            pass

    # =====================================================================
    # Admin — /trocas_relatorio [dias]
    # =====================================================================
    @bot.message_handler(commands=['trocas_relatorio'])
    def cmd_trocas_relatorio(message):
        if not _is_admin(message.from_user.id):
            return
        partes = message.text.split()
        dias = int(partes[1]) if len(partes) > 1 and partes[1].isdigit() else None
        gerar_relatorio_trocas(bot, message.chat.id, dias=dias)


# --------------------------------------------------------------------------
# Relatório (agora lê do log próprio — instantâneo, não varre todo mundo)
# --------------------------------------------------------------------------
def gerar_relatorio_trocas(bot, chat_id, dias=None):
    periodo_str = f"(Últimos {dias} dias)" if dias else "(Todos)"
    bot.send_message(chat_id, f"🔎 Gerando relatório de trocas {periodo_str}...")

    log = _read_json(LOG_PATH, list)
    cutoff = datetime.now(TZ) - timedelta(days=dias) if dias else None

    eventos = []
    for entrada in log:
        if cutoff:
            try:
                ts = datetime.fromisoformat(entrada["timestamp"])
            except Exception:
                continue
            if ts < cutoff:
                continue
        eventos.append(entrada)

    if not eventos:
        bot.send_message(chat_id, f"✅ Nenhum evento de troca registrado no período.")
        return

    contagem = {}
    for e in eventos:
        contagem[e.get("status", "?")] = contagem.get(e.get("status", "?"), 0) + 1
    resumo = "\n".join(f"• {status}: {qtd}" for status, qtd in sorted(contagem.items()))

    linhas = [f"Relatório de Trocas {periodo_str}\nTotal de eventos: {len(eventos)}\n\nResumo:\n{resumo}\n"]
    for e in eventos:
        login_antigo = e.get('login_antigo') or {}
        login_novo = e.get('login_novo') or {}
        linhas.append(
            "----------------------------------------\n"
            f"Data: {e.get('timestamp','N/A')}\n"
            f"Status: {e.get('status','N/A')}\n"
            f"Cliente: {e.get('user_id','N/A')}\n"
            f"Serviço: {e.get('servico','N/A')}\n"
            f"Problema: {e.get('problema','N/A')}\n"
            f"Login antigo: {login_antigo.get('email','N/A')}:{login_antigo.get('senha','N/A')}\n"
            f"Login novo: {login_novo.get('email','N/A')}:{login_novo.get('senha','N/A')}\n"
        )

    try:
        filename = f"relatorio_trocas_{int(time.time())}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("\n".join(linhas))
        with open(filename, 'rb') as f:
            bot.send_document(chat_id, f, caption=f"📄 Relatório com {len(eventos)} eventos de troca.")
        os.remove(filename)
    except Exception as e:
        print(f"[RELATÓRIO] Erro ao enviar arquivo: {e}")
        bot.send_message(chat_id, "Ocorreu um erro ao gerar e enviar o arquivo de relatório.")
