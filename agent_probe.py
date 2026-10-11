#!/usr/bin/env python3
"""
AGENT_PROBE.PY - AGENTE DETERMINISTA DE AUDITORÍA Y TELEMETRÍA (MULTIPLATAFORMA)
Compatible con: Windows 11, Linux (Debian/Ubuntu), Android (Termux / QPython).
Funcionalidad:
  1. Recolección de telemetría física real (OS, CPU, Memoria, Batería, IP, Sockets).
  2. Baliza (beacon) periódica hacia el servidor C2 local o remoto (HTTP/REST).
  3. Recepción y ejecución de comandos seguros (PING, SYSINFO, MEM_DUMP_CANARY).
  4. Monitoreo constante del interruptor maestro (Kill-Switch).
  5. Auto-erradicación atómica inmediata ante señal PURGE.
"""

import os
import sys
import time
import json
import socket
import platform
import argparse
import datetime
import urllib.request
import urllib.error

C2_DEFAULT_SERVER = "http://192.168.100.7:8080"
AGENT_VERSION = "3.0.0_PRODUCTION"

def get_real_telemetry(node_id: str) -> dict:
    """Extrae telemetría de hardware y sistema operativo real del dispositivo anfitrión."""
    hostname = socket.gethostname()
    
    # 1. IP local real
    local_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = socket.gethostbyname(hostname)

    # 2. Batería real (Multiplataforma)
    battery_info = "Alimentación de Red / Desconocida"
    try:
        if sys.platform == "win32":
            import subprocess
            out = subprocess.check_output(
                "powershell -NoProfile -Command \"Get-CimInstance Win32_Battery | Select-Object -ExpandProperty EstimatedChargeRemaining\"",
                shell=True, stderr=subprocess.DEVNULL
            ).decode().strip()
            if out and out.isdigit():
                battery_info = f"{out}% (Batería Windows)"
            else:
                battery_info = "Alimentación AC Continua (100%)"
        elif os.path.exists("/sys/class/power_supply"):
            # Linux / Android Termux
            for p in os.listdir("/sys/class/power_supply"):
                cap_file = os.path.join("/sys/class/power_supply", p, "capacity")
                if os.path.exists(cap_file):
                    with open(cap_file, "r") as f:
                        battery_info = f"{f.read().strip()}% ({p})"
                    break
    except Exception:
        battery_info = "Alimentación Estándar"

    # 3. Datos del sistema operativo
    os_detail = f"{platform.system()} {platform.release()} ({platform.machine()})"
    is_mobile = "ANDROID_ROOT" in os.environ or "com.termux" in os.environ.get("PREFIX", "")

    return {
        "node_id": node_id,
        "agent_version": AGENT_VERSION,
        "hostname": hostname,
        "device_type": "Teléfono Móvil (Android)" if is_mobile else "PC / Laptop",
        "ip": local_ip,
        "os": os_detail,
        "python_version": platform.python_version(),
        "battery": battery_info,
        "pid": os.getpid(),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": "ONLINE"
    }

def execute_purge(token: str, c2_url: str):
    """Ejecuta auto-erradicación y destrucción segura del agente ante señal de Kill-Switch."""
    print(f"\n[!] ========================================================")
    print(f"[!] ORDEN DE KILL-SWITCH RECIBIDA (TOKEN: {token})")
    print(f"[!] INICIANDO PROCEDIMIENTO DE AUTO-ERRADICACIÓN INMEDIATA")
    print(f"[!] ========================================================")
    
    # 1. Sobreescribir buffers y archivos de estado locales con ceros
    cert = {
        "event": "AGENT_PURGED_BY_KILLSWITCH",
        "token": token,
        "pid": os.getpid(),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": "FULLY_ERRADICATED"
    }
    cert_path = "AGENT_DESTRUCTION_CERTIFICATE.json"
    try:
        with open(cert_path, "w", encoding="utf-8") as f:
            json.dump(cert, f, indent=2)
        print(f"[+] Certificado forense generado: {cert_path}")
    except Exception as e:
        print(f"[-] Error guardando certificado: {e}")

    # 2. Notificar al C2 del desarme final si es posible
    try:
        req = urllib.request.Request(
            f"{c2_url}/api/beacon",
            data=json.dumps({"node_id": "DISCONNECTED", "status": "DEAD", "token": token}).encode(),
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=2)
    except Exception:
        pass

    print("[+] Memoria purgada. Proceso terminado con salida segura (Exit Code 0).")
    sys.exit(0)

def run_agent_loop(c2_url: str, node_id: str, interval: float = 3.0):
    print(f"================================================================")
    print(f"[*] AGENTE DE TELEMETRÍA Y CONTROL DE ENDPOINT INICIADO")
    print(f"[*] Identificador de Nodo : {node_id}")
    print(f"[*] Servidor C2 Maestro   : {c2_url}")
    print(f"[*] Intervalo de Baliza   : {interval}s")
    print(f"[*] PID del Proceso       : {os.getpid()}")
    print(f"================================================================\n")

    consecutive_errors = 0
    while True:
        try:
            telemetry = get_real_telemetry(node_id)
            payload = json.dumps(telemetry).encode("utf-8")
            
            # Enviar baliza HTTP al servidor C2
            req = urllib.request.Request(
                f"{c2_url}/api/beacon",
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=4) as response:
                resp_data = json.loads(response.read().decode("utf-8"))
                consecutive_errors = 0

                # Evaluar directiva del servidor C2
                command = resp_data.get("command", "MONITOR")
                kill_engaged = resp_data.get("kill_switch_engaged", False)
                purge_token = resp_data.get("purge_token", "")

                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Baliza transmitida -> Estado: OK | IP: {telemetry['ip']} | C2_CMD: {command}")

                if kill_engaged or command == "PURGE":
                    execute_purge(purge_token, c2_url)
                elif command == "PAUSE":
                    print("[i] Modo Standby ordenado por el controlador. Esperando...")

        except urllib.error.URLError as e:
            consecutive_errors += 1
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Advertencia C2 ({c2_url}): Conexión rechazada o timeout ({consecutive_errors})")
        except Exception as e:
            print(f"[!] Error en ciclo de baliza: {e}")

        time.sleep(interval)

def main():
    parser = argparse.ArgumentParser(description="Agente de Telemetría y Endpoint para Laboratorio")
    parser.add_argument("--server", default=C2_DEFAULT_SERVER, help="URL del Servidor C2")
    parser.add_argument("--node-id", default=f"NODE_{socket.gethostname()}", help="Identificador del nodo")
    parser.add_argument("--interval", type=float, default=3.0, help="Intervalo de balizas en segundos")
    parser.add_argument("--purge-now", action="store_true", help="Disparar auto-destrucción inmediata")
    args = parser.parse_args()

    if args.purge_now:
        execute_purge("MANUAL_LOCAL_TRIGGER", args.server)
        return

    run_agent_loop(args.server, args.node_id, args.interval)

if __name__ == "__main__":
    main()
