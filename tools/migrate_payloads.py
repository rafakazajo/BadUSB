#!/usr/bin/env python3
"""
migrate_payloads.py — Migra los payloads del BadUSB:
  - Añade/actualiza la línea META con OS y categoría
  - Renombra los archivos quitando la categoría del nombre

Uso: python3 migrate_payloads.py
     (conecta al dongle en http://192.168.4.1)
"""

import requests
import getpass
import sys

BASE_URL = "http://192.168.4.1"

# old_name -> (new_name, os, category)
# Si new_name == old_name: solo actualiza META, sin renombrar.
MIGRATIONS = {
    # WINDOWS — renombrar + META
    "windows-broma-rickroll.txt":       ("windows-rickroll.txt",         "windows", "broma"),
    "windows-broma-popup.txt":          ("windows-popup.txt",            "windows", "broma"),
    "windows-broma-wallpaper.txt":      ("windows-wallpaper.txt",        "windows", "broma"),
    "windows-info-browser-history.txt": ("windows-browser-history.txt",  "windows", "exfil"),
    "windows-info-screenshot.txt":      ("windows-screenshot.txt",       "windows", "exfil"),
    "windows-disable_UAC.txt":          ("windows-disable-uac.txt",      "windows", "evasion"),
    "windows-disable_defender.txt":     ("windows-disable-defender.txt", "windows", "evasion"),
    "windows-util-clear-logs.txt":      ("windows-clear-logs.txt",       "windows", "util"),
    # WINDOWS — solo META
    "windows-backdoor-user.txt":        ("windows-backdoor-user.txt",    "windows", "acceso"),
    "windows-keylogger.txt":            ("windows-keylogger.txt",        "windows", "exfil"),
    # LINUX — renombrar + META
    "linux-broma-popup.txt":            ("linux-popup.txt",              "linux",   "broma"),
    "linux-broma-wallpaper.txt":        ("linux-wallpaper.txt",          "linux",   "broma"),
    "linux-util-clear-logs.txt":        ("linux-clear-logs.txt",         "linux",   "util"),
    # LINUX — solo META
    "linux-backdoor-user.txt":          ("linux-backdoor-user.txt",      "linux",   "acceso"),
    "linux-bindshell.txt":              ("linux-bindshell.txt",          "linux",   "acceso"),
    "linux-revshell.txt":               ("linux-revshell.txt",           "linux",   "acceso"),
    "linux-rickroll.txt":               ("linux-rickroll.txt",           "linux",   "broma"),
    "linux-forkbomb.txt":               ("linux-forkbomb.txt",           "linux",   "broma"),
    # MACOS — renombrar + META
    "macos-broma-popup.txt":            ("macos-popup.txt",              "macos",   "broma"),
    "macos-broma-wallpaper.txt":        ("macos-wallpaper.txt",          "macos",   "broma"),
    "macos-info-screenshot.txt":        ("macos-screenshot.txt",         "macos",   "exfil"),
    # MACOS — solo META
    "macos-backdoor-user.txt":          ("macos-backdoor-user.txt",      "macos",   "acceso"),
    "macos-bindshell.txt":              ("macos-bindshell.txt",          "macos",   "acceso"),
    "macos-revshell.txt":               ("macos-revshell.txt",           "macos",   "acceso"),
}


def login(password: str) -> str:
    r = requests.post(
        f"{BASE_URL}/api/login",
        data={"password": password},
        timeout=5,
    )
    r.raise_for_status()
    token = r.cookies.get("session")
    if not token:
        body = {}
        try:
            body = r.json()
        except Exception:
            pass
        token = body.get("token") or body.get("session")
    if not token:
        raise RuntimeError("Login OK pero no se recibió token de sesión")
    return token


def get_payload_list(session: requests.Session) -> list:
    r = session.get(f"{BASE_URL}/api/state", timeout=5)
    r.raise_for_status()
    return [p["name"] for p in r.json().get("payloads", [])]


def download_payload(session: requests.Session, name: str) -> str:
    r = session.get(f"{BASE_URL}/api/payload", params={"name": name}, timeout=5)
    r.raise_for_status()
    return r.text


def update_meta(content: str, os_tag: str, category: str) -> str:
    """Inserta o reemplaza la línea META. La deja siempre al principio."""
    meta_line = f"META {os_tag} {category}"
    lines = content.splitlines(keepends=True)

    for i, line in enumerate(lines):
        if line.strip().upper().startswith("META"):
            if lines[i].rstrip("\r\n") == meta_line:
                return content  # ya está correcto, sin cambios
            lines[i] = meta_line + "\n"
            return "".join(lines)

    # No existía línea META — insertar al principio
    return meta_line + "\n" + content


def upload_payload(session: requests.Session, name: str, content: str) -> None:
    r = session.post(
        f"{BASE_URL}/api/payload",
        data={"name": name, "content": content},
        timeout=5,
    )
    r.raise_for_status()


def delete_payload(session: requests.Session, name: str) -> None:
    r = session.post(
        f"{BASE_URL}/api/payload/delete",
        data={"name": name},
        timeout=5,
    )
    r.raise_for_status()


def main():
    print("=== Migración de payloads BadUSB ===")
    print(f"Dongle: {BASE_URL}\n")

    password = getpass.getpass("Contraseña del dongle: ")

    print("Conectando...", end=" ", flush=True)
    try:
        token = login(password)
    except Exception as e:
        print(f"\nError al hacer login: {e}")
        sys.exit(1)
    print("OK")

    session = requests.Session()
    session.cookies.set("session", token)

    print("Obteniendo lista de payloads...", end=" ", flush=True)
    try:
        current = get_payload_list(session)
    except Exception as e:
        print(f"\nError al obtener estado: {e}")
        sys.exit(1)
    print(f"{len(current)} encontrados\n")

    ok = skipped = errors = 0

    for old_name, (new_name, os_tag, category) in MIGRATIONS.items():
        if old_name not in current:
            print(f"  [SKIP]   {old_name}")
            skipped += 1
            continue

        rename = old_name != new_name
        label = "RENAME" if rename else "META  "
        dest = f" → {new_name}" if rename else ""
        print(f"  [{label}] {old_name}{dest}  (META {os_tag} {category})", end=" ", flush=True)

        try:
            content = download_payload(session, old_name)
            updated = update_meta(content, os_tag, category)
            upload_payload(session, new_name, updated)
            if rename:
                delete_payload(session, old_name)
            print("OK")
            ok += 1
        except Exception as e:
            print(f"ERROR: {e}")
            errors += 1

    print(f"\n{'='*36}")
    print(f"  OK:      {ok}")
    print(f"  Skip:    {skipped}  (no estaban en el dongle)")
    print(f"  Errores: {errors}")
    if errors == 0:
        print("\nMigración completada sin errores.")
    else:
        print("\nHubo errores. Revisa los afectados manualmente.")


if __name__ == "__main__":
    main()
