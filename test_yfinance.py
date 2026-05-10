"""
Sanity check de yfinance para el universo de la estrategia v1.
Verifica que los 15 activos devuelven datos limpios desde 2018-01-01.
"""

import yfinance as yf

universo = [
    "BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "ADA-USD",
    "AAPL", "MSFT", "GOOGL", "NVDA", "META",
    "JPM", "V", "JNJ", "UNH", "PG",
]

start = "2018-01-01"
end = "2023-01-01"

print(f"{'Ticker':<10} {'Filas':<8} {'Desde':<12} {'Hasta':<12} {'OK?'}")
print("-" * 55)

for ticker in universo:
    try:
        df = yf.download(
            ticker,
            start=start,
            end=end,
            progress=False,
            auto_adjust=False,
        )
        if df.empty:
            print(f"{ticker:<10} {'0':<8} {'-':<12} {'-':<12} VACIO")
            continue
        first = df.index[0].strftime("%Y-%m-%d")
        last = df.index[-1].strftime("%Y-%m-%d")
        ok = "OK" if first <= "2018-01-05" else "TARDIO"
        print(f"{ticker:<10} {len(df):<8} {first:<12} {last:<12} {ok}")
    except Exception as e:
        print(f"{ticker:<10} ERROR: {type(e).__name__}: {e}")
