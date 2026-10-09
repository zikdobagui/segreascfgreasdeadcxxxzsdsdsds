"""Estoque remoto. Nunca usa acessos.json como fallback nem repete POST incerto."""
import html
import json
import math
import sqlite3
import threading
from functools import wraps
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / 'settings' / 'estoque_api.json'
JOURNAL = ROOT / 'database' / 'reservas_api.sqlite3'
URL = 'https://vendasdoramon.squareweb.app/api/stock'
LOCK = threading.RLock()
PURCHASE_LOCK = threading.RLock()


def serializar(bot):
    """Impede que dois handlers debitem simultaneamente o mesmo saldo."""
    def decorator(fn):
        @wraps(fn)
        def wrapped(event, *args, **kwargs):
            with PURCHASE_LOCK:
                try:
                    return fn(event, *args, **kwargs)
                except EstoqueAPIError as exc:
                    bot.send_message(event.from_user.id, str(exc))
        return wrapped
    return decorator


def comprar(api, servico, buyer_id, sale_id, preco):
    """Separa custo do fornecedor e preço do cliente; estorna em falha."""
    with PURCHASE_LOCK:
        price = round(float(preco), 2)
        if not math.isfinite(price) or price < 0:
            raise EstoqueAPIError('Preço inválido.')
        if not api.InfoUser.tirar_saldo(buyer_id, price):
            raise EstoqueAPIError('Saldo insuficiente para concluir a compra.')
        try:
            result = reservar(servico, buyer_id, sale_id)
        except Exception:
            api.InfoUser.add_saldo(buyer_id, price)
            raise
        if result is None:
            api.InfoUser.add_saldo(buyer_id, price)
            return None
        return (result[0], price, *result[2:])


class EstoqueAPIError(RuntimeError):
    pass


def config():
    try:
        return json.loads(CONFIG.read_text(encoding='utf-8'))
    except FileNotFoundError:
        return {}


def salvar_config(**changes):
    with LOCK:
        data = config()
        data.update(changes)
        CONFIG.parent.mkdir(parents=True, exist_ok=True)
        tmp = CONFIG.with_suffix('.tmp')
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        tmp.replace(CONFIG)


def request(method, path='', key=None, **kwargs):
    key = key if key is not None else config().get('key', '')
    if not key:
        raise EstoqueAPIError('Configure a chave em /admin → API de estoque.')
    try:
        response = requests.request(method, URL + path, headers={'X-Stock-Key': key},
                                    timeout=(5, 25), allow_redirects=False, **kwargs)
    except requests.RequestException:
        raise EstoqueAPIError('API indisponível. Consulte o suporte antes de repetir a compra.') from None
    if response.status_code != 200 and response.status_code != 201:
        reasons = {401: 'Chave da API inválida.', 403: 'API bloqueada: verifique chave e saldo no bot raiz.',
                   402: 'Saldo insuficiente no bot raiz.', 409: 'Reserva recusada ou estoque indisponível.'}
        raise EstoqueAPIError(reasons.get(response.status_code, 'API recusou a operação. Consulte o suporte.'))
    try:
        return response.json()
    except ValueError:
        raise EstoqueAPIError('Resposta inválida da API. Consulte o suporte.') from None


def normalizar(payload):
    """Aceita catálogos agregados PT/EN; campos desconhecidos falham fechados."""
    rows = payload
    if isinstance(rows, dict):
        for field in ('products', 'stock', 'services', 'produtos', 'acessos', 'data'):
            if field in rows:
                rows = rows[field]
                break
    if isinstance(rows, dict):
        # Alguns fornecedores agrupam o catálogo por nome do serviço.
        rows = [dict(value, nome=name) for name, value in rows.items() if isinstance(value, dict)]
        if not rows:
            raise EstoqueAPIError('Formato do catálogo não reconhecido.')
    if not isinstance(rows, list):
        raise EstoqueAPIError('Formato do catálogo não reconhecido.')
    result = []
    for row in rows:
        try:
            name = row.get('nome', row.get('service', row.get('name')))
            price = float(row.get('valor', row.get('price', row.get('cost', row.get('base_price')))))
            quantity = row.get('estoque', row.get('quantidade', row.get('quantity', row.get('stock', row.get('count', row.get('available'))))))
            if quantity is None and row.get('email') and row.get('senha'):
                quantity = 1
            if not isinstance(name, str) or not name.strip() or not math.isfinite(price) or price < 0:
                raise ValueError()
            if isinstance(quantity, bool) or int(quantity) != float(quantity) or int(quantity) < 0:
                raise ValueError()
            days = row.get('duracao', row.get('duration', row.get('days')))
            result.append({'nome': name, 'custo': price, 'quantidade': int(quantity),
                           'descricao': str(row.get('descricao', row.get('description', '')) or ''),
                           'duracao': int(days) if days is not None else None})
        except (AttributeError, TypeError, ValueError, OverflowError):
            raise EstoqueAPIError('Produto com preço ou quantidade inválidos na API.') from None
    return result


def definir_porcentagem(value):
    try:
        percent = Decimal(str(value).strip().removesuffix('%').strip().replace(',', '.'))
        if not percent.is_finite() or percent < 0 or percent > 10000:
            raise ValueError()
    except (InvalidOperation, ValueError):
        raise ValueError('Informe uma porcentagem entre 0 e 10000. Exemplo: 50 ou 12,5%.') from None
    salvar_config(modo_preco='porcentagem', porcentagem_lucro=str(percent))


def catalogo(key=None):
    rows = normalizar(request('GET', key=key))
    cfg = config()
    prices = cfg.get('precos', {})
    for row in rows:
        if cfg.get('modo_preco') == 'porcentagem':
            percent = Decimal(str(cfg.get('porcentagem_lucro', '0')))
            row['valor'] = float((Decimal(str(row['custo'])) * (1 + percent / 100)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        else:
            row['valor'] = float(prices.get(row['nome'].casefold(), row['custo']))
        row['duracao'] = row['duracao'] or int(cfg.get('duracao_padrao', 30))
    return rows


@contextmanager
def journal():
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(JOURNAL, timeout=30)
    try:
        db.execute('CREATE TABLE IF NOT EXISTS reservas (sale_id TEXT PRIMARY KEY, buyer_id TEXT, service TEXT, status TEXT, access TEXT, erro TEXT)')
        with db:
            yield db
    finally:
        db.close()


def pendentes():
    with journal() as db:
        return db.execute("SELECT sale_id, buyer_id, service, status FROM reservas WHERE status != 'recebida'").fetchall()


def reservar(servico, buyer_id, sale_id):
    if not buyer_id or not sale_id:
        raise EstoqueAPIError('Compra sem identificação. Contate o suporte.')
    # Registro durável ANTES do POST; mesmo timeout/reinício não compra outra conta.
    with LOCK, journal() as db:
        if db.execute('SELECT 1 FROM reservas WHERE sale_id=?', (sale_id,)).fetchone():
            raise EstoqueAPIError('Pedido já processado ou pendente. Consulte o suporte.')
        product = next((r for r in catalogo() if r['nome'].casefold() == servico.casefold() and r['quantidade'] > 0), None)
        if product is None:
            return None
        db.execute('INSERT INTO reservas VALUES (?, ?, ?, ?, NULL, NULL)',
                   (sale_id, str(buyer_id), product['nome'], 'pendente'))
        db.commit()
        try:
            payload = request('POST', '/reserve', json={'service': product['nome'], 'buyer_id': str(buyer_id), 'sale_id': str(sale_id)})
            # Guarda a resposta antes de validar para permitir recuperação pelo suporte.
            db.execute('UPDATE reservas SET access=? WHERE sale_id=?', (json.dumps(payload, ensure_ascii=False), sale_id))
            db.commit()
            access = payload.get('access')
            if not isinstance(access, dict) or not access.get('email') or not access.get('senha'):
                raise EstoqueAPIError('Reserva retornou acesso incompleto. Consulte o suporte.')
            if access.get('nome', product['nome']).casefold() != product['nome'].casefold():
                raise EstoqueAPIError('Reserva retornou outro produto. Consulte o suporte.')
            result = (product['nome'], product['valor'], access['email'], access['senha'],
                      access.get('descricao') or product['descricao'], access.get('duracao') or product['duracao'])
            db.execute("UPDATE reservas SET status='recebida' WHERE sale_id=?", (sale_id,))
            db.commit()
            return result
        except Exception:
            db.execute("UPDATE reservas SET status='verificar', erro='Conferir reserva no fornecedor antes de tentar novamente' WHERE sale_id=?", (sale_id,))
            db.commit()
            raise


def criar_controle(base):
    class ControleRemoto(base):
        remoto = True

        @staticmethod
        def _load_acessos():
            # Compatibilidade com telas legadas: uma entrada de metadados por unidade.
            # Nunca contém credenciais de login, só entregues por /reserve.
            return {'acessos': [dict(p, quantidade=1, estoque=1, email='', senha='')
                                for p in catalogo() for _ in range(p['quantidade'])]}

        @staticmethod
        def _save_acessos(data):
            raise EstoqueAPIError('O estoque é gerenciado no bot raiz. Esta API só permite consultar e reservar.')

        @classmethod
        def pegar_primeiro_disponivel(cls, servico, buyer_id=None, sale_id=None):
            return reservar(servico, buyer_id, sale_id)

        @classmethod
        def mudar_valor_por_nome(cls, nome, novo_valor):
            price = float(novo_valor)
            if not math.isfinite(price) or price < 0:
                return False
            if not any(p['nome'].casefold() == nome.casefold() for p in catalogo()):
                return False
            with LOCK:
                prices = config().get('precos', {})
                prices[nome.casefold()] = price
                salvar_config(precos=prices, modo_preco='fixo')
            return True

        @classmethod
        def mudar_valor_de_todos(cls, valor):
            price = float(valor)
            if not math.isfinite(price) or price < 0:
                return False
            rows = catalogo()
            with LOCK:
                prices = config().get('precos', {})
                prices.update({p['nome'].casefold(): price for p in rows})
                salvar_config(precos=prices, modo_preco='fixo')
            return bool(rows)

        @classmethod
        def entregar_acesso(cls, nome, email):
            raise EstoqueAPIError('Use a reserva da API para receber o acesso.')

        pegar_info_entrega = entregar_acesso

    return ControleRemoto
