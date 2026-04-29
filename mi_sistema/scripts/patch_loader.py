"""
Patch loader: cambia el primary loader de cripto de OKX a CCXT-Binance
dentro del contenedor de Vibe-Trading.

Modifica dos archivos:
  - /app/agent/backtest/runner.py
  - /app/agent/backtest/loaders/registry.py
"""

import sys


def patch_file(path: str, replacements: list[tuple[str, str]]) -> bool:
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        print(f"ERROR leyendo {path}: {e}")
        return False

    original = text
    for old, new in replacements:
        if old not in text:
            print(f"  AVISO: patron NO encontrado en {path}")
            print(f"         buscaba: {old}")
            continue
        text = text.replace(old, new)
        print(f"  OK: reemplazado en {path}")

    if text == original:
        print(f"  Sin cambios en {path}")
        return False

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return True


def main() -> int:
    print("=== Parcheando _MARKET_TO_SOURCE en runner.py ===")
    runner_changed = patch_file(
        "/app/agent/backtest/runner.py",
        [('"crypto": "okx",', '"crypto": "ccxt",')],
    )

    print()
    print("=== Parcheando FALLBACK_CHAINS en registry.py ===")
    registry_changed = patch_file(
        "/app/agent/backtest/loaders/registry.py",
        [('"crypto":    ["okx", "ccxt"],', '"crypto":    ["ccxt", "okx"],')],
    )

    print()
    print("=== Verificacion ===")
    for path in [
        "/app/agent/backtest/runner.py",
        "/app/agent/backtest/loaders/registry.py",
    ]:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if '"crypto"' in line:
                    print(f"  {path}: {line.rstrip()}")

    if not runner_changed and not registry_changed:
        print()
        print("ATENCION: ningun archivo cambio. Revisa si los patrones ya estaban modificados.")
        return 1

    print()
    print("Listo. Reinicia el contenedor para que cargue los cambios.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
