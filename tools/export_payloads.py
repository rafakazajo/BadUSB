#!/usr/bin/env python3
"""Exporta todos los payloads del dongle a un .zip local."""
import getpass, zipfile, urllib.parse, urllib.request, json
from pathlib import Path

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
    req = urllib.request.Request(
        f"{BASE}/api/state",
        headers={"Cookie": f"session={token}"}
    )
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


pw = getpass.getpass("Contraseña: ")
print("Conectando...", end=" ", flush=True)
token = login(pw)
print("OK")

state = get_state(token)
payloads = state.get("payloads", [])
print(f"{len(payloads)} payloads encontrados\n")

out = Path("payloads_export.zip")
with zipfile.ZipFile(out, "w") as z:
    for p in payloads:
        name = p["name"]
        try:
            content = get_payload(token, name)
            z.writestr(name, content)
            print(f"  OK  {name}")
        except Exception as e:
            print(f"  ERR {name}: {e}")

print(f"\nGuardado en {out}")
