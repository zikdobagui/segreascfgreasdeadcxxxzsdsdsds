# Backup ZIP + Google Drive (6h)
1) `pip install -r requirements-backup.txt`
2) Coloque `credentials.json` na raiz (ou exporte `GDRIVE_CREDENTIALS_FILE`)
3) No seu arquivo principal, após criar `bot` e `ADMIN_ID`:

```python
import schedule
import backup_manager

backup_manager.ensure_backup_schedule(bot, ADMIN_ID)

def _schedule_loop():
    import time, schedule
    while True:
        schedule.run_pending()
        time.sleep(1)

import threading
threading.Thread(target=_schedule_loop, daemon=True).start()
```

### Comando /backup (opcional)
```python
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

@bot.message_handler(commands=['backup'])
def cmd_backup(message):
    if str(message.from_user.id) != str(ADMIN_ID):
        return bot.reply_to(message, "Acesso negado.")
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📦 Backup agora", callback_data="backup_now"),
        InlineKeyboardButton("🗃️ Pasta backups", callback_data="backup_path")
    )
    bot.send_message(message.chat.id, "Selecione uma opção de backup:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data in {"backup_now", "backup_path"})
def cb_backup(c):
    if str(c.from_user.id) != str(ADMIN_ID):
        return bot.answer_callback_query(c.id, "Acesso negado.", show_alert=True)
    import os, backup_manager
    if c.data == "backup_path":
        bp = os.path.abspath(backup_manager.BACKUP_DIR)
        bot.answer_callback_query(c.id, "Ok!")
        return bot.send_message(c.message.chat.id, f"📁 `{bp}`", parse_mode="Markdown")
    if c.data == "backup_now":
        bot.answer_callback_query(c.id, "Iniciando…")
        bot.edit_message_text("⏳ Fazendo backup…", c.message.chat.id, c.message.message_id)
        backup_manager.run_backup_async(bot=bot, admin_id=ADMIN_ID, label="manual")
```
