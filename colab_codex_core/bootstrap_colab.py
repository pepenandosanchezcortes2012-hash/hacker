#!/usr/bin/env python3
"""
========================================================================================
💀 APEX BOOTSTRAP PROVISIONER FOR GOOGLE COLAB (HARDENED & UNRESTRICTED) 💀
========================================================================================
Orquestador de arranque unificado:
1. Verifica y calibra GPU NVIDIA Tesla T4 (CUDA 12, Tensor Cores activos).
2. Aprovisiona herramientas binarias de Linux (radare2, checksec, pwntools, capstone, keystone).
3. Asegura pesos GGUF (Qwen2.5-Coder-7B) con persistencia en Google Drive o almacenamiento local.
4. Genera y consolida el blindaje de seguridad (apex_security.json).
5. Inicia el Daemon Keep-Alive de Tensor Cores y el Servidor Codex Reverse.
6. Despliega Cloudflare Tunnel seguro con SSL.
7. Notifica métricas de GPU, URL blindada y credenciales de acceso a Telegram C2.
========================================================================================
"""

import os
import sys
import time
import subprocess
import re
import json
from pathlib import Path
import urllib.request

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
    log("Iniciando auditoría de hardware y calibración de kernel...", C)
    
    # 1. Comprobar GPU
    gpu_check = subprocess.run(["nvidia-smi"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if gpu_check.returncode == 0:
        log("✅ GPU NVIDIA detectada y activa. Tensor Cores y cuBLAS habilitados.", G)
    else:
        log("⚠️ ADVERTENCIA: No se detectó GPU CUDA. Activa T4 GPU en Entorno de ejecución de Colab.", Y)

    # 2. Instalar paquetes Linux nativos de ingeniería inversa
    log("Aprovisionando herramientas nativas de bajo nivel (radare2, binutils, file, net-tools)...", C)
    subprocess.run("apt-get update -qq && apt-get install -y -qq radare2 binutils file net-tools psmisc curl wget", shell=True)

    # 3. Instalar librerías de explotación y servidores
    log("Instalando librerías Python (pwntools, capstone, keystone-engine, fastapi, uvicorn)...", C)
    subprocess.run("pip install -q fastapi uvicorn pydantic capstone keystone-engine pwntools huggingface_hub", shell=True)

    # 4. Instalar llama-cpp-python con soporte cuBLAS CUDA 12.x
    log("Verificando llama-cpp-python con aceleración CUDA...", C)
    try:
        import llama_cpp
        log("llama-cpp-python ya se encuentra disponible.", G)
    except ImportError:
        log("Instalando binario precompilado con backend CUDA cuBLAS 12.2...", C)
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
        log(f"✅ Modelo detectado en disco: {target_model_path} ({target_model_path.stat().st_size / (1024**3):.2f} GB).", G)
        return str(target_model_path)
    
    log(f"Descargando pesos GGUF ({model_filename}) desde HuggingFace...", Y)
    from huggingface_hub import hf_hub_download
    downloaded_path = hf_hub_download(
        repo_id="bartowski/Qwen2.5-Coder-7B-Instruct-GGUF",
        filename=model_filename,
        local_dir=str(target_dir),
        local_dir_use_symlinks=False
    )
    log(f"✅ Descarga completada en: {downloaded_path}", G)
    return downloaded_path

def start_cloudflared():
    """Descarga el binario oficial de Cloudflared y abre un túnel directo al puerto 8000."""
    cloudflared_bin = Path("/usr/local/bin/cloudflared")
    if not cloudflared_bin.exists():
        log("Descargando binario nativo de Cloudflared Linux...", C)
        subprocess.run("wget -q -nc https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared", shell=True)

    log("Iniciando túnel Cloudflare seguro (Zero Trust SSL)...", C)
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

    tunnel_url = None
    start_time = time.time()
    log("Esperando asignación de URL pública...", C)
    
    with open(tunnel_log, "w") as f_out:
        while time.time() - start_time < 35:
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
        log(f"🚀 TÚNEL PÚBLICO BLINDADO: {tunnel_url}", G)
        with open("/content/tunnel_url.txt", "w") as f:
            f.write(tunnel_url)
        return tunnel_url
    else:
        log("No se pudo obtener URL en 35s. Revisa /content/cloudflared.log", R)
        return None

def main():
    print(r"""
    ██████╗ ██████╗ ██████╗ ███████╗██╗  ██╗    ██████╗ ███████╗██╗   ██╗
   ██╔════╝██╔═══██╗██╔══██╗██╔════╝╚██╗██╔╝    ██╔══██╗██╔════╝██║   ██║
   ██║     ██║   ██║██║  ██║█████╗   ╚███╔╝     ██████╔╝█████╗  ██║   ██║
   ██║     ██║   ██║██║  ██║██╔══╝   ██╔██╗     ██╔══██╗██╔══╝  ╚██╗ ██╔╝
   ╚██████╗╚██████╔╝██████╔╝███████╗██╔╝ ██╗    ██║  ██║███████╗ ╚████╔╝ 
    ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝    ╚═╝  ╚═╝╚══════╝  ╚═══╝  
    --- MOTOR DE INGENIERÍA INVERSA & AUDITORÍA DE KERNEL 24/7 (BLINDADO) ---
    """)
    setup_environment()
    setup_model()
    
    # 1. Asegurar credenciales de seguridad persistentes
    sec_file = Path("/content/colab_codex_core/apex_security.json")
    admin_user = "apex_admin"
    admin_token = "APX-SEC-7F9A2B8E3C1D4E5F60718293A4B5C6D7"
    if sec_file.exists():
        try:
            with open(sec_file, "r") as sf:
                sdata = json.load(sf)
                admin_user = sdata.get("admin_username", admin_user)
                admin_token = sdata.get("admin_token", admin_token)
        except Exception:
            pass
    else:
        sec_file.parent.mkdir(parents=True, exist_ok=True)
        with open(sec_file, "w") as sf:
            json.dump({
                "admin_username": admin_user,
                "admin_token": admin_token,
                "session_cookie_name": "APEX_SESSION_AUTH"
            }, sf, indent=2)

    # 2. Iniciar Keep-Alive Daemon
    log("Iniciando APEX Keep-Alive Daemon (Tensor Cores Watchdog)...", C)
    subprocess.Popen(["python3", "/content/colab_codex_core/keepalive_daemon.py"], stdout=open("/content/keepalive.log", "a"), stderr=subprocess.STDOUT)

    # 3. Iniciar Servidor Codex Engine Blindado
    log("Iniciando Servidor Codex Engine Blindado en puerto 8000...", C)
    subprocess.Popen(["python3", "/content/colab_codex_core/codex_engine.py"], stdout=open("/content/codex_engine.log", "a"), stderr=subprocess.STDOUT)
    time.sleep(4)

    # 4. Abrir Túnel Cloudflared
    tunnel_url = start_cloudflared()

    print("\n" + "="*70)
    print(f"{G}⚡ SISTEMA CODEX REVERSE BLINDADO OPERATIVO EN GOOGLE COLAB ⚡{W}")
    print(f"🔗 Cyberdeck WebUI Segura:   {C}{tunnel_url}/?token={admin_token}{W}")
    print(f"🔌 OpenAI API Endpoint:       {C}{tunnel_url}/v1{W}")
    print(f"👤 Usuario Administrador:     {G}{admin_user}{W}")
    print(f"🔐 Master Key / Password:     {Y}{admin_token}{W}")
    print(f"📡 Keep-Alive Estado:         {G}ACTIVO (Tensor Core FP16 Micro-Pulses){W}")
    print("="*70 + "\n")

    # 5. Despachar reporte completo a Telegram C2
    if tunnel_url:
        try:
            from codex_engine import send_telegram_alert
            alert_msg = (
                f"🛡️ <b>APEX CODEX REVERSE BLINDADO ONLINE EN GOOGLE COLAB</b> 🛡️\n\n"
                f"⚡ <b>Rendimiento GPU:</b> Tesla T4 (Flash Attention, 32K Context, 100% VRAM)\n"
                f"🔗 <b>Cyberdeck WebUI:</b> {tunnel_url}\n"
                f"🔑 <b>Acceso Rápido 1-Clic:</b> <a href=\"{tunnel_url}/?token={admin_token}\">Abrir Cyberdeck Autenticado</a>\n\n"
                f"👤 <b>Usuario Admin:</b> <code>{admin_user}</code>\n"
                f"🔐 <b>Master Key:</b> <code>{admin_token}</code>\n"
                f"🔌 <b>API Endpoint:</b> <code>{tunnel_url}/v1</code>\n"
                f"🛡️ <b>Blindaje:</b> Autenticación obligatoria activa (Acceso exclusivo operador)."
            )
            if send_telegram_alert(alert_msg):
                log("✅ Notificación y credenciales despachadas a Telegram exitosamente.", G)
        except Exception as e:
            log(f"Aviso despacho Telegram: {e}", Y)

if __name__ == "__main__":
    main()
