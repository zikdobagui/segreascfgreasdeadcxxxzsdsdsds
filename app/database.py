"""
database.py — backend SQLite (drop-in replacement)

Mantém EXATAMENTE as mesmas funções e assinaturas do database.py original
(save_user_data, load_user_data, initialize_user, update_user_balance,
is_user_banned, add_purchase, add_payment, add_saldo, add_pagamento,
get_user_balance, get_top_users, update_usernames, get_top_depositors,
get_top_recent_depositors, get_top_products_last_30_days,
check_pagamento_ja_processado, registrar_indicacao, get_user_indicacoes,
gerar_link_indicacao, verificar_sistema_afiliados_ativo,
get_valor_por_indicacao, get_top_indicadores) para que nenhum outro
módulo do bot precise ser alterado.

O que mudou nesta versão (fase 2 — compras/pagamentos fora do blob JSON):
- Antes, `compras` e `pagamentos` viviam DENTRO do JSON da coluna `data` da
  tabela `users`, então cada nova compra/pagamento reescrevia o blob
  INTEIRO (que só cresce). Um usuário com muito histórico deixava a escrita
  dele mais pesada — e como as escritas são serializadas (_write_lock),
  isso também atrasava a fila de escrita de TODOS os outros usuários.
- Agora `compras` e `pagamentos` são a fonte de verdade: cada item novo
  vira 1 INSERT (barato, não redimensiona nada). O blob salvo em
  `users.data` NÃO contém mais essas duas listas — elas são reconstruídas
  em `load_user_data()` a partir das tabelas, na mesma ordem/formato de
  antes, então `user_data["compras"]` e `user_data["pagamentos"]`
  continuam existindo exatamente como o resto do bot espera.
- A detecção de "o que é novo" é por POSIÇÃO: comparamos o tamanho da
  lista recebida em save_user_data() com quantas linhas já existem na
  tabela pra aquele usuário, e inserimos só a sobra (o "rabo" da lista).
  Isso pressupõe que compras/pagamentos só recebem `append` (nunca são
  reordenados/removidos) — é o que todo o código atual faz.
"""

import os
import json
import re
import sqlite3
import threading
from datetime import datetime, timedelta

DB_DIR = "database"
DB_FILE = os.path.join(DB_DIR, "bot.db")

_write_lock = threading.RLock()
_local = threading.local()


def _connect():
    """Retorna uma conexão SQLite por thread (reutilizada entre chamadas)."""
    conn = getattr(_local, "conn", None)
    if conn is None:
        os.makedirs(DB_DIR, exist_ok=True)
        conn = sqlite3.connect(DB_FILE, timeout=30, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("PRAGMA foreign_keys=ON")
        _local.conn = conn
    return conn


def _add_column_if_missing(conn, table, column, coltype):
    try:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e):
            raise


def _init_schema():
    conn = _connect()
    with _write_lock:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                banned TEXT DEFAULT 'False',
                saldo REAL DEFAULT 0.0,
                total_pagos REAL DEFAULT 0.0,
                total_compras INTEGER DEFAULT 0,
                total_ganho_indicacoes REAL DEFAULT 0.0,
                indicado_por INTEGER,
                data TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_users_saldo ON users(saldo);
            CREATE INDEX IF NOT EXISTS idx_users_total_pagos ON users(total_pagos);
            CREATE INDEX IF NOT EXISTS idx_users_total_ganho ON users(total_ganho_indicacoes);

            CREATE TABLE IF NOT EXISTS pagamentos (
                id_pagamento TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                valor REAL NOT NULL,
                data TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_pagamentos_user ON pagamentos(user_id);
            CREATE INDEX IF NOT EXISTS idx_pagamentos_data ON pagamentos(data);

            CREATE TABLE IF NOT EXISTS compras (
                rowid_ai INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                produto TEXT,
                data TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_compras_user ON compras(user_id);
            CREATE INDEX IF NOT EXISTS idx_compras_data ON compras(data);
            CREATE INDEX IF NOT EXISTS idx_compras_produto ON compras(produto);

            CREATE TABLE IF NOT EXISTS indicacoes (
                rowid_ai INTEGER PRIMARY KEY AUTOINCREMENT,
                indicador_id INTEGER NOT NULL,
                indicado_id INTEGER NOT NULL,
                valor_ganho REAL,
                data TEXT,
                UNIQUE(indicador_id, indicado_id)
            );
            CREATE INDEX IF NOT EXISTS idx_indicacoes_indicador ON indicacoes(indicador_id);

            CREATE TABLE IF NOT EXISTS movimentacoes_saldo (
                rowid_ai INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                tipo TEXT NOT NULL,
                valor REAL NOT NULL,
                saldo_anterior REAL,
                saldo_novo REAL,
                admin_id INTEGER,
                motivo TEXT,
                data TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_movsaldo_user ON movimentacoes_saldo(user_id);
            CREATE INDEX IF NOT EXISTS idx_movsaldo_data ON movimentacoes_saldo(data);
            """
        )
        # Colunas novas pra compras/pagamentos carregarem o registro
        # completo (antes só existiam dentro do JSON). data_raw guarda a
        # string original "dd/mm/aaaa HH:MM:SS" pra não mudar o que o bot
        # já mostra (ex.: fazer_txt_do_historico); `data` continua em ISO
        # pra ordenação/filtros por período.
        _add_column_if_missing(conn, "compras", "valor", "REAL")
        _add_column_if_missing(conn, "compras", "email", "TEXT")
        _add_column_if_missing(conn, "compras", "senha", "TEXT")
        _add_column_if_missing(conn, "compras", "data_raw", "TEXT")
        _add_column_if_missing(conn, "pagamentos", "data_raw", "TEXT")
        conn.commit()


_init_schema()

# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

# Casa "dd/mm/aaaa" + qualquer separador (" as ", " às ", " Ã s ", etc,
# incluindo variações de encoding) + "HH:MM:SS". O bug original usava
# strptime com "%d/%m/%Y %H:%M:%S" direto na string, que nunca batia por
# causa da palavra "as"/"às" no meio — então a conversão pra ISO nunca
# funcionava e o filtro de "últimos N dias" comparava texto no formato
# errado (ex.: "31/10/2024..." >= "2026-07-15..." dá True por comparação
# de string, mesmo sendo uma data de mais de um ano atrás).
_DATE_RE = re.compile(r"(\d{2}/\d{2}/\d{4}).*?(\d{2}:\d{2}:\d{2})")


def _parse_date_safe(date_str):
    if not date_str:
        return None
    match = _DATE_RE.search(date_str)
    if not match:
        return None
    try:
        return datetime.strptime(f"{match.group(1)} {match.group(2)}", "%d/%m/%Y %H:%M:%S")
    except (ValueError, TypeError):
        return None


def _to_iso(date_str):
    """Converte 'dd/mm/aaaa HH:MM:SS' -> 'aaaa-mm-dd HH:MM:SS' para permitir
    comparação/ordenação correta em SQL (string compare). Se já vier em ISO,
    ou não for parseável, devolve como veio (fallback seguro)."""
    dt = _parse_date_safe(date_str)
    if dt:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return date_str or datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _sync_compras(conn, user_id, compras_list):
    """Insere só as compras que ainda não estão na tabela (o 'rabo' da
    lista, por posição). Não faz nada se não houver itens novos."""
    if not compras_list:
        return
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM compras WHERE user_id = ?", (user_id,)
    ).fetchone()
    already = row["n"] if row else 0
    novas = compras_list[already:]
    for c in novas:
        data_raw = c.get("data")
        conn.execute(
            """INSERT INTO compras (user_id, produto, valor, email, senha, data, data_raw)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                c.get("servico") or c.get("produto"),
                c.get("valor"),
                c.get("email"),
                c.get("senha"),
                _to_iso(data_raw),
                data_raw,
            ),
        )


def _sync_pagamentos(conn, user_id, pagamentos_list):
    """Mesma ideia de _sync_compras, mas usando INSERT OR IGNORE por
    segurança extra (id_pagamento já é PRIMARY KEY, então duplicata nunca
    quebra nada mesmo que o corte por posição erre)."""
    if not pagamentos_list:
        return
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM pagamentos WHERE user_id = ?", (user_id,)
    ).fetchone()
    already = row["n"] if row else 0
    novos = pagamentos_list[already:]
    for p in novos:
        id_pagamento = p.get("id_pagamento") or p.get("id")
        if not id_pagamento:
            continue
        data_raw = p.get("data")
        conn.execute(
            """INSERT OR IGNORE INTO pagamentos (id_pagamento, user_id, valor, data, data_raw)
               VALUES (?, ?, ?, ?, ?)""",
            (str(id_pagamento), user_id, float(p.get("valor", 0) or 0), _to_iso(data_raw), data_raw),
        )


def _load_compras(conn, user_id):
    rows = conn.execute(
        "SELECT produto, valor, email, senha, data, data_raw FROM compras "
        "WHERE user_id = ? ORDER BY rowid_ai",
        (user_id,),
    ).fetchall()
    return [
        {
            "servico": r["produto"],
            "valor": r["valor"],
            "email": r["email"],
            "senha": r["senha"],
            "data": r["data_raw"] or r["data"],
        }
        for r in rows
    ]


def _load_pagamentos(conn, user_id):
    rows = conn.execute(
        "SELECT id_pagamento, valor, data, data_raw FROM pagamentos "
        "WHERE user_id = ? ORDER BY rowid",
        (user_id,),
    ).fetchall()
    return [
        {
            "id_pagamento": r["id_pagamento"],
            "valor": r["valor"],
            "data": r["data_raw"] or r["data"],
        }
        for r in rows
    ]


def _row_to_userdata(conn, row):
    if row is None:
        return None
    data = json.loads(row["data"])
    # Garante que os campos indexados fiquem sempre coerentes com o blob
    data["id"] = row["user_id"]
    # compras/pagamentos não moram mais no blob — remonta a partir das tabelas
    data["compras"] = _load_compras(conn, row["user_id"])
    data["pagamentos"] = _load_pagamentos(conn, row["user_id"])
    return data


# ---------------------------------------------------------------------------
# API pública (mesmos nomes/assinaturas do database.py original)
# ---------------------------------------------------------------------------

def save_user_data(user_id, user_data):
    user_id = int(user_id)
    conn = _connect()
    with _write_lock:
        # 1) sincroniza só o que for novo em compras/pagamentos (INSERTs
        #    baratos, O(itens novos) — não O(histórico inteiro))
        _sync_compras(conn, user_id, user_data.get("compras", []))
        _sync_pagamentos(conn, user_id, user_data.get("pagamentos", []))

        # 2) grava o blob "core" SEM compras/pagamentos — ele deixa de
        #    crescer junto com o histórico do usuário
        slim_data = {k: v for k, v in user_data.items() if k not in ("compras", "pagamentos")}
        payload = json.dumps(slim_data, ensure_ascii=False)

        conn.execute(
            """
            INSERT INTO users (user_id, username, banned, saldo, total_pagos,
                                total_compras, total_ganho_indicacoes, indicado_por, data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username,
                banned=excluded.banned,
                saldo=excluded.saldo,
                total_pagos=excluded.total_pagos,
                total_compras=excluded.total_compras,
                total_ganho_indicacoes=excluded.total_ganho_indicacoes,
                indicado_por=excluded.indicado_por,
                data=excluded.data
            """,
            (
                user_id,
                user_data.get("username", f"User{user_id}"),
                str(user_data.get("banned", "False")),
                float(user_data.get("saldo", 0.0) or 0.0),
                float(user_data.get("total_pagos", 0.0) or 0.0),
                int(user_data.get("total_compras", 0) or 0),
                float(user_data.get("total_ganho_indicacoes", 0.0) or 0.0),
                user_data.get("indicado_por"),
                payload,
            ),
        )
        conn.commit()


def load_user_data(user_id):
    conn = _connect()
    row = conn.execute(
        "SELECT * FROM users WHERE user_id = ?", (int(user_id),)
    ).fetchone()
    return _row_to_userdata(conn, row)


def initialize_user(user_id, username=None):
    user_data = {
        "id": user_id,
        "username": username if username else f"User{user_id}",
        "banned": "False",
        "afiliado_por": 0,
        "saldo": 0.0,
        "gift_redeemed": 0.0,
        "total_compras": 0,
        "compras": [],
        "total_pagos": 0.0,
        "pagamentos": [],
        "pontos_indicado": 0,
        "afiliacoes": 0,
        "afiliados": [],
        "indicado_por": None,
        "indicacoes": [],
        "total_ganho_indicacoes": 0.0,
    }
    save_user_data(user_id, user_data)
    return user_data


def update_user_balance(user_id, value):
    user_data = load_user_data(user_id)
    if user_data:
        user_data["saldo"] = float(user_data.get("saldo", 0.0)) + float(value)
        save_user_data(user_id, user_data)
        return True
    return False


def is_user_banned(user_id):
    user_data = load_user_data(user_id)
    if user_data:
        return user_data.get("banned", "False") == "True"
    return False


def add_purchase(user_id, purchase):
    user_data = load_user_data(user_id)
    if user_data:
        user_data.setdefault("compras", []).append(purchase)
        user_data["total_compras"] = user_data.get("total_compras", 0) + 1
        save_user_data(user_id, user_data)
        # (o INSERT em `compras` já aconteceu dentro de save_user_data ->
        # _sync_compras; não duplica mais aqui)


def add_payment(user_id, payment):
    user_data = load_user_data(user_id)
    if user_data:
        user_data.setdefault("pagamentos", []).append(payment)
        user_data["total_pagos"] = float(user_data.get("total_pagos", 0.0)) + float(payment["valor"])
        save_user_data(user_id, user_data)
        # (o INSERT em `pagamentos` já aconteceu dentro de save_user_data ->
        # _sync_pagamentos; não duplica mais aqui)


def add_saldo(user_id, saldo):
    user_data = load_user_data(user_id)
    if user_data:
        user_data["saldo"] = float(user_data.get("saldo", 0.0)) + float(saldo)
        save_user_data(user_id, user_data)


def add_pagamento(user_id, valor, id_pagamento):
    user_data = load_user_data(user_id)
    if user_data is None:
        user_data = initialize_user(user_id)

    user_data.setdefault("total_pagos", 0.0)
    user_data.setdefault("pagamentos", [])

    data_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    user_data["total_pagos"] = float(user_data["total_pagos"]) + float(valor)
    user_data["pagamentos"].append(
        {"valor": valor, "id_pagamento": id_pagamento, "data": data_str}
    )
    save_user_data(user_id, user_data)


def get_user_balance(user_id):
    user_data = load_user_data(user_id)
    if user_data:
        return user_data.get("saldo", 0.0)
    return 0.0


def get_all_user_ids():
    """Retorna todos os user_id cadastrados no banco (substitui os.listdir('database/users'))."""
    conn = _connect()
    rows = conn.execute("SELECT user_id FROM users").fetchall()
    return [r["user_id"] for r in rows]


def get_top_users(top_n=20):
    conn = _connect()
    rows = conn.execute(
        "SELECT user_id, username, saldo FROM users ORDER BY saldo DESC LIMIT ?",
        (top_n,),
    ).fetchall()
    return [
        {"username": r["username"], "id": r["user_id"], "saldo": r["saldo"]}
        for r in rows
    ]


def update_usernames():
    """Normaliza usernames que começam com '@' (mantido por compatibilidade)."""
    conn = _connect()
    rows = conn.execute("SELECT user_id, username FROM users").fetchall()
    with _write_lock:
        for r in rows:
            uname = r["username"]
            if isinstance(uname, str) and uname.startswith("@"):
                novo = uname.lstrip("@")
                conn.execute(
                    "UPDATE users SET username=? WHERE user_id=?", (novo, r["user_id"])
                )
        conn.commit()


def get_top_depositors(top_n=10):
    conn = _connect()
    rows = conn.execute(
        "SELECT user_id, username, total_pagos FROM users WHERE total_pagos > 0 "
        "ORDER BY total_pagos DESC LIMIT ?",
        (top_n,),
    ).fetchall()
    return [
        {"username": r["username"], "id": r["user_id"], "total_pagos": r["total_pagos"]}
        for r in rows
    ]


def get_top_recent_depositors(top_n=10, days=30):
    conn = _connect()
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    rows = conn.execute(
        """
        SELECT p.user_id AS user_id, COALESCE(u.username, 'User'||p.user_id) AS username,
               SUM(p.valor) AS total_recent_pagos
        FROM pagamentos p
        LEFT JOIN users u ON u.user_id = p.user_id
        WHERE p.data >= ?
        GROUP BY p.user_id
        ORDER BY total_recent_pagos DESC
        LIMIT ?
        """,
        (cutoff, top_n),
    ).fetchall()
    return [
        {
            "username": r["username"],
            "id": r["user_id"],
            "total_recent_pagos": r["total_recent_pagos"],
        }
        for r in rows
    ]


def get_top_products_last_30_days(top_n=10, days=30):
    conn = _connect()
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    rows = conn.execute(
        """
        SELECT produto, COUNT(*) AS vendas
        FROM compras
        WHERE data >= ? AND produto IS NOT NULL
        GROUP BY produto
        ORDER BY vendas DESC
        LIMIT ?
        """,
        (cutoff, top_n),
    ).fetchall()
    return [{"produto": r["produto"], "vendas": r["vendas"]} for r in rows]


def check_pagamento_ja_processado(id_pagamento):
    conn = _connect()
    row = conn.execute(
        "SELECT 1 FROM pagamentos WHERE id_pagamento = ? LIMIT 1", (str(id_pagamento),)
    ).fetchone()
    return row is not None


def registrar_indicacao(indicador_id, indicado_id, valor_ganho):
    indicador_data = load_user_data(indicador_id)
    if not indicador_data:
        indicador_data = initialize_user(indicador_id)

    indicado_data = load_user_data(indicado_id)
    if not indicado_data:
        indicado_data = initialize_user(indicado_id)

    indicador_data.setdefault("indicacoes", [])
    indicador_data.setdefault("total_ganho_indicacoes", 0.0)

    ja_contabilizado = any(
        item.get("user_id") == indicado_id for item in indicador_data["indicacoes"]
    )
    if not ja_contabilizado:
        nova_indicacao = {
            "user_id": indicado_id,
            "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "valor_ganho": float(valor_ganho),
        }
        indicador_data["indicacoes"].append(nova_indicacao)
        indicador_data["total_ganho_indicacoes"] = float(
            indicador_data.get("total_ganho_indicacoes", 0.0)
        ) + float(valor_ganho)
        indicador_data["saldo"] = float(indicador_data.get("saldo", 0.0)) + float(valor_ganho)
        save_user_data(indicador_id, indicador_data)

        conn = _connect()
        with _write_lock:
            conn.execute(
                "INSERT OR IGNORE INTO indicacoes (indicador_id, indicado_id, valor_ganho, data) "
                "VALUES (?, ?, ?, ?)",
                (
                    int(indicador_id),
                    int(indicado_id),
                    float(valor_ganho),
                    _to_iso(nova_indicacao["data"]),
                ),
            )
            conn.commit()

    if not indicado_data.get("indicado_por"):
        indicado_data["indicado_por"] = indicador_id
        save_user_data(indicado_id, indicado_data)

    return True


def get_user_indicacoes(user_id):
    user_data = load_user_data(user_id)
    if user_data:
        return {
            "indicacoes": user_data.get("indicacoes", []),
            "total_indicacoes": len(user_data.get("indicacoes", [])),
            "total_ganho": user_data.get("total_ganho_indicacoes", 0.0),
        }
    return {"indicacoes": [], "total_indicacoes": 0, "total_ganho": 0.0}


def gerar_link_indicacao(user_id):
    try:
        with open("settings/credenciais.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        user_bot = config.get("user_bot", "rlfornecedor_bot")
        return f"https://t.me/{user_bot}?start=ref_{user_id}"
    except Exception:
        return f"https://t.me/rlfornecedor_bot?start=ref_{user_id}"


def verificar_sistema_afiliados_ativo():
    try:
        with open("settings/credenciais.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        return config.get("afiliados_sistema", {}).get("ativo", False)
    except Exception:
        return False


def get_valor_por_indicacao():
    try:
        with open("settings/credenciais.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        return float(config.get("afiliados_sistema", {}).get("valor_por_indicacao", 5.0))
    except Exception:
        return 5.0


def cleanup_old_records(days=60):
    """Apaga de `compras` e `pagamentos` os registros com mais de `days`
    dias. Não toca em saldo, total_pagos, total_compras nem em nenhum
    outro campo do usuário — esses contadores continuam intactos, é só
    o histórico linha-a-linha que é limpo.

    Cuidado: `pagamentos` também é usado por check_pagamento_ja_processado
    para não creditar o mesmo PIX duas vezes. Apagar um registro velho
    faz esse ID "esquecer" que já foi processado — só é seguro se o
    gateway nunca reenviar uma confirmação depois de `days` dias.
    """
    conn = _connect()
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    with _write_lock:
        cur_compras = conn.execute("DELETE FROM compras WHERE data < ?", (cutoff,))
        cur_pagamentos = conn.execute("DELETE FROM pagamentos WHERE data < ?", (cutoff,))
        conn.commit()
        return {
            "compras_removidas": cur_compras.rowcount,
            "pagamentos_removidos": cur_pagamentos.rowcount,
            "cutoff": cutoff,
        }


# ---------------------------------------------------------------------------
# Gerenciamento de saldos (painel admin — histórico, relatórios e saldo parado)
# ---------------------------------------------------------------------------

def registrar_movimentacao_saldo(user_id, tipo, valor, saldo_anterior, saldo_novo,
                                  admin_id=None, motivo=None):
    """Grava no log um evento de alteração de saldo feito pelo admin.
    tipo: 'adicao', 'remocao' ou 'ajuste'.
    valor: quanto foi movimentado (para 'ajuste', é a diferença aplicada)."""
    conn = _connect()
    data_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _write_lock:
        conn.execute(
            """INSERT INTO movimentacoes_saldo
               (user_id, tipo, valor, saldo_anterior, saldo_novo, admin_id, motivo, data)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (int(user_id), tipo, float(valor), float(saldo_anterior or 0.0),
             float(saldo_novo or 0.0), admin_id, motivo, data_str),
        )
        conn.commit()


def get_movimentacoes_saldo(user_id=None, limit=50, offset=0):
    """Retorna o histórico de movimentações (mais recentes primeiro).
    Se user_id for informado, filtra só as daquele cliente."""
    conn = _connect()
    if user_id is not None:
        rows = conn.execute(
            """SELECT * FROM movimentacoes_saldo WHERE user_id=?
               ORDER BY rowid_ai DESC LIMIT ? OFFSET ?""",
            (int(user_id), limit, offset),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT * FROM movimentacoes_saldo
               ORDER BY rowid_ai DESC LIMIT ? OFFSET ?""",
            (limit, offset),
        ).fetchall()
    return [dict(r) for r in rows]


def count_movimentacoes_saldo(user_id=None):
    conn = _connect()
    if user_id is not None:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM movimentacoes_saldo WHERE user_id=?", (int(user_id),)
        ).fetchone()
    else:
        row = conn.execute("SELECT COUNT(*) AS n FROM movimentacoes_saldo").fetchone()
    return row["n"] if row else 0


def get_clientes_com_saldo(limit=None, offset=0, saldo_minimo=0.01):
    """Lista clientes com saldo > saldo_minimo, do maior para o menor."""
    conn = _connect()
    sql = ("SELECT user_id, username, saldo FROM users WHERE saldo >= ? "
           "ORDER BY saldo DESC")
    params = [saldo_minimo]
    if limit is not None:
        sql += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
    rows = conn.execute(sql, params).fetchall()
    return [{"id": r["user_id"], "username": r["username"], "saldo": r["saldo"]} for r in rows]


def count_clientes_com_saldo(saldo_minimo=0.01):
    conn = _connect()
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM users WHERE saldo >= ?", (saldo_minimo,)
    ).fetchone()
    return row["n"] if row else 0


def get_relatorio_saldo_geral():
    """Agrega estatísticas gerais sobre os saldos de todos os clientes,
    para o botão '📊 Relatório geral' do painel de saldos."""
    conn = _connect()
    agg = conn.execute(
        """SELECT COUNT(*) AS qtd, COALESCE(SUM(saldo),0) AS total,
                  COALESCE(AVG(saldo),0) AS media
           FROM users WHERE saldo >= 0.01"""
    ).fetchone()
    maior = conn.execute(
        "SELECT user_id, username, saldo FROM users ORDER BY saldo DESC LIMIT 1"
    ).fetchone()
    hoje = datetime.now().strftime("%Y-%m-%d")
    mov_hoje = conn.execute(
        """SELECT tipo, COALESCE(SUM(valor),0) AS total, COUNT(*) AS qtd
           FROM movimentacoes_saldo WHERE substr(data,1,10)=? GROUP BY tipo""",
        (hoje,),
    ).fetchall()
    entradas_hoje = sum(r["total"] for r in mov_hoje if r["tipo"] == "adicao")
    saidas_hoje = sum(r["total"] for r in mov_hoje if r["tipo"] == "remocao")
    qtd_mov_hoje = sum(r["qtd"] for r in mov_hoje)
    historico_total = conn.execute(
        """SELECT tipo, COALESCE(SUM(valor),0) AS total FROM movimentacoes_saldo
           GROUP BY tipo"""
    ).fetchall()
    total_adicionado = sum(r["total"] for r in historico_total if r["tipo"] == "adicao")
    total_removido = sum(r["total"] for r in historico_total if r["tipo"] == "remocao")
    return {
        "qtd_clientes_com_saldo": agg["qtd"] or 0,
        "total_em_saldo": agg["total"] or 0.0,
        "saldo_medio": agg["media"] or 0.0,
        "maior_saldo_id": maior["user_id"] if maior else None,
        "maior_saldo_username": maior["username"] if maior else None,
        "maior_saldo_valor": maior["saldo"] if maior else 0.0,
        "movimentacoes_hoje": qtd_mov_hoje,
        "entradas_hoje": entradas_hoje,
        "saidas_hoje": saidas_hoje,
        "total_adicionado_historico": total_adicionado,
        "total_removido_historico": total_removido,
    }


def get_clientes_saldo_parado(dias=30, saldo_minimo=0.01, limit=200):
    """Clientes com saldo (>= saldo_minimo) cuja última atividade (compra,
    pagamento/recarga ou movimentação de admin) foi há mais de `dias` dias,
    ou que nunca tiveram nenhuma atividade registrada."""
    conn = _connect()
    cutoff = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d %H:%M:%S")
    rows = conn.execute(
        """
        SELECT id, username, saldo, ultima_atividade FROM (
            SELECT u.user_id AS id, u.username AS username, u.saldo AS saldo,
                   MAX(COALESCE(c.ultima, ''), COALESCE(p.ultima, ''), COALESCE(m.ultima, '')) AS ultima_atividade
            FROM users u
            LEFT JOIN (SELECT user_id, MAX(data) AS ultima FROM compras GROUP BY user_id) c
                   ON c.user_id = u.user_id
            LEFT JOIN (SELECT user_id, MAX(data) AS ultima FROM pagamentos GROUP BY user_id) p
                   ON p.user_id = u.user_id
            LEFT JOIN (SELECT user_id, MAX(data) AS ultima FROM movimentacoes_saldo GROUP BY user_id) m
                   ON m.user_id = u.user_id
            WHERE u.saldo >= ?
        ) sub
        WHERE (ultima_atividade = '' OR ultima_atividade < ?)
        ORDER BY saldo DESC
        LIMIT ?
        """,
        (saldo_minimo, cutoff, limit),
    ).fetchall()
    return [
        {
            "id": r["id"],
            "username": r["username"],
            "saldo": r["saldo"],
            "ultima_atividade": r["ultima_atividade"] or None,
        }
        for r in rows
    ]


def get_top_indicadores(top_n=10):
    conn = _connect()
    rows = conn.execute(
        """
        SELECT indicador_id, COUNT(*) AS total_indicacoes, SUM(valor_ganho) AS total_ganho
        FROM indicacoes
        GROUP BY indicador_id
        ORDER BY total_indicacoes DESC
        LIMIT ?
        """,
        (top_n,),
    ).fetchall()
    result = []
    for r in rows:
        urow = conn.execute(
            "SELECT username FROM users WHERE user_id=?", (r["indicador_id"],)
        ).fetchone()
        username = urow["username"] if urow else f"User{r['indicador_id']}"
        result.append(
            {
                "username": username,
                "id": r["indicador_id"],
                "total_indicacoes": r["total_indicacoes"],
                "total_ganho": r["total_ganho"] or 0.0,
            }
        )
    return result
