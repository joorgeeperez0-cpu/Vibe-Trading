"""
Backtest local sin Docker, reutilizando el engine de Vibe-Trading (agent/backtest)
SOLO EN LECTURA, sobre OHLCV ya archivados en un results/*/artifacts/.

Por que existe (2026-09-13):
- run_backtest.ps1 necesita Docker y descarga datos en vivo via CCXT. Binance
  Espana esta bloqueado desde 2026-07-01 y los datos pueden haber cambiado.
- Para comparar dos signal engines hay que aislar el efecto del motor: mismos
  OHLCV, mismo engine (CryptoEngine), misma config. Este script lee los
  ohlcv_*.csv archivados del backtest de referencia y ejecuta el mismo
  BaseEngine.run_backtest que usa el runner.
- Paso obligatorio: reproducir primero las metricas archivadas del motor de
  referencia. Si no cuadran, el harness no es valido.

Uso:
    python mi_sistema/scripts/run_backtest_local.py \
        --config mi_sistema/configs/v15_cripto_top7_walkforward.json \
        --data mi_sistema/results/v15_cripto_top7_walkforward/artifacts \
        --engine signal_engine_v1_stopfix \
        --out mi_sistema/results/v1_stopfix/wf_2023_2026
"""

from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "agent"))

from backtest.engines.crypto import CryptoEngine  # noqa: E402
from backtest.metrics import calc_bars_per_year  # noqa: E402


class _ArchivedLoader:
    """Loader que devuelve los OHLCV archivados, recortados al rango de la config."""

    def __init__(self, data_dir: Path, start: str, end: str):
        self.data_dir = data_dir
        self.start = pd.Timestamp(start)
        self.end = pd.Timestamp(end)

    def fetch(self, codes, start_date, end_date, fields=None, interval="1D"):
        out = {}
        for code in codes:
            f = self.data_dir / f"ohlcv_{code}.csv"
            if not f.exists():
                continue
            df = pd.read_csv(f, index_col=0, parse_dates=True)
            df = df[(df.index >= self.start) & (df.index <= self.end)]
            if not df.empty:
                out[code] = df
        return out


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--data", required=True, help="carpeta con ohlcv_<code>.csv archivados")
    ap.add_argument("--engine", required=True, help="nombre del signal engine en mi_sistema/ (sin .py)")
    ap.add_argument("--out", required=True, help="carpeta de salida (se crea <out>/artifacts)")
    args = ap.parse_args()

    config_path = (REPO / args.config).resolve()
    data_dir = (REPO / args.data).resolve()
    engine_path = (REPO / "mi_sistema" / f"{args.engine}.py").resolve()
    out_dir = (REPO / args.out).resolve()

    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("engine", "daily") != "daily":
        sys.exit("Solo soportado engine=daily")

    spec = importlib.util.spec_from_file_location("signal_engine", engine_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    signal_engine = module.SignalEngine()

    loader = _ArchivedLoader(data_dir, config["start_date"], config["end_date"])
    out_dir.mkdir(parents=True, exist_ok=True)

    engine = CryptoEngine(config)
    engine.run_backtest(config, loader, signal_engine, out_dir,
                        bars_per_year=calc_bars_per_year(config.get("interval", "1D"), "ccxt"))

    run_info = {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "harness": "mi_sistema/scripts/run_backtest_local.py",
        "config": str(config_path.relative_to(REPO)),
        "config_sha256": _sha256(config_path),
        "signal_engine": str(engine_path.relative_to(REPO)),
        "signal_engine_sha256": _sha256(engine_path),
        "ohlcv_source": str(data_dir.relative_to(REPO)),
        "engine": "agent/backtest/engines/crypto.py CryptoEngine (sin modificar)",
        "bars_per_year": calc_bars_per_year(config.get("interval", "1D"), "ccxt"),
        "python": sys.version.split()[0],
        "pandas": pd.__version__,
    }
    (out_dir / "run_info.json").write_text(json.dumps(run_info, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
