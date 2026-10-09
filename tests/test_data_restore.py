from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import zipfile
import telebot

from app import data_restore as restore
from app import restore_handlers
import bot as launcher


class RestoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source.db"
        with closing(sqlite3.connect(self.source)) as conn:
            conn.execute("CREATE TABLE users(user_id INTEGER PRIMARY KEY, data TEXT, saldo REAL)")
            conn.execute("INSERT INTO users VALUES(1, '{}', 23.5)")
            conn.commit()
        self.zip = self.root / "upload.zip"
        self.entries = {
            "database/bot.db": self.source.read_bytes(),
            "database/example.json": b'{"value": 7}',
            "textos/start.txt": b"novo texto",
            "data/users.json": b"{}",
        }
        for name in restore.FOLDERS:
            (self.root / name).mkdir()
            (self.root / name / "old.txt").write_text("anterior", encoding="utf-8")

    def archive(self, entries=None):
        with zipfile.ZipFile(self.zip, "w", zipfile.ZIP_DEFLATED) as zipf:
            for name, content in (entries or self.entries).items():
                info = zipfile.ZipInfo(name)
                info.filename = name  # não normalizar caminhos maliciosos no Windows
                zipf.writestr(info, content)
        return self.zip

    def prepare(self):
        return restore.prepare(self.root, self.archive())

    def assert_old_data(self):
        for name in restore.FOLDERS:
            self.assertEqual((self.root / name / "old.txt").read_text(), "anterior")
            self.assertEqual(len(list((self.root / name).iterdir())), 1)

    def test_prepare_does_not_touch_live_data_and_replace_keeps_backup(self):
        self.assertEqual(self.prepare()["files"], 4)
        self.assert_old_data()
        restore.queue(self.root, 123)
        restore.apply_pending(self.root)
        self.assertEqual((self.root / "textos/start.txt").read_text(), "novo texto")
        self.assertFalse((self.root / "textos/old.txt").exists())
        with closing(sqlite3.connect(self.root / "database/bot.db")) as conn:
            self.assertEqual(conn.execute("SELECT saldo FROM users").fetchone()[0], 23.5)
        result = json.loads((self.root / restore.STATE_DIR / "result.json").read_text())
        self.assertTrue(result["ok"])
        for name in restore.FOLDERS:
            self.assertEqual((self.root / result["backup"] / name / "old.txt").read_text(), "anterior")
        restore.apply_pending(self.root)  # não reaplica o ZIP no próximo boot

    def test_rejects_traversal(self):
        for name in ("../escape.txt", "/database/a", "database/../escape", "database\\..\\escape",
                     "database/C:bad", "database/a./x"):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    restore.prepare(self.root, self.archive({**self.entries, name: b"bad"}))
                self.assert_old_data()
                self.assertFalse((self.root / restore.STATE_DIR / "candidate").exists())

    def test_accepts_wrapper_and_ignores_project_files(self):
        entries = {"backup/" + k: v for k, v in self.entries.items()}
        entries.update({"backup/": b"", "backup/bot.py": b"do not execute",
                        "backup/settings/credenciais.json": b"private config"})
        summary = restore.prepare(self.root, self.archive(entries))
        self.assertEqual(summary["ignored"], 3)
        candidate = self.root / restore.STATE_DIR / "candidate"
        self.assertFalse((candidate / "settings").exists())
        self.assertTrue((candidate / "database/bot.db").exists())
        self.assert_old_data()

    def test_full_backup_at_root_ignores_code_and_metadata(self):
        summary = restore.prepare(self.root, self.archive({**self.entries, "bot.py": b"code",
            ".DS_Store": b"metadata", "__MACOSX/._database": b"metadata"}))
        self.assertEqual(summary["ignored"], 3)
        self.assertEqual(summary["files"], 4)

    def test_ambiguous_backups_rejected(self):
        entries = {prefix + k: v for prefix in ("old/", "new/") for k, v in self.entries.items()}
        with self.assertRaisesRegex(ValueError, "mais de um"):
            restore.prepare(self.root, self.archive(entries))
        self.assert_old_data()

    def test_rejects_missing_folder_broken_json_and_broken_database(self):
        variants = [
            {k: v for k, v in self.entries.items() if k != "database/bot.db"},
            {**self.entries, "data/users.json": b"{"},
            {**self.entries, "database/bot.db": b"not sqlite"},
        ]
        for entries in variants:
            with self.subTest(entries=list(entries)):
                with self.assertRaises(ValueError):
                    restore.prepare(self.root, self.archive(entries))
                self.assert_old_data()

    def test_rejects_symlink_and_duplicate_paths(self):
        self.archive()
        with zipfile.ZipFile(self.zip, "a") as zipf:
            info = zipfile.ZipInfo("database/link")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            zipf.writestr(info, "../../settings")
        with self.assertRaises(ValueError):
            restore.prepare(self.root, self.zip)
        self.archive({**self.entries, "data/USERS.json": b"{}"})
        with self.assertRaises(ValueError):
            restore.prepare(self.root, self.zip)
        self.assert_old_data()

    def test_limits(self):
        for setting, value in (("MAX_ZIP_BYTES", 1), ("MAX_EXPANDED_BYTES", 1), ("MAX_FILES", 1)):
            with self.subTest(setting=setting), patch.object(restore, setting, value):
                with self.assertRaises(ValueError):
                    restore.prepare(self.root, self.archive())
                self.assert_old_data()

    def test_empty_directories_allowed(self):
        restore.prepare(self.root, self.archive({"database/bot.db": self.source.read_bytes(),
                                               "data/": b"", "textos/": b""}))
        restore.queue(self.root, 123)
        restore.apply_pending(self.root)
        self.assertEqual(list((self.root / "textos").iterdir()), [])

    def test_missing_data_folder_is_preserved(self):
        entries = {k: v for k, v in self.entries.items() if not k.startswith("data/")}
        result = restore.prepare(self.root, self.archive(entries))
        self.assertEqual(result["folders"], ["database", "textos"])
        restore.queue(self.root, 123)
        restore.apply_pending(self.root)
        self.assertEqual((self.root / "data/old.txt").read_text(), "anterior")
        self.assertEqual((self.root / "textos/start.txt").read_text(), "novo texto")

    def test_windows_paths_inside_wrapper(self):
        entries = {"backup\\" + k.replace("/", "\\"): v for k, v in self.entries.items()}
        result = restore.prepare(self.root, self.archive(entries))
        self.assertEqual(result["files"], 4)
        self.assertTrue((self.root / restore.STATE_DIR / "candidate/database/bot.db").is_file())

    def test_flat_database_contents_are_recognized(self):
        result = restore.prepare(self.root, self.archive({
            "bot.db": self.source.read_bytes(), "example.json": b"{}"}))
        self.assertEqual(result["folders"], ["database"])
        restore.queue(self.root, 123)
        restore.apply_pending(self.root)
        self.assertTrue((self.root / "database/bot.db").is_file())
        self.assertEqual((self.root / "data/old.txt").read_text(), "anterior")
        self.assertEqual((self.root / "textos/old.txt").read_text(), "anterior")

    def test_text_only_restore_does_not_require_or_replace_database(self):
        result = restore.prepare(self.root, self.archive({"textos/start.txt": b"novo texto"}))
        self.assertEqual(result["folders"], ["textos"])
        restore.queue(self.root, 123)
        restore.apply_pending(self.root)
        self.assertEqual((self.root / "database/old.txt").read_text(), "anterior")
        self.assertEqual((self.root / "textos/start.txt").read_text(), "novo texto")

    def test_wal_is_incorporated_before_replacement(self):
        conn = sqlite3.connect(self.source)
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("UPDATE users SET saldo=99")
            conn.commit()
            self.entries["database/bot.db"] = self.source.read_bytes()
            self.entries["database/bot.db-wal"] = Path(str(self.source) + "-wal").read_bytes()
            self.entries["database/bot.db-shm"] = Path(str(self.source) + "-shm").read_bytes()
            self.prepare()
        finally:
            conn.close()
        restore.queue(self.root, 123)
        restore.apply_pending(self.root)
        with closing(sqlite3.connect(self.root / "database/bot.db")) as restored:
            self.assertEqual(restored.execute("SELECT saldo FROM users").fetchone()[0], 99)

    def test_failed_swap_rolls_back_all_folders(self):
        self.prepare()
        restore.queue(self.root, 123)
        real_replace = os.replace

        def fail_once(src, dst):
            if Path(src) == self.root / restore.STATE_DIR / "candidate/textos":
                raise OSError("simulated disk error")
            return real_replace(src, dst)

        with patch.object(restore.os, "replace", side_effect=fail_once):
            restore.apply_pending(self.root)
        self.assert_old_data()
        self.assertFalse(json.loads((self.root / restore.STATE_DIR / "result.json").read_text())["ok"])

    def test_interrupted_swap_is_recovered_on_next_boot(self):
        self.prepare()
        restore.queue(self.root, 123)
        real_replace = os.replace

        def interrupt(src, dst):
            if Path(src) == self.root / restore.STATE_DIR / "candidate/textos":
                raise KeyboardInterrupt()
            return real_replace(src, dst)

        with patch.object(restore.os, "replace", side_effect=interrupt):
            with self.assertRaises(KeyboardInterrupt):
                restore.apply_pending(self.root)
        self.assertTrue((self.root / restore.STATE_DIR / "journal.json").exists())
        restore.apply_pending(self.root)
        self.assert_old_data()

    def test_confirmed_restore_cannot_be_discarded(self):
        self.prepare()
        restore.queue(self.root, 123)
        with self.assertRaises(ValueError):
            restore.discard(self.root)
        with self.assertRaises(ValueError):
            restore.queue(self.root, 123)

    def test_launcher_applies_only_between_finished_workers(self):
        calls = []
        worker1, worker2 = Mock(), Mock()
        worker1.wait.side_effect = lambda: calls.append("worker1_finished") or restore.RESTART_CODE
        worker2.wait.side_effect = lambda: calls.append("worker2_finished") or 0
        with patch.object(launcher.subprocess, "Popen", side_effect=[worker1, worker2]), \
                patch.object(launcher.signal, "signal"), \
                patch.object(restore, "apply_pending", side_effect=lambda root: calls.append("apply")):
            self.assertEqual(launcher.supervise(self.root), 0)
        self.assertEqual(calls, ["apply", "worker1_finished", "apply", "worker2_finished"])


class HandlerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bot = Mock()
        self.handlers = {}

        def register(**kwargs):
            def decorator(fn):
                self.handlers[fn.__name__] = fn
                return fn
            return decorator

        self.bot.message_handler.side_effect = register
        self.bot.callback_query_handler.side_effect = register
        restore_handlers.registrar(self.bot, 123, self.root)
        self.env = patch.dict(os.environ, {"BOT_RESTORE_SUPERVISED": "1"})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.message = SimpleNamespace(from_user=SimpleNamespace(id=123),
                                       chat=SimpleNamespace(id=123, type="private"))

    def test_owner_only_and_private_only(self):
        self.message.from_user.id = 456
        self.handlers["begin"](self.message)
        self.bot.send_message.assert_not_called()
        self.message.from_user.id = 123
        self.message.chat.type = "group"
        self.handlers["begin"](self.message)
        self.bot.send_message.assert_not_called()

    def test_upload_confirmation_and_stale_button(self):
        self.handlers["begin"](self.message)
        self.message.document = SimpleNamespace(file_name="data.zip", file_size=3, file_id="test")
        self.bot.get_file.return_value = SimpleNamespace(file_size=3, file_path="test")
        self.bot.download_file.return_value = b"zip"
        with patch.object(restore, "prepare", return_value={"files": 4, "bytes": 3}):
            self.handlers["receive"](self.message)
        markup = self.bot.send_message.call_args.kwargs["reply_markup"]
        callback = markup.keyboard[0][0].callback_data
        call = SimpleNamespace(id="callback", data=callback, message=self.message,
                               from_user=self.message.from_user)
        with patch.object(restore, "queue") as queue, patch.object(restore_handlers.os, "_exit") as exit_:
            call.from_user = SimpleNamespace(id=999)
            self.handlers["confirm"](call)
            queue.assert_not_called()
            call.from_user = self.message.from_user
            self.handlers["confirm"](call)
            queue.assert_called_once_with(self.root, 123)
            exit_.assert_called_once_with(75)
            self.handlers["confirm"](call)
            queue.assert_called_once()

    def test_zip_without_command_or_file_size_is_validated(self):
        self.message.document = SimpleNamespace(file_name="data.zip", file_size=None, file_id="test")
        self.bot.get_file.return_value = SimpleNamespace(file_size=3, file_path="test")
        self.bot.download_file.return_value = b"zip"
        with patch.object(restore, "prepare", return_value={"files": 4, "bytes": 3}) as prepare:
            self.handlers["receive"](self.message)
        prepare.assert_called_once()
        self.assertIn("reply_markup", self.bot.send_message.call_args.kwargs)

    def test_pending_edit_cannot_consume_zip(self):
        real_bot = telebot.TeleBot("123456:TEST_TOKEN", threaded=False)
        real_bot.send_message = Mock()
        real_bot.get_file = Mock(return_value=SimpleNamespace(file_size=3, file_path="test"))
        real_bot.download_file = Mock(return_value=b"zip")
        restore_handlers.registrar(real_bot, 123, self.root)
        edit_callback = Mock()
        real_bot.register_next_step_handler_by_chat_id(123, edit_callback)
        message = telebot.types.Message.de_json({
            "message_id": 1, "date": 1, "chat": {"id": 123, "type": "private"},
            "from": {"id": 123, "is_bot": False, "first_name": "Owner"},
            "document": {"file_id": "test", "file_unique_id": "test", "file_name": "backup.zip", "file_size": 3},
        })
        with patch.object(restore, "prepare", return_value={"files": 4, "bytes": 3}) as prepare:
            real_bot.process_new_messages([message])
        edit_callback.assert_not_called()
        prepare.assert_called_once()
        self.assertIn("reply_markup", real_bot.send_message.call_args.kwargs)

    def test_direct_unauthorized_upload_does_not_download(self):
        self.message.from_user.id = 999
        self.handlers["receive"](self.message)
        self.bot.get_file.assert_not_called()

    def test_unsupervised_upload_reports_problem(self):
        with patch.dict(os.environ, {"BOT_RESTORE_SUPERVISED": "0"}):
            self.handlers["receive"](self.message)
        self.bot.get_file.assert_not_called()
        self.assertIn("bot.py", self.bot.send_message.call_args.args[1])

    def test_cancel_and_expiration_never_queue(self):
        self.handlers["begin"](self.message)
        self.handlers["cancel"](self.message)
        with patch.object(restore, "queue") as queue:
            call = SimpleNamespace(id="x", data="restore:yes:old", message=self.message,
                                   from_user=self.message.from_user)
            self.handlers["confirm"](call)
            queue.assert_not_called()

    def test_result_is_sent_once(self):
        work = self.root / restore.STATE_DIR
        work.mkdir()
        (work / "result.json").write_text(json.dumps({"chat_id": 123, "ok": True, "backup": "backup"}))
        restore_handlers.notify_result(self.bot, 123, self.root)
        restore_handlers.notify_result(self.bot, 123, self.root)
        self.bot.send_message.assert_called_once()


if __name__ == "__main__":
    unittest.main()
