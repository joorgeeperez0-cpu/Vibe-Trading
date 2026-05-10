"""
Variante de v1.5 con SMA(250) en vez de SMA(200).
Solo para test de sensibilidad. NO usar en paper trading hasta validar.
"""

from typing import Dict
import numpy as np
import pandas as pd


def _is_crypto(code: str) -> bool:
    upper = code.upper()
    return upper.endswith("-USDT") or upper.endswith("/USDT")


def _atr(df: pd.DataFrame, period: int = 20) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean()


class SignalEngine:
    DONCHIAN_HIGH = 55
    DONCHIAN_LOW = 20
    SMA_PERIOD = 250  # variante: SMA(250)
    ATR_PERIOD = 20
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
