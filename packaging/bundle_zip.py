#!/usr/bin/env python3
"""
Utilitário multiplataforma para empacotamento de releases do OpenValora.
Gera arquivos .zip para Windows e macOS sem depender de shells ou comandos externos.
"""
import os
import sys
import zipfile
import shutil

def get_version() -> str:
    version = "0.1.0"
    main_path = os.path.join(os.path.dirname(__file__), "..", "app", "main.py")
    if os.path.exists(main_path):
        with open(main_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("__version__"):
                    version = line.split("=")[1].strip(" \t\r\n\"'")
                    break
    return version

def bundle_windows():
    version = get_version()
    dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dist"))
    os.makedirs(dist_dir, exist_ok=True)
    
    exe_candidate = os.path.join(dist_dir, "openvalora.exe")
    if not os.path.exists(exe_candidate):
        exe_candidate = os.path.join(dist_dir, "OpenValora.exe")
    if not os.path.exists(exe_candidate):
        for root, _, files in os.walk(dist_dir):
            for file in files:
                if file.lower().endswith(".exe"):
                    exe_candidate = os.path.join(root, file)
                    break
    
    if not os.path.exists(exe_candidate):
        print(f"[bundle_zip] ERRO: Nenhum executável .exe encontrado em {dist_dir}")
        sys.exit(1)

    zip_ver = os.path.join(dist_dir, f"OpenValora-{version}-Windows-x64.zip")
    zip_latest = os.path.join(dist_dir, "OpenValora-Windows-x64.zip")

    print(f"[bundle_zip] Compactando {exe_candidate} -> {zip_ver}...")
    with zipfile.ZipFile(zip_ver, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(exe_candidate, arcname="openvalora.exe")
    
    shutil.copyfile(zip_ver, zip_latest)
    print(f"[bundle_zip] Sucesso! Pacotes criados:\n  - {zip_ver}\n  - {zip_latest}")

if __name__ == "__main__":
    bundle_windows()
