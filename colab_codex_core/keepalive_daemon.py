#!/usr/bin/env python3
"""
========================================================================================
💀 APEX KEEPALIVE & VITALITY DAEMON — TENSOR CORE P0 & KERNEL WATCHDOG 💀
========================================================================================
Misión: Mantener la sesión de Google Colab en estado de máxima vitalidad contra
desconexiones por inactividad (Idle Timeout) y forzar la GPU NVIDIA Tesla T4 a
permanecer en su estado de mayor rendimiento (P-State P0 Boost Clock).

Mecanismos de vitalidad y blindaje:
1. GPU Tensor Core Micro-Pulse: Cálculos tensoriales FP16 con autocast en CUDA cada
   35 segundos para activar los Tensor Cores de la arquitectura Turing (TU104).
2. I/O Heartbeat: Pulsos de persistencia en disco y Google Drive.
3. Process Supervisor: Vigila el servidor Codex Reverse (FastAPI) y Cloudflared.
   Si alguno cae por OOM o señal SIGTERM, lo relanza de inmediato.
========================================================================================
"""

import os
import sys
import time
import subprocess
import logging
from datetime import datetime
from pathlib import Path

# Rutas de telemetría y persistencia
LOG_PATH = Path("/content/keepalive_daemon.log")
DRIVE_PULSE_PATH = Path("/content/drive/MyDrive/HACKER_CODEX_CORE/logs/heartbeat.txt")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [KEEPALIVE-DAEMON] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("KeepAliveDaemon")

def try_import_torch():
    try:
        import torch
        return torch
    except ImportError:
        logger.warning("PyTorch no detectado en el entorno actual. Operando en modo fallback.")
        return None

def gpu_tensor_pulse(torch_module):
    """
    Ejecuta un pulso tensorial en precisión media (FP16) aprovechando
    directamente los 320 Tensor Cores de la GPU NVIDIA Tesla T4.
    Forza a los clocks de la GPU a mantenerse en P-State P0 de máxima frecuencia.
    """
    if torch_module and torch_module.cuda.is_available():
        try:
            device = torch_module.device("cuda:0")
            # Operación tensorial optimizada para arquitectura Turing Tensor Cores
            with torch_module.amp.autocast(device_type="cuda", dtype=torch_module.float16):
                a = torch_module.randn((256, 256), device=device, dtype=torch_module.float16)
                b = torch_module.randn((256, 256), device=device, dtype=torch_module.float16)
                c = torch_module.matmul(a, b)
                torch_module.cuda.synchronize(device)
                del a, b, c
            return True
        except Exception as e:
            logger.error(f"Error en pulso tensorial CUDA: {e}")
            return False
    return False

def disk_heartbeat():
    """Registra pulso de vida en el sistema de archivos local y en Google Drive."""
    now_str = datetime.now().isoformat()
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open("/content/.keepalive_pulse", "w") as f:
            f.write(f"VITAL_TENSOR_PULSE:{now_str}\n")
            
        if DRIVE_PULSE_PATH.parent.exists():
            with open(DRIVE_PULSE_PATH, "a") as df:
                df.write(f"VITAL_TENSOR_PULSE_OK: {now_str}\n")
    except Exception as e:
        logger.debug(f"Error en pulso de disco: {e}")

def check_and_revive_processes():
    """
    Supervisa que los servicios críticos (codex_engine y cloudflared) sigan activos.
    Si algún proceso ha muerto, lo resucita con sesión desacoplada.
    """
    services = {
        "codex_engine.py": {
            "cmd": ["python3", "/content/colab_codex_core/codex_engine.py"],
            "log": "/content/codex_engine.log",
            "file": Path("/content/colab_codex_core/codex_engine.py")
        },
        "cloudflared": {
            "cmd": ["cloudflared", "tunnel", "--url", "http://localhost:8000"],
            "log": "/content/cloudflared.log",
            "file": Path("/usr/local/bin/cloudflared")
        }
    }
    
    for name, s_cfg in services.items():
        try:
            check = subprocess.run(
                ["pgrep", "-f", name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if check.returncode != 0:
                logger.warning(f"⚠️ Alerta: Servicio crítico '{name}' no detectado en procesos activos. Iniciando resurrección...")
                if s_cfg["file"].exists():
                    subprocess.Popen(
                        s_cfg["cmd"],
                        stdout=open(s_cfg["log"], "a"),
                        stderr=subprocess.STDOUT,
                        preexec_fn=os.setpgrp
                    )
                    logger.info(f"✅ Servicio '{name}' relanzado con PID desacoplado.")
        except Exception as e:
            logger.error(f"Error supervisando proceso {name}: {e}")

def main():
    logger.info("⚡ Iniciando APEX KEEPALIVE & VITALITY DAEMON v3.0 (Tensor Core P0 Watchdog)...")
    torch_mod = try_import_torch()
    
    if torch_mod and torch_mod.cuda.is_available():
        gpu_name = torch_mod.cuda.get_device_name(0)
        vram_mb = torch_mod.cuda.get_device_properties(0).total_memory / (1024**2)
        logger.info(f"🎯 Aceleración Activa: GPU={gpu_name} | VRAM Total={vram_mb:.1f} MB | Tensor Cores activados.")
    else:
        logger.info("ℹ️ Operando en modo CPU (Sin GPU CUDA detectada en este runtime).")

    pulse_count = 0
    cycle_interval = 35  # Segundos entre pulsos
    
    while True:
        try:
            pulse_count += 1
            gpu_ok = gpu_tensor_pulse(torch_mod)
            disk_heartbeat()
            
            # Supervisar procesos cada 2 ciclos (~70 segundos)
            if pulse_count % 2 == 0:
                check_and_revive_processes()
                
            if pulse_count % 10 == 0:
                logger.info(f"💓 Pulso #{pulse_count} verificado | GPU_TENSOR_PULSE={'OK' if gpu_ok else 'SKIP'}")
                
            time.sleep(cycle_interval)
        except KeyboardInterrupt:
            logger.info("Keepalive daemon terminado por orden del operador.")
            break
        except Exception as e:
            logger.error(f"Excepción en ciclo keepalive: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
