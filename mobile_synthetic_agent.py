#!/usr/bin/env python3
"""
================================================================================
MOBILE_SYNTHETIC_AGENT.PY - AGENTE MÓVIL SINTÉTICO (SIMULADOR ANDROID / ADB)
================================================================================
Autor: APEX Autonomous Systems & Mobile Defensive Lab
Objetivo: Simulación y telemetría de endpoints móviles (Android 14)
Función:
    Simula un agente en dispositivo móvil que monitorea el interruptor maestro.
    Al recibir la señal PURGE:
    - Ejecuta revocación de permisos simulada.
    - Purga cache y bases de datos SQLite locales.
    - Emite comando de auto-desinstalación y descarte de sandbox.
================================================================================
"""

import argparse
import datetime
import json
import os
import sys
import time
from pathlib import Path
import urllib.request

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

KILLSWITCH_REMOTE_URL = "https://raw.githubusercontent.com/pepenandosanchezcortes2012-hash/hacker/main/killswitch_state.json"
LOCAL_FALLBACK_FILE = "killswitch_state.json"


def simulate_mobile_killswitch(token: str = "APEX-ZERO-PURGE-9921"):
    print("\n[📱 ANDROID DAEMON: KILL-SWITCH DETECTADO]")
    print(f"[*] Token de Erradicación: {token}")
    print("[*] Ejecutando purga en sandbox /data/data/com.apex.agent.synthetic...")
    
    steps = [
        "Revocando permisos críticos de accesibilidad y overlay...",
        "Sobrescribiendo base de datos SQLite y storage interno...",
        "Desregistrando BroadcastReceiver de arranque (BOOT_COMPLETED)...",
        "Enviando señal am force-stop y pm uninstall..."
    ]
    for step in steps:
        time.sleep(0.3)
        print(f"  [+] {step}")

    cert = {
        "device": "Android 14 ARM64 (Synthetic)",
        "package": "com.apex.agent.synthetic",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": "UNINSTALLED_AND_PURGED",
        "purge_token": token
    }
    with open("MOBILE_DESTRUCTION_CERTIFICATE.json", "w", encoding="utf-8") as f:
        json.dump(cert, f, indent=2)
        
    print("[🛡️ REMEDIACIÓN COMPLETADA] Dispositivo móvil libre de la muestra sintética.\n")


def main():
    parser = argparse.ArgumentParser(description="Simulador de Agente Móvil con Kill-Switch")
    parser.add_argument("--kill-now", action="store_true", help="Disparar purga móvil inmediata")
    args = parser.parse_args()

    if args.kill_now:
        simulate_mobile_killswitch()
        return

    print("================================================================")
    print("📱 AGENTE MÓVIL SINTÉTICO: com.apex.agent.synthetic")
    print("🌐 Supervisión de Kill-Switch C2 vía HTTP/HTTPS")
    print("================================================================\n")

    # Realizar 2 consultas de comprobación
    for i in range(2):
        print(f"[*] Baliza móvil #{i+1} enviada al controlador. Estado: SYNCHRONIZED.")
        time.sleep(1.0)
    
    print("\n[INFO] Ejecute con --kill-now para simular la purga atómica.")

if __name__ == "__main__":
    main()
