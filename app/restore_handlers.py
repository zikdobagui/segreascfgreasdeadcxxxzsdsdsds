"""Importação de dados pelo dono, em conversa privada, com confirmação."""
import json
import logging
import os
from pathlib import Path
import secrets
import tempfile
import threading
import time

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from app import data_restore

SESSION_SECONDS = 600


def notify_result(bot, owner_id, root="."):
    path = Path(root).resolve() / data_restore.STATE_DIR / "result.json"
    if not path.exists():
        return
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
        if int(result["chat_id"]) != int(owner_id):
            return
        if result["ok"]:
            text = ("✅ As pastas database, textos e data foram substituídas. "
                    "O bot carregou os dados importados.\n"
                    f"Backup anterior no servidor: {result['backup']}")
        else:
            text = ("❌ A restauração não foi concluída. Os dados anteriores foram "
                    "preservados ou recuperados. Envie um novo ZIP para tentar novamente.")
        bot.send_message(owner_id, text)
        path.unlink()
    except Exception:
        logging.exception("Não foi possível informar o resultado da restauração")


def registrar(bot, owner_id, root="."):
    root = Path(root).resolve()
    owner_id = int(owner_id)
    state = {}
    lock = threading.Lock()

    def authorized(message, user=None):
        user = user or message.from_user
        return (user.id == owner_id and message.chat.type == "private"
                and message.chat.id == owner_id)

    def active():
        return state and time.monotonic() < state["expires"]

    @bot.message_handler(commands=["restaurar_dados"])
    def begin(message):
        if not authorized(message):
            return
        if os.getenv("BOT_RESTORE_SUPERVISED") != "1":
            bot.send_message(owner_id, "Inicie o bot pelo bot.py da raiz ou pelo start.py para restaurar dados.")
            return
        with lock:
            try:
                data_restore.discard(root)
            except ValueError as exc:
                bot.send_message(owner_id, str(exc))
                return
            state.clear()
            state.update(expires=time.monotonic() + SESSION_SECONDS, token=None)
            bot.clear_step_handler_by_chat_id(owner_id)
            bot.send_message(owner_id,
                "Envie um ZIP de até 20 MB contendo na raiz as três pastas:\n"
                "database/ (incluindo bot.db)\ntextos/\ndata/\n\n"
                "A substituição será TOTAL: arquivos atuais ausentes no ZIP também serão removidos. "
                "Use uma cópia feita com o bot de origem parado, incluindo os arquivos SQLite -wal, "
                "se existirem. Evite restaurar durante compras ou pagamentos em andamento.\n\n"
                "Vou validar o arquivo e pedir sua confirmação antes de reiniciar. "
                "As pastas anteriores ficarão guardadas no servidor.\n"
                "Prazo: 10 minutos. Para cancelar: /cancelar_restauracao")

    @bot.message_handler(commands=["cancelar_restauracao"])
    def cancel(message):
        if not authorized(message):
            return
        with lock:
            try:
                data_restore.discard(root)
            except ValueError as exc:
                bot.send_message(owner_id, str(exc))
                return
            state.clear()
            bot.send_message(owner_id, "Restauração cancelada. Os dados atuais não foram alterados.")

    @bot.message_handler(content_types=["document"],
                         func=lambda m: authorized(m) and bool(state))
    def receive(message):
        with lock:
            if not active():
                state.clear()
                data_restore.discard(root)
                bot.send_message(owner_id, "Prazo expirado. Use /restaurar_dados novamente.")
                return
            document = message.document
            if not (document.file_name or "").lower().endswith(".zip"):
                bot.send_message(owner_id, "Envie um arquivo .zip.")
                return
            if not document.file_size or document.file_size > data_restore.MAX_ZIP_BYTES:
                bot.send_message(owner_id, "O ZIP deve ter no máximo 20 MB.")
                return
            state["token"] = None  # Invalida qualquer confirmação de um ZIP anterior.
            upload = None
            try:
                info = bot.get_file(document.file_id)
                if info.file_size and info.file_size > data_restore.MAX_ZIP_BYTES:
                    raise ValueError("O ZIP deve ter no máximo 20 MB.")
                payload = bot.download_file(info.file_path)
                if len(payload) > data_restore.MAX_ZIP_BYTES:
                    raise ValueError("O ZIP deve ter no máximo 20 MB.")
                work = root / data_restore.STATE_DIR
                work.mkdir(parents=True, exist_ok=True)
                with tempfile.NamedTemporaryFile(dir=work, suffix=".zip", delete=False) as stream:
                    upload = Path(stream.name)
                    stream.write(payload)
                summary = data_restore.prepare(root, upload)
                token = secrets.token_hex(8)
                state.update(token=token, expires=time.monotonic() + SESSION_SECONDS)
                markup = InlineKeyboardMarkup()
                markup.row(InlineKeyboardButton("Substituir e reiniciar", callback_data=f"restore:yes:{token}"))
                markup.row(InlineKeyboardButton("Cancelar", callback_data=f"restore:no:{token}"))
                bot.send_message(owner_id,
                    f"ZIP validado: {summary['files']} arquivos.\n\n"
                    "Confirmar a substituição completa de database, textos e data? "
                    "O bot reiniciará e guardará um backup das pastas anteriores.",
                    reply_markup=markup)
            except Exception as exc:
                logging.exception("Falha ao validar importação de dados")
                state["token"] = None
                reason = str(exc) if isinstance(exc, ValueError) else "Não foi possível baixar ou validar o ZIP."
                bot.send_message(owner_id, f"❌ {reason}\nOs dados atuais não foram alterados. Envie outro ZIP.")
            finally:
                if upload:
                    upload.unlink(missing_ok=True)

    @bot.callback_query_handler(func=lambda c: (c.data or "").startswith("restore:"))
    def confirm(call):
        if not call.message or not authorized(call.message, call.from_user):
            bot.answer_callback_query(call.id, "Somente o dono, no privado.", show_alert=True)
            return
        with lock:
            parts = call.data.split(":")
            if (len(parts) != 3 or parts[1] not in ("yes", "no") or not active()
                    or not state.get("token") or not secrets.compare_digest(parts[2], state["token"])):
                bot.answer_callback_query(call.id, "Confirmação expirada. Use /restaurar_dados.", show_alert=True)
                return
            bot.answer_callback_query(call.id)
            if parts[1] == "no":
                data_restore.discard(root)
                state.clear()
                bot.send_message(owner_id, "Cancelado. Nenhum dado atual foi alterado.")
                return
            data_restore.queue(root, owner_id)
            state.clear()
            try:
                bot.send_message(owner_id, "Reiniciando para substituir os dados. Aguarde a mensagem de resultado.")
            finally:
                # Todas as threads/conexões terminam ANTES de o launcher trocar as pastas.
                os._exit(data_restore.RESTART_CODE)
