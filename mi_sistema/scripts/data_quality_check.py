"""
Validacion cruzada semanal de calidad de datos: yfinance vs FMP.

Compara el cierre de la ultima vela CERRADA comun a ambas fuentes para
BTC, ETH y SPY. Si alguna diverge mas de THRESHOLD_PCT, escribe un WARNING
en mi_sistema/scripts/data_quality_log.txt. Cada ejecucion deja al menos una
linea (OK / WARNING / SKIP) para que quede rastro de que se ha comprobado.

Pensado para lanzarse los domingos desde check_v15_cripto.py (tarea diaria),
pero se puede ejecutar a mano cualquier dia:

    python mi_sistema/scripts/data_quality_check.py

Requiere la variable de entorno FMP_API_KEY (NUNCA commitear la clave).
Sin clave, registra un SKIP y sale sin error: la validacion nunca debe
bloquear la generacion de senales.
"""

from __future__ import annotations
import json
import os
import sys
import urllib.parse
import urllib.request

import pandas as pd
import yfinance as yf

THRESHOLD_PCT = 0.5
LOOKBACK_DAYS = 10

# yfinance ticker -> FMP symbol
PAIRS = {
    "BTC-USD": "BTCUSD",
    "ETH-USD": "ETHUSD",
    "SPY": "SPY",
}

FMP_URL = "https://financialmodelingprep.com/stable/historical-price-eod/light"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(SCRIPT_DIR, "data_quality_log.txt")


def _log(lines: list[str]) -> None:
    stamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        for line in lines:
            f.write(f"[{stamp}] {line}\n")


def _yf_closes(ticker: str) -> pd.Series:
    end = pd.Timestamp.today() + pd.Timedelta(days=2)
    start = end - pd.Timedelta(days=LOOKBACK_DAYS + 2)
    df = yf.download(ticker, start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"),
                     progress=False, auto_adjust=False)
    if df.empty:
        return pd.Series(dtype=float)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    s = df["Close"].dropna()
    s.index = pd.DatetimeIndex(s.index).normalize()
    return s[~s.index.duplicated(keep="last")]


def _fmp_closes(symbol: str, api_key: str) -> pd.Series:
    today = pd.Timestamp.today().normalize()
    params = urllib.parse.urlencode({
        "symbol": symbol,
        "from": (today - pd.Timedelta(days=LOOKBACK_DAYS)).strftime("%Y-%m-%d"),
        "to": today.strftime("%Y-%m-%d"),
        "apikey": api_key,
    })
    with urllib.request.urlopen(f"{FMP_URL}?{params}", timeout=30) as resp:
        data = json.load(resp)
    if not isinstance(data, list) or not data:
        return pd.Series(dtype=float)
    s = pd.Series({pd.Timestamp(r["date"]): float(r["price"]) for r in data if "price" in r})
    return s.sort_index()


def run() -> int:
    """Ejecuta la validacion. Devuelve el numero de warnings emitidos."""
    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        msg = "SKIP validacion yfinance vs FMP: FMP_API_KEY no definida"
        print(f"  {msg}")
        _log([msg])
        return 0

    # Excluir el dia UTC en curso: la vela cripto de hoy aun no esta cerrada.
    current_utc_day = pd.Timestamp.now(tz="UTC").normalize().tz_localize(None)

    lines = []
    warnings = 0
    for yf_ticker, fmp_symbol in PAIRS.items():
        try:
            yfs = _yf_closes(yf_ticker)
            fmps = _fmp_closes(fmp_symbol, api_key)
        except Exception as exc:  # red, rate limit, cambio de API...
            warnings += 1
            lines.append(f"WARNING {yf_ticker}: error descargando datos ({type(exc).__name__}: {exc})")
            continue
        common = yfs.index.intersection(fmps.index)
        common = common[common < current_utc_day]
        if common.empty:
            warnings += 1
            lines.append(f"WARNING {yf_ticker}: sin fechas comunes entre yfinance y FMP")
            continue
        d = common.max()
        yv, fv = float(yfs[d]), float(fmps[d])
        div = abs(yv / fv - 1) * 100
        tag = "WARNING" if div > THRESHOLD_PCT else "OK"
        warnings += tag == "WARNING"
        lines.append(f"{tag} {yf_ticker} {d.strftime('%Y-%m-%d')}: yfinance {yv:.4f} vs FMP {fv:.4f} -> divergencia {div:.3f}% (umbral {THRESHOLD_PCT}%)")

    for line in lines:
        print(f"  {line}")
    _log(lines)
    return warnings


if __name__ == "__main__":
    run()
    sys.exit(0)
