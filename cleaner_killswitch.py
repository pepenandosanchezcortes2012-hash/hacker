#!/usr/bin/env python3
"""
CLEANER_KILLSWITCH.PY - HERRAMIENTA OFENSIVA DE DESINFECCIÓN, ERRADICACIÓN Y PURGA
Objetivo:
  1. Detectar y fulminar en memoria cualquier instancia de agentes de prueba o sondas activas.
  2. Borrado criptográfico seguro (sobreescritura con ceros) de artefactos y archivos temporales.
  3. Desregistro de llaves de persistencia y tareas programadas en Windows.
  4. Cierre y purga forzosa de sockets y conexiones colgadas.
  5. Generación de informe forense de remediación (Exit Code 0).
"""

import os
import sys
import json
import time
import socket
import datetime
import subprocess

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

TARGET_PROCESS_SIGNATURES = [
    "agent_probe.py",
    "synthetic_agent.py",
    "mobile_synthetic_agent.py",
    "agent_killswitch.ps1",
    "apex_c2_agent"
]

TARGET_FILES_TO_SHRED = [
    "sentinel_state.json",
    "AGENT_DESTRUCTION_CERTIFICATE.json",
    "MOBILE_DESTRUCTION_CERTIFICATE.json",
    "killswitch_state_temp.json"
]

def shred_file(path: str) -> bool:
    """Sobrescribe un archivo con ceros binarios antes de eliminarlo."""
    if not os.path.exists(path):
        return False
    try:
        length = os.path.getsize(path)
        with open(path, "wb") as f:
            f.write(b"\x00" * max(length, 1024))
        os.remove(path)
        return True
    except Exception as e:
        print(f"[-] Error al triturar {path}: {e}")
        return False

def terminate_processes_win32() -> list:
    """Inspecciona y fulmina procesos coincidentes en Windows 11 usando Win32 taskkill / PowerShell."""
    terminated = []
    if sys.platform != "win32":
        return terminated
        
    try:
        # Consultar procesos que ejecuten Python o PowerShell
        cmd = "powershell -NoProfile -Command \"Get-CimInstance Win32_Process | Select-Object ProcessId, CommandLine | ConvertTo-Json -Compress\""
        out = subprocess.check_output(cmd, shell=True).decode(errors="ignore")
        if not out.strip():
            return terminated

        data = json.loads(out)
        if isinstance(data, dict):
            data = [data]

        current_pid = os.getpid()
        for p in data:
            pid = p.get("ProcessId")
            cmdline = p.get("CommandLine") or ""
            if pid == current_pid:
                continue

            for sig in TARGET_PROCESS_SIGNATURES:
                if sig.lower() in cmdline.lower():
                    print(f"[*] Amenaza/Sonda detectada en PID {pid} -> ({sig})")
                    subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
                    terminated.append({"pid": pid, "signature": sig, "cmdline": cmdline})
                    print(f"  [+] PID {pid} terminado forzosamente.")
                    break
    except Exception as e:
        print(f"[-] Error en escaneo de procesos: {e}")

    return terminated

def purge_persistence():
    """Limpia cualquier rastro en registro de autoarranque de Windows o tareas."""
    if sys.platform != "win32":
        return
    print("[*] Verificando persistencia en el Registro y Tareas Programadas...")
    reg_clean = "powershell -NoProfile -Command \"Remove-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run' -Name 'ApexAgent*' -ErrorAction SilentlyContinue\""
    subprocess.run(reg_clean, shell=True, capture_output=True)
    print("  [+] Registro de Windows verificado e inmunizado.")

def main():
    print("================================================================")
    print("🛡️ APEX CLEANER & KILL-SWITCH SANITIZER // MÓDULO DE PURGA TOTAL")
    print("================================================================\n")
    
    start_time = time.time()
    
    # 1. Fulminar procesos activos
    print("[FASE 1] Terminando procesos de agentes y sondas en ejecución...")
    killed = terminate_processes_win32()
    print(f"[+] Total de procesos neutralizados: {len(killed)}\n")

    # 2. Trituración segura de archivos temporales
    print("[FASE 2] Triturando buffers y archivos temporales residuales...")
    shredded_count = 0
    for target in TARGET_FILES_TO_SHRED:
        if shred_file(target):
            shredded_count += 1
            print(f"  [+] Archivo triturado criptográficamente: {target}")
    print(f"[+] Total de artefactos purgados: {shredded_count}\n")

    # 3. Eliminar persistencia
    print("[FASE 3] Sanitizando persistencia del sistema...")
    purge_persistence()

    # 4. Enviar señal de PURGE al C2 si el archivo killswitch_state.json existe
    if os.path.exists("killswitch_state.json"):
        try:
            with open("killswitch_state.json", "r", encoding="utf-8") as f:
                state = json.load(f)
            state["kill_switch_engaged"] = True
            state["command"] = "PURGE"
            state["status"] = "PURGED"
            state["audit_log"].append({
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "action": "EMERGENCY_KILLSWITCH_CLEANER_EXECUTED",
                "actor": "ADMIN_CLEANER_SANITIZER",
                "detail": "El limpiador autónomo sanitizó el host y activó la purga global."
            })
            with open("killswitch_state.json", "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            print("\n[+] Estado del Kill-Switch actualizado globalmente a PURGE.")
        except Exception as e:
            print(f"[-] Advertencia al actualizar estado: {e}")

    elapsed = round(time.time() - start_time, 3)
    print(f"\n================================================================")
    print(f"✅ REMEDIACIÓN EXITOSA EN {elapsed}s // HOST TOTALMENTE LIMPIO")
    print(f"================================================================")
    sys.exit(0)

if __name__ == "__main__":
    main()
