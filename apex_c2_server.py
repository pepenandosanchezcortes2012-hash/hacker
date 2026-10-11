#!/usr/bin/env python3
"""
APEX_C2_SERVER.PY - SERVIDOR WEB C2 Y CONTROLADOR DE ENDPOINTS DETERMINISTA
Sirve el Dashboard de Control en http://192.168.100.7:8080 y http://localhost:8080
Soporta escaneo en vivo del kernel de Windows, recepción de balizas de agentes,
descarga directa de binarios y conmutación de Kill-Switch en tiempo real.
"""

import os
import sys
import json
import time
import socket
import datetime
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import urllib.parse
from real_network_scanner import scan_network

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PORT = 8080
HOST = "0.0.0.0"

class ApexC2RequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Evitar problemas de caché y habilitar CORS para accesos móviles locales
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ["/", "/index.html"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            target_html = "killswitch_dashboard.html" if os.path.exists("killswitch_dashboard.html") else "index.html"
            with open(target_html, "rb") as f:
                self.wfile.write(f.read())
            return

        elif path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            if not os.path.exists("killswitch_state.json"):
                scan_network()
            with open("killswitch_state.json", "rb") as f:
                self.wfile.write(f.read())
            return

        elif path == "/api/scan":
            state = scan_network()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(state, ensure_ascii=False).encode("utf-8"))
            return

        elif path == "/download/bundle":
            bundle = "APEX_CYBER_EDR_SUITE.zip"
            if not os.path.exists(bundle):
                bundle = "CYBER_KILLSWITCH_TEST_BUNDLE.zip"
            if os.path.exists(bundle):
                self.send_response(200)
                self.send_header("Content-Type", "application/zip")
                self.send_header("Content-Disposition", f"attachment; filename={bundle}")
                self.send_header("Content-Length", str(os.path.getsize(bundle)))
                self.end_headers()
                with open(bundle, "rb") as f:
                    self.wfile.write(f.read())
                return
            else:
                self.send_error(404, "Bundle no encontrado.")
                return

        elif path.startswith("/download/"):
            fname = path.replace("/download/", "")
            allowed = ["agent_probe.py", "cleaner_killswitch.py", "cleaner_killswitch.ps1", "agent_killswitch.ps1", "README_KILLSWITCH.md"]
            if fname in allowed and os.path.exists(fname):
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Disposition", f"attachment; filename={fname}")
                self.send_header("Content-Length", str(os.path.getsize(fname)))
                self.end_headers()
                with open(fname, "rb") as f:
                    self.wfile.write(f.read())
                return
            else:
                self.send_error(404, "Archivo no disponible para descarga.")
                return

        # Servir archivos estáticos por defecto si existen
        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        
        try:
            req_data = json.loads(body)
        except Exception:
            req_data = {}

        if path == "/api/killswitch":
            # Conmutar estado del Kill-Switch
            command = req_data.get("command", "MONITOR")
            status = req_data.get("status", "ACTIVE")
            
            with open("killswitch_state.json", "r", encoding="utf-8") as f:
                state = json.load(f)

            state["command"] = command
            state["status"] = status
            state["kill_switch_engaged"] = (command == "PURGE")
            state["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            state["audit_log"].append({
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "action": f"KILLSWITCH_SWITCHED_TO_{command}",
                "actor": "WEB_DASHBOARD_OPERATOR",
                "detail": f"El operador conmutó el estado del controlador a {command}."
            })

            with open("killswitch_state.json", "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(state, ensure_ascii=False).encode("utf-8"))
            return

        elif path == "/api/beacon":
            # Recepción de baliza desde un agente en ejecución
            with open("killswitch_state.json", "r", encoding="utf-8") as f:
                state = json.load(f)

            node_id = req_data.get("node_id", "UNKNOWN_NODE")
            # Buscar o actualizar el dispositivo en la lista
            found = False
            for dev in state["devices"]:
                if dev.get("id") == node_id:
                    dev["status"] = req_data.get("status", "ONLINE")
                    dev["last_beacon"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    dev["battery"] = req_data.get("battery", dev.get("battery"))
                    dev["os"] = req_data.get("os", dev.get("os"))
                    found = True
                    break
            
            if not found and node_id != "DISCONNECTED":
                state["devices"].append({
                    "id": node_id,
                    "device_name": req_data.get("hostname", node_id),
                    "device_type": req_data.get("device_type", "Endpoint"),
                    "icon": "📱" if "Móvil" in req_data.get("device_type", "") else "💻",
                    "mac": "ESTABLISHED_TCP",
                    "vendor": "Agente Registrado",
                    "os": req_data.get("os", "Desconocido"),
                    "ip": req_data.get("ip", self.client_address[0]),
                    "battery": req_data.get("battery", "Activo"),
                    "status": "ONLINE",
                    "last_beacon": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "latency_ms": 1.2,
                    "is_local_host": False
                })

            state["active_devices_count"] = len([d for d in state["devices"] if d.get("status") == "ONLINE"])

            with open("killswitch_state.json", "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)

            # Responder al agente con la directiva actual
            response_payload = {
                "status": state["status"],
                "command": state["command"],
                "kill_switch_engaged": state["kill_switch_engaged"],
                "purge_token": state["purge_token"]
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(response_payload, ensure_ascii=False).encode("utf-8"))
            return

        self.send_error(404, "Endpoint no encontrado")

def run_server():
    server_address = (HOST, PORT)
    httpd = ThreadingHTTPServer(server_address, ApexC2RequestHandler)
    print(f"================================================================")
    print(f"🚀 SERVIDOR APEX C2 INICIADO CON ÉXITO")
    print(f"🌐 Acceso Local Host   : http://localhost:{PORT}")
    print(f"📱 Acceso Celular/LAN  : http://192.168.100.7:{PORT}")
    print(f"📦 Endpoint API Estado : http://192.168.100.7:{PORT}/api/status")
    print(f"🔍 Escaneo de Red      : http://192.168.100.7:{PORT}/api/scan")
    print(f"================================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Deteniendo servidor C2...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
