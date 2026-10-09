import ast
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import start
from app import healthcheck, limpeza_cache_boot


class StartupTests(unittest.TestCase):
    def test_supervisor_marks_external_healthcheck(self):
        with patch.object(start.subprocess, 'Popen') as spawn:
            start._spawn('bot')
        self.assertEqual(spawn.call_args.kwargs['env']['BOT_EXTERNAL_HEALTHCHECK'], '1')
        self.assertEqual(spawn.call_args.args[0][-3:], ['-u', '-m', 'bot'])

    def test_polling_startup_does_not_duplicate_healthcheck_or_notify_synchronously(self):
        source = (Path(__file__).resolve().parents[1] / 'app' / 'bot.py').read_text(encoding='utf-8')
        node = next(n for n in ast.parse(source).body
                    if isinstance(n, ast.FunctionDef) and n.name == 'start_polling')
        for supervised in (False, True):
            with self.subTest(supervised=supervised), tempfile.TemporaryDirectory() as temp:
                bot = Mock()
                bot.infinity_polling.side_effect = KeyboardInterrupt
                threads = Mock()
                notify = Mock()
                ns = {'bot': bot, 'threading': threads, 'send_startup_notification': notify}
                exec(compile(ast.Module(body=[node], type_ignores=[]), 'startup', 'exec'), ns)
                previous = os.getcwd()
                try:
                    os.chdir(temp)
                    with patch.dict(os.environ, {'BOT_EXTERNAL_HEALTHCHECK': '1' if supervised else '0'}), \
                            patch.object(limpeza_cache_boot, 'limpar_cache_boot') as clean:
                        with self.assertRaises(KeyboardInterrupt):
                            ns['start_polling']()
                        clean.assert_called_once_with()
                    targets = [c.kwargs['target'] for c in threads.Thread.call_args_list]
                    self.assertEqual(targets.count(healthcheck.start_healthcheck_server), 0 if supervised else 1)
                    self.assertIn(notify, targets)
                    notify.assert_not_called()
                    bot.infinity_polling.assert_called_once()
                finally:
                    if ns.get('_lock_file_handle'):
                        ns['_lock_file_handle'].close()
                    os.chdir(previous)
