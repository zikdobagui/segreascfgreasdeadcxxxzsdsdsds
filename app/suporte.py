"""Rotinas agrupadas de suporte."""

# ==================== LOGGER ====================
import logging
import os
from datetime import datetime

# Configura o diretório de logs
os.makedirs('logs', exist_ok=True)

# Configura o logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/bot_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

def log_info(message):
    """Registra uma mensagem de informação."""
    logging.info(message)

def log_error(message):
    """Registra uma mensagem de erro."""
    logging.error(message)

def log_warning(message):
    """Registra uma mensagem de aviso."""
    logging.warning(message)

# Cria um logger para ser importado em outros módulos
logger = logging.getLogger(__name__)

# ==================== SISTEMA_ENCERRAMENTO ====================
"""Encerramento seguro do processo e handlers globais de erro/sinal."""
import sys
import signal
import traceback


def safe_exit(reason="manual"):
    try:
        print(f"[EXIT] Encerrando processo: {reason}")
        sys.stdout.flush()
        sys.stderr.flush()
    except Exception:
        pass
    import os as _os
    _os._exit(0)


def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
    """Handler para exceções não capturadas"""
    if issubclass(exc_type, KeyboardInterrupt):
        # Permitir KeyboardInterrupt normal
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    print(f"[UNCAUGHT] Exceção não capturada: {exc_type.__name__}: {exc_value}")
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    # Não sair automaticamente - deixar supervisor lidar


def handle_signal(signum, frame):
    """Handler para sinais do sistema"""
    print(f"[SIGNAL] Recebido sinal {signum}")
    if signum in (signal.SIGTERM, signal.SIGINT):
        safe_exit(f"signal_{signum}")


def instalar_handlers_globais():
    """Instala o excepthook e os handlers de SIGTERM/SIGINT."""
    sys.excepthook = handle_uncaught_exception
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, handle_signal)
    if hasattr(signal, 'SIGINT'):
        signal.signal(signal.SIGINT, handle_signal)
