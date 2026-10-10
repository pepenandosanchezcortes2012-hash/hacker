#!/usr/bin/env python3
"""
========================================================================================
💀 APEX REVERSING ARSENAL — UNRESTRICTED BINARY & KERNEL ANALYSIS TOOLKIT 💀
========================================================================================
Módulo de instrumentación estática, dinámica y binaria de alto rendimiento para el
motor Codex Reverse. Diseñado sin limitaciones artificiales de procesamiento:
- checksec / ELF Mitigations (NX, Canary, PIE, RELRO, Fortify, ASLR)
- Capstone / Keystone (Desensamblado y ensamblado multi-arquitectura x86/ARM/MIPS)
- Radare2 / r2pipe (Decompilación, deconstrucción CFG y extracción de símbolos)
- Pwntools (Patrones cíclicos De Bruijn, shellcode, offsets y ROP)
- Análisis de entropía de Shannon y detección de empaquetadores/cifrado (UPX/AES)
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
        """Extrae metadata técnica y firmas de bajo nivel de archivos y binarios."""
        if not os.path.exists(filepath):
            return {"error": f"Archivo no encontrado en sistema de archivos: {filepath}"}
            
        result = {
            "path": filepath,
            "size_bytes": os.path.getsize(filepath),
            "file_type": "Unknown",
            "is_elf": False,
            "is_pe": False,
            "is_mach_o": False
        }
        
        try:
            p_file = subprocess.run(["file", "-b", filepath], capture_output=True, text=True, timeout=15)
            result["file_type"] = p_file.stdout.strip()
            upper_ft = result["file_type"].upper()
            if "ELF" in upper_ft:
                result["is_elf"] = True
            elif "PE32" in upper_ft or "MS-DOS" in upper_ft:
                result["is_pe"] = True
            elif "MACH-O" in upper_ft:
                result["is_mach_o"] = True
        except Exception as e:
            result["file_error"] = str(e)
            
        return result

    @staticmethod
    def run_checksec(filepath: str) -> Dict[str, Any]:
        """Audita exhaustivamente todas las mitigaciones de seguridad activas en el binario ELF."""
        if not os.path.exists(filepath):
            return {"error": f"Archivo no existe: {filepath}"}
            
        mitigations = {
            "RELRO": "Unknown",
            "Stack Canary": "Unknown",
            "NX": "Unknown",
            "PIE": "Unknown",
            "RPATH": "None",
            "RUNPATH": "None",
            "Fortify": "Unknown",
            "Symbols": "Unknown"
        }
        
        # 1. Inspección de primer orden con Pwntools ELF
        try:
            from pwn import ELF
            elf = ELF(filepath, checksec=False)
            mitigations["RELRO"] = str(elf.relro)
            mitigations["Stack Canary"] = "Enabled" if elf.canary else "Disabled"
            mitigations["NX"] = "Enabled" if elf.nx else "Disabled"
            mitigations["PIE"] = "Enabled" if elf.pie else "Disabled"
            mitigations["Arch"] = f"{elf.arch} ({elf.bits} bits, {elf.endian})"
            mitigations["Symbols"] = "Present" if elf.sym else "Stripped"
            mitigations["Entrypoint"] = hex(elf.entry) if hasattr(elf, "entry") else "N/A"
            return mitigations
        except Exception:
            pass

        # 2. Fallback a binario nativo checksec o readelf
        try:
            res = subprocess.run(["checksec", "--file=" + filepath], capture_output=True, text=True, timeout=15)
            raw = res.stdout + res.stderr
            for line in raw.splitlines():
                if "RELRO:" in line: mitigations["RELRO"] = line.split("RELRO:")[-1].strip()
                if "Stack:" in line or "Canary:" in line: mitigations["Stack Canary"] = line.strip()
                if "NX:" in line: mitigations["NX"] = line.split("NX:")[-1].strip()
                if "PIE:" in line: mitigations["PIE"] = line.split("PIE:")[-1].strip()
                if "RPATH:" in line: mitigations["RPATH"] = line.split("RPATH:")[-1].strip()
                if "RUNPATH:" in line: mitigations["RUNPATH"] = line.split("RUNPATH:")[-1].strip()
                if "Symbols:" in line: mitigations["Symbols"] = line.split("Symbols:")[-1].strip()
        except Exception as e:
            mitigations["error"] = str(e)
            
        return mitigations

    @staticmethod
    def extract_strings(filepath: str, min_len: int = 4, limit: int = 500) -> List[str]:
        """Extrae cadenas ASCII y UTF-8 legibles sin restricciones artificiales."""
        if not os.path.exists(filepath):
            return []
        try:
            p = subprocess.run(["strings", "-n", str(min_len), filepath], capture_output=True, text=True, timeout=20)
            lines = [l.strip() for l in p.stdout.splitlines() if l.strip()]
            return lines if limit is None or limit <= 0 else lines[:limit]
        except Exception:
            return []

    @staticmethod
    def calculate_entropy(filepath: str) -> float:
        """
        Calcula la entropía de Shannon precisa (0.0 a 8.0 bits por byte).
        - Entropía < 6.0: Código o texto plano no ofuscado.
        - Entropía entre 6.0 y 7.2: Binario compilado estándar.
        - Entropía > 7.2: Alta probabilidad de empaquetado (UPX) o cifrado criptográfico.
        """
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
        Desensambla secuencias de bytes binarios o shellcode usando Capstone.
        Soporta arquitecturas: x86_64, x86, arm64, arm32, mips.
        """
        try:
            from capstone import Cs, CS_ARCH_X86, CS_MODE_64, CS_MODE_32, CS_ARCH_ARM, CS_MODE_ARM, CS_ARCH_ARM64, CS_ARCH_MIPS, CS_MODE_MIPS32
        except ImportError:
            return ["Error: Librería Capstone no disponible. Instala con 'pip install capstone'."]

        clean_hex = hex_bytes.replace(" ", "").replace("\\x", "").replace("0x", "").replace("\n", "").replace(",", "").strip()
        try:
            code = bytes.fromhex(clean_hex)
        except ValueError as ve:
            return [f"Hexadecimal inválido: {ve}"]

        arch_clean = arch.lower().strip()
        if arch_clean in ("x86_64", "x64", "amd64"):
            md = Cs(CS_ARCH_X86, CS_MODE_64)
        elif arch_clean in ("x86", "i386", "32"):
            md = Cs(CS_ARCH_X86, CS_MODE_32)
        elif arch_clean in ("arm64", "aarch64"):
            md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
        elif arch_clean in ("arm", "arm32"):
            md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
        elif arch_clean in ("mips", "mips32"):
            md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32)
        else:
            md = Cs(CS_ARCH_X86, CS_MODE_64)

        instructions = []
        for i in md.disasm(code, base_addr):
            instructions.append(f"0x{i.address:08x}:\t{i.mnemonic:<8}\t{i.op_str}")
            
        return instructions if instructions else ["No se decodificaron instrucciones válidas para la arquitectura especificada."]

    @staticmethod
    def assemble_asm(asm_code: str, arch: str = "x86_64") -> Dict[str, Any]:
        """
        Ensambla código ASM de bajo nivel a código de máquina (opcodes/shellcode) mediante Keystone.
        """
        try:
            from keystone import Ks, KS_ARCH_X86, KS_MODE_64, KS_MODE_32, KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN
        except ImportError:
            return {"error": "Keystone no instalado. Instala con 'pip install keystone-engine'."}

        arch_clean = arch.lower().strip()
        if arch_clean in ("x86_64", "x64"):
            ks = Ks(KS_ARCH_X86, KS_MODE_64)
        elif arch_clean in ("x86", "32"):
            ks = Ks(KS_ARCH_X86, KS_MODE_32)
        elif arch_clean in ("arm64", "aarch64"):
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
        Deconstruye y desensambla el flujo de control (CFG) de una función binaria con radare2.
        """
        if not shutil.which("r2"):
            return "radare2 ('r2') no está disponible en el PATH del sistema."
            
        cmd = f"r2 -q -c 'aaa; s {function_name}; pdf' {filepath}"
        try:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
            output = res.stdout.strip()
            if not output:
                return f"No se encontró salida para la función '{function_name}'. Verifica símbolos o direcciones con 'afl'."
            return output
        except Exception as e:
            return f"Error ejecutando radare2: {e}"

    @staticmethod
    def generate_cyclic_pattern(length: int = 200) -> str:
        """Genera una secuencia de Bruijn única para calcular distancias de desbordamiento en el stack."""
        try:
            from pwn import cyclic
            return cyclic(length).decode("latin-1", errors="ignore")
        except Exception:
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
        """Determina el desplazamiento exacto (offset) del crash dentro del patrón de Bruijn."""
        try:
            from pwn import cyclic_find
            return cyclic_find(pattern_substr)
        except Exception:
            pattern = ReversingArsenal.generate_cyclic_pattern(20000)
            return pattern.find(pattern_substr)
