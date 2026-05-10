"""
Calculo automatico del rebalance mensual de v2 ETFs.

Descarga datos de yfinance, calcula momentum 126 dias de cada ETF,
verifica filtro de regimen SPY > SMA(200), muestra los top 3, y AUTOMATICAMENTE
escribe la fila correspondiente al final de mi_sistema/paper_log_v2_etfs.csv.

Si ya hay una entrada para la fecha de hoy, no la sobreescribe (avisa)
salvo que se pase el flag --force, en cuyo caso reemplaza la fila existente.

Uso:
    python mi_sistema/scripts/check_v2_etfs.py
    python mi_sistema/scripts/check_v2_etfs.py --force
"""

from __future__ import annotations
import sys
import os

try:
    import yfinance as yf
    import pandas as pd
except ImportError:
    sys.exit("Falta yfinance o pandas. Instala con: pip install yfinance pandas")


CAPITAL_V2 = 500.0  # capital teorico asignado a v2 ETFs

ETF_TRADEABLES = ["QQQ", "IWM", "EFA", "EEM", "GLD", "TLT"]
REGIME_TICKER = "SPY"
MOMENTUM_DAYS = 126
SMA_DAYS = 200
TOP_N = 3


def _download(tickers: list[str], days: int = 400) -> pd.DataFrame:
    """Descarga ultimos `days` dias de cierre ajustado para los tickers."""
    end = pd.Timestamp.today()
    start = end - pd.Timedelta(days=days * 1.5)  # margen para fines de semana
    df = yf.download(
        tickers,
        start=start.strftime("%Y-%m-%d"),
        end=end.strftime("%Y-%m-%d"),
        progress=False,
        auto_adjust=False,
    )
    if isinstance(df.columns, pd.MultiIndex):
        # cuando hay multiples tickers, multiindex con (Field, Ticker)
        closes = df["Close"]
    else:
        # un solo ticker
        closes = df[["Close"]].rename(columns={"Close": tickers[0]})
    return closes.dropna(how="all")


def main() -> int:
    force = "--force" in sys.argv
    print("=" * 60)
    print(f"v2 ETFs - check de rebalance mensual")
    print(f"Fecha: {pd.Timestamp.today().strftime('%Y-%m-%d')}")
    print("=" * 60)
    print()

    all_tickers = ETF_TRADEABLES + [REGIME_TICKER]
    closes = _download(all_tickers)

    # Verificar que tenemos datos para todos
    missing = [t for t in all_tickers if t not in closes.columns]
    if missing:
        print(f"ERROR: faltan datos para: {missing}")
        return 1

    # 1. Regime filter SPY > SMA(200)
    spy = closes[REGIME_TICKER].dropna()
    spy_sma = spy.rolling(SMA_DAYS).mean()
    spy_today = float(spy.iloc[-1])
    spy_sma_today = float(spy_sma.iloc[-1])
    regime_on = spy_today > spy_sma_today

    print(f"REGIME FILTER (SPY > SMA{SMA_DAYS})")
    print(f"  SPY hoy:        ${spy_today:.2f}")
    print(f"  SPY SMA{SMA_DAYS}:    ${spy_sma_today:.2f}")
    print(f"  Estado regimen: {'ON' if regime_on else 'OFF (TODO A CASH)'}")
    print()

    if not regime_on:
        print("=" * 60)
        print("DECISION: TODO A CASH. SPY esta por debajo de su SMA(200).")
        print("Si tenias posiciones, vendelas todas. Apunta en el log:")
        print(f'  fecha,OFF,...,...,"none",all_to_cash,"0%","SPY < SMA{SMA_DAYS}, todo a cash"')
        print("=" * 60)
        return 0

    # 2. Calcular momentum 126 dias para cada ETF tradeable
    print(f"MOMENTUM {MOMENTUM_DAYS} DIAS POR ETF")
    momentums = {}
    for ticker in ETF_TRADEABLES:
        series = closes[ticker].dropna()
        if len(series) < MOMENTUM_DAYS + 1:
            print(f"  {ticker}: SIN DATOS SUFICIENTES")
            continue
        price_now = float(series.iloc[-1])
        price_then = float(series.iloc[-MOMENTUM_DAYS - 1])
        mom_pct = (price_now / price_then - 1) * 100
        momentums[ticker] = mom_pct
        print(f"  {ticker:<5} ${price_now:>8.2f}  momentum: {mom_pct:>+7.2f} %")
    print()

    # 3. Filtrar positivos y ordenar
    positives = {t: m for t, m in momentums.items() if m > 0}
    if not positives:
        print("DECISION: TODO A CASH. Ningun ETF tiene momentum positivo.")
        return 0

    sorted_tickers = sorted(positives.items(), key=lambda x: x[1], reverse=True)
    top3 = sorted_tickers[:TOP_N]

    # 4. Calcular pesos y cantidades
    weight_each = 1.0 / TOP_N
    capital_each = CAPITAL_V2 * weight_each

    print(f"TOP {TOP_N} SELECCIONADOS (con momentum positivo)")
    print()
    print(f"  Capital v2 asignado: {CAPITAL_V2:.0f} EUR (asume 1 EUR = 1 USD para simplicidad)")
    print(f"  Capital por ETF:     {capital_each:.2f} EUR (peso {weight_each*100:.1f} %)")
    print()
    print(f"  {'Ticker':<7} {'Mom %':<10} {'Precio':<12} {'Cantidad acciones':<20}")
    print(f"  {'-'*7} {'-'*10} {'-'*12} {'-'*20}")

    csv_top3 = []
    csv_pesos = []
    for ticker, mom_pct in top3:
        price = float(closes[ticker].iloc[-1])
        shares = capital_each / price
        print(f"  {ticker:<7} {mom_pct:>+7.2f} %  ${price:>9.2f}   {shares:.4f}")
        csv_top3.append(ticker)
        csv_pesos.append(f"{ticker}={weight_each*100:.0f}%")

    print()
    print("=" * 60)
    print("ESCRITURA EN paper_log_v2_etfs.csv")
    print("=" * 60)
    fecha = pd.Timestamp.today().strftime("%Y-%m-%d")
    mom_values = []
    for t in ETF_TRADEABLES:
        if t in momentums:
            mom_values.append(f"{momentums[t]:.2f}")
        else:
            mom_values.append("nan")

    # Posiciones expandidas a 3 columnas separadas (rellenar con 'cash' si <3 seleccionados)
    pos_cols = []
    for i in range(TOP_N):
        pos_cols.append(csv_top3[i] if i < len(csv_top3) else "cash")

    csv_row = ",".join([
        fecha,
        "ON",
        *mom_values,
        *pos_cols,
        "rebalance",
        "ejecutado por script",
    ])

    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.normpath(os.path.join(script_dir, "..", "paper_log_v2_etfs.csv"))

    already_exists = False
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith(fecha + ","):
                    already_exists = True
                    break

    if already_exists and not force:
        print(f"  AVISO: ya existe entrada para {fecha} en el log.")
        print(f"  No se sobreescribe. Para forzar reemplazo, lanza con --force:")
        print(f"  python mi_sistema/scripts/check_v2_etfs.py --force")
        print()
        print("FILA QUE SE HABRIA ESCRITO:")
        print(f"  {csv_row}")
    elif already_exists and force:
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        new_lines = []
        for line in lines:
            if line.startswith(fecha + ","):
                new_lines.append(csv_row + "\n")
            else:
                new_lines.append(line)
        with open(log_path, "w", encoding="utf-8", newline="") as f:
            f.writelines(new_lines)
        print(f"  OK: fila de {fecha} REEMPLAZADA con datos actualizados (--force).")
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

    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
