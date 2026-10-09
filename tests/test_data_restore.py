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

    def test_rejects_traversal_and_unrelated_files(self):
        for name in ("../escape.txt", "/database/a", "database/../escape", "database\\a",
                     "database/C:bad", "settings/credenciais.json", "database/a./x"):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    restore.prepare(self.root, self.archive({**self.entries, name: b"bad"}))
                self.assert_old_data()
                self.assertFalse((self.root / restore.STATE_DIR / "candidate").exists())

    def test_rejects_missing_folder_broken_json_and_broken_database(self):
        variants = [
            {k: v for k, v in self.entries.items() if not k.startswith("data/")},
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
