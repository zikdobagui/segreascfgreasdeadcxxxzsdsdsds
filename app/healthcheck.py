#!/usr/bin/env python3
"""
Healthcheck HTTP simples para SquareCloud
Expõe endpoint /health para verificar se o bot está rodando
"""

import threading
import time
import os
import json
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

class HealthCheckHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silenciar logs HTTP para reduzir spam
        pass
    
    def do_GET(self):
        path = urlparse(self.path).path
        
        if path == '/health':
            self.send_health_response()
        elif path == '/status':
            self.send_status_response()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def send_health_response(self):
        """Endpoint básico para SquareCloud healthcheck"""
        try:
            # Verificar se lockfile do bot existe (indica que está rodando)
            lockfile = "bot_instance.lock"
            bot_running = os.path.exists(lockfile)
            
            if bot_running:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = {
                    "status": "ok",
                    "timestamp": datetime.now().isoformat(),
                    "bot_running": True
                }
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_response(503)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = {
                    "status": "error",
                    "timestamp": datetime.now().isoformat(),
                    "bot_running": False,
                    "error": "Bot lockfile not found"
                }
                self.wfile.write(json.dumps(response).encode())
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
            self.wfile.write(json.dumps(response).encode())
    
    def send_status_response(self):
        """Endpoint com informações detalhadas"""
        try:
            lockfile = "bot_instance.lock"
            bot_running = os.path.exists(lockfile)
            
            # Ler PID se disponível
            bot_pid = None
            if bot_running:
                try:
                    with open(lockfile, 'r') as f:
                        bot_pid = f.read().strip()
                except Exception:
                    pass
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            response = {
                "status": "ok" if bot_running else "bot_down",
                "timestamp": datetime.now().isoformat(),
                "bot_running": bot_running,
                "bot_pid": bot_pid,
                "healthcheck_pid": os.getpid(),
                "uptime_seconds": time.time() - start_time
            }
            self.wfile.write(json.dumps(response, indent=2).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
            self.wfile.write(json.dumps(response).encode())

def start_healthcheck_server():
    """Inicia servidor HTTP em thread separada"""
    global start_time
    start_time = time.time()
    
    port = int(os.environ.get('PORT', 8080))
    
    try:
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        print(f"[HEALTHCHECK] Servidor iniciado na porta {port}")
        print(f"[HEALTHCHECK] Endpoints: /health, /status")
        server.serve_forever()
    except Exception as e:
        print(f"[HEALTHCHECK] Erro ao iniciar servidor: {e}")

if __name__ == "__main__":
    # Executar como processo independente
    start_healthcheck_server()
