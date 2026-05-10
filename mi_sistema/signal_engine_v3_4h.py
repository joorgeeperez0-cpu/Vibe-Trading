"""
Estrategia v3 4h - Donchian breakout sobre cripto en timeframe 4 horas.

Adaptacion intradia de v1.5. Mismas reglas pero ajustadas a barras de 4h:
- Donchian high: 60 barras (~10 dias).
- Donchian low: 20 barras (~3.3 dias).
- SMA filtro: 120 barras (~20 dias).
- ATR period: 30 barras (~5 dias).
- ATR mult cripto: 2.0 (mismo que v1.5).
- Risk per trade: 1 % del capital.

Hipotesis previa: 3-5x mas trades que v1.5 daily, pero Sharpe probablemente
similar o algo inferior. Si Sharpe walk-forward >= 1.0 y MDD <= 20 %, viable.
"""

from typing import Dict
import numpy as np
import pandas as pd


def _is_crypto(code: str) -> bool:
    upper = code.upper()
    return upper.endswith("-USDT") or upper.endswith("/USDT")


def _atr(df: pd.DataFrame, period: int = 30) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean()


class SignalEngine:
    DONCHIAN_HIGH = 60     # ~10 dias en 4h
    DONCHIAN_LOW = 20      # ~3.3 dias en 4h
    SMA_PERIOD = 120       # ~20 dias en 4h
    ATR_PERIOD = 30        # ~5 dias en 4h
    ATR_MULT_CRYPTO = 2.0
    ATR_MULT_STOCK = 1.5
    RISK_PER_TRADE = 0.01

    def generate(self, data_map: Dict[str, pd.DataFrame]) -> Dict[str, pd.Series]:
        signals: Dict[str, pd.Series] = {}

        for code, df_in in data_map.items():
            if df_in is None or df_in.empty:
                signals[code] = pd.Series(0.0, index=pd.DatetimeIndex([]))
                continue

            df = df_in.copy()
            for col in ("open", "high", "low", "close", "volume"):
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            df = df.dropna(subset=["close", "high", "low"])

            min_history = self.SMA_PERIOD + self.DONCHIAN_HIGH
            if len(df) < min_history:
                signals[code] = pd.Series(0.0, index=df.index)
                continue

            sma = df["close"].rolling(self.SMA_PERIOD).mean()
            donch_high = df["high"].rolling(self.DONCHIAN_HIGH).max().shift(1)
            donch_low = df["low"].rolling(self.DONCHIAN_LOW).min().shift(1)
            atr = _atr(df, self.ATR_PERIOD)

            atr_mult = self.ATR_MULT_CRYPTO if _is_crypto(code) else self.ATR_MULT_STOCK

            closes = df["close"].values.astype(float)
            highs = df["high"].values.astype(float)
            lows = df["low"].values.astype(float)
            sma_v = sma.values.astype(float)
            dhigh_v = donch_high.values.astype(float)
            dlow_v = donch_low.values.astype(float)
            atr_v = atr.values.astype(float)

            n = len(df)
            sig = np.zeros(n, dtype=float)

            in_position = False
            current_weight = 0.0
            stop_price = 0.0

            for i in range(n):
                if not in_position:
                    can_evaluate = (
                        not np.isnan(dhigh_v[i])
                        and not np.isnan(sma_v[i])
                        and not np.isnan(atr_v[i])
                        and atr_v[i] > 0
                    )
                    if can_evaluate and closes[i] > dhigh_v[i] and closes[i] > sma_v[i]:
                        entry_price = closes[i]
                        stop_price = entry_price - atr_mult * atr_v[i]
                        if stop_price < entry_price:
                            risk_pct = (entry_price - stop_price) / entry_price
                            current_weight = min(1.0, self.RISK_PER_TRADE / risk_pct) if risk_pct > 0 else 0.0
                            sig[i] = current_weight
                            in_position = True
                else:
                    if not np.isnan(atr_v[i]) and atr_v[i] > 0:
                        new_stop = closes[i] - atr_mult * atr_v[i]
                        if new_stop > stop_price:
                            stop_price = new_stop

                    exit_now = False
                    if lows[i] <= stop_price:
                        exit_now = True
                    elif not np.isnan(dlow_v[i]) and closes[i] < dlow_v[i]:
                        exit_now = True

                    if exit_now:
                        sig[i] = 0.0
                        current_weight = 0.0
                        in_position = False
                    else:
                        sig[i] = current_weight

            signals[code] = pd.Series(sig, index=df.index, name=code)

        return signals
