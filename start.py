import subprocess, time, threading, os, signal, sys, traceback
from datetime import datetime

PROCS = {
    "app.healthcheck": None,  # Healthcheck primeiro
    "bot": None,
    # "gerenciador.py": None,  # DESATIVADO - Causa conflito com bot.py
    # Atualização em massa é opcional: execute python -m app.update_usernames manualmente.
    # Não consultar todos os usuários do backup a cada inicialização.
}

# Backoff tracking per process
RESTART_ATTEMPTS = {}
MAX_RESTART_ATTEMPTS = 10
HEARTBEAT_INTERVAL = 60  # seconds

def _heartbeat():
    while True:
        try:
            print(f"[SUPERVISOR] heartbeat ok (pid={os.getpid()})")
            sys.stdout.flush()
        except Exception:
            pass
        time.sleep(HEARTBEAT_INTERVAL)

def _spawn(script):
    try:
        child_env = os.environ.copy()
        if script == "bot":
            child_env["BOT_EXTERNAL_HEALTHCHECK"] = "1"
        p = subprocess.Popen([sys.executable, "-u", "-m", script], cwd=os.path.dirname(os.path.abspath(__file__)), env=child_env, stdout=None, stderr=None)
        print(f"[SUPERVISOR] started {script} (pid={p.pid})")
        return p
    except Exception as e:
        print(f"[SUPERVISOR] failed to start {script}: {e}")
        traceback.print_exc()
        return None

def _ensure_running():
    for script in list(PROCS.keys()):
        p = PROCS[script]
        if p is None or p.poll() is not None:
            # if previously existed, log exit code and apply backoff
            if p is not None:
                attempts = RESTART_ATTEMPTS.get(script, 0) + 1
                RESTART_ATTEMPTS[script] = attempts
                
                if attempts > MAX_RESTART_ATTEMPTS:
                    print(f"[SUPERVISOR] {script} exceeded max restarts ({MAX_RESTART_ATTEMPTS}), skipping")
                    continue
                
                # Exponential backoff: 5s, 10s, 20s, 40s, max 300s (5min)
                backoff = min(300, 5 * (2 ** (attempts - 1)))
                print(f"[SUPERVISOR] {script} exited with code {p.returncode}; attempt {attempts}/{MAX_RESTART_ATTEMPTS}, restarting in {backoff}s")
                time.sleep(backoff)
            else:
                # First start
                RESTART_ATTEMPTS[script] = 0
            
            PROCS[script] = _spawn(script)
            
            # Reset counter on successful start after some time
            if PROCS[script] is not None:
                def reset_counter():
                    time.sleep(300)  # 5 minutes
                    if script in RESTART_ATTEMPTS and RESTART_ATTEMPTS[script] > 0:
                        print(f"[SUPERVISOR] {script} stable for 5min, resetting restart counter")
                        RESTART_ATTEMPTS[script] = 0
                threading.Thread(target=reset_counter, daemon=True).start()

def start_scripts():
    # start heartbeat thread
    threading.Thread(target=_heartbeat, daemon=True).start()

    # main supervise loop
    try:
        while True:
            _ensure_running()
            time.sleep(10)
    except KeyboardInterrupt:
        print("[SUPERVISOR] KeyboardInterrupt: terminating children...")
        for p in PROCS.values():
            try:
                if p and p.poll() is None:
                    p.terminate()
            except Exception:
                pass
        time.sleep(2)
        for p in PROCS.values():
            try:
                if p and p.poll() is None:
                    p.kill()
            except Exception:
                pass

if __name__ == "__main__":
    start_scripts()
