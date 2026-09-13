"""
Diagnostico de salidas de v1 (signal_engine_v1.py) sobre los OHLCV archivados.
Clasifica cada salida:
  - stop_real:      low <= stop vigente desde el cierre anterior (un stop real tambien habria saltado)
  - stop_fantasma:  low > stop anterior pero low <= stop subido con el close del mismo dia (solo existe por el bug)
  - donchian:       close < Donchian20
Y mide el retorno de cada trade (close de entrada -> open del dia siguiente a la
salida, que es donde ejecuta el engine), para ver si las salidas fantasma
recortaban ganadores o protegian de perdidas.

Salida: mi_sistema/results/v1_stopfix/v1_exit_types_<periodo>.csv

Uso: python mi_sistema/scripts/diag_v1_exit_types.py
"""

from __future__ import annotations
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
RES = REPO / "mi_sistema" / "results"
PERIODS = {
    "is_2018_2022": RES / "v15_cripto_top7_in_sample" / "artifacts",
    "wf_2023_2026": RES / "v15_cripto_top7_walkforward" / "artifacts",
}
CODES = ["BTC-USDT", "ETH-USDT", "SOL-USDT", "XRP-USDT", "ADA-USDT", "BNB-USDT", "AVAX-USDT"]
K = 2.0


def _atr(df, period=20):
    tr = pd.concat([df.high - df.low, (df.high - df.close.shift()).abs(), (df.low - df.close.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def classify(df: pd.DataFrame, code: str) -> list:
    if len(df) < 255:
        return []
    sma = df.close.rolling(200).mean().values
    dh = df.high.rolling(55).max().shift(1).values
    dl = df.low.rolling(20).min().shift(1).values
    atr = _atr(df).values
    c, lo, op = df.close.values, df.low.values, df.open.values
    dates = df.index
    out, inpos, stop, entry_i = [], False, 0.0, None
    for i in range(len(df)):
        if not inpos:
            if not np.isnan(dh[i]) and not np.isnan(sma[i]) and not np.isnan(atr[i]) and atr[i] > 0 and c[i] > dh[i] and c[i] > sma[i]:
                inpos, stop, entry_i = True, c[i] - K * atr[i], i
            continue
        prev_stop = stop
        if not np.isnan(atr[i]) and atr[i] > 0:
            stop = max(stop, c[i] - K * atr[i])
        kind = None
        if lo[i] <= stop:
            kind = "stop_real" if lo[i] <= prev_stop else "stop_fantasma"
        elif not np.isnan(dl[i]) and c[i] < dl[i]:
            kind = "donchian"
        if kind:
            exit_px = op[i + 1] if i + 1 < len(df) else c[i]
            out.append({
                "code": code, "entry_date": dates[entry_i].date(), "exit_signal_date": dates[i].date(), "type": kind,
                "entry_close": c[entry_i], "exit_open_next": exit_px,
                "ret_pct": (exit_px / c[entry_i] - 1) * 100,
                "exit_day_close_vs_stop_pct": (c[i] / stop - 1) * 100,
                "exit_day_ret_pct": (c[i] / c[i - 1] - 1) * 100,
            })
            inpos = False
    return out


def main() -> int:
    for period, path in PERIODS.items():
        rows = []
        for code in CODES:
            f = path / f"ohlcv_{code}.csv"
            if f.exists():
                rows += classify(pd.read_csv(f, index_col=0, parse_dates=True), code)
        d = pd.DataFrame(rows)
        d.to_csv(RES / "v1_stopfix" / f"v1_exit_types_{period}.csv", index=False, float_format="%.4f")
        g = d.groupby("type").agg(n=("ret_pct", "size"), ret_medio_pct=("ret_pct", "mean"),
                                  ganadores_pct=("ret_pct", lambda s: (s > 0).mean() * 100),
                                  dia_salida_alcista_pct=("exit_day_ret_pct", lambda s: (s > 0).mean() * 100),
                                  close_sobre_stop_medio_pct=("exit_day_close_vs_stop_pct", "mean"))
        print(f"\n=== v1 {period}: {len(d)} salidas ===")
        print(g.round(2).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
