# rl_maintenance.py  (V2 anti-trava)
import os, json, time, threading
from typing import List, Tuple

_STATE_DIR = os.path.join("settings")
_STATE_FILE = os.path.join(_STATE_DIR, "maintenance.json")
_LAST_NOTIFY = {}  # chat_id -> ts
_MAINTENANCE_MESSAGE = "🚧 Estamos em manutenção agora. Por favor, tente novamente mais tarde."

# ---- Configs anti-trava (pode ajustar por env) ----
BROADCAST_ENABLED = os.getenv("MAINT_BROADCAST", "1") != "0"
MAX_NOTIFY = int(os.getenv("MAINT_MAX_NOTIFY", "200"))   # máx. usuários por rodada
NOTIFY_SLEEP = float(os.getenv("MAINT_SLEEP", "0.02"))   # pausa entre envios (seg)
THROTTLE_SECONDS = int(os.getenv("MAINT_THROTTLE", "60"))

CMD_ON = "/manutencao_on"
CMD_OFF = "/manutencao_off"
CMD_OFF2 = "/manutencao_offline"     # alias aceito
CMD_STATUS = "/manutencao"

def get_maintenance_message() -> str:
    """Returns the current maintenance message from file or default."""
    try:
        _ensure_state_dir()
        msg_file = os.path.join(_STATE_DIR, "maintenance_message.txt")
        if os.path.exists(msg_file):
            with open(msg_file, "r", encoding="utf-8") as f:
                saved_msg = f.read().strip()
                if saved_msg:
                    return saved_msg
    except Exception:
        pass
    return _MAINTENANCE_MESSAGE

def set_maintenance_message(msg: str):
    """Sets and saves a new maintenance message."""
    global _MAINTENANCE_MESSAGE
    if isinstance(msg, str) and msg.strip():
        _MAINTENANCE_MESSAGE = msg
        # Salvar em arquivo para persistir
        try:
            _ensure_state_dir()
            msg_file = os.path.join(_STATE_DIR, "maintenance_message.txt")
            with open(msg_file, "w", encoding="utf-8") as f:
                f.write(msg)
        except Exception as e:
            print(f"[MAINTENANCE] Erro ao salvar mensagem: {e}")

def _ensure_state_dir():
    os.makedirs(_STATE_DIR, exist_ok=True)

def _read_state():
    _ensure_state_dir()
    if not os.path.exists(_STATE_FILE):
        return {"on": False}
    try:
        with open(_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"on": False}

def _write_state(on: bool):
    _ensure_state_dir()
    try:
        with open(_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({"on": on, "ts": int(time.time())}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def is_on() -> bool:
    st = _read_state()
    return bool(st.get("on", False))

def maintenance_on():
    _write_state(True)

def maintenance_off():
    _write_state(False)

def _extract_uid_and_chat(update) -> Tuple[int|None, int|None, str|None, str|None]:
    uid = chat_id = None
    text = cb = None
    try:
        if hasattr(update, "message") and update.message:
            msg = update.message
            chat_id = getattr(getattr(msg, "chat", None), "id", None)
            uid = getattr(getattr(msg, "from_user", None), "id", None)
            text = getattr(msg, "text", None)
        elif hasattr(update, "callback_query") and update.callback_query:
            cq = update.callback_query
            chat_id = getattr(getattr(cq, "message", None), "chat", None)
            chat_id = getattr(chat_id, "id", None)
            uid = getattr(getattr(cq, "from_user", None), "id", None)
            cb = getattr(cq, "data", None)
    except Exception:
        pass
    return uid, chat_id, text, cb

def _throttle(chat_id: int, seconds: int = THROTTLE_SECONDS) -> bool:
    now = time.time()
    last = _LAST_NOTIFY.get(chat_id, 0)
    if now - last >= seconds:
        _LAST_NOTIFY[chat_id] = now
        return True
    return False

def _notify_all_users_sync(bot, exclude_ids=None):
    """Envio com limites e pausas para não travar o loop principal."""
    if not BROADCAST_ENABLED:
        return
    exclude = set(exclude_ids or [])
    enviados = 0
    try:
        # CORREÇÃO: percorria database/users/*.json, pasta que não existe
        # mais após a migração para SQLite (o broadcast não notificava
        # ninguém). Agora usa database.get_all_user_ids().
        from app import database
        for uid in database.get_all_user_ids():
            if enviados >= MAX_NOTIFY:
                return
            if not isinstance(uid, int) or uid in exclude:
                continue
            try:
                bot.send_message(uid, get_maintenance_message())
                enviados += 1
                if NOTIFY_SLEEP > 0:
                    time.sleep(NOTIFY_SLEEP)
            except Exception:
                pass
    except Exception:
        pass

def notify_all_users(bot, exclude_ids=None):
    """Roda em thread separada para não travar o bot."""
    th = threading.Thread(target=_notify_all_users_sync, args=(bot, exclude_ids), daemon=True)
    th.start()

def _handle_admin_command(bot, uid, chat_id, text, admin_ids):
    if not text:
        return False
    if uid not in admin_ids:
        return False
    t = text.strip().lower()
    if t == CMD_ON:
        maintenance_on()
        bot.send_message(chat_id, "🎛️ Modo manutenção **ativado**. Usuários comuns serão temporariamente bloqueados.")
        try:
            notify_all_users(bot, exclude_ids=list(admin_ids))
        except Exception as _e:
            print(f"[maintenance] notify_all_users: {_e}")
        return True
    if t in (CMD_OFF, CMD_OFF2):
        maintenance_off()
        bot.send_message(chat_id, "✅ Modo manutenção **desativado**.")
        return True
    if t == CMD_STATUS:
        bot.send_message(chat_id, f"🧰 Status manutenção: {'ATIVADO' if is_on() else 'DESATIVADO'}")
        return True
    return False

def _handle_admin_callback(bot, uid, chat_id, data, admin_ids):
    if not data:
        return False
    if uid not in admin_ids:
        return False
    d = str(data).lower()

    # Ativar manutenção (suporta botões do painel e aliases antigos)
    if d in ("manutencao_on", "maintenance_on", "admin_maintenance_on"):
        maintenance_on()
        bot.send_message(chat_id, "🎛️ Modo manutenção **ativado** via painel.")
        try:
            notify_all_users(bot, exclude_ids=list(admin_ids))
        except Exception as _e:
            print(f"[maintenance] notify_all_users: {_e}")
        return True

    # Desativar manutenção (suporta botões do painel e aliases antigos)
    if d in ("manutencao_off", "maintenance_off", "manutencao_offline", "admin_maintenance_off"):
        maintenance_off()
        bot.send_message(chat_id, "✅ Modo manutenção **desativado** via painel.")
        return True

    # Abrir menu de configuração de mensagem (o bot.py trata os subpassos)
    if d == "admin_maintenance_message":
        # Deixar o bot.py processar este callback - não interceptar
        return False

    return False

def install_maintenance_filter(bot, admin_ids: List[int]):
    """Instala filtro apenas uma vez e sem travar o loop."""
    # evita reinstalar
    if getattr(bot, "_MAINT_FILTER_INSTALLED", False):
        return
    setattr(bot, "_MAINT_FILTER_INSTALLED", True)

    admin_ids = set(admin_ids or [])
    original = bot.process_new_updates

    def patched(updates):
        to_forward = []
        for up in updates:
            uid, chat_id, text, cb = _extract_uid_and_chat(up)
            # Bypass: sempre encaminhar o callback de configurar mensagem de manutenção
            # para que o bot.py trate diretamente, independente do modo manutenção
            try:
                if cb:
                    d = str(cb).lower()
                    # Callbacks de configuração de mensagem removidos
                    if False:  # Desabilitado
                        try:
                            print(f"[MAINTENANCE/FILTER] bypass -> {d} (forward to bot.py)")
                        except Exception:
                            pass
                        to_forward.append(up)
                        continue
            except Exception:
                pass
            handled = False
            if text:
                handled = _handle_admin_command(bot, uid, chat_id, text, admin_ids)
            if cb and not handled:
                handled = _handle_admin_callback(bot, uid, chat_id, cb, admin_ids)

            if is_on():
                if uid in admin_ids:
                    to_forward.append(up)  # ADM sempre passa
                else:
                    try:
                        if chat_id is not None and _throttle(chat_id):
                            bot.send_message(chat_id, get_maintenance_message())
                    except Exception:
                        pass
            else:
                to_forward.append(up)

        if to_forward:
            return original(to_forward)

    bot.process_new_updates = patched