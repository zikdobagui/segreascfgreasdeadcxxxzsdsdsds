import ast
import html
import json
import tempfile
import unittest
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import requests
from app import estoque_api as stock


CATALOG = {'products': [{'service': 'Netflix', 'price': 10, 'stock': 3, 'duration': 30}]}
ACCESS = {'access': {'nome': 'Netflix', 'valor': 10, 'email': 'teste@example.test', 'senha': 'senha-teste'}}


class RemoteStockTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.cfg = patch.object(stock, 'CONFIG', root / 'settings' / 'estoque_api.json')
        self.db = patch.object(stock, 'JOURNAL', root / 'database' / 'reservas.sqlite3')
        self.cfg.start()
        self.db.start()
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(self.cfg.stop)
        self.addCleanup(self.db.stop)
        stock.salvar_config(key='secret-test-key', precos={'netflix': 25})
        self.http = patch.object(stock.requests, 'request')
        self.request = self.http.start()
        self.addCleanup(self.http.stop)
        self.request.side_effect = lambda method, *a, **kw: self.response(CATALOG if method == 'GET' else ACCESS)

    @staticmethod
    def response(data, status=200):
        return SimpleNamespace(status_code=status, json=lambda: data, text=json.dumps(data))

    def test_get_uses_key_and_never_reserves(self):
        self.assertEqual(stock.catalogo()[0]['quantidade'], 3)
        call = self.request.call_args
        self.assertEqual(call.args, ('GET', stock.URL))
        self.assertEqual(call.kwargs['headers'], {'X-Stock-Key': 'secret-test-key'})
        self.assertFalse(call.kwargs['allow_redirects'])

    def test_admin_diagnostic_includes_status_and_redacts_key(self):
        self.request.side_effect = None
        self.request.return_value = self.response({'error': 'unauthorized secret-test-key'}, 401)
        with self.assertRaises(stock.EstoqueAPIError) as raised:
            stock.catalogo()
        self.assertIn('HTTP 401', raised.exception.diagnostico)
        self.assertIn('unauthorized', raised.exception.diagnostico)
        self.assertNotIn('secret-test-key', raised.exception.diagnostico)
        self.assertNotIn('unauthorized', str(raised.exception))

    def test_network_diagnostics_do_not_echo_exception_secrets(self):
        for error, expected in [(requests.Timeout('secret-test-key'), 'Tempo limite'),
                                (requests.ConnectionError('secret-test-key'), 'DNS'),
                                (requests.exceptions.SSLError('secret-test-key'), 'TLS')]:
            self.request.side_effect = error
            with self.assertRaises(stock.EstoqueAPIError) as raised:
                stock.catalogo()
            self.assertIn(expected, raised.exception.diagnostico)
            self.assertNotIn('secret-test-key', raised.exception.diagnostico)

    def test_non_json_error_shows_real_body_with_key_hidden(self):
        self.request.side_effect = None
        self.request.return_value = SimpleNamespace(status_code=403, json=Mock(side_effect=ValueError()),
                                                    text='<html>Forbidden\nsecret-test-key</html>')
        with self.assertRaises(stock.EstoqueAPIError) as raised:
            stock.catalogo()
        self.assertIn('HTTP 403', raised.exception.diagnostico)
        self.assertIn('<html>Forbidden\n[CHAVE OCULTA]</html>', raised.exception.diagnostico)
        self.assertNotIn('secret-test-key', raised.exception.diagnostico)
        self.assertNotIn('saldo', raised.exception.diagnostico)

    def test_real_response_preserves_json_and_redacts_sensitive_fields(self):
        response = self.response({'error': 'blocked', 'request_id': 'abc', 'token': 'private-token', 'senha': 'private password'})
        detail = stock.detalhe_resposta(response, 'test-key')
        self.assertIn('"request_id": "abc"', detail)
        self.assertNotIn('private-token', detail)
        self.assertNotIn('private password', detail)

    def test_real_response_handles_empty_and_large_bodies(self):
        self.assertEqual(stock.detalhe_resposta(SimpleNamespace(text=''), 'key'), '[corpo vazio]')
        detail = stock.detalhe_resposta(SimpleNamespace(text='x' * 1600), 'key')
        self.assertTrue(detail.startswith('x' * 1500 + '\n'))
        self.assertIn('truncado', detail)

    def test_success_with_invalid_json_shows_real_body(self):
        self.request.side_effect = None
        self.request.return_value = SimpleNamespace(status_code=200, json=Mock(side_effect=ValueError()),
                                                    text='<html>Challenge</html>')
        with self.assertRaises(stock.EstoqueAPIError) as raised:
            stock.catalogo()
        self.assertIn('<html>Challenge</html>', raised.exception.diagnostico)

    def test_invalid_header_key_is_rejected_before_network(self):
        for key in ('key\nvalue', 'chave🔑'):
            with self.assertRaises(stock.EstoqueAPIError):
                stock.catalogo(key=key)
        self.request.assert_not_called()

    def test_admin_key_failure_shows_diagnostic_and_preserves_saved_key(self):
        from app import painel_estoque_api
        callbacks = []
        bot = Mock()
        bot.callback_query_handler.side_effect = lambda **kw: lambda fn: callbacks.append(fn) or fn
        api = SimpleNamespace(Admin=SimpleNamespace(verificar_admin=lambda _: False),
                              CredentialsChange=SimpleNamespace(id_dono=lambda: 1))
        with patch.dict(sys.modules, {'telebot.types': SimpleNamespace(InlineKeyboardMarkup=Mock(), InlineKeyboardButton=Mock())}):
            painel_estoque_api.registrar(bot, api)
        chat = SimpleNamespace(id=1, type='private')
        callbacks[0](SimpleNamespace(from_user=SimpleNamespace(id=1), id='c', data='stock_api_chave',
                                     message=SimpleNamespace(chat=chat)))
        handler, action, owner = bot.register_next_step_handler.call_args.args[1:]
        self.request.side_effect = None
        self.request.return_value = self.response({'error': 'unauthorized new-secret'}, 401)
        handler(SimpleNamespace(from_user=SimpleNamespace(id=1), chat=chat, text='new-secret', message_id=5), action, owner)
        self.assertEqual(stock.config()['key'], 'secret-test-key')
        messages = [call.args[1] for call in bot.send_message.call_args_list]
        self.assertTrue(any('HTTP 401' in message and 'unauthorized' in message for message in messages))
        self.assertFalse(any('new-secret' in message for message in messages))
        self.assertFalse(any('✅ Configuração salva.' in message for message in messages))

    def test_percentage_overrides_fixed_price_and_follows_api_cost(self):
        stock.definir_porcentagem('50%')
        self.assertEqual(stock.catalogo()[0]['valor'], 15)
        self.request.side_effect = None
        self.request.return_value = self.response({'products': [{'nome': 'Netflix', 'valor': 20, 'estoque': 1}]})
        self.assertEqual(stock.catalogo()[0]['valor'], 30)

    def test_percentage_rounding_and_reservation_price(self):
        stock.definir_porcentagem('12,55%')
        self.assertEqual(stock.catalogo()[0]['valor'], 11.26)
        self.assertEqual(stock.reservar('Netflix', 123, 'porcentagem')[1], 11.26)
        stock.definir_porcentagem('0')
        self.assertEqual(stock.catalogo()[0]['valor'], 10)

    def test_invalid_percentage_does_not_change_settings(self):
        before = stock.config()
        for value in ('-1', 'nan', 'inf', 'abc', '10001'):
            with self.assertRaises(ValueError):
                stock.definir_porcentagem(value)
        self.assertEqual(stock.config(), before)

    def test_missing_key_never_uses_local_stock(self):
        stock.salvar_config(key='')
        with self.assertRaises(stock.EstoqueAPIError):
            stock.catalogo()
        self.request.assert_not_called()

    def test_reserved_cost_does_not_replace_retail_price(self):
        result = stock.reservar('netflix', 123, 'pedido-1')
        self.assertEqual(result, ('Netflix', 25, 'teste@example.test', 'senha-teste', '', 30))
        post = self.request.call_args
        self.assertEqual(post.kwargs['json'], {'service': 'Netflix', 'buyer_id': '123', 'sale_id': 'pedido-1'})
        with stock.journal() as db:
            row = db.execute('SELECT status, access FROM reservas').fetchone()
        self.assertEqual(row[0], 'recebida')
        self.assertEqual(json.loads(row[1]), ACCESS)

    def test_timeout_is_durable_and_never_reposts(self):
        self.request.side_effect = [self.response(CATALOG), requests.Timeout('secret must not leak')]
        with self.assertRaises(stock.EstoqueAPIError) as raised:
            stock.reservar('Netflix', 123, 'pedido-timeout')
        self.assertNotIn('secret', str(raised.exception))
        with self.assertRaises(stock.EstoqueAPIError):
            stock.reservar('Netflix', 123, 'pedido-timeout')
        self.assertEqual(self.request.call_count, 2)
        self.assertEqual(stock.pendentes()[0][3], 'verificar')

    def test_parallel_duplicate_order_posts_once(self):
        def run(_):
            try:
                return stock.reservar('Netflix', 123, 'mesmo-pedido')
            except stock.EstoqueAPIError:
                return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(run, range(2)))
        self.assertEqual(sum(r is not None for r in results), 1)
        self.assertEqual(sum(c.args[0] == 'POST' for c in self.request.call_args_list), 1)

    def test_invalid_access_saved_for_reconciliation(self):
        self.request.side_effect = [self.response(CATALOG), self.response({'access': {'email': 'x'}})]
        with self.assertRaises(stock.EstoqueAPIError):
            stock.reservar('Netflix', 123, 'incompleto')
        with stock.journal() as db:
            row = db.execute('SELECT status, access FROM reservas').fetchone()
        self.assertEqual(row[0], 'verificar')
        self.assertIn('email', row[1])

    def test_supplier_rejection_refunds_customer(self):
        api = SimpleNamespace(InfoUser=SimpleNamespace(tirar_saldo=Mock(return_value=True), add_saldo=Mock()))
        self.request.side_effect = [self.response(CATALOG), self.response({}, 402)]
        with self.assertRaises(stock.EstoqueAPIError):
            stock.comprar(api, 'Netflix', 123, 'sem-saldo-raiz', 25)
        api.InfoUser.tirar_saldo.assert_called_once_with(123, 25)
        api.InfoUser.add_saldo.assert_called_once_with(123, 25)

    def test_customer_without_balance_does_not_reserve(self):
        api = SimpleNamespace(InfoUser=SimpleNamespace(tirar_saldo=Mock(return_value=False), add_saldo=Mock()))
        with self.assertRaises(stock.EstoqueAPIError):
            stock.comprar(api, 'Netflix', 123, 'sem-saldo-cliente', 25)
        self.request.assert_not_called()

    def test_out_of_stock_refunds_without_post(self):
        api = SimpleNamespace(InfoUser=SimpleNamespace(tirar_saldo=Mock(return_value=True), add_saldo=Mock()))
        self.request.return_value = self.response({'products': []})
        self.request.side_effect = None
        self.assertIsNone(stock.comprar(api, 'Netflix', 123, 'esgotado', 25))
        api.InfoUser.add_saldo.assert_called_once_with(123, 25)
        self.assertTrue(all(c.args[0] == 'GET' for c in self.request.call_args_list))

    def test_catalog_rejects_invalid_quantities_prices_and_unknown_shape(self):
        for payload in ({'unexpected': True}, {'products': [{'nome': 'X', 'valor': 1}]},
                        {'products': [{'nome': 'X', 'valor': 'nan', 'estoque': 1}]},
                        {'products': [{'nome': 'X', 'valor': 1, 'estoque': -1}]}):
            with self.subTest(payload=payload), self.assertRaises(stock.EstoqueAPIError):
                stock.normalizar(payload)

    def test_legacy_views_count_remote_units_without_credentials(self):
        # Carrega apenas a classe para não iniciar o bot nem tocar no banco real.
        source = (Path(stock.__file__).parent / 'central.py').read_text(encoding='utf-8')
        node = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name == 'ControleLogins')
        ns = {'html': html}
        exec(compile(ast.Module(body=[node], type_ignores=[]), 'central.py', 'exec'), ns)
        control = stock.criar_controle(ns['ControleLogins'])
        self.assertEqual(control.estoque_total(), 3)
        self.assertEqual(control.pegar_estoque('Netflix'), 3)
        self.assertEqual(control.pegar_info('Netflix')[1], 25)
        self.assertEqual(control.peek_primeiro_disponivel('Netflix')[2:4], ('', ''))
        self.assertEqual(len(control.pegar_servicos()), 3)
        with self.assertRaises(stock.EstoqueAPIError):
            control.zerar_estoque()

    def test_cart_partial_failure_charges_and_rewards_only_reserved_unit(self):
        source = (Path(stock.__file__).parent / 'bot.py').read_text(encoding='utf-8')
        node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'cb_cart_buy')
        node.decorator_list = []
        balance = [100.0]
        def debit(uid, amount):
            balance[0] -= amount
            return True
        def refund(uid, amount):
            balance[0] += amount
        api = SimpleNamespace(InfoUser=SimpleNamespace(tirar_saldo=debit, add_saldo=refund),
                              ControleLogins=SimpleNamespace(peek_primeiro_disponivel=lambda _: ('Netflix', 25, '', '', '', 30)))
        posts = []
        def http(method, *args, **kwargs):
            if method == 'GET':
                return self.response(CATALOG)
            posts.append(kwargs['json'])
            return self.response(ACCESS) if len(posts) == 1 else self.response({}, 402)
        self.request.side_effect = http
        ns = {'bot': Mock(), 'api': api, 'estoque_api': stock, 'user_carts': {123: {'Netflix': 2}},
              'user_cart_msgs': {}, '_cancel_cart_timer': Mock(), 'get_user_balance': lambda _: balance[0],
              'entregar': Mock(), 'sistema_cashback_vip': Mock()}
        exec(compile(ast.Module(body=[node], type_ignores=[]), 'cart', 'exec'), ns)
        event = SimpleNamespace(from_user=SimpleNamespace(id=123), id='callback',
                                message=SimpleNamespace(message_id=10, chat=SimpleNamespace(id=123)))
        modules = {'telebot.types': SimpleNamespace(InlineKeyboardMarkup=Mock(), InlineKeyboardButton=Mock()),
                   'app.Oferta_relampago': SimpleNamespace(verificar_preco=lambda _, price: price)}
        with patch.dict(sys.modules, modules):
            ns['cb_cart_buy'](event)
        self.assertEqual(balance[0], 75)
        self.assertEqual(ns['user_carts'][123], {'Netflix': 1})
        ns['entregar'].assert_called_once()
        ns['sistema_cashback_vip'].processar_compra_cashback.assert_called_once_with(ns['bot'], 123, 25)

    def test_admin_rejects_non_admin_and_rechecks_key_sender(self):
        from app import painel_estoque_api
        callbacks = []
        bot = Mock()
        bot.callback_query_handler.side_effect = lambda **kw: lambda fn: callbacks.append(fn) or fn
        api = SimpleNamespace(Admin=SimpleNamespace(verificar_admin=lambda _: False),
                              CredentialsChange=SimpleNamespace(id_dono=lambda: 1))
        types = SimpleNamespace(InlineKeyboardMarkup=Mock(), InlineKeyboardButton=Mock())
        with patch.dict(sys.modules, {'telebot.types': types}):
            painel_estoque_api.registrar(bot, api)
        event = SimpleNamespace(from_user=SimpleNamespace(id=2), id='c', data='stock_api_chave',
                                message=SimpleNamespace(chat=SimpleNamespace(id=2, type='private')))
        callbacks[0](event)
        bot.register_next_step_handler.assert_not_called()
        event.from_user.id = 1
        event.message.chat.id = 1
        callbacks[0](event)
        args = bot.register_next_step_handler.call_args.args
        handler, action, owner = args[1:]
        handler(SimpleNamespace(from_user=SimpleNamespace(id=2), chat=event.message.chat, text='stolen-key'), action, owner)
        self.assertEqual(stock.config()['key'], 'secret-test-key')
        self.request.assert_not_called()

    def test_promotion_partial_failure_delivers_reserved_unit_at_proportional_price(self):
        source = (Path(stock.__file__).parent / 'sistema_promocoes.py').read_text(encoding='utf-8')
        node = next(n for n in ast.walk(ast.parse(source)) if isinstance(n, ast.FunctionDef) and n.name == 'callback_comprar_promocao')
        node.decorator_list = []
        balance = [100.0]
        def debit(uid, amount):
            balance[0] = round(balance[0] - amount, 2)
            return True
        def refund(uid, amount):
            balance[0] = round(balance[0] + amount, 2)
        api = SimpleNamespace(InfoUser=SimpleNamespace(tirar_saldo=debit, add_saldo=refund, saldo=lambda _: balance[0]),
                              ControleLogins=SimpleNamespace(pegar_estoque=lambda _: 3))
        self.request.side_effect = [self.response(CATALOG), self.response(ACCESS),
                                    self.response(CATALOG), self.response({}, 402)]
        ns = {'bot': Mock(), 'api': api, 'estoque_api': stock, 'entregar_func': Mock(),
              'load_promos': lambda: {'Pacote': {'valor': 40.01, 'itens': {'Netflix': 2}}}}
        exec(compile(ast.Module(body=[node], type_ignores=[]), 'promotion', 'exec'), ns)
        event = SimpleNamespace(from_user=SimpleNamespace(id=123), id='callback', data='comprar_promocao Pacote',
                                message=SimpleNamespace(message_id=11, chat=SimpleNamespace(id=123)))
        ns['callback_comprar_promocao'](event)
        self.assertEqual(balance[0], 79.99)
        ns['entregar_func'].assert_called_once()
        self.assertEqual(ns['entregar_func'].call_args.args[2], 20.01)
        self.assertIn('Entregues 1 de 2', ns['bot'].send_message.call_args.args[1])


if __name__ == '__main__':
    unittest.main()
