# backup_manager.py
import os
import re
import gc
import time
import glob
import zipfile
import threading
from datetime import datetime
import json as _json_bk # Renomeado para evitar conflito com json global, se houver

BACKUP_DIR = os.getenv("BACKUP_DIR", "backups")
BACKUPS_TO_KEEP = 1 # Define quantos backups manter (1 = apenas o mais recente)
IGNORE_DIRS = {BACKUP_DIR, ".data_restore", ".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".idea", ".vscode", ".mypy_cache", "node_modules"}
IGNORE_FILE_PATTERNS = [r".*\.pyc$", r".*\.log$", r".*\.tmp$", r".*\.sqlite3-journal$"]
TELEGRAM_DOC_LIMIT = 53_500_000 # Limite de ~50MB para documentos no Telegram
# Limite total de tamanho para a pasta de backups (em bytes). Default ~2 GB.
MAX_BACKUP_SIZE_BYTES = int(os.getenv("MAX_BACKUP_SIZE_BYTES", str(2 * 1024 * 1024 * 1024)))  # 2 GiB

# ===== Persistência do estado de ativação (Enabled/Disabled) =====
BACKUP_STATE_FILE = os.getenv("BACKUP_STATE_FILE", os.path.join("settings", "backup_state.json"))

def _read_state() -> bool:
    """Lê o estado (ativado/desativado) do backup automático."""
    try:
        os.makedirs(os.path.dirname(BACKUP_STATE_FILE), exist_ok=True)
        if not os.path.exists(BACKUP_STATE_FILE):
            # Se o arquivo não existe, cria com 'enabled: true' como padrão
            with open(BACKUP_STATE_FILE, "w", encoding="utf-8") as f:
                f.write('{"enabled": true}')
            return True
        import json # Importa json localmente para evitar conflitos
        with open(BACKUP_STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return bool(data.get("enabled", True)) # Padrão é true se a chave não existir
    except Exception as e:
        print(f"[backup_state] Erro ao ler estado: {e}")
        return True # Retorna true como fallback seguro em caso de erro

def _write_state(enabled: bool):
    """Escreve o estado (ativado/desativado) do backup automático."""
    try:
        os.makedirs(os.path.dirname(BACKUP_STATE_FILE), exist_ok=True)
        import json # Importa json localmente
        with open(BACKUP_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({"enabled": bool(enabled)}, f, ensure_ascii=False, indent=2)
        print(f"[backup_state] Estado do backup automático salvo como: {'ATIVADO' if enabled else 'DESATIVADO'}")
    except Exception as _e:
        print(f"[backup_state] Erro ao salvar estado: {_e}")

def is_enabled() -> bool:
    """Verifica se o backup automático está ativado."""
    return _read_state()

def set_enabled(enabled: bool):
    """Define o estado (ativado/desativado) do backup automático."""
    _write_state(enabled)
    # A lógica de reagendamento foi movida para bot.py

# ===== Funções de Gerenciamento de Arquivos e Pastas =====

def _should_ignore(path: str) -> bool:
    """Verifica se um caminho deve ser ignorado no backup."""
    # Normaliza separadores de diretório
    path = path.replace("\\", "/")
    parts = path.split("/")
    # Ignora se qualquer parte do caminho está na lista de diretórios ignorados
    if any(p in IGNORE_DIRS for p in parts if p):
        return True
    # Ignora se o nome do arquivo corresponde a algum padrão ignorado
    filename = parts[-1]
    for pat in IGNORE_FILE_PATTERNS:
        if re.fullmatch(pat, filename):
            return True
    return False

def _zip_directory(base_dir: str, zip_path: str):
    """Cria um arquivo ZIP do diretório base, ignorando pastas/arquivos especificados."""
    base_dir = os.path.abspath(base_dir)
    print(f"[zip] Iniciando compressão de '{base_dir}' para '{zip_path}'")
    count_files = 0
    total_size = 0
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for root, dirs, files in os.walk(base_dir):
            # Modifica a lista 'dirs' in-place para não percorrer diretórios ignorados
            dirs[:] = [d for d in dirs if not _should_ignore(os.path.relpath(os.path.join(root, d), base_dir))]

            for f in files:
                file_path = os.path.join(root, f)
                # Calcula o caminho relativo para armazenar no ZIP
                arc_path = os.path.relpath(file_path, base_dir)

                # Pula o próprio arquivo ZIP que está sendo criado e arquivos ignorados
                if _should_ignore(arc_path) or os.path.abspath(file_path) == os.path.abspath(zip_path):
                    continue

                try:
                    zf.write(file_path, arcname=arc_path)
                    count_files += 1
                    total_size += os.path.getsize(file_path)
                except Exception as e:
                    print(f"[zip] Erro ao adicionar '{arc_path}': {e}")
    print(f"[zip] Compressão concluída: {count_files} arquivos adicionados, tamanho original total: {_human_mb(total_size)} MB.")


def _prune_old_backups():
    """Remove backups antigos, mantendo apenas BACKUPS_TO_KEEP (o mais recente)."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    # Lista todos os .zip no diretório de backup e ordena por nome (que inclui timestamp)
    zips = sorted(glob.glob(os.path.join(BACKUP_DIR, "*.zip")))

    # Se houver mais backups do que o permitido
    if len(zips) > BACKUPS_TO_KEEP:
        # Calcula quantos precisam ser removidos
        to_remove_count = len(zips) - BACKUPS_TO_KEEP
        # Pega os mais antigos (todos exceto os últimos BACKUPS_TO_KEEP)
        backups_to_remove = zips[:to_remove_count]
        print(f"[prune] Encontrados {len(zips)} backups. Removendo {len(backups_to_remove)} mais antigo(s)...")
        removed_count = 0
        for old_backup in backups_to_remove:
            try:
                os.remove(old_backup)
                print(f"[prune] Backup antigo removido: {os.path.basename(old_backup)}")
                removed_count += 1
            except Exception as e:
                print(f"[prune] Erro ao remover backup antigo '{old_backup}': {e}")
        print(f"[prune] {removed_count} backup(s) antigo(s) removido(s).")
    else:
        print(f"[prune] {len(zips)} backup(s) encontrado(s). Nenhum backup antigo para remover (limite: {BACKUPS_TO_KEEP}).")

def _total_backup_size() -> int:
    """Calcula o tamanho total ocupado pelos arquivos .zip na pasta de backup."""
    try:
        total = 0
        # Soma o tamanho de cada arquivo .zip encontrado
        for p in glob.glob(os.path.join(BACKUP_DIR, "*.zip")):
            try:
                total += os.path.getsize(p)
            except Exception:
                pass # Ignora arquivos que não puderam ser acessados
        return total
    except Exception as e:
        print(f"[size_check] Erro ao calcular tamanho total dos backups: {e}")
        return 0

def _prune_by_size():
    """Remove backups mais antigos se o tamanho total da pasta exceder MAX_BACKUP_SIZE_BYTES."""
    try:
        # Lista os arquivos .zip ordenados por data de modificação (mais antigo primeiro)
        files = sorted(glob.glob(os.path.join(BACKUP_DIR, "*.zip")), key=os.path.getmtime)
        # Calcula o tamanho total atual
        total = sum(os.path.getsize(f) for f in files)
        print(f"[prune_size] Tamanho total atual: {_human_mb(total)} MB. Limite: {_human_mb(MAX_BACKUP_SIZE_BYTES)} MB.")

        # Enquanto o total exceder o limite e ainda houver arquivos para remover
        while total > MAX_BACKUP_SIZE_BYTES and files:
            # Pega o arquivo mais antigo da lista
            oldest = files.pop(0)
            try:
                size_old = os.path.getsize(oldest)
                os.remove(oldest)
                total -= size_old # Atualiza o tamanho total
                print(f"[prune_size] Removido backup mais antigo '{os.path.basename(oldest)}' ({_human_mb(size_old)} MB) para respeitar limite de espaço.")
            except Exception as e:
                print(f"[prune_size] Erro ao remover backup antigo '{oldest}': {e}")
                # Se não conseguir remover, para o loop para evitar ficar preso
                break
        if total <= MAX_BACKUP_SIZE_BYTES:
            print(f"[prune_size] Tamanho total da pasta de backups ({_human_mb(total)} MB) está dentro do limite.")

    except Exception as e:
        print(f"[prune_size] Erro inesperado durante a poda por tamanho: {e}")

def create_backup_zip(project_root: str = ".", label: str = "") -> str:
    """Cria um backup ZIP do projeto no diretório BACKUP_DIR."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # Limpa o label para usar no nome do arquivo
    safe_label = re.sub(r"[^a-zA-Z0-9_-]+", "-", label or "auto")
    zip_name = f"backup_{safe_label}_{timestamp}.zip"
    zip_path = os.path.join(BACKUP_DIR, zip_name)
    _zip_directory(project_root, zip_path) # Chama a função que faz a compressão
    return os.path.abspath(zip_path) # Retorna o caminho absoluto do ZIP criado

# ===== Envio para Admin e Divisão de Arquivos Grandes =====

def _split_file(file_path: str, part_size: int) -> list[str]:
    """Divide um arquivo grande em partes menores."""
    parts = []
    base = os.path.basename(file_path)
    dirn = os.path.dirname(file_path)
    part_num = 1
    try:
        with open(file_path, "rb") as src:
            while True:
                chunk = src.read(part_size)
                if not chunk: # Fim do arquivo
                    break
                part_name = f"{base}.part{part_num:02d}" # Ex: backup.zip.part01
                part_path = os.path.join(dirn, part_name)
                with open(part_path, "wb") as dst:
                    dst.write(chunk)
                parts.append(part_path)
                part_num += 1
        print(f"[split] Arquivo '{base}' dividido em {len(parts)} partes.")
    except Exception as e:
        print(f"[split] Erro ao dividir arquivo '{file_path}': {e}")
        # Tenta remover partes criadas parcialmente em caso de erro
        for part_file in parts:
            try: os.remove(part_file)
            except: pass
        return [] # Retorna lista vazia em caso de erro
    return parts

def _human_mb(nbytes: int) -> float:
    """Converte bytes para megabytes (arredondado)."""
    try:
        return round(nbytes / (1024 * 1024), 2)
    except Exception:
        return 0.0

# ===== Controle de mensagens de backup antigas (evitar poluir o chat) =====
BACKUP_MSG_STATE_FILE = os.getenv("BACKUP_MSG_STATE_FILE", os.path.join("settings", "backup_last_msgs.json"))

def _load_last_backup_msgs() -> dict:
    """Lê os ids das últimas mensagens de backup enviadas, por admin."""
    try:
        os.makedirs(os.path.dirname(BACKUP_MSG_STATE_FILE), exist_ok=True)
        if not os.path.exists(BACKUP_MSG_STATE_FILE):
            return {}
        with open(BACKUP_MSG_STATE_FILE, "r", encoding="utf-8") as f:
            return _json_bk.load(f)
    except Exception as e:
        print(f"[backup_msgs] Erro ao ler estado de mensagens: {e}")
        return {}

def _save_last_backup_msgs(data: dict):
    """Salva os ids das últimas mensagens de backup enviadas, por admin."""
    try:
        os.makedirs(os.path.dirname(BACKUP_MSG_STATE_FILE), exist_ok=True)
        with open(BACKUP_MSG_STATE_FILE, "w", encoding="utf-8") as f:
            _json_bk.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[backup_msgs] Erro ao salvar estado de mensagens: {e}")

def _delete_previous_backup_messages(bot, admin_id: int):
    """Apaga a(s) mensagem(ns) do backup anterior enviado a este admin, para não poluir o chat."""
    data = _load_last_backup_msgs()
    old_ids = data.get(str(admin_id), [])
    for msg_id in old_ids:
        try:
            bot.delete_message(admin_id, msg_id)
            print(f"[backup_msgs] Mensagem antiga de backup {msg_id} apagada.")
        except Exception as e:
            print(f"[backup_msgs] Não foi possível apagar mensagem antiga {msg_id} (pode já ter sido apagada): {e}")

def _store_backup_messages(admin_id: int, message_ids: list):
    """Salva os ids das mensagens do backup atual, substituindo o registro anterior."""
    data = _load_last_backup_msgs()
    data[str(admin_id)] = [mid for mid in message_ids if mid]
    _save_last_backup_msgs(data)


def send_backup_to_admin(bot, admin_id: int, zip_path: str):
    """Envia o backup ao admin, dividindo se necessário, e apaga o backup anterior do chat."""
    # Apaga a(s) mensagem(ns) do backup anterior antes de enviar o novo
    try:
        _delete_previous_backup_messages(bot, admin_id)
    except Exception as e:
        print(f"[send] Erro ao tentar apagar backups antigos do chat: {e}")

    try:
        size = os.path.getsize(zip_path)
        print(f"[send] Tamanho do backup: {_human_mb(size)} MB.")
    except Exception as e:
        print(f"[send] Erro ao obter tamanho do backup '{zip_path}': {e}")
        try: bot.send_message(admin_id, f"⚠️ Erro ao acessar o arquivo de backup: {e}")
        except: pass
        return

    # Tenta enviar diretamente se for menor que o limite do Telegram
    if 0 < size < TELEGRAM_DOC_LIMIT:
        print(f"[send] Enviando arquivo único para admin {admin_id}...")
        caption = (
            f"🧩 *Backup Concluído*\n"
            f"Arquivo: `{os.path.basename(zip_path)}`\n"
            f"Tamanho: ~{_human_mb(size)} MB"
        )
        try:
            with open(zip_path, "rb") as f:
                sent_msg = bot.send_document(admin_id, f, caption=caption, parse_mode="Markdown")
            print(f"[send] Arquivo único enviado com sucesso.")
            try:
                _store_backup_messages(admin_id, [sent_msg.message_id])
            except Exception as e:
                print(f"[send] Erro ao salvar id da mensagem de backup: {e}")
        except Exception as e:
            print(f"[send] Erro ao enviar arquivo único: {e}")
            try: bot.send_message(admin_id, f"⚠️ Falha ao enviar o arquivo de backup: {e}")
            except: pass
        return

    # Se o arquivo for muito grande, divide e envia em partes
    if size >= TELEGRAM_DOC_LIMIT:
        print(f"[send] Backup excede o limite ({_human_mb(TELEGRAM_DOC_LIMIT)} MB). Dividindo em partes...")
        try: bot.send_message(admin_id, f"🧩 O arquivo de backup é maior que o limite de {_human_mb(TELEGRAM_DOC_LIMIT)} MB. Enviando em partes...")
        except: pass

        # Define o tamanho de cada parte um pouco abaixo do limite
        part_size = TELEGRAM_DOC_LIMIT - 1_048_576 # Deixa 1MB de margem
        parts = _split_file(zip_path, part_size)
        parts_paths_to_clean = list(parts) # Copia lista para limpeza posterior

        if not parts:
            print("[send] Falha ao dividir o arquivo.")
            try: bot.send_message(admin_id, "⚠️ Falha ao dividir o arquivo de backup em partes.")
            except: pass
            return

        total_parts = len(parts)
        print(f"[send] Enviando {total_parts} partes para admin {admin_id}...")
        success_parts = 0
        sent_part_msg_ids = []
        for i, part_path in enumerate(parts, start=1):
            caption = (
                f"🧩 *Backup (Parte {i}/{total_parts})*\n"
                f"Arquivo Original: `{os.path.basename(zip_path)}`\n"
                f"Parte: `{os.path.basename(part_path)}`\n"
                f"Tamanho desta parte: ~{_human_mb(os.path.getsize(part_path))} MB"
            )
            try:
                with open(part_path, "rb") as f:
                    sent_msg = bot.send_document(admin_id, f, caption=caption, parse_mode="Markdown")
                print(f"[send] Parte {i}/{total_parts} enviada.")
                sent_part_msg_ids.append(sent_msg.message_id)
                success_parts += 1
                time.sleep(1) # Pequena pausa entre envios
            except Exception as e:
                print(f"[send] Erro ao enviar parte {i}/{total_parts} ('{part_path}'): {e}")
                try: bot.send_message(admin_id, f"⚠️ Falha ao enviar a parte {i}/{total_parts}: {e}")
                except: pass
                # Se uma parte falhar, pode ser melhor parar ou tentar novamente depois
                # Por simplicidade, continuamos tentando enviar as outras

        if sent_part_msg_ids:
            try:
                _store_backup_messages(admin_id, sent_part_msg_ids)
            except Exception as e:
                print(f"[send] Erro ao salvar ids das mensagens de backup (partes): {e}")

        # Envia instruções de como juntar as partes
        if success_parts > 0:
            print("[send] Enviando instruções para juntar as partes.")
            try:
                # Instruções adaptadas para usar o nome base do arquivo ZIP
                zip_basename = os.path.basename(zip_path)
                instr = (
                    f"📦 *Como Juntar as Partes do Backup ({zip_basename})*:\n\n"
                    f"1. Baixe todas as partes (`.part01`, `.part02`, etc.) para a *mesma pasta* no seu computador.\n"
                    f"2. Abra o terminal ou prompt de comando nessa pasta.\n"
                    f"3. Execute *um* dos comandos abaixo (dependendo do seu sistema):\n\n"
                    f"   <b>Windows (CMD):</b>\n"
                    f"   <code>copy /b \"{zip_basename}.part*\" \"{zip_basename}\"</code>\n\n"
                    f"   <b>Linux / macOS (Terminal):</b>\n"
                    f"   <code>cat \"{zip_basename}.part\"* > \"{zip_basename}\"</code>\n\n"
                    f"4. Isso criará o arquivo `{zip_basename}` completo. Você pode então abrir este arquivo ZIP normalmente.\n\n"
                    f"<i>Certifique-se de que os nomes das partes estejam corretos (ex: .part01, .part02...).</i>"
                )
                bot.send_message(admin_id, instr, parse_mode='HTML')
            except Exception as e:
                print(f"[send] Erro ao enviar instruções: {e}")
        else:
             print("[send] Nenhuma parte foi enviada com sucesso.")
             try: bot.send_message(admin_id, "⚠️ Nenhuma parte do backup pôde ser enviada.")
             except: pass

        # Limpa os arquivos de partes criados
        print("[send] Limpando arquivos de partes temporários...")
        cleaned_parts = 0
        for part_file in parts_paths_to_clean:
            try:
                os.remove(part_file)
                cleaned_parts += 1
            except Exception as e:
                print(f"[send] Erro ao limpar parte '{part_file}': {e}")
        print(f"[send] {cleaned_parts} arquivos de partes removidos.")

    elif size <= 0:
        print("[send] Arquivo de backup vazio ou inválido.")
        try: bot.send_message(admin_id, "⚠️ O arquivo de backup gerado está vazio ou inválido.")
        except: pass


# ===== Upload para Google Drive (Opcional) =====
def _try_upload_gdrive(zip_path: str) -> str | None:
    """Tenta fazer upload do backup para o Google Drive se gdrive_uploader estiver disponível."""
    try:
        # Tenta importar a função de upload
        from app.gdrive_uploader import upload_to_drive
        print("[gdrive] Módulo gdrive_uploader encontrado. Tentando upload...")
        try:
            # Chama a função de upload
            link = upload_to_drive(zip_path)
            if link:
                print(f"[gdrive] Upload para Google Drive bem-sucedido: {link}")
                return link
            else:
                print("[gdrive] Upload para Google Drive falhou (sem link retornado).")
                return None
        except Exception as e:
            print(f"[gdrive] Erro durante o upload para Google Drive: {e}")
            return None
    except ImportError:
        # Se o módulo não existe, simplesmente ignora
        print("[gdrive] Módulo gdrive_uploader não encontrado. Upload para Google Drive pulado.")
        return None
    except Exception as e:
        # Captura outros erros inesperados relacionados ao GDrive
        print(f"[gdrive] Erro inesperado relacionado ao Google Drive: {e}")
        return None


# ===== Execução Principal do Backup (síncrona e assíncrona) =====

def _job_run_backup(bot=None, admin_id: int | None = None, label: str = "auto"):
    """
    Executa o processo de backup: cria o ZIP, tenta upload no GDrive,
    envia via Telegram se necessário, e faz a poda de backups antigos.
    Recebe 'bot' e 'admin_id' como argumentos diretos.
    """
    print(f"[backup] _job_run_backup iniciado - label: {label}, admin_id fornecido: {admin_id is not None}")
    zip_path = None # Inicializa para garantir que a variável exista no finally
    try:
        start = time.time()
        print(f"[backup] Criando backup ZIP...")
        zip_path = create_backup_zip(".", label=label) # Cria o backup
        took = round(time.time() - start, 2)
        print(f"[backup] Backup criado em {took}s: {zip_path}")

        # Tentar upload no Google Drive
        drive_link = _try_upload_gdrive(zip_path)

        # Se bot e admin_id foram passados, envia notificações/arquivos
        if bot and admin_id:
            try:
                print(f"[backup] Enviando notificação inicial para admin {admin_id}")
                bot.send_message(admin_id, f"🗂️ Backup ({label}) concluído em {took}s.")
            except Exception as e:
                print(f"[backup] Erro ao enviar notificação inicial: {e}")

            if drive_link:
                # Se o upload pro Drive funcionou, envia o link
                print(f"[backup] Upload para Drive realizado: {drive_link}")
                bot.send_message(admin_id, f"☁️ Link do Backup no Google Drive:\n{drive_link}", disable_web_page_preview=True)
            else:
                # Se não conseguiu fazer upload ou a função não existe, envia pelo Telegram
                print(f"[backup] Enviando backup por Telegram para {admin_id}")
                send_backup_to_admin(bot, admin_id, zip_path)
                bot.send_message(admin_id, f"✅ Backup enviado via Telegram.")
        else:
            # Se bot ou admin_id não foram fornecidos (ex: execução manual sem contexto)
            print(f"[backup] Bot ou admin_id não fornecidos para notificação/envio.")
            if drive_link:
                print(f"[backup] Link do Drive (sem envio): {drive_link}")

        # Após envio/upload, realiza poda de arquivos antigos
        try:
            _prune_old_backups()
            _prune_by_size()
            print("[backup] Poda de backups antigos concluída.")
        except Exception as _pe:
            print(f"[backup] Erro durante a poda de backups: {_pe}")

        return zip_path # Retorna o caminho do arquivo zip criado

    except Exception as e:
        print(f"[backup] Erro CRÍTICO em _job_run_backup: {e}")
        # Tentar notificar o admin sobre o erro, se possível
        if bot and admin_id:
            try:
                bot.send_message(admin_id, f"⚠️ Erro CRÍTICO ao executar o backup ({label}):\n`{e}`", parse_mode="Markdown")
            except Exception as notify_err:
                print(f"[backup] Falha ao notificar admin sobre o erro crítico: {notify_err}")
        # Não re-levanta a exceção aqui para não quebrar a thread do scheduler
    finally:
        # Limpeza de memória
        gc.collect()
        print(f"[backup] _job_run_backup finalizado para label: {label}")


def run_backup_async(bot=None, admin_id: int | None = None, label: str = "auto"):
    """Inicia a execução do backup em uma thread separada."""
    print(f"[async] Disparando thread de backup - label: {label}, admin_id: {admin_id}")
    th = threading.Thread(
        target=_job_run_backup,
        kwargs={"bot": bot, "admin_id": admin_id, "label": label},
        daemon=True # Define como daemon para não impedir o bot de sair
    )
    th.start()
    return th # Retorna a thread (opcional, pode ser usado para join() se necessário)


# ===== Configuração do Intervalo de Backup (lido/escrito em settings.json) =====

SETTINGS_FILE = os.getenv("SETTINGS_FILE", os.path.join(os.getcwd(), "settings.json"))

def _load_settings():
    """Carrega as configurações do arquivo settings.json."""
    try:
        # Garante que o diretório exista
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return _json_bk.load(f)
    except FileNotFoundError:
        print("[settings] Arquivo settings.json não encontrado, usando defaults.")
        return {} # Retorna dicionário vazio se o arquivo não existir
    except _json_bk.JSONDecodeError as e:
        print(f"[settings] Erro ao decodificar settings.json: {e}. Usando defaults.")
        return {} # Retorna dicionário vazio se o JSON for inválido
    except Exception as e:
        print(f"[settings] Erro inesperado ao carregar settings.json: {e}. Usando defaults.")
        return {} # Fallback geral

def _save_settings(data: dict):
    """Salva as configurações no arquivo settings.json."""
    try:
        # Garante que o diretório exista
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            _json_bk.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as _e:
        print(f"[settings] Erro ao salvar settings.json: {_e}")

def get_backup_interval_minutes() -> int:
    """Obtém o intervalo de backup em minutos a partir das configurações."""
    cfg = _load_settings()
    try:
        # Tenta ler o valor, usa 360 (6 horas) como padrão
        m = int(cfg.get("backup_interval_minutes", 360))
    except (ValueError, TypeError):
        m = 360 # Fallback se o valor não for um número
    # Garante que o valor esteja dentro dos limites (1 min a 24h)
    m = max(1, min(24*60, m))
    return m

def set_backup_interval_minutes(minutes: int) -> int:
    """Define o intervalo de backup em minutos no settings.json e retorna o valor validado."""
    try:
        minutes = int(minutes)
    except (ValueError, TypeError):
        minutes = 360 # Default 6h se o valor for inválido
    # Garante que o valor esteja entre 1 minuto e 24 horas
    minutes = max(1, min(24*60, minutes))
    cfg = _load_settings()
    cfg["backup_interval_minutes"] = minutes
    _save_settings(cfg)
    print(f"[backup] Intervalo de backup definido para {minutes} minutos.")
    # A lógica de reagendamento foi movida para bot.py
    return minutes # Retorna o valor efetivamente salvo

def _humanize_minutes(m: int) -> str:
    """Converte minutos para um formato legível (ex: 60 -> "1h", 90 -> "90min")."""
    m = int(m) # Garante que é inteiro
    if m < 1: m = 1 # Mínimo de 1 minuto

    if m >= 60:
        hours = m // 60
        remaining_minutes = m % 60
        if remaining_minutes == 0:
            return f"{hours}h" # Ex: 1h, 2h
        else:
            return f"{hours}h {remaining_minutes}min" # Ex: 1h 30min
    else:
        return f"{m}min" # Ex: 30min, 45min

# --- Fim do backup_manager.py ---
