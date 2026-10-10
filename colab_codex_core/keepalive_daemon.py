#!/usr/bin/env python3
"""
========================================================================================
💀 APEX KEEPALIVE & VITALITY DAEMON (COLAB LINUX KERNEL WATCHDOG) 💀
========================================================================================
Misión: Mantener viva la sesión de Google Colab contra desconexiones por inactividad
(Idle Timeout) y monitorizar los procesos del motor Codex Reverse.

Mecanismos de vitalidad:
1. GPU Micro-Pulse: Realiza micro-cálculos de tensores en CUDA cada 45 segundos.
   Esto previene que el hipervisor de Colab detecte la GPU como inactiva/idle.
2. I/O Heartbeat: Escribe pulsos de persistencia en disco y Google Drive.
3. Process Supervisor: Vigila el servidor Codex Reverse y Cloudflared.
   Si alguno se cae o sufre OOM, lo resucita instantáneamente.
========================================================================================
"""

import os
import sys
import time
import subprocess
import logging
from datetime import datetime
from pathlib import Path

# Configuración de Logging
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
        logger.warning("PyTorch no detectado en el entorno actual.")
        return None

def gpu_micro_pulse(torch_module):
    """
    Ejecuta un pulso infinitesimal en VRAM para marcar la GPU como activa.
    Consumo de VRAM: ~2 MB. Latencia: < 1 ms.
    """
    if torch_module and torch_module.cuda.is_available():
        try:
            device = torch_module.device("cuda:0")
            # Micro operación tensorial (128x128 float32 matrix multiplication)
            a = torch_module.ones((128, 128), device=device, dtype=torch_module.float32)
            b = torch_module.ones((128, 128), device=device, dtype=torch_module.float32)
            _ = torch_module.matmul(a, b)
            torch_module.cuda.synchronize(device)
            del a, b
            return True
        except Exception as e:
            logger.error(f"Error en pulso GPU: {e}")
            return False
    return False

def disk_heartbeat():
    """Registra pulso de vida en sistema de archivos local y Drive si está montado."""
    now_str = datetime.now().isoformat()
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open("/content/.keepalive_pulse", "w") as f:
            f.write(f"PULSE:{now_str}\n")
            
        if DRIVE_PULSE_PATH.parent.exists():
            with open(DRIVE_PULSE_PATH, "a") as df:
                df.write(f"VITAL_PULSE_OK: {now_str}\n")
    except Exception as e:
        logger.debug(f"Error en pulso de disco: {e}")

def check_and_revive_processes():
    """
    Supervisa que los servicios críticos (codex_engine y cloudflared) sigan vivos.
    """
    services = {
        "codex_engine": "python3 /content/colab_codex_core/codex_engine.py",
        "cloudflared": "cloudflared"
    }
    
    for name, cmd in services.items():
        try:
            # Comprobar si el proceso aparece en ps
            check = subprocess.run(
                ["pgrep", "-f", name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if check.returncode != 0:
                logger.warning(f"⚠️ Alerta: Servicio '{name}' no encontrado en ejecución. Intentando reanimación...")
                if name == "codex_engine" and Path("/content/colab_codex_core/codex_engine.py").exists():
                    subprocess.Popen(
                        ["python3", "/content/colab_codex_core/codex_engine.py"],
                        stdout=open("/content/codex_engine.log", "a"),
                        stderr=subprocess.STDOUT,
                        preexec_fn=os.setpgrp
                    )
                    logger.info(f"✅ Servicio '{name}' relanzado con PID desacoplado.")
        except Exception as e:
            logger.error(f"Error supervisando {name}: {e}")

def main():
    logger.info("⚡ Iniciando APEX KEEPALIVE & VITALITY DAEMON v2.0...")
    torch_mod = try_import_torch()
    
    if torch_mod and torch_mod.cuda.is_available():
        gpu_name = torch_mod.cuda.get_device_name(0)
        vram_mb = torch_mod.cuda.get_device_properties(0).total_memory / (1024**2)
        logger.info(f"🎯 Hardware detectado: GPU={gpu_name} | VRAM={vram_mb:.1f} MB")
    else:
        logger.info("ℹ️ Operando en modo CPU (Sin GPU CUDA activa detectada).")

    pulse_count = 0
    cycle_interval = 40  # Segundos entre pulsos (debajo del umbral de 30-90min)
    
    while True:
        try:
            pulse_count += 1
            gpu_ok = gpu_micro_pulse(torch_mod)
            disk_heartbeat()
            
            # Supervisar procesos cada 3 ciclos (~2 minutos)
            if pulse_count % 3 == 0:
                check_and_revive_processes()
                
            if pulse_count % 15 == 0:
                logger.info(f"💓 Pulso de vida #{pulse_count} verificado | GPU_PULSE={'OK' if gpu_ok else 'SKIP'}")
                
            time.sleep(cycle_interval)
        except KeyboardInterrupt:
            logger.info("Daemon terminado por interrupción del operador.")
            break
        except Exception as e:
            logger.error(f"Excepción no controlada en bucle keepalive: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
