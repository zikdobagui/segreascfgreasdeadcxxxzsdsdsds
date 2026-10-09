"""Launcher: aplica restaurações somente entre duas execuções do bot."""
import os
from pathlib import Path
import signal
import subprocess
import sys
from contextlib import contextmanager


@contextmanager
def exclusive_lock(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    stream = path.open("a+")
    try:
        if os.name == "nt":
            import msvcrt
            if path.stat().st_size == 0:
                stream.write(" ")
                stream.flush()
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        stream.close()


def supervise(root):
    from app.data_restore import apply_pending, RESTART_CODE, STATE_DIR
    child = None

    def stop(signum, frame):
        if child is not None and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=15)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    with exclusive_lock(root / STATE_DIR / "launcher.lock"):
        while True:
            # Também recusa restaurar se uma execução antiga ainda usa os dados.
            with exclusive_lock(root / "bot_instance.lock"):
                apply_pending(root)
            env = os.environ.copy()
            env["BOT_RESTORE_SUPERVISED"] = "1"
            child = subprocess.Popen(
                [sys.executable, "-u", str(root / "bot.py"), "--worker"],
                cwd=root, env=env,
            )
            code = child.wait()
            if code != RESTART_CODE:
                return code

def main():
    root = Path(__file__).resolve().parent
    os.chdir(root)
    if "--worker" in sys.argv and os.getenv("BOT_RESTORE_SUPERVISED") == "1":
        from app.bot import start_polling
        start_polling()
        return 0
    return supervise(root)

if __name__ == "__main__":
    sys.exit(main())
