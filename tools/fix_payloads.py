#!/usr/bin/env python3
"""Descarga todos los payloads del dongle, aplica los fixes conocidos y los sube de nuevo.
Conectate a la red del dongle antes de ejecutar.

Fixes aplicados:
  - DEFAULT_DELAY → DEFAULTDELAY en todos los payloads
  - windows-backdoor-user.txt: reemplaza 'soporte' por 'helpdesk' (bug de nombre de usuario)
  - linux-revshell.txt: reemplaza placeholder [IP] por 0.0.0.0
"""
import getpass, urllib.parse, urllib.request, json

BASE = "http://192.168.4.1"


def login(password):
    data = urllib.parse.urlencode({"password": password}).encode()
    req = urllib.request.Request(f"{BASE}/api/login", data=data)
    with urllib.request.urlopen(req, timeout=5) as r:
        for h, v in r.getheaders():
            if h.lower() == "set-cookie" and "session=" in v:
                for p in v.split(";"):
                    if p.strip().startswith("session="):
                        return p.strip().split("=", 1)[1]
    raise RuntimeError("Login OK pero sin token")


def get_state(token):
    req = urllib.request.Request(f"{BASE}/api/state", headers={"Cookie": f"session={token}"})
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())


def get_payload(token, name):
    params = urllib.parse.urlencode({"name": name})
    req = urllib.request.Request(
        f"{BASE}/api/payload?{params}",
        headers={"Cookie": f"session={token}"}
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        return r.read().decode("utf-8")


def put_payload(token, name, content):
    data = urllib.parse.urlencode({"name": name, "content": content}).encode()
    req = urllib.request.Request(
        f"{BASE}/api/payload",
        data=data,
        headers={"Cookie": f"session={token}"},
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        return r.status


def fix(name, content):
    """Aplica todos los fixes conocidos. Devuelve el contenido corregido."""
    fixed = content

    # Fix universal: DEFAULT_DELAY → DEFAULTDELAY
    fixed = fixed.replace("DEFAULT_DELAY", "DEFAULTDELAY")

    # Fix especifico: windows-backdoor-user.txt tenia 'soporte' en vez de 'helpdesk'
    if name == "windows-backdoor-user.txt":
        fixed = fixed.replace("soporte", "helpdesk")

    # Fix especifico: linux-revshell.txt tenia el placeholder literal [IP]
    if name == "linux-revshell.txt":
        fixed = fixed.replace("[IP]", "0.0.0.0")

    return fixed


pw = getpass.getpass("Contraseña: ")
print("Conectando...", end=" ", flush=True)
token = login(pw)
print("OK\n")

state = get_state(token)
payloads = state.get("payloads", [])
print(f"{len(payloads)} payloads encontrados\n")

ok = skip = err = 0
for p in payloads:
    name = p["name"]
    try:
        original = get_payload(token, name)
        patched = fix(name, original)
        if patched == original:
            print(f"  --   {name}")
            skip += 1
            continue
        put_payload(token, name, patched)
        print(f"  OK   {name}")
        ok += 1
    except Exception as e:
        print(f"  ERR  {name}: {e}")
        err += 1

print(f"\nActualizados: {ok}  Sin cambios: {skip}  Errores: {err}")
