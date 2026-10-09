"""Restauração offline: nunca importar módulos que abrem os bancos neste arquivo."""
import json
import os
from pathlib import Path
import shutil
import sqlite3
import stat
import uuid
import zipfile

FOLDERS = ("database", "textos", "data")
MAX_ZIP_BYTES = 20_000_000
MAX_EXPANDED_BYTES = 200_000_000
MAX_FILES = 10_000
RESTART_CODE = 75
STATE_DIR = ".data_restore"


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    with temp.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def discard(root):
    work = Path(root).resolve() / STATE_DIR
    if (work / "pending.json").exists() or (work / "journal.json").exists():
        raise ValueError("Já existe uma restauração confirmada. Aguarde o reinício.")
    candidate = work / "candidate"
    if candidate.exists():
        shutil.rmtree(candidate)


def _validate_data(candidate):
    database = candidate / "database" / "bot.db"
    if not database.is_file():
        raise ValueError("O ZIP precisa conter database/bot.db.")
    files = [p for p in candidate.rglob("*") if p.is_file()]
    for path in files:
        if path.suffix.lower() == ".json":
            try:
                json.loads(path.read_text(encoding="utf-8-sig"))
            except (ValueError, UnicodeError) as exc:
                raise ValueError(f"JSON inválido: {path.relative_to(candidate)}") from exc
        if path.name.endswith(("-wal", "-shm", "-journal")):
            base = path.with_name(path.name.rsplit("-", 1)[0])
            if not base.is_file():
                raise ValueError("Arquivo auxiliar SQLite sem o banco correspondente.")
    for path in files:
        if not path.exists() or path.name.endswith(("-wal", "-shm", "-journal")):
            continue
        with path.open("rb") as stream:
            is_sqlite = stream.read(16) == b"SQLite format 3\x00"
        if path.suffix.lower() not in (".db", ".sqlite", ".sqlite3") and not is_sqlite:
            continue
        if not is_sqlite:
            raise ValueError(f"Banco SQLite inválido: {path.name}")
        # Reconstrói SHM e incorpora o WAL do ZIP, somente na cópia isolada.
        path.with_name(path.name + "-shm").unlink(missing_ok=True)
        conn = sqlite3.connect(str(path), timeout=5)
        try:
            if conn.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
                raise ValueError(f"Banco corrompido: {path.name}")
            if path == database:
                columns = {r[1] for r in conn.execute("PRAGMA table_info(users)")}
                if not {"user_id", "data", "saldo"}.issubset(columns):
                    raise ValueError("bot.db não possui a tabela de usuários esperada.")
            if conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()[0] != 0:
                raise ValueError(f"Não foi possível consolidar o banco {path.name}.")
            conn.execute("PRAGMA journal_mode=DELETE")
        finally:
            conn.close()


def prepare(root, zip_path):
    """Extrai/valida em staging; não modifica nenhum dado em uso."""
    root = Path(root).resolve()
    if Path(zip_path).stat().st_size > MAX_ZIP_BYTES:
        raise ValueError("O ZIP deve ter no máximo 20 MB.")
    discard(root)
    candidate = root / STATE_DIR / "candidate"
    candidate.mkdir(parents=True)
    try:
        with zipfile.ZipFile(zip_path) as archive:
            entries = archive.infolist()
            if not entries or len(entries) > MAX_FILES:
                raise ValueError("ZIP vazio ou com mais de 10.000 entradas.")
            if sum(i.file_size for i in entries) > MAX_EXPANDED_BYTES:
                raise ValueError("O conteúdo descompactado excede 200 MB.")
            seen, folders = set(), set()
            total = count = 0
            for entry in entries:
                name = entry.orig_filename
                parts = name.rstrip("/").split("/")
                mode = entry.external_attr >> 16
                if ("\\" in name or "\x00" in name or any(p in ("", ".", "..") for p in parts)
                        or any(":" in p or p.endswith((".", " ")) for p in parts)
                        or parts[0] not in FOLDERS
                        or stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR)
                        or entry.flag_bits & 1):
                    raise ValueError("ZIP contém caminho não permitido, link ou arquivo criptografado.")
                if len(parts) == 1 and not entry.is_dir():
                    raise ValueError("database, textos e data precisam ser pastas.")
                key = "/".join(parts).casefold()
                if key in seen:
                    raise ValueError("ZIP contém caminhos duplicados.")
                seen.add(key)
                folders.add(parts[0])
                target = candidate.joinpath(*parts)
                if entry.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(entry) as source, target.open("xb") as dest:
                    while chunk := source.read(1024 * 1024):
                        total += len(chunk)
                        if total > MAX_EXPANDED_BYTES:
                            raise ValueError("O conteúdo descompactado excede 200 MB.")
                        dest.write(chunk)
                count += 1
            if folders != set(FOLDERS):
                raise ValueError("Inclua as três pastas na raiz do ZIP: database, textos e data.")
        _validate_data(candidate)
        return {"files": count, "bytes": total}
    except Exception:
        discard(root)
        raise


def queue(root, chat_id):
    work = Path(root).resolve() / STATE_DIR
    if (work / "pending.json").exists() or (work / "journal.json").exists():
        raise ValueError("Já existe uma restauração em andamento.")
    if not all((work / "candidate" / name).is_dir() for name in FOLDERS):
        raise ValueError("Envie e valide um ZIP antes de confirmar.")
    _write_json(work / "pending.json", {"id": uuid.uuid4().hex, "chat_id": int(chat_id)})


def _rollback(root, record):
    work = root / STATE_DIR
    backup = work / "backups" / record["id"]
    rejected = backup / "rejected"
    rejected.mkdir(parents=True, exist_ok=True)
    for name in FOLDERS:
        live, old = root / name, backup / name
        # Se já foi revertido, old não existe e rejected/name existe.
        if old.exists():
            if live.exists():
                os.replace(live, rejected / name)
            os.replace(old, live)
        elif not record["existed"][name] and live.exists():
            os.replace(live, rejected / name)
    _write_json(work / "result.json", {
        "chat_id": record["chat_id"], "ok": False,
        "backup": str(backup.relative_to(root)),
    })
    (work / "pending.json").unlink(missing_ok=True)
    (work / "journal.json").unlink()


def apply_pending(root):
    """Chamado exclusivamente pelo launcher, sem processo do bot em execução."""
    root = Path(root).resolve()
    work = root / STATE_DIR
    journal = work / "journal.json"
    if journal.exists():
        _rollback(root, _read_json(journal))
        return
    pending = work / "pending.json"
    if not pending.exists():
        return
    record = _read_json(pending)
    candidate = work / "candidate"
    # Valida novamente após o processo antigo fechar todas as conexões.
    try:
        _validate_data(candidate)
        for name in FOLDERS:
            if (root / name).is_symlink() or not (candidate / name).is_dir():
                raise ValueError("Pastas inválidas para restauração.")
        record["existed"] = {name: (root / name).exists() for name in FOLDERS}
        backup = work / "backups" / record["id"]
        backup.mkdir(parents=True)
        _write_json(journal, record)
        for name in FOLDERS:
            if record["existed"][name]:
                os.replace(root / name, backup / name)
            os.replace(candidate / name, root / name)
        _write_json(work / "result.json", {
            "chat_id": record["chat_id"], "ok": True,
            "backup": str(backup.relative_to(root)),
        })
        pending.unlink()
        journal.unlink()
    except Exception:
        if journal.exists():
            _rollback(root, record)
        else:
            _write_json(work / "result.json", {
                "chat_id": record["chat_id"], "ok": False, "backup": None,
            })
            pending.unlink(missing_ok=True)
        # Se o rollback falhar, a exceção impede a inicialização com dados parciais.
