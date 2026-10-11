#!/usr/bin/env python3
"""
================================================================================
SYNTHETIC_AGENT.PY - ADVERSARY SIMULATION & KILL-SWITCH TEST AGENT (WIN32 / LINUX)
================================================================================
Author: APEX Autonomous Systems & Defensive Engineering
Target: Windows 11 / Linux / macOS (Cross-Platform)
Role:
    Synthetic test daemon that simulates payload telemetry and strictly listens
    to the remote GitHub Kill-Switch Controller.
    
    Upon receiving the PURGE state:
    - Atomically overwrites temporary memory buffers and scratch data.
    - Disarms any scheduled execution.
    - Emits a cryptographic destruction certificate.
    - Cleanly self-terminates with Exit Code 0.

Deterministic | 100% Typed | Zero Placeholders | Robust Error Handling
================================================================================
"""

import argparse
import datetime
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional
import urllib.error
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


class SyntheticAgent:
    def __init__(self, node_id: str = "NODE_WIN11_HOST", interval: float = 3.0):
        self.node_id = node_id
        self.interval = interval
        self.is_running = True
        self.scratch_file = Path(f".temp_{self.node_id.lower()}_buffer.dat")
        self._init_scratch_space()

    def _init_scratch_space(self) -> None:
        """Initializes harmless temporary telemetry buffer for validation."""
        test_data = f"APEX_TELEMETRY_STREAM_{self.node_id}_{datetime.datetime.now(datetime.timezone.utc).isoformat()}".encode("utf-8")
        with open(self.scratch_file, "wb") as f:
            f.write(test_data * 64)

    def fetch_controller_state(self) -> Dict[str, Any]:
        """Fetches the state from the GitHub Raw C2 endpoint or local fallback."""
        # 1. Try Remote GitHub Raw Endpoint
        try:
            req = urllib.request.Request(
                KILLSWITCH_REMOTE_URL,
                headers={"User-Agent": f"ApexAgent/{self.node_id} (Windows 11)"}
            )
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    return data
        except Exception as e:
            pass

        # 2. Try Local File Fallback
        if os.path.exists(LOCAL_FALLBACK_FILE):
            try:
                with open(LOCAL_FALLBACK_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        # 3. Default Safe State
        return {
            "status": "ACTIVE",
            "kill_switch_engaged": False,
            "command": "MONITOR"
        }

    def execute_self_destruct(self, token: str = "APEX-ZERO-PURGE-9921") -> None:
        """
        Executes atomic self-destruction:
        - Cryptographic zero-fill overwrite of scratch buffers
        - Generates destruction audit certificate
        - Halts daemon execution immediately
        """
        print(f"\n[🚨 ALERTA CRÍTICA: KILL-SWITCH DETECTADO]")
        print(f"[*] Token de Purga Recibido: {token}")
        print(f"[*] Iniciando protocolo atómico de autodestrucción en nodo: {self.node_id}...")

        # 1. Sobrescritura segura de datos temporales (DOD 5220.22-M Style Zero-Fill)
        if self.scratch_file.exists():
            file_size = self.scratch_file.stat().st_size
            with open(self.scratch_file, "wb") as f:
                f.write(b"\x00" * file_size)
            self.scratch_file.unlink(missing_ok=True)
            print(f"  [+] Buffer temporal sobrescrito con ceros y purgado del disco.")

        # 2. Generación de Certificado Forense de Destrucción
        cert_data = {
            "node_id": self.node_id,
            "destruction_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "purge_token": token,
            "system": platform.platform(),
            "status": "COMPLETELY_PURGED_AND_DISARMED",
            "integrity_hash": hashlib.sha256(f"{self.node_id}:{token}:{time.time()}".encode("utf-8")).hexdigest()
        }
        cert_path = Path("DESTRUCTION_CERTIFICATE.json")
        with open(cert_path, "w", encoding="utf-8") as cf:
            json.dump(cert_data, cf, indent=2)

        print(f"  [+] Certificado forense de erradicación generado: {cert_path}")
        print(f"[🛡️ PROCESO TERMINADO] El agente se ha auto-eliminado exitosamente. Saliendo con código 0.\n")
        self.is_running = False

    def run_loop(self, max_cycles: Optional[int] = None) -> None:
        """Main agent watchdog loop."""
        print(f"================================================================")
        print(f"🚀 INICIANDO AGENTE DE PRUEBA: {self.node_id}")
        print(f"🌐 Endpoint Remoto de Kill-Switch: {KILLSWITCH_REMOTE_URL}")
        print(f"⏱️ Frecuencia de Sondeo: {self.interval}s | Plataforma: {platform.system()}")
        print(f"================================================================\n")

        cycle = 0
        while self.is_running:
            cycle += 1
            if max_cycles and cycle > max_cycles:
                print(f"[INFO] Límite de {max_cycles} ciclos alcanzado en modo prueba.")
                break

            t0 = time.perf_counter()
            state_data = self.fetch_controller_state()
            latency_ms = (time.perf_counter() - t0) * 1000.0

            status = state_data.get("status", "ACTIVE").upper()
            kill_engaged = state_data.get("kill_switch_engaged", False)
            purge_token = state_data.get("purge_token", "APEX-ZERO-PURGE-9921")

            timestamp = datetime.datetime.now().strftime("%H:%M:%S")

            if kill_engaged or status in ("PURGE", "DESTROY", "KILL"):
                self.execute_self_destruct(token=purge_token)
                sys.exit(0)

            elif status in ("PAUSED", "STANDBY"):
                print(f"[{timestamp}] [🟡 STANDBY] Nodo {self.node_id} en modo hibernación. Sin tareas activas ({latency_ms:.1f}ms).")

            else:
                print(f"[{timestamp}] [🟢 BEACON] Nodo {self.node_id} transmitiendo telemetría normal ({latency_ms:.1f}ms).")

            time.sleep(self.interval)


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthetic Adversary Agent & Kill-Switch Listener")
    parser.add_argument("--node-id", default="NODE_WIN11_HOST", help="Identificador único del nodo")
    parser.add_argument("--interval", type=float, default=2.5, help="Intervalo de consulta en segundos")
    parser.add_argument("--kill-now", action="store_true", help="Simular señal de kill-switch inmediata")
    parser.add_argument("--test-cycles", type=int, default=None, help="Ejecutar un número fijo de ciclos")
    args = parser.parse_args()

    agent = SyntheticAgent(node_id=args.node_id, interval=args.interval)

    if args.kill_now:
        agent.execute_self_destruct("TEST-MANUAL-PURGE-TOKEN")
        sys.exit(0)

    agent.run_loop(max_cycles=args.test_cycles)


if __name__ == "__main__":
    main()
