#!/usr/bin/env python3
"""Sube en bloque los payloads de DuckyScripts a la API de FleaByte.

Hay que estar conectado a la red WiFi del propio dongle al ejecutarlo.
Los nombres se prefijan con el sistema operativo porque FleaByte los
guarda todos en el mismo espacio plano, sin carpetas.

Cada archivo debería tener una línea META con OS y categoría, p.ej.:
    META windows broma
Si falta la categoría, el script sube el archivo y avisa.
"""

import getpass
import sys
import urllib.parse
import urllib.request
from pathlib import Path

DONGLE_BASE = "http://192.168.4.1"
SCRIPTS_DIR = Path.home() / "Dev" / "BadUSB" / "DuckyScripts"
OS_FOLDERS = ["windows", "linux", "macos"]
MAX_BYTES = 16384  # mismo límite que MAX_SCRIPT_BYTES en config.h


def login(password: str) -> str:
    data = urllib.parse.urlencode({"password": password}).encode()
    req = urllib.request.Request(f"{DONGLE_BASE}/api/login", data=data, method="POST")
    with urllib.request.urlopen(req, timeout=5) as resp:
        # El token llega en la cookie Set-Cookie: session=TOKEN
        for header, value in resp.getheaders():
            if header.lower() == "set-cookie" and "session=" in value:
                for part in value.split(";"):
                    part = part.strip()
                    if part.startswith("session="):
                        return part.split("=", 1)[1]
    raise RuntimeError("Login OK pero no se recibió token de sesión")


def upload(token: str, name: str, content: str) -> None:
    data = urllib.parse.urlencode({"name": name, "content": content}).encode()
    req = urllib.request.Request(
        f"{DONGLE_BASE}/api/payload",
        data=data,
        method="POST",
        headers={"Cookie": f"session={token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            print(f"  OK   {name} ({resp.status})")
    except urllib.error.URLError as e:
        print(f"  FAIL {name}: {e}")


def check_meta(content: str, filename: str) -> None:
    """Avisa si el archivo no tiene META con OS y categoría."""
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("META"):
            words = stripped.split()
            if len(words) < 3:
                print(f"  WARN {filename}: META incompleta (falta categoría) — '{stripped}'")
            return
    print(f"  WARN {filename}: sin línea META")


def main() -> int:
    if not SCRIPTS_DIR.exists():
        print(f"No existe {SCRIPTS_DIR}")
        return 1

    password = getpass.getpass("Contraseña del dongle: ")
    print("Conectando...", end=" ", flush=True)
    try:
        token = login(password)
    except Exception as e:
        print(f"\nError al hacer login: {e}")
        return 1
    print("OK\n")

    for os_name in OS_FOLDERS:
        folder = SCRIPTS_DIR / os_name
        if not folder.exists():
            continue
        scripts = sorted(folder.glob("*.txt"))
        if not scripts:
            continue
        print(f"[{os_name.upper()}]")
        for script in scripts:
            content = script.read_text(encoding="utf-8")
            if len(content.encode("utf-8")) > MAX_BYTES:
                print(f"  SKIP {script.name}: supera los {MAX_BYTES} bytes")
                continue
            check_meta(content, script.name)
            upload(token, f"{os_name}-{script.name}", content)
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
