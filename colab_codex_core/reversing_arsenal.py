#!/usr/bin/env python3
"""
========================================================================================
💀 APEX REVERSING ARSENAL — LINUX NATIVE BINARY ANALYSIS TOOLKIT 💀
========================================================================================
Módulo de instrumentación estática, dinámica y binaria para el motor Codex Reverse.
Expone wrappers directos sobre:
- checksec (Mitigaciones de binario: NX, Canary, PIE, RELRO)
- capstone / keystone (Desensamblado y ensamblado multiaquitectura)
- radare2 / r2pipe (Extracción de funciones, cadenas, llamadas y CFG)
- pwntools (Generación de patrones cíclicos, offsets, shellcode y ROP)
- Análisis de entropía y heurística de algoritmos criptográficos/empaquetado
========================================================================================
"""

import os
import sys
import math
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

class ReversingArsenal:
    @staticmethod
    def inspect_file(filepath: str) -> Dict[str, Any]:
        """Extrae metadata básica con 'file' y 'readelf'."""
        if not os.path.exists(filepath):
            return {"error": f"Archivo no encontrado: {filepath}"}
            
        result = {
            "path": filepath,
            "size_bytes": os.path.getsize(filepath),
            "file_type": "Unknown",
            "arch": "Unknown",
            "is_elf": False,
            "is_pe": False
        }
        
        # Ejecutar 'file'
        try:
            p_file = subprocess.run(["file", "-b", filepath], capture_output=True, text=True, timeout=5)
            result["file_type"] = p_file.stdout.strip()
            if "ELF" in result["file_type"]:
                result["is_elf"] = True
            elif "PE32" in result["file_type"] or "MS-DOS" in result["file_type"]:
                result["is_pe"] = True
        except Exception as e:
            result["file_error"] = str(e)
            
        return result

    @staticmethod
    def run_checksec(filepath: str) -> Dict[str, str]:
        """Ejecuta checksec sobre un binario ELF para determinar mitigaciones."""
        if not os.path.exists(filepath):
            return {"error": "Archivo no existe"}
            
        mitigations = {
            "RELRO": "Unknown",
            "Stack Canary": "Unknown",
            "NX": "Unknown",
            "PIE": "Unknown",
            "RPATH": "None",
            "RUNPATH": "None",
            "Symbols": "Unknown"
        }
        
        # Intentar pwntools primero si está instalado
        try:
            from pwn import ELF
            elf = ELF(filepath, checksec=False)
            mitigations["RELRO"] = str(elf.relro)
            mitigations["Stack Canary"] = "Enabled" if elf.canary else "Disabled"
            mitigations["NX"] = "Enabled" if elf.nx else "Disabled"
            mitigations["PIE"] = "Enabled" if elf.pie else "Disabled"
            mitigations["Arch"] = f"{elf.arch} ({elf.bits} bits, {elf.endian})"
            return mitigations
        except Exception:
            pass

        # Fallback a comando checksec o readelf
        try:
            res = subprocess.run(["checksec", "--file=" + filepath], capture_output=True, text=True, timeout=5)
            raw = res.stdout + res.stderr
            for line in raw.splitlines():
                if "RELRO:" in line: mitigations["RELRO"] = line.split("RELRO:")[-1].strip()
                if "Stack:" in line or "Canary:" in line: mitigations["Stack Canary"] = line.strip()
                if "NX:" in line: mitigations["NX"] = line.split("NX:")[-1].strip()
                if "PIE:" in line: mitigations["PIE"] = line.split("PIE:")[-1].strip()
        except Exception as e:
            mitigations["error"] = str(e)
            
        return mitigations

    @staticmethod
    def extract_strings(filepath: str, min_len: int = 6, limit: int = 50) -> List[str]:
        """Extrae cadenas imprimibles de interés."""
        if not os.path.exists(filepath):
            return []
        try:
            p = subprocess.run(["strings", "-n", str(min_len), filepath], capture_output=True, text=True, timeout=10)
            lines = [l.strip() for l in p.stdout.splitlines() if l.strip()]
            return lines[:limit]
        except Exception:
            return []

    @staticmethod
    def calculate_entropy(filepath: str) -> float:
        """Calcula la entropía de Shannon del archivo (0.0 a 8.0). >7.2 indica cifrado o compresión (UPX)."""
        if not os.path.exists(filepath):
            return 0.0
        try:
            with open(filepath, "rb") as f:
                data = f.read()
            if not data:
                return 0.0
            byte_counts = [0] * 256
            for b in data:
                byte_counts[b] += 1
            entropy = 0.0
            total = len(data)
            for count in byte_counts:
                if count > 0:
                    p = count / total
                    entropy -= p * math.log2(p)
            return round(entropy, 4)
        except Exception:
            return 0.0

    @staticmethod
    def disassemble_raw_bytes(hex_bytes: str, arch: str = "x86_64", base_addr: int = 0x1000) -> List[str]:
        """
        Desensambla una cadena hexadecimal o shellcode usando Capstone.
        Soporta x86, x86_64, arm, arm64, mips.
        """
        try:
            from capstone import Cs, CS_ARCH_X86, CS_MODE_64, CS_MODE_32, CS_ARCH_ARM, CS_MODE_ARM, CS_ARCH_ARM64
        except ImportError:
            return ["Error: Capstone no está instalado. Ejecuta 'pip install capstone'."]

        clean_hex = hex_bytes.replace(" ", "").replace("\\x", "").replace("\n", "").strip()
        try:
            code = bytes.fromhex(clean_hex)
        except ValueError as ve:
            return [f"Hexadecimal inválido: {ve}"]

        if arch.lower() in ("x86_64", "x64", "amd64"):
            md = Cs(CS_ARCH_X86, CS_MODE_64)
        elif arch.lower() in ("x86", "i386", "32"):
            md = Cs(CS_ARCH_X86, CS_MODE_32)
        elif arch.lower() in ("arm64", "aarch64"):
            md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
        elif arch.lower() in ("arm", "arm32"):
            md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
        else:
            md = Cs(CS_ARCH_X86, CS_MODE_64)

        instructions = []
        for i in md.disasm(code, base_addr):
            instructions.append(f"0x{i.address:x}:\t{i.mnemonic}\t{i.op_str}")
            
        return instructions if instructions else ["No se pudieron desensamblar instrucciones válidas."]

    @staticmethod
    def assemble_asm(asm_code: str, arch: str = "x86_64") -> Dict[str, Any]:
        """
        Ensambla código ASM a bytes de máquina / shellcode usando Keystone.
        """
        try:
            from keystone import Ks, KS_ARCH_X86, KS_MODE_64, KS_MODE_32, KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN
        except ImportError:
            return {"error": "Keystone no instalado. Ejecuta 'pip install keystone-engine'."}

        if arch.lower() in ("x86_64", "x64"):
            ks = Ks(KS_ARCH_X86, KS_MODE_64)
        elif arch.lower() in ("x86", "32"):
            ks = Ks(KS_ARCH_X86, KS_MODE_32)
        elif arch.lower() in ("arm64", "aarch64"):
            ks = Ks(KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN)
        else:
            ks = Ks(KS_ARCH_X86, KS_MODE_64)

        try:
            encoding, count = ks.asm(asm_code)
            raw_bytes = bytes(encoding)
            hex_str = raw_bytes.hex()
            c_style = "".join([f"\\x{b:02x}" for b in raw_bytes])
            return {
                "count": count,
                "length": len(raw_bytes),
                "hex": hex_str,
                "c_string": c_style,
                "raw_bytes": list(raw_bytes)
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def radare2_disasm_function(filepath: str, function_name: str = "main") -> str:
        """
        Desensambla una función específica de un binario usando radare2.
        """
        if not shutil.which("r2"):
            return "radare2 ('r2') no está disponible en el PATH del sistema."
            
        cmd = f"r2 -q -c 'aaa; s {function_name}; pdf' {filepath}"
        try:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=20)
            output = res.stdout.strip()
            if not output:
                return f"No se encontró salida para la función '{function_name}'. Revisa el nombre o ejecuta sobre símbolos existentes."
            return output
        except Exception as e:
            return f"Error ejecutando radare2: {e}"

    @staticmethod
    def generate_cyclic_pattern(length: int = 200) -> str:
        """Genera un patrón de Bruijn (De Bruijn sequence) para calcular offsets de desbordamiento."""
        try:
            from pwn import cyclic
            return cyclic(length).decode("latin-1", errors="ignore")
        except Exception:
            # Implementación De Bruijn nativa de respaldo
            charset = "abcdefghijklmnopqrstuvwxyz"
            res = []
            for a in charset:
                for b in charset:
                    for c in charset:
                        for d in charset:
                            res.append(a + b + c + d)
                            if len("".join(res)) >= length:
                                return "".join(res)[:length]
            return "".join(res)[:length]

    @staticmethod
    def find_cyclic_offset(pattern_substr: str) -> int:
        """Calcula el offset dentro del patrón De Bruijn."""
        try:
            from pwn import cyclic_find
            return cyclic_find(pattern_substr)
        except Exception:
            # Búsqueda manual
            pattern = ReversingArsenal.generate_cyclic_pattern(10000)
            idx = pattern.find(pattern_substr)
            return idx
