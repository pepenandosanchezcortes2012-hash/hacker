#!/usr/bin/env python3
"""
========================================================================================
💀 APEX BOOTSTRAP PROVISIONER FOR GOOGLE COLAB 💀
========================================================================================
Orquestador de arranque unificado:
1. Verifica GPU NVIDIA (Tesla T4, A100, L4).
2. Aprovisiona herramientas binarias de Linux (radare2, checksec, pwntools, etc.).
3. Descarga o vincula pesos GGUF (Qwen2.5-Coder-7B) con persistencia en Google Drive.
4. Despliega Cloudflare Tunnel sin necesidad de registro ni tarjetas.
5. Inicia el Daemon Keep-Alive y el Servidor Codex Reverse.
6. Notifica la URL del Túnel y credenciales a Telegram C2.
========================================================================================
"""

import os
import sys
import time
import subprocess
import re
from pathlib import Path

# Colores de terminal
G = "\033[92m"
C = "\033[96m"
Y = "\033[93m"
R = "\033[91m"
W = "\033[0m"

def log(msg, color=C):
    print(f"{color}[APEX-BOOTSTRAP]{W} {msg}")

def run_cmd(cmd, check=True):
    return subprocess.run(cmd, shell=True, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def setup_environment():
    log("Iniciando auditoría de hardware y entorno Linux...", C)
    
    # Comprobar GPU
    gpu_check = subprocess.run(["nvidia-smi"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if gpu_check.returncode == 0:
        log("GPU NVIDIA detectada y activa en el hipervisor.", G)
    else:
        log("ADVERTENCIA: No se detectó GPU CUDA. Para máxima velocidad, activa GPU en 'Entorno de ejecución' -> 'Cambiar tipo de entorno de ejecución' -> 'T4 GPU'.", Y)

    # Instalar paquetes Linux nativos de ingeniería inversa
    log("Instalando utilidades de bajo nivel (radare2, binutils, strings, file, net-tools)...", C)
    subprocess.run("apt-get update -qq && apt-get install -y -qq radare2 binutils file net-tools psmisc curl wget", shell=True)

    # Instalar librerías Python necesarias
    log("Aprovisionando arsenal de Python (pwntools, capstone, keystone-engine, fastapi, uvicorn)...", C)
    subprocess.run("pip install -q fastapi uvicorn pydantic capstone keystone-engine pwntools huggingface_hub", shell=True)

    # Instalar llama-cpp-python con aceleración CUDA
    log("Comprobando llama-cpp-python con backend CUDA cuBLAS...", C)
    try:
        import llama_cpp
        log("llama-cpp-python ya se encuentra disponible.", G)
    except ImportError:
        log("Compilando/Instalando rueda optimizada para CUDA...", C)
        # Usar rueda precompilada con CUDA 12.x para evitar 15 minutos de compilación en Colab
        cmd = "pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu122"
        subprocess.run(cmd, shell=True)

def setup_model():
    """Descarga o vincula el modelo Qwen2.5-Coder-7B en Google Drive para persistencia total."""
    drive_dir = Path("/content/drive/MyDrive/HACKER_CODEX_CORE/models")
    local_dir = Path("/content/models")
    
    target_dir = drive_dir if Path("/content/drive/MyDrive").exists() else local_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    
    model_filename = "Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf"
    target_model_path = target_dir / model_filename
    
    if target_model_path.exists() and target_model_path.stat().st_size > 1000000000:
        log(f"✅ Modelo ya presente en disco: {target_model_path} ({target_model_path.stat().st_size / (1024**3):.2f} GB). Salteando descarga.", G)
        return str(target_model_path)
    
    log(f"Descargando pesos GGUF optimizados ({model_filename}) desde HuggingFace...", Y)
    from huggingface_hub import hf_hub_download
    downloaded_path = hf_hub_download(
        repo_id="bartowski/Qwen2.5-Coder-7B-Instruct-GGUF",
        filename=model_filename,
        local_dir=str(target_dir),
        local_dir_use_symlinks=False
    )
    log(f"✅ Modelo asegurado en: {downloaded_path}", G)
    return downloaded_path

def start_cloudflared():
    """Descarga el binario oficial de Cloudflared y abre un túnel directo al puerto 8000."""
    cloudflared_bin = Path("/usr/local/bin/cloudflared")
    if not cloudflared_bin.exists():
        log("Descargando binario nativo de Cloudflared Linux...", C)
        subprocess.run("wget -q -nc https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared", shell=True)

    log("Iniciando túnel Cloudflare seguro (Zero-Config, SSL)...", C)
    tunnel_log = Path("/content/cloudflared.log")
    if tunnel_log.exists():
        tunnel_log.unlink()

    # Matar instancias previas si las hay
    subprocess.run("killall cloudflared 2>/dev/null", shell=True)

    # Iniciar túnel en segundo plano
    proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", "http://localhost:8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    # Escanear la salida para capturar la URL pública de trycloudflare
    tunnel_url = None
    start_time = time.time()
    log("Esperando asignación de URL pública...", C)
    
    with open(tunnel_log, "w") as f_out:
        while time.time() - start_time < 30:
            line = proc.stdout.readline()
            if not line:
                time.sleep(0.5)
                continue
            f_out.write(line)
            f_out.flush()
            if "trycloudflare.com" in line:
                match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
                if match:
                    tunnel_url = match.group(0)
                    break

    if tunnel_url:
        log(f"🚀 TÚNEL PÚBLICO ESTABLECIDO CON ÉXITO: {tunnel_url}", G)
        with open("/content/tunnel_url.txt", "w") as f:
            f.write(tunnel_url)
        return tunnel_url
    else:
        log("No se pudo obtener URL en 30s. Revisa /content/cloudflared.log", R)
        return None

def main():
    print(r"""
    ██████╗ ██████╗ ██████╗ ███████╗██╗  ██╗    ██████╗ ███████╗██╗   ██╗
   ██╔════╝██╔═══██╗██╔══██╗██╔════╝╚██╗██╔╝    ██╔══██╗██╔════╝██║   ██║
   ██║     ██║   ██║██║  ██║█████╗   ╚███╔╝     ██████╔╝█████╗  ██║   ██║
   ██║     ██║   ██║██║  ██║██╔══╝   ██╔██╗     ██╔══██╗██╔══╝  ╚██╗ ██╔╝
   ╚██████╗╚██████╔╝██████╔╝███████╗██╔╝ ██╗    ██║  ██║███████╗ ╚████╔╝ 
    ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝    ╚═╝  ╚═╝╚══════╝  ╚═══╝  
    --- MOTOR DE INGENIERÍA INVERSA & AUDITORÍA DE KERNEL 24/7 ---
    """)
    setup_environment()
    setup_model()
    
    # Iniciar Keep-Alive Daemon
    log("Iniciando APEX Keep-Alive Daemon (Vigilante de GPU y Procesos)...", C)
    subprocess.Popen(["python3", "/content/colab_codex_core/keepalive_daemon.py"], stdout=open("/content/keepalive.log", "a"), stderr=subprocess.STDOUT)

    # Iniciar Servidor Codex Engine
    log("Iniciando Servidor Codex Engine en puerto 8000...", C)
    subprocess.Popen(["python3", "/content/colab_codex_core/codex_engine.py"], stdout=open("/content/codex_engine.log", "a"), stderr=subprocess.STDOUT)
    time.sleep(3)

    # Abrir Túnel
    tunnel_url = start_cloudflared()

    print("\n" + "="*70)
    print(f"{G}⚡ SISTEMA CODEX REVERSE OPERATIVO EN GOOGLE COLAB ⚡{W}")
    print(f"🔗 Cyberdeck WebUI:        {C}{tunnel_url}{W}")
    print(f"🔌 OpenAI API Endpoint:    {C}{tunnel_url}/v1{W}")
    print(f"📡 Keep-Alive Estado:      {G}ACTIVO (GPU Micro-Pulse + Audio Oscillator){W}")
    print("="*70 + "\n")

    # Intentar enviar alerta Telegram
    try:
        from codex_engine import send_telegram_alert
        alert_msg = (
            f"💀 <b>CODEX REVERSE ONLINE EN GOOGLE COLAB</b> 💀\n\n"
            f"🔗 <b>WebUI Cyberdeck:</b> {tunnel_url}\n"
            f"🔌 <b>API Endpoint:</b> <code>{tunnel_url}/v1</code>\n"
            f"⚡ <b>Modelo:</b> Qwen2.5-Coder-7B-Instruct (4-bit CUDA)\n"
            f"🛡️ <b>Keep-Alive:</b> Micro-pulsos de GPU activos 24/7."
        )
        if send_telegram_alert(alert_msg):
            log("Notificación C2 enviada a Telegram con éxito.", G)
    except Exception as e:
        log(f"No se pudo despachar alerta Telegram: {e}", Y)

if __name__ == "__main__":
    main()
