"""
Check diario automatico para v1.5 cripto (Donchian 55/20 + SMA200 + ATR stop).

Descarga datos de yfinance, simula la estrategia desde el inicio del paper
trading (2026-05-01) hasta hoy, reporta el estado, y AUTOMATICAMENTE
escribe la fila correspondiente al final de mi_sistema/paper_log.csv.

Si ya hay una entrada para la fecha de hoy, no la sobreescribe (avisa)
salvo que se pase el flag --force, en cuyo caso reemplaza la fila existente.

Uso:
    python mi_sistema/scripts/check_v15_cripto.py
    python mi_sistema/scripts/check_v15_cripto.py --force
"""

from __future__ import annotations
import sys
import os

try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
except ImportError:
    sys.exit("Falta yfinance/pandas/numpy. Instala con: pip install yfinance pandas numpy")


CAPITAL_V15 = 500.0  # capital teorico v1.5

# Tickers en formato yfinance (cripto usa -USD, no -USDT)
UNIVERSE = ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "ADA-USD", "BNB-USD", "AVAX-USD"]

# Inicio del paper trading
PAPER_START = pd.Timestamp("2026-05-01")

# Parametros de la estrategia v1.5
DONCHIAN_HIGH = 55
DONCHIAN_LOW = 20
SMA_PERIOD = 200
ATR_PERIOD = 20
ATR_MULT_CRYPTO = 2.0
RISK_PER_TRADE = 0.01


def _download_one(ticker: str) -> pd.DataFrame:
    """Descarga ~2 anos de datos diarios para un ticker."""
    end = pd.Timestamp.today()
    start = end - pd.Timedelta(days=720)
    df = yf.download(ticker, start=start.strftime("%Y-%m-%d"),
                     end=end.strftime("%Y-%m-%d"),
                     progress=False, auto_adjust=False)
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    df.columns = [c.lower() for c in df.columns]
    return df.dropna(subset=["close"])


def _atr(df: pd.DataFrame, period: int = 20) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def _simulate(df: pd.DataFrame, ticker: str) -> dict:
    """
    Simula la estrategia desde PAPER_START hasta el ultimo dia disponible.
    Devuelve estado actual y senal del dia mas reciente.
    """
    df = df.copy()
    df["sma"] = df["close"].rolling(SMA_PERIOD).mean()
    df["donch_high"] = df["high"].rolling(DONCHIAN_HIGH).max().shift(1)
    df["donch_low"] = df["low"].rolling(DONCHIAN_LOW).min().shift(1)
    df["atr"] = _atr(df, ATR_PERIOD)

    # Filtrar desde el inicio del paper
    df_paper = df[df.index >= PAPER_START].copy()
    if df_paper.empty:
        return {"status": "FUERA", "signal_today": "ninguna", "reason": "sin datos en periodo paper"}

    in_position = False
    entry_price = None
    entry_date = None
    stop_price = None
    weight = 0.0
    last_signal = "ninguna"
    last_signal_date = None

    closes = df_paper["close"].values
    highs = df_paper["high"].values
    lows = df_paper["low"].values
    sma_v = df_paper["sma"].values
    dhigh_v = df_paper["donch_high"].values
    dlow_v = df_paper["donch_low"].values
    atr_v = df_paper["atr"].values
    dates = df_paper.index

    for i in range(len(df_paper)):
        last_signal_today = None

        if not in_position:
            can_enter = (
                not np.isnan(dhigh_v[i])
                and not np.isnan(sma_v[i])
                and not np.isnan(atr_v[i])
                and atr_v[i] > 0
            )
            if can_enter and closes[i] > dhigh_v[i] and closes[i] > sma_v[i]:
                entry_price = float(closes[i])
                entry_date = dates[i]
                stop_price = entry_price - ATR_MULT_CRYPTO * float(atr_v[i])
                risk_pct = (entry_price - stop_price) / entry_price
                weight = min(1.0, RISK_PER_TRADE / risk_pct) if risk_pct > 0 else 0.0
                in_position = True
                last_signal_today = f"ENTRADA a ${entry_price:.4f} stop ${stop_price:.4f} peso {weight*100:.1f}%"
        else:
            # Trailing stop
            if not np.isnan(atr_v[i]) and atr_v[i] > 0:
                new_stop = float(closes[i]) - ATR_MULT_CRYPTO * float(atr_v[i])
                if new_stop > stop_price:
                    stop_price = new_stop

            # Salidas
            if lows[i] <= stop_price:
                last_signal_today = f"SALIDA por stop a ${stop_price:.4f}"
                in_position = False
                entry_price = None
                stop_price = None
                weight = 0.0
            elif not np.isnan(dlow_v[i]) and closes[i] < dlow_v[i]:
                last_signal_today = f"SALIDA por Donchian a ${closes[i]:.4f}"
                in_position = False
                entry_price = None
                stop_price = None
                weight = 0.0

        if last_signal_today:
            last_signal = last_signal_today
            last_signal_date = dates[i]

    # Estado final
    if in_position:
        status = "EN_POSICION"
        details = {
            "entry_date": entry_date.strftime("%Y-%m-%d"),
            "entry_price": entry_price,
            "stop_price": stop_price,
            "weight": weight,
        }
    else:
        status = "FUERA"
        details = {}

    # Senal de hoy especificamente
    last_date = dates[-1]
    today = pd.Timestamp.today().normalize()
    is_today = (last_date.normalize() == today)
    signal_today = last_signal if (last_signal_date is not None and last_signal_date == last_date) else "ninguna"

    # Diagnostics: indicadores del ultimo dia para ver distancia a entrada
    diagnostics = {
        "close": float(closes[-1]),
        "sma200": float(sma_v[-1]) if not np.isnan(sma_v[-1]) else None,
        "donch_high_55": float(dhigh_v[-1]) if not np.isnan(dhigh_v[-1]) else None,
        "donch_low_20": float(dlow_v[-1]) if not np.isnan(dlow_v[-1]) else None,
        "atr_20": float(atr_v[-1]) if not np.isnan(atr_v[-1]) else None,
    }

    return {
        "ticker": ticker,
        "status": status,
        "details": details,
        "signal_today": signal_today,
        "last_bar_date": last_date.strftime("%Y-%m-%d"),
        "is_today": is_today,
        "diagnostics": diagnostics,
    }


def main() -> int:
    force = "--force" in sys.argv
    today = pd.Timestamp.today().strftime("%Y-%m-%d")

    print("=" * 64)
    print(f"v1.5 CRIPTO - check diario")
    print(f"Fecha: {today}")
    print("=" * 64)
    print()

    results = []
    for ticker in UNIVERSE:
        df = _download_one(ticker)
        if df.empty:
            print(f"  {ticker}: SIN DATOS")
            results.append({"ticker": ticker, "status": "SIN_DATOS", "signal_today": "ninguna"})
            continue
        result = _simulate(df, ticker)
        results.append(result)

    print("ESTADO ACTUAL POR ACTIVO")
    print("-" * 64)
    in_position_count = 0
    for r in results:
        ticker_short = r["ticker"].replace("-USD", "")
        if r["status"] == "EN_POSICION":
            in_position_count += 1
            d = r["details"]
            print(f"  {ticker_short:<6} EN POSICION  entrada {d['entry_date']} a ${d['entry_price']:.4f}  stop ${d['stop_price']:.4f}  peso {d['weight']*100:.1f}%")
        elif r["status"] == "FUERA":
            print(f"  {ticker_short:<6} FUERA")
        else:
            print(f"  {ticker_short:<6} {r['status']}")
    print()

    # Diagnostics: distancia a las condiciones de entrada
    print("DISTANCIA A CONDICIONES DE ENTRADA")
    print("-" * 64)
    print(f"  {'Ticker':<6} {'Close':>11}   {'SMA200':>11} {'gap%':>7}   {'Donch55_H':>11} {'gap%':>7}")
    for r in results:
        if "diagnostics" not in r:
            continue
        d = r["diagnostics"]
        ticker_short = r["ticker"].replace("-USD", "")
        close = d["close"]
        sma = d.get("sma200")
        dhigh = d.get("donch_high_55")

        if sma:
            sma_pct = (close / sma - 1) * 100
            sma_str = f"${sma:>10,.2f}"
            sma_gap = f"{sma_pct:>+6.1f}%"
        else:
            sma_str = "        N/A"
            sma_gap = "    -- "

        if dhigh:
            dhigh_pct = (close / dhigh - 1) * 100
            dhigh_str = f"${dhigh:>10,.2f}"
            dhigh_gap = f"{dhigh_pct:>+6.1f}%"
        else:
            dhigh_str = "        N/A"
            dhigh_gap = "    -- "

        # Indicador visual: para entrar hace falta close > SMA200 Y close > Donch55
        if sma and dhigh and close > sma and close > dhigh:
            armed = " <- ENTRADA HOY"
        elif sma and close > sma:
            armed = " <- regimen ON, falta breakout Donchian"
        else:
            armed = ""

        print(f"  {ticker_short:<6} ${close:>10,.2f}   {sma_str} {sma_gap}   {dhigh_str} {dhigh_gap}{armed}")
    print()

    # Senales nuevas hoy
    new_signals = []
    for r in results:
        if r["signal_today"] != "ninguna":
            ticker_short = r["ticker"].replace("-USD", "")
            new_signals.append((ticker_short, r["signal_today"]))

    print("SEÑALES NUEVAS HOY")
    print("-" * 64)
    if not new_signals:
        print("  Ninguna. No hay que hacer nada.")
    else:
        for ticker, signal in new_signals:
            print(f"  {ticker}: {signal}")
    print()

    # Resumen
    print("RESUMEN")
    print("-" * 64)
    print(f"  Posiciones abiertas: {in_position_count} de 7")
    print(f"  Senales nuevas hoy:  {len(new_signals)}")
    print()

    # Construir mapa de estado por ticker (orden fijo BTC ETH SOL XRP ADA BNB AVAX)
    status_map = {}
    for r in results:
        ticker_short = r["ticker"].replace("-USD", "")
        if r["status"] == "EN_POSICION":
            status_map[ticker_short] = "EN_POSICION"
        elif r["status"] == "FUERA":
            status_map[ticker_short] = "FUERA"
        else:
            status_map[ticker_short] = r["status"]

    ticker_order = ["BTC", "ETH", "SOL", "XRP", "ADA", "BNB", "AVAX"]
    status_cols = ",".join([status_map.get(t, "FUERA") for t in ticker_order])

    # Entradas y salidas como string corto (separadas por punto y coma para no romper CSV)
    if new_signals:
        entradas_list = [t for t, s in new_signals if "ENTRADA" in s]
        salidas_list = [t for t, s in new_signals if "SALIDA" in s]
        entradas = "+".join(entradas_list) if entradas_list else "ninguna"
        salidas = "+".join(salidas_list) if salidas_list else "ninguna"
        notas = "Senales: " + " | ".join([f"{t} {s.split(' ')[0]}" for t, s in new_signals])
    else:
        entradas = "ninguna"
        salidas = "ninguna"
        notas = "Sin senales"

    csv_row = f"{today},{status_cols},{in_position_count},{entradas},{salidas},{notas}"

    # Auto-escribir al paper_log.csv
    print("ESCRITURA EN paper_log.csv")
    print("-" * 64)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.normpath(os.path.join(script_dir, "..", "paper_log.csv"))

    # Verificar si ya hay entrada para hoy
    already_exists = False
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith(today + ","):
                    already_exists = True
                    break

    if already_exists and not force:
        print(f"  AVISO: ya existe una entrada para {today}.")
        print(f"  No se sobreescribe. Para forzar reemplazo, lanza con --force:")
        print(f"  python mi_sistema/scripts/check_v15_cripto.py --force")
        print()
        print("FILA QUE SE HABRIA ESCRITO:")
        print(f"  {csv_row}")
    elif already_exists and force:
        # Reemplazar la fila existente de hoy
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        new_lines = []
        for line in lines:
            if line.startswith(today + ","):
                new_lines.append(csv_row + "\n")
            else:
                new_lines.append(line)
        with open(log_path, "w", encoding="utf-8", newline="") as f:
            f.writelines(new_lines)
        print(f"  OK: fila de {today} REEMPLAZADA con datos actualizados (--force).")
        print(f"  Archivo: {log_path}")
        print()
        print(f"  {csv_row}")
    else:
        with open(log_path, "a", encoding="utf-8", newline="") as f:
            f.write(csv_row + "\n")
        print(f"  OK: fila anadida al log.")
        print(f"  Archivo: {log_path}")
        print()
        print(f"  {csv_row}")

    print("=" * 64)

    return 0


if __name__ == "__main__":
    sys.exit(main())
