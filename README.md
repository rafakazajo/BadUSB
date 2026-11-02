# BadUSB — LilyGO T-Dongle-S3

Proyecto personal de BadUSB basado en el firmware [FleaByte](https://github.com/b3rt1ng/FleaByte) para el dispositivo **LilyGO T-Dongle-S3** (ESP32-S3).

Incluye el firmware modificado, payloads DuckyScript propios y herramientas Python/Shell para gestionar los payloads desde la línea de comandos.

> **Aviso:** Este proyecto es de uso educativo y para entornos controlados. El uso de dispositivos BadUSB contra sistemas sin autorización es ilegal.

---

## Hardware

- **Dispositivo:** LilyGO T-Dongle-S3
- **MCU:** ESP32-S3
- **Flash:** 16 MB
- **Firmware base:** FleaByte v0.4.1

## Estructura

    BadUSB/
    ├── fleabyte/          Firmware (basado en FleaByte)
    ├── tools/             Scripts Python y Shell para gestión
    ├── payloads/          Payloads DuckyScript (48 scripts)
    ├── DOCS.md            Documentación técnica del firmware
    └── NOTES.md           Notas técnicas del hardware

## Payloads

Los payloads están en `payloads/` organizados con el prefijo `windows-`, `linux-` o `macos-` y una línea `META <os> <categoría>` al inicio.

Categorías: `broma`, `exfil`, `acceso`, `evasion`, `util`

Los payloads que usan Telegram para exfiltración tienen `YOUR_BOT_TOKEN` y `YOUR_CHAT_ID` como placeholders. Sustitúyelos por tus valores antes de subirlos al dongle.

## Herramientas (`tools/`)

| Script | Descripción |
|--------|-------------|
| `build.sh` | Compila el firmware con arduino-cli |
| `flash.sh` | Compila y flashea al dispositivo |
| `create_payloads.py` | Crea y sube payloads nuevos al dongle |
| `import_payloads.py` | Sube en bloque desde una carpeta local |
| `export_payloads.py` | Exporta todos los payloads a un `.zip` |
| `migrate_payloads.py` | Renombra payloads y actualiza líneas META |
| `fix_payloads.py` | Corrige errores comunes en payloads existentes |
| `release.sh` | Genera un binario flasheable en `release/` |

## Requisitos

- [arduino-cli](https://arduino.github.io/arduino-cli/)
- Plataforma `esp32:esp32` instalada
- Python 3 (stdlib + `requests` para algunos scripts)

## Compilar y flashear

    bash tools/build.sh   # Solo compilar
    bash tools/flash.sh   # Compilar y flashear

El primer flash requiere mantener pulsado el botón al conectar el dongle. Los siguientes los gestiona `flash.sh` automáticamente.

## Créditos

Firmware basado en [FleaByte](https://github.com/b3rt1ng/FleaByte) de b3rt1ng, publicado bajo licencia MIT.
