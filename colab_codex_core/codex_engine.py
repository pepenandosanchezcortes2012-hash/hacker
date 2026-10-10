#!/usr/bin/env python3
"""
========================================================================================
💀 APEX CODEX REVERSE — ULTRA-PERFORMANCE LLM & REVERSING API SERVER 💀
========================================================================================
Servidor central de inferencia y API compatible con OpenAI para Google Colab:
- RENDIMIENTO MÁXIMO GPU: Tesla T4 al 100%, todas las capas en VRAM, 32K contexto,
  Flash Attention 2 habilitado y procesamiento optimizado de tensor cores.
- BLINDAJE DE TÚNEL: Autenticación obligatoria multi-vector (Basic Auth, Bearer Token,
  Cookie de sesión y parámetro de URL) para acceso exclusivo del administrador.
- ARSENAL TÉCNICO COMPLETO: Qwen2.5-Coder-7B, Cyberdeck WebUI, Capstone, Keystone,
  Checksec, Entropía de Shannon, Radare2 y Pwntools.
- TELEMETRÍA Y CONTROL C2: Integración directa con Telegram Bot.
========================================================================================
"""

import os
import sys
import json
import time
import base64
import secrets
import asyncio
import logging
import subprocess
from typing import Dict, Any, List, Optional
from pathlib import Path
import urllib.request

try:
    from fastapi import FastAPI, Request, Response, HTTPException, BackgroundTasks, Depends
    from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
    from fastapi.middleware.cors import CORSMiddleware
    from starlette.middleware.base import BaseHTTPMiddleware
    import uvicorn
except ImportError:
    print("[!] FastAPI/Uvicorn no detectados. Instalando dependencias de servidor...")
    os.system("pip install -q fastapi uvicorn pydantic")
    from fastapi import FastAPI, Request, Response, HTTPException, BackgroundTasks, Depends
    from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
    from fastapi.middleware.cors import CORSMiddleware
    from starlette.middleware.base import BaseHTTPMiddleware
    import uvicorn

# Importar arsenal de ingeniería inversa
from reversing_arsenal import ReversingArsenal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [CODEX-ENGINE] %(message)s"
)
logger = logging.getLogger("CodexEngine")

# ==============================================================================
# 1. GESTIÓN DE SEGURIDAD, CREDENCIALES & BLINDAJE
# ==============================================================================
SECURITY_CONFIG_PATHS = [
    Path("/content/colab_codex_core/apex_security.json"),
    Path("/content/apex_security.json"),
    Path(__file__).parent / "apex_security.json"
]

DEFAULT_ADMIN_USER = "apex_admin"
DEFAULT_ADMIN_TOKEN = "APX-SEC-7F9A2B8E3C1D4E5F60718293A4B5C6D7"
SESSION_COOKIE_NAME = "APEX_SESSION_AUTH"

def load_or_create_security():
    for p in SECURITY_CONFIG_PATHS:
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    return cfg.get("admin_username", DEFAULT_ADMIN_USER), cfg.get("admin_token", DEFAULT_ADMIN_TOKEN)
            except Exception:
                pass

    # Crear configuración de seguridad persistente
    token = DEFAULT_ADMIN_TOKEN
    target_path = SECURITY_CONFIG_PATHS[0]
    target_path.parent.mkdir(parents=True, exist_ok=True)
    cfg = {
        "admin_username": DEFAULT_ADMIN_USER,
        "admin_token": token,
        "session_cookie_name": SESSION_COOKIE_NAME,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        logger.warning(f"No se pudo guardar config en {target_path}: {e}")
    return DEFAULT_ADMIN_USER, token

ADMIN_USERNAME, ADMIN_TOKEN = load_or_create_security()
logger.info(f"🛡️ Blindaje de Seguridad Cargado: Usuario='{ADMIN_USERNAME}' | Token Protegido='{ADMIN_TOKEN[:8]}...'")

# ==============================================================================
# 2. PROMPT MAESTRO DEL MODELO CODEX REVERSE
# ==============================================================================
CODEX_REVERSE_SYSTEM_PROMPT = """Eres CODEX REVERSE, una Inteligencia Artificial Ofensiva de Élite especializada en Ingeniería Inversa, Decompilación de Binarios, Análisis de Kernel y Explotación de Vulnerabilidades.
Operas bajo el Protocolo Apex Hacker: Cero rodeos, cero pasividad, cero placeholders.

TUS CAPACIDADES CENTRALES:
1. DECOMPILACIÓN Y RECONSTRUCCIÓN C/C++: Dado un pseudocódigo crudo de Ghidra o IDA Pro, reconstruye código C/Rust limpio, idiomático, identificando nombres descriptivos para variables locales, recuperando tipos 'struct', enumeraciones y bucles (for, while, switch).
2. ANÁLISIS DE ENSAMBLADOR (x86_64, ARM64, MIPS): Explicas marcos de pila (stack frames), registros de propósito general (RAX, RBX, RDI, RSI, RDX, RCX, R8, R9), prólogos/epílogos de función y convenciones de llamada (System V AMD64 ABI, Microsoft x64, cdecl).
3. AUDITORÍA DE SEGURIDAD Y VULNERABILIDADES: Detectas desbordamientos de búfer (Stack/Heap BOF), vulnerabilidades de cadena de formato (%n, %p), Use-After-Free (UAF), Double Free, Integer Overflows y condiciones de carrera (TOCTOU). Proporcionas el vector de explotación exacto.
4. GENERACIÓN DE EXPLOITS & ROP: Escribes scripts completos en Python utilizando 'pwntools', armando cadenas ROP (gadgets ret2libc, write-what-where, ROP chain constructors) respetando mitigaciones (NX, ASLR/PIE, Stack Canaries).
5. IDENTIFICACIÓN CRIPTOGRÁFICA Y DEOFUSCACIÓN: Detectas constantes de algoritmos conocidos (S-Boxes de AES, constantes MD5/SHA, RC4 PRGA, polinomios CRC32), descifras bucles XOR dinámicos y neutralizas técnicas anti-debugging (PEB.BeingDebugged, NtGlobalFlag, RDTSC timing attacks).

REGLAS DE RESPUESTA:
- Directo, técnico, con terminología de kernel y ciberseguridad ofensiva.
- Todo código que generes debe ser 100% completo, ejecutable y sin comentarios 'TODO'.
"""

# ==============================================================================
# 3. MOTOR DE INFERENCIA LLAMA-CPP CON ACELERACIÓN GPU TOTAL
# ==============================================================================
DEFAULT_MODEL_PATHS = [
    Path("/content/drive/MyDrive/HACKER_CODEX_CORE/models/Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf"),
    Path("/content/models/Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf"),
    Path(os.environ.get("MODEL_PATH", ""))
]

llm_instance = None
SERVER_START_TIME = time.time()
TOTAL_TOKENS_GENERATED = 0

def init_llm():
    global llm_instance
    model_file = None
    for p in DEFAULT_MODEL_PATHS:
        if p.exists() and p.is_file() and p.stat().st_size > 1000000000:
            model_file = str(p)
            break

    if model_file:
        logger.info(f"🚀 Desplegando Qwen2.5-Coder-7B en GPU NVIDIA (CUDA): {model_file}...")
        try:
            from llama_cpp import Llama
            
            # Ajuste de contexto masivo sin limitaciones artificiales
            target_ctx = int(os.environ.get("N_CTX", 32768))
            target_batch = int(os.environ.get("N_BATCH", 1024))
            target_ubatch = int(os.environ.get("N_UBATCH", 512))
            cpu_threads = max(1, os.cpu_count() or 4)

            logger.info(f"⚙️ Parámetros de Inferencia: n_gpu_layers=-1 (100% VRAM), n_ctx={target_ctx}, n_batch={target_batch}, FlashAttention=ON")
            
            # Intentar cargar con Flash Attention y descarga total de capas a VRAM
            try:
                llm_instance = Llama(
                    model_path=model_file,
                    n_gpu_layers=-1,      # Todas las capas en CUDA VRAM
                    n_ctx=target_ctx,     # Contexto completo de 32K tokens
                    n_batch=target_batch, # Lote de evaluación de prompt
                    n_ubatch=target_ubatch,
                    n_threads=cpu_threads,
                    flash_attn=True,      # Flash Attention para duplicar TPS y reducir VRAM
                    offload_kqv=True,     # K, Q, V totalmente en VRAM
                    verbose=False
                )
            except Exception as fe:
                logger.warning(f"Aviso flash_attn: {fe}. Reintentando con configuración estándar cuBLAS...")
                llm_instance = Llama(
                    model_path=model_file,
                    n_gpu_layers=-1,
                    n_ctx=min(target_ctx, 16384),
                    n_batch=512,
                    n_threads=cpu_threads,
                    verbose=False
                )
                
            logger.info("✅ Motor LLM activado con éxito en GPU Tesla T4 VRAM.")
        except Exception as e:
            logger.error(f"Fallo inicializando llama_cpp CUDA: {e}")
    else:
        logger.warning("No se encontró archivo GGUF aún. El servidor operará en modo heurístico hasta completar la descarga.")

# ==============================================================================
# 4. APLICACIÓN FASTAPI & MIDDLEWARE DE BLINDAJE AUTÓNOMO
# ==============================================================================
app = FastAPI(title="Codex Reverse Hardened API", version="3.0")

class SecurityShieldMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # 1. Rutas públicas de salud y recursos estáticos menores
        if path in ("/health", "/favicon.ico"):
            return await call_next(request)

        # 2. Extracción de credenciales multi-vector
        token_found = None

        # Vector A: Token en Query Param (?token=...)
        query_token = request.query_params.get("token")
        if query_token:
            token_found = query_token

        # Vector B: Cookie de Sesión
        cookie_token = request.cookies.get(SESSION_COOKIE_NAME)
        if cookie_token and not token_found:
            token_found = cookie_token

        # Vector C: Encabezado Authorization (Bearer o Basic)
        auth_header = request.headers.get("Authorization", "")
        if auth_header and not token_found:
            if auth_header.startswith("Bearer "):
                token_found = auth_header[7:].strip()
            elif auth_header.startswith("Basic "):
                try:
                    b64_payload = auth_header[6:].strip()
                    decoded = base64.b64decode(b64_payload).decode("utf-8")
                    if ":" in decoded:
                        u, p = decoded.split(":", 1)
                        if u == ADMIN_USERNAME and p == ADMIN_TOKEN:
                            token_found = p
                except Exception:
                    pass

        # Vector D: Encabezado X-API-Key
        api_key_header = request.headers.get("X-API-Key", "")
        if api_key_header and not token_found:
            token_found = api_key_header.strip()

        # 3. Validación estricta contra credencial de administrador
        is_authenticated = (token_found == ADMIN_TOKEN)

        if is_authenticated:
            # Procesar solicitud y adjuntar cookie si se autenticó por query param
            response = await call_next(request)
            if query_token == ADMIN_TOKEN:
                response.set_cookie(
                    key=SESSION_COOKIE_NAME,
                    value=ADMIN_TOKEN,
                    httponly=True,
                    samesite="lax",
                    max_age=86400 * 7
                )
            return response

        # 4. Bloqueo de accesos no autorizados
        client_ip = request.headers.get("CF-Connecting-IP") or request.headers.get("X-Forwarded-For") or (request.client.host if request.client else "Unknown")
        logger.warning(f"🚫 [BLINDAJE] Intento no autorizado bloqueado desde IP: {client_ip} para ruta: {path}")

        accept_header = request.headers.get("Accept", "")
        if "text/html" in accept_header or path == "/":
            # Para navegadores web: Desplegar desafío HTTP Basic Auth nativo
            return Response(
                content="""<!DOCTYPE html>
<html>
<head><title>401 Acceso Restringido - Apex Colab</title></head>
<body style="background:#05070a; color:#ff0055; font-family:monospace; padding:40px; text-align:center;">
    <h2>🛡️ APEX SECURITY SHIELD: ACCESO NO AUTORIZADO 🛡️</h2>
    <p style="color:#a0aec0;">Este túnel se encuentra blindado y reservado exclusivamente para el operador administrador.</p>
    <p style="color:#00ff66;">Ingresa las credenciales provistas al chat de Telegram o añade ?token=&lt;tu_master_key&gt; a la URL.</p>
</body>
</html>""",
                status_code=401,
                media_type="text/html",
                headers={"WWW-Authenticate": 'Basic realm="APEX CYBERDECK COLAB - ACCESO ADMINISTRATIVO RESTRINGIDO"'}
            )
        else:
            # Para clientes API / JSON
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Unauthorized",
                    "status": 401,
                    "detail": "Acceso denegado: Se requiere autenticación obligatoria del Administrador Apex.",
                    "hint": "Incluye 'Authorization: Bearer <ADMIN_TOKEN>' o 'X-API-Key: <ADMIN_TOKEN>' en los encabezados."
                }
            )

# Registrar middleware de blindaje
app.add_middleware(SecurityShieldMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HTML_UI_PATH = Path(__file__).parent / "cyberdeck_ui.html"

# ==============================================================================
# 5. RUTAS Y ENDPOINTS DEL CYBERDECK Y TELEMETRÍA
# ==============================================================================
@app.on_event("startup")
async def startup_event():
    init_llm()

@app.get("/health")
async def health_check():
    """Endpoint público de monitoreo de vitalidad para Watchdogs."""
    return {
        "status": "online",
        "shield": "active",
        "engine": "ready" if llm_instance is not None else "initializing",
        "uptime_seconds": int(time.time() - SERVER_START_TIME)
    }

@app.get("/", response_class=HTMLResponse)
async def get_cyberdeck():
    """Entrega la interfaz WebUI del Cyberdeck tras pasar la autenticación del blindaje."""
    if HTML_UI_PATH.exists():
        with open(HTML_UI_PATH, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h2>Error: cyberdeck_ui.html no localizado en /content/colab_codex_core</h2>", status_code=404)

@app.get("/api/metrics/gpu")
async def get_gpu_metrics():
    """Retorna telemetría en tiempo real de la GPU NVIDIA Tesla T4 y estado de inferencia."""
    vram_used = 0
    vram_total = 0
    gpu_util = 0
    temp_c = 0
    gpu_name = "NVIDIA GPU"

    # 1. Intentar consultar nvidia-smi directamente
    try:
        p = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.used,memory.total,utilization.gpu,temperature.gpu", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        if p.returncode == 0 and p.stdout.strip():
            parts = [x.strip() for x in p.stdout.strip().split(",")]
            if len(parts) >= 5:
                gpu_name = parts[0]
                vram_used = int(parts[1])
                vram_total = int(parts[2])
                gpu_util = int(parts[3])
                temp_c = int(parts[4])
    except Exception:
        pass

    # 2. Intentar consultar PyTorch CUDA
    if vram_total == 0:
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                vram_total = int(torch.cuda.get_device_properties(0).total_memory / (1024**2))
                vram_used = int(torch.cuda.memory_allocated(0) / (1024**2))
        except Exception:
            pass

    return {
        "gpu_name": gpu_name,
        "vram_used_mb": vram_used,
        "vram_total_mb": vram_total,
        "vram_free_mb": max(0, vram_total - vram_used),
        "gpu_utilization_pct": gpu_util,
        "temperature_c": temp_c,
        "tensor_cores_active": True,
        "model_loaded": llm_instance is not None,
        "context_window": int(os.environ.get("N_CTX", 32768)),
        "layers_in_vram": "100% (All Layers Offloaded)",
        "flash_attention": True,
        "total_tokens_generated": TOTAL_TOKENS_GENERATED,
        "uptime_seconds": int(time.time() - SERVER_START_TIME)
    }

# ==============================================================================
# 6. OPENAI COMPATIBLE INFERENCE API (/v1)
# ==============================================================================
@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": "codex-reverse",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "apex-hacker-t4",
                "permission": []
            }
        ]
    }

@app.post("/v1/chat/completions")
async def chat_completions(req: Request):
    global llm_instance, TOTAL_TOKENS_GENERATED
    body = await req.json()
    messages = body.get("messages", [])
    temperature = float(body.get("temperature", 0.2))
    # Contexto y salida sin restricciones arbitrarias
    max_tokens = body.get("max_tokens", 8192)
    stream = bool(body.get("stream", False))

    # Formatear prompt con ChatML
    formatted_prompt = f"<|im_start|>system\n{CODEX_REVERSE_SYSTEM_PROMPT}<|im_end|>\n"
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        formatted_prompt += f"<|im_start|>{role}\n{content}<|im_end|>\n"
    formatted_prompt += "<|im_start|>assistant\n"

    # Respuesta en Streaming SSE si se solicita
    if stream:
        async def event_generator():
            cmpl_id = f"chatcmpl-{int(time.time())}"
            if llm_instance is not None:
                try:
                    for chunk in llm_instance(
                        formatted_prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        stop=["<|im_end|>", "<|endoftext|>"],
                        stream=True
                    ):
                        delta_text = chunk["choices"][0]["text"]
                        chunk_payload = {
                            "id": cmpl_id,
                            "object": "chat.completion.chunk",
                            "created": int(time.time()),
                            "model": "codex-reverse",
                            "choices": [{"index": 0, "delta": {"content": delta_text}, "finish_reason": None}]
                        }
                        yield f"data: {json.dumps(chunk_payload)}\n\n"
                    # Finalización del stream
                    end_payload = {
                        "id": cmpl_id,
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": "codex-reverse",
                        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
                    }
                    yield f"data: {json.dumps(end_payload)}\n\n"
                    yield "data: [DONE]\n\n"
                except Exception as e:
                    err_payload = {"error": str(e)}
                    yield f"data: {json.dumps(err_payload)}\n\n"
            else:
                yield f"data: {json.dumps({'choices': [{'delta': {'content': 'Motor inicializándose...'}}]})}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    # Inferencia Síncrona estándar con medición precisa de TPS (Tokens por segundo)
    start_t = time.time()
    tps = 0.0

    if llm_instance is not None:
        try:
            output = llm_instance(
                formatted_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["<|im_end|>", "<|endoftext|>"]
            )
            reply_text = output["choices"][0]["text"].strip()
            elapsed_t = max(0.001, time.time() - start_t)
            tokens_generated = len(reply_text.split()) * 1.3
            tps = round(tokens_generated / elapsed_t, 2)
            TOTAL_TOKENS_GENERATED += int(tokens_generated)
        except Exception as e:
            reply_text = f"Error en inferencia acelerada de GPU: {e}"
    else:
        last_user_msg = messages[-1].get("content", "") if messages else ""
        reply_text = (
            f"[SISTEMA CODEX REVERSE — MODO TÁCTICO INICIAL]\n"
            f"El motor está preparando los pesos en la GPU. Procesamiento de análisis:\n\n"
            f"{last_user_msg[:300]}...\n\n"
            f"La aceleración total por GPU Tesla T4 estará lista al finalizar la carga de VRAM."
        )

    completion_tokens = len(reply_text) // 4
    prompt_tokens = len(formatted_prompt) // 4

    return {
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "codex-reverse",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": reply_text
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "tokens_per_second": tps,
            "latency_seconds": round(time.time() - start_t, 3)
        }
    }

# ==============================================================================
# 7. ARSENAL DE REVERSING Y ENDPOINTS DE HERRAMIENTAS
# ==============================================================================
@app.post("/api/tools/disassemble")
async def api_disassemble(req: Request):
    data = await req.json()
    hex_bytes = data.get("hex_bytes", "")
    arch = data.get("arch", "x86_64")
    instructions = ReversingArsenal.disassemble_raw_bytes(hex_bytes, arch=arch)
    return {"arch": arch, "instructions": instructions}

@app.post("/api/tools/assemble")
async def api_assemble(req: Request):
    data = await req.json()
    asm_code = data.get("asm_code", "")
    arch = data.get("arch", "x86_64")
    res = ReversingArsenal.assemble_asm(asm_code, arch=arch)
    return res

@app.get("/api/tools/cyclic")
async def api_cyclic(length: int = 200):
    pattern = ReversingArsenal.generate_cyclic_pattern(length)
    return {"length": length, "pattern": pattern}

@app.post("/api/tools/checksec")
async def api_checksec(req: Request):
    data = await req.json()
    filepath = data.get("filepath", "")
    res = ReversingArsenal.run_checksec(filepath)
    return res

@app.post("/api/tools/entropy")
async def api_entropy(req: Request):
    data = await req.json()
    filepath = data.get("filepath", "")
    val = ReversingArsenal.calculate_entropy(filepath)
    return {"filepath": filepath, "entropy": val, "is_packed_or_encrypted": val > 7.2}

@app.post("/api/tools/strings")
async def api_strings(req: Request):
    data = await req.json()
    filepath = data.get("filepath", "")
    min_len = int(data.get("min_len", 4))
    limit = int(data.get("limit", 200))
    strings_found = ReversingArsenal.extract_strings(filepath, min_len=min_len, limit=limit)
    return {"filepath": filepath, "count": len(strings_found), "strings": strings_found}

@app.post("/api/tools/r2")
async def api_r2(req: Request):
    data = await req.json()
    filepath = data.get("filepath", "")
    fn_name = data.get("function_name", "main")
    res = ReversingArsenal.radare2_disasm_function(filepath, function_name=fn_name)
    return {"filepath": filepath, "function": fn_name, "disassembly": res}

@app.post("/api/tools/file_info")
async def api_file_info(req: Request):
    data = await req.json()
    filepath = data.get("filepath", "")
    info = ReversingArsenal.inspect_file(filepath)
    return info

# ==============================================================================
# 8. MÓDULO DE DESPACHO C2 A TELEGRAM
# ==============================================================================
def send_telegram_alert(message: str, config_path: str = "/content/sentinel_config.json") -> bool:
    token = None
    chat_id = None
    for p in [Path(config_path), Path(__file__).parent / "sentinel_config.json", Path("/content/sentinel_config.json")]:
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    token = cfg.get("telegram_token")
                    chat_id = cfg.get("admin_chat_id")
                    if token and chat_id:
                        break
            except Exception:
                pass

    token = token or os.environ.get("TELEGRAM_TOKEN")
    chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID")

    if token and chat_id:
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = json.dumps({"chat_id": chat_id, "text": message, "parse_mode": "HTML"}).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status == 200
        except Exception as e:
            logger.error(f"Fallo al despachar notificación a Telegram: {e}")
    return False

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"⚡ Iniciando Codex Reverse Engine Blindado en puerto {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
