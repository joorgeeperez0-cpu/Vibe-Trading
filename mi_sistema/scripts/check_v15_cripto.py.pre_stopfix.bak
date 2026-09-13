"""
Check diario automatico para v1.5 cripto (Donchian 55/20 + SMA200 + ATR stop).

FASE 1 FIXES (2026-09-13):
- Fix 1: rango de descarga incluye la vela de hoy (end + 2 dias).
- Fix 2: cada fila se etiqueta con la fecha real de la vela usada, no con today().
- Fix 3: detecta datos desactualizados y avisa.
- Fix 4: BACKFILL. Escribe todas las filas faltantes hasta la ultima vela
  disponible, con sus entradas/salidas correctas.

FASE 2 FIXES (2026-09-13):
- Fix 1b: se descarta la vela del dia UTC en curso (incompleta). Solo se
  opera con velas cerradas, igual que en el backtest validado.
- Fix 2b: se eliminan velas con fecha duplicada devueltas por yfinance.

FASE 3 (2026-09-13):
- Estado persistente en mi_sistema/positions_state.json (entry_date,
  entry_price, stop_price, weight por ticker + ultima vela procesada).
  Si existe, la simulacion se reanuda desde el dia siguiente a la ultima vela
  procesada, en lugar de re-simular desde 2026-05-01. Asi un fallo futuro de
  datos historicos no puede reescribir retroactivamente senales ya emitidas.
- Validacion cruzada yfinance vs FMP los domingos (data_quality_check.py).

La logica de senal es identica a mi_sistema/signal_engine_v1.py y a
mi_sistema/pine/v15_donchian.pine. No cambiar aqui sin replicar alli.

Uso:
    python mi_sistema/scripts/check_v15_cripto.py
    python mi_sistema/scripts/check_v15_cripto.py --force          # reemplaza filas ya escritas del rango simulado
    python mi_sistema/scripts/check_v15_cripto.py --rebuild-state  # ignora positions_state.json y re-simula desde PAPER_START
    python mi_sistema/scripts/check_v15_cripto.py --data-check     # fuerza la validacion yfinance vs FMP aunque no sea domingo
"""

from __future__ import annotations
import json
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
TICKER_ORDER = ["BTC", "ETH", "SOL", "XRP", "ADA", "BNB", "AVAX"]

# Inicio del paper trading
PAPER_START = pd.Timestamp("2026-05-01")

# Parametros de la estrategia v1.5
DONCHIAN_HIGH = 55
DONCHIAN_LOW = 20
SMA_PERIOD = 200
ATR_PERIOD = 20
ATR_MULT_CRYPTO = 2.0
RISK_PER_TRADE = 0.01

# Tolerancia para validar el estado guardado contra los datos recien descargados
STATE_PRICE_TOLERANCE_PCT = 1.0

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "paper_log.csv"))
STATE_PATH = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "positions_state.json"))

FLAT = {"in_position": False, "entry_date": None, "entry_price": None, "stop_price": None, "weight": 0.0}


def _short(ticker: str) -> str:
    return ticker.replace("-USD", "")


def _download_one(ticker: str) -> pd.DataFrame:
    """
    Descarga ~2 anos de datos diarios para un ticker.

    Fix 1: end se pone a hoy+2 dias para que yfinance NO excluya la vela de hoy.
    yfinance interpreta end como fecha exclusiva, asi que sumamos margen.
    """
    end = pd.Timestamp.today() + pd.Timedelta(days=2)
    start = end - pd.Timedelta(days=720)
    df = yf.download(
        ticker,
        start=start.strftime("%Y-%m-%d"),
        end=end.strftime("%Y-%m-%d"),
        progress=False,
        auto_adjust=False,
    )
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    df.columns = [c.lower() for c in df.columns]
    df = df.dropna(subset=["close"])

    # Fix 2b (2026-09-13): eliminar velas con fecha repetida (yfinance a veces
    # devuelve la misma vela varias veces). Nos quedamos con la ultima version.
    if df.index.tz is not None:
        df.index = df.index.tz_convert("UTC").tz_localize(None)
    df.index = df.index.normalize()
    dups = int(df.index.duplicated(keep="last").sum())
    if dups:
        print(f"  AVISO {_short(ticker)}: {dups} vela(s) duplicada(s) eliminada(s)")
    df = df[~df.index.duplicated(keep="last")].sort_index()

    # Fix 1b (2026-09-13): descartar la vela del dia UTC en curso. Las velas
    # diarias cripto de yfinance van de 00:00 a 24:00 UTC; la de hoy esta
    # incompleta hasta medianoche UTC. El backtest validado solo usa velas
    # cerradas, y como el log es append-only una senal calculada con una vela
    # parcial quedaria congelada para siempre.
    current_utc_day = pd.Timestamp.now(tz="UTC").normalize().tz_localize(None)
    df = df[df.index < current_utc_day]
    return df


def _atr(df: pd.DataFrame, period: int = 20) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean()


# ---------------------------------------------------------------------------
# Estado persistente
# ---------------------------------------------------------------------------

def _load_state(path: str) -> dict | None:
    """
    Carga positions_state.json. Devuelve None si no existe.
    Estructura devuelta: {"last_bar_date": Timestamp, "positions": {BTC: {...FLAT keys...}}}
    """
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    positions = {}
    for tk_short in TICKER_ORDER:
        p = raw.get("positions", {}).get(tk_short)
        if not p or p.get("status") != "EN_POSICION":
            positions[tk_short] = dict(FLAT)
            continue
        positions[tk_short] = {
            "in_position": True,
            "entry_date": pd.Timestamp(p["entry_date"]),
            "entry_price": float(p["entry_price"]),
            "stop_price": float(p["stop_price"]),
            "weight": float(p["weight"]),
        }
    return {"last_bar_date": pd.Timestamp(raw["last_bar_date"]), "positions": positions}


def _save_state(path: str, last_bar_date: pd.Timestamp, histories: dict) -> None:
    """Guarda el estado final de cada ticker. Escritura atomica (tmp + replace)."""
    positions = {}
    for tk_short in TICKER_ORDER:
        final = histories[f"{tk_short}-USD"]["final"]
        if final["in_position"]:
            positions[tk_short] = {
                "status": "EN_POSICION",
                "entry_date": final["entry_date"].strftime("%Y-%m-%d"),
                "entry_price": round(final["entry_price"], 8),
                "stop_price": round(final["stop_price"], 8),
                "weight": round(final["weight"], 6),
            }
        else:
            positions[tk_short] = {"status": "FUERA", "entry_date": None, "entry_price": None,
                                   "stop_price": None, "weight": 0.0}
    payload = {
        "strategy": "v1.5 cripto (Donchian 55/20 + SMA200 + ATR stop)",
        "last_bar_date": last_bar_date.strftime("%Y-%m-%d"),
        "updated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "positions": positions,
    }
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def _validate_state_against_data(state: dict, data: dict) -> list:
    """
    Comprueba que el precio de entrada guardado coincide con el close de la
    vela de entrada en los datos recien descargados. Si no coincide, los datos
    historicos han cambiado (o el estado esta corrupto): se avisa, pero se
    respeta el estado, que es lo que se registro en su momento.
    """
    warnings = []
    for tk_short, pos in state["positions"].items():
        if not pos["in_position"]:
            continue
        df = data.get(f"{tk_short}-USD")
        if df is None or df.empty or pos["entry_date"] not in df.index:
            warnings.append(f"{tk_short}: vela de entrada {pos['entry_date'].strftime('%Y-%m-%d')} no esta en los datos descargados")
            continue
        close = float(df.loc[pos["entry_date"], "close"])
        div = abs(close / pos["entry_price"] - 1) * 100
        if div > STATE_PRICE_TOLERANCE_PCT:
            warnings.append(
                f"{tk_short}: entry_price guardado {pos['entry_price']:.4f} vs close actual {close:.4f} "
                f"({div:.2f}% > {STATE_PRICE_TOLERANCE_PCT}%). Los datos historicos han cambiado."
            )
    return warnings


# ---------------------------------------------------------------------------
# Simulacion
# ---------------------------------------------------------------------------

def _simulate(df: pd.DataFrame, ticker: str, start_date: pd.Timestamp, init: dict) -> dict:
    """
    Simula la estrategia sobre las velas con fecha >= start_date, partiendo del
    estado `init` (claves de FLAT). Los indicadores se calculan sobre el df
    completo, asi que reanudar desde un estado guardado da exactamente el mismo
    resultado que simular desde PAPER_START.

    Retorno:
    {
      "ticker": "BTC-USD",
      "by_date": {Timestamp: {"status", "signal", "entry_price", "entry_date", "stop_price", "weight"}},
      "final": {...claves de FLAT...},        # estado tras la ultima vela simulada
      "last_bar_date": Timestamp | None,       # ultima vela disponible en los datos
      "diagnostics_last": {close, sma200, donch_high_55, donch_low_20, atr_20}
    }
    """
    df = df.copy()
    df["sma"] = df["close"].rolling(SMA_PERIOD).mean()
    df["donch_high"] = df["high"].rolling(DONCHIAN_HIGH).max().shift(1)
    df["donch_low"] = df["low"].rolling(DONCHIAN_LOW).min().shift(1)
    df["atr"] = _atr(df, ATR_PERIOD)

    last = df.iloc[-1]
    diagnostics_last = {
        "close": float(last["close"]),
        "sma200": None if np.isnan(last["sma"]) else float(last["sma"]),
        "donch_high_55": None if np.isnan(last["donch_high"]) else float(last["donch_high"]),
        "donch_low_20": None if np.isnan(last["donch_low"]) else float(last["donch_low"]),
        "atr_20": None if np.isnan(last["atr"]) else float(last["atr"]),
    }

    in_position = init["in_position"]
    entry_price = init["entry_price"]
    entry_date = init["entry_date"]
    stop_price = init["stop_price"]
    weight = init["weight"]

    df_sim = df[df.index >= start_date]
    closes = df_sim["close"].values
    lows = df_sim["low"].values
    sma_v = df_sim["sma"].values
    dhigh_v = df_sim["donch_high"].values
    dlow_v = df_sim["donch_low"].values
    atr_v = df_sim["atr"].values
    dates = df_sim.index

    by_date = {}

    for i in range(len(df_sim)):
        signal = None

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
                signal = f"ENTRADA a ${entry_price:.4f} stop ${stop_price:.4f} peso {weight * 100:.1f}%"
        else:
            # Trailing stop ATR
            if not np.isnan(atr_v[i]) and atr_v[i] > 0:
                new_stop = float(closes[i]) - ATR_MULT_CRYPTO * float(atr_v[i])
                if new_stop > stop_price:
                    stop_price = new_stop

            exit_signal = None
            # Salida por stop
            if lows[i] <= stop_price:
                exit_signal = f"SALIDA por stop a ${stop_price:.4f}"
            # Salida por Donchian bajo
            elif not np.isnan(dlow_v[i]) and closes[i] < dlow_v[i]:
                exit_signal = f"SALIDA por Donchian a ${closes[i]:.4f}"
            if exit_signal:
                signal = exit_signal
                in_position = False
                entry_price = None
                entry_date = None
                stop_price = None
                weight = 0.0

        by_date[dates[i]] = {
            "status": "EN_POSICION" if in_position else "FUERA",
            "signal": signal,
            "entry_price": entry_price,
            "entry_date": entry_date,
            "stop_price": stop_price,
            "weight": weight,
        }

    return {
        "ticker": ticker,
        "by_date": by_date,
        "final": {"in_position": in_position, "entry_date": entry_date, "entry_price": entry_price,
                  "stop_price": stop_price, "weight": weight},
        "last_bar_date": df.index[-1],
        "diagnostics_last": diagnostics_last,
    }


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------

def _get_registered_dates(log_path: str) -> set:
    """Devuelve el conjunto de fechas ya presentes en paper_log.csv."""
    if not os.path.exists(log_path):
        return set()
    registered = set()
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("fecha,"):
                continue
            fecha = line.split(",", 1)[0]
            registered.add(fecha)
    return registered


def _build_row_for_date(bar_date: pd.Timestamp, histories: dict) -> str:
    """
    Construye la fila CSV para una fecha dada usando el estado y las senales
    de cada ticker en esa fecha.
    """
    date_str = bar_date.strftime("%Y-%m-%d")

    status_cols = []
    entradas = []
    salidas = []
    signals_desc = []

    for tk_short in TICKER_ORDER:
        tk_full = f"{tk_short}-USD"
        history = histories.get(tk_full, {})
        by_date = history.get("by_date", {})
        record = by_date.get(bar_date)
        if record is None:
            status_cols.append("FUERA")
            continue
        status_cols.append(record["status"])
        signal = record.get("signal")
        if signal:
            if "ENTRADA" in signal:
                entradas.append(tk_short)
            elif "SALIDA" in signal:
                salidas.append(tk_short)
            signals_desc.append(f"{tk_short} {signal.split(' ')[0]}")

    posiciones = sum(1 for s in status_cols if s == "EN_POSICION")
    entradas_str = "+".join(entradas) if entradas else "ninguna"
    salidas_str = "+".join(salidas) if salidas else "ninguna"
    notas = ("Senales: " + " | ".join(signals_desc)) if signals_desc else "Sin senales"

    return f"{date_str},{','.join(status_cols)},{posiciones},{entradas_str},{salidas_str},{notas}"


def _detect_stale_data(histories: dict) -> list:
    """
    Detecta datos desactualizados.
    Devuelve lista de warnings tipo "BTC: ultima vela 2026-09-10 (3 dias atras)".
    """
    warnings = []
    today = pd.Timestamp.today().normalize()
    for tk_short in TICKER_ORDER:
        tk_full = f"{tk_short}-USD"
        last_bar = histories.get(tk_full, {}).get("last_bar_date")
        if last_bar is None:
            warnings.append(f"{tk_short}: sin datos")
            continue
        gap_days = (today - last_bar.normalize()).days
        if gap_days >= 2:
            warnings.append(f"{tk_short}: ultima vela {last_bar.strftime('%Y-%m-%d')} ({gap_days} dias atras)")
    return warnings


def _run_weekly_data_check(today: pd.Timestamp, forced: bool) -> None:
    """Domingos (o con --data-check): validacion yfinance vs FMP. Nunca rompe el check."""
    if not forced and today.weekday() != 6:
        return
    print("VALIDACION CRUZADA yfinance vs FMP")
    print("-" * 64)
    try:
        sys.path.insert(0, SCRIPT_DIR)
        import data_quality_check
        n = data_quality_check.run()
        if n:
            print(f"  {n} warning(s). Revisa mi_sistema/scripts/data_quality_log.txt")
    except Exception as exc:
        print(f"  ERROR en validacion cruzada (se ignora): {type(exc).__name__}: {exc}")
    print()


def main() -> int:
    force = "--force" in sys.argv
    rebuild_state = "--rebuild-state" in sys.argv
    today = pd.Timestamp.today().normalize()

    print("=" * 64)
    print(f"v1.5 CRIPTO - check diario (estado persistente)")
    print(f"Fecha ejecucion: {today.strftime('%Y-%m-%d')}")
    print("=" * 64)
    print()

    # 1. Descargar datos
    data = {ticker: _download_one(ticker) for ticker in UNIVERSE}
    for ticker, df in data.items():
        if df.empty:
            print(f"  {_short(ticker)}: SIN DATOS")

    # 2. Cargar estado (o arrancar desde PAPER_START)
    state = None if rebuild_state else _load_state(STATE_PATH)
    if state is None:
        start_date = PAPER_START
        init_positions = {tk: dict(FLAT) for tk in TICKER_ORDER}
        origin = "--rebuild-state" if rebuild_state else "sin positions_state.json"
        print(f"Estado: simulacion completa desde {PAPER_START.strftime('%Y-%m-%d')} ({origin})")
    else:
        start_date = state["last_bar_date"] + pd.Timedelta(days=1)
        init_positions = state["positions"]
        print(f"Estado: reanudando desde positions_state.json (ultima vela procesada {state['last_bar_date'].strftime('%Y-%m-%d')})")
        state_warnings = _validate_state_against_data(state, data)
        for w in state_warnings:
            print(f"  AVISO estado: {w}")
    print()

    # 3. Simular
    histories = {}
    for ticker in UNIVERSE:
        df = data[ticker]
        tk_short = _short(ticker)
        if df.empty:
            histories[ticker] = {"ticker": ticker, "by_date": {}, "final": init_positions[tk_short],
                                 "last_bar_date": None, "diagnostics_last": {}}
            continue
        histories[ticker] = _simulate(df, ticker, start_date, init_positions[tk_short])

    # 4. Detectar datos rancios
    stale_warnings = _detect_stale_data(histories)
    if stale_warnings:
        print("AVISO: datos posiblemente desactualizados")
        print("-" * 64)
        for w in stale_warnings:
            print(f"  {w}")
        print()

    all_last_bars = [h["last_bar_date"] for h in histories.values() if h.get("last_bar_date") is not None]
    if not all_last_bars:
        print("ERROR: no hay datos para ningun ticker. Abortando (estado sin cambios).")
        return 1
    latest_bar = max(all_last_bars).normalize()

    print(f"Ultima vela cerrada disponible: {latest_bar.strftime('%Y-%m-%d')}")
    if state is not None and latest_bar < state["last_bar_date"]:
        print(f"AVISO: la ultima vela ({latest_bar.strftime('%Y-%m-%d')}) es ANTERIOR a la ultima procesada "
              f"({state['last_bar_date'].strftime('%Y-%m-%d')}). Posible problema de datos. Estado sin cambios.")
    print()

    # 5. Estado actual
    print("ESTADO ACTUAL POR ACTIVO (segun ultima vela cerrada)")
    print("-" * 64)
    for tk_short in TICKER_ORDER:
        final = histories[f"{tk_short}-USD"]["final"]
        if final["in_position"]:
            print(
                f"  {tk_short:<6} EN POSICION  entrada {final['entry_date'].strftime('%Y-%m-%d')}"
                f"  a ${final['entry_price']:.4f}  stop ${final['stop_price']:.4f}"
                f"  peso {final['weight'] * 100:.1f}%"
            )
        else:
            print(f"  {tk_short:<6} FUERA")
    print()

    # 6. Distancias a condiciones de entrada
    print("DISTANCIA A CONDICIONES DE ENTRADA")
    print("-" * 64)
    print(f"  {'Ticker':<6} {'Close':>11}   {'SMA200':>11} {'gap%':>7}   {'Donch55_H':>11} {'gap%':>7}")
    for tk_short in TICKER_ORDER:
        d = histories[f"{tk_short}-USD"].get("diagnostics_last", {})
        if not d:
            continue
        close = d.get("close")
        sma = d.get("sma200")
        dhigh = d.get("donch_high_55")

        sma_str = f"${sma:>10,.2f}" if sma else "        N/A"
        sma_gap = f"{(close / sma - 1) * 100:>+6.1f}%" if sma and close else "    -- "
        dhigh_str = f"${dhigh:>10,.2f}" if dhigh else "        N/A"
        dhigh_gap = f"{(close / dhigh - 1) * 100:>+6.1f}%" if dhigh and close else "    -- "

        if sma and dhigh and close and close > sma and close > dhigh:
            armed = " <- ENTRADA ARMADA"
        elif sma and close and close > sma:
            armed = " <- regimen ON, falta breakout Donchian"
        else:
            armed = ""
        print(f"  {tk_short:<6} ${close:>10,.2f}   {sma_str} {sma_gap}   {dhigh_str} {dhigh_gap}{armed}")
    print()

    # 7. BACKFILL: escribir filas de fechas simuladas no registradas
    registered_dates = _get_registered_dates(LOG_PATH)
    all_dates = set()
    for history in histories.values():
        all_dates.update(history.get("by_date", {}).keys())

    to_write = []
    to_replace = []
    for bar_date in sorted(all_dates):
        if bar_date < PAPER_START:
            continue
        date_str = bar_date.strftime("%Y-%m-%d")
        row = _build_row_for_date(bar_date, histories)
        if date_str in registered_dates:
            if force:
                to_replace.append((date_str, row))
        else:
            to_write.append((date_str, row))

    if state is not None and registered_dates:
        last_csv = max(registered_dates)
        if last_csv != state["last_bar_date"].strftime("%Y-%m-%d"):
            print(f"AVISO: ultima fecha en paper_log.csv ({last_csv}) != ultima vela del estado "
                  f"({state['last_bar_date'].strftime('%Y-%m-%d')}). Revisar coherencia log/estado.")
            print()

    print("ESCRITURA EN paper_log.csv (BACKFILL activo)")
    print("-" * 64)

    if not to_write and not to_replace:
        print("  Nada que escribir. Todas las fechas simuladas ya estan en el log.")
    else:
        if to_replace:
            with open(LOG_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()
            replacement_map = {d: r + "\n" for d, r in to_replace}
            new_lines = []
            for line in lines:
                if line.strip().startswith("fecha,"):
                    new_lines.append(line)
                    continue
                fecha = line.split(",", 1)[0]
                new_lines.append(replacement_map.get(fecha, line))
            with open(LOG_PATH, "w", encoding="utf-8", newline="") as f:
                f.writelines(new_lines)
            print(f"  {len(to_replace)} fila(s) REEMPLAZADA(s) por --force:")
            for d, _ in to_replace:
                print(f"    - {d}")

        if to_write:
            with open(LOG_PATH, "a", encoding="utf-8", newline="") as f:
                for _, row in to_write:
                    f.write(row + "\n")
            print(f"  {len(to_write)} fila(s) NUEVA(s) anadida(s) al log:")
            for d, row in to_write:
                print(f"    + {d}  {row.split(',')[-1]}")

    print()
    print(f"  Archivo: {LOG_PATH}")
    print()

    # 8. Guardar estado (solo avanza; nunca retrocede si los datos vienen cortos)
    if state is None or latest_bar > state["last_bar_date"]:
        _save_state(STATE_PATH, latest_bar, histories)
        print(f"  Estado guardado en {STATE_PATH} (ultima vela {latest_bar.strftime('%Y-%m-%d')})")
    else:
        print(f"  Estado sin cambios ({STATE_PATH})")
    print("=" * 64)
    print()

    # 9. Validacion cruzada semanal
    _run_weekly_data_check(today, forced="--data-check" in sys.argv)

    return 0


if __name__ == "__main__":
    sys.exit(main())
