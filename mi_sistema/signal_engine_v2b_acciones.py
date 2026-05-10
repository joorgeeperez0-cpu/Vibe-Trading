"""
Estrategia v2b acciones - Cross-Sectional Momentum 12m skip-1, Top 3, Regime SPY.

Diferencias respecto a v2 original:
- Ventana de momentum: 252 dias bursatiles (12 meses), no 126 (6 meses).
- Skip-1: el momentum se calcula desde t-252 hasta t-21 (ignora el ultimo mes).
  Esto evita el efecto de reversion a corto plazo documentado en literatura.
- Mismo top 3, mismo regime filter (SPY > SMA(200)), mismo rebalanceo mensual.

Skip-1 momentum reduce overlap con mean reversion de corto plazo y suele subir
el Sharpe del cross-sectional momentum entre 0.2-0.3 puntos en estudios academicos
(Asness 1994, Moskowitz et al 2012).
"""

from typing import Dict
import numpy as np
import pandas as pd


class SignalEngine:
    MOMENTUM_LOOKBACK = 252   # 12 meses bursatiles
    MOMENTUM_SKIP = 21        # ignorar ultimo mes (~21 dias bursatiles)
    TOP_N = 3
    REGIME_TICKER = "SPY.US"
    REGIME_SMA = 200

    def generate(self, data_map: Dict[str, pd.DataFrame]) -> Dict[str, pd.Series]:
        signals: Dict[str, pd.Series] = {}

        if self.REGIME_TICKER not in data_map:
            for code, df in data_map.items():
                signals[code] = pd.Series(0.0, index=df.index)
            return signals

        # SPY regime filter
        spy_df = data_map[self.REGIME_TICKER].copy()
        for col in ("open", "high", "low", "close", "volume"):
            if col in spy_df.columns:
                spy_df[col] = pd.to_numeric(spy_df[col], errors="coerce")
        spy_df = spy_df.dropna(subset=["close"])
        spy_close = spy_df["close"]
        spy_sma = spy_close.rolling(self.REGIME_SMA).mean()
        regime_ok = (spy_close > spy_sma).fillna(False)

        # Tickers tradeables
        tradable_codes = [c for c in data_map.keys() if c != self.REGIME_TICKER]

        # DataFrame con closes alineados
        closes_dict = {}
        for code in tradable_codes:
            df = data_map[code].copy()
            for col in ("open", "high", "low", "close", "volume"):
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            df = df.dropna(subset=["close"])
            closes_dict[code] = df["close"]

        if not closes_dict:
            for code in data_map:
                signals[code] = pd.Series(0.0, index=data_map[code].index)
            return signals

        closes_df = pd.DataFrame(closes_dict)

        regime_ok_aligned = regime_ok.reindex(closes_df.index, method="ffill").fillna(False)

        # Skip-1 momentum: (close_t-21 / close_t-252) - 1
        # Es el rendimiento desde t-252 hasta t-21, ignorando el ultimo mes
        close_lookback = closes_df.shift(self.MOMENTUM_LOOKBACK)
        close_skip = closes_df.shift(self.MOMENTUM_SKIP)
        momentum = (close_skip / close_lookback) - 1

        # Iterar dia a dia para gestionar weights
        current_weights = {code: 0.0 for code in tradable_codes}
        weights_per_day = {code: np.zeros(len(closes_df), dtype=float) for code in tradable_codes}

        prev_month_year = None
        for i, date in enumerate(closes_df.index):
            cur_month_year = (date.year, date.month)
            is_rebalance_day = (prev_month_year is not None and cur_month_year != prev_month_year)
            regime_today = bool(regime_ok_aligned.loc[date]) if date in regime_ok_aligned.index else False

            if is_rebalance_day:
                if regime_today:
                    m_today = momentum.loc[date].dropna() if date in momentum.index else pd.Series(dtype=float)
                    m_positive = m_today[m_today > 0]
                    if len(m_positive) > 0:
                        top = m_positive.nlargest(self.TOP_N).index.tolist()
                        new_weights = {code: 0.0 for code in tradable_codes}
                        weight_each = 1.0 / self.TOP_N
                        for ticker in top:
                            new_weights[ticker] = weight_each
                        current_weights = new_weights
                    else:
                        current_weights = {code: 0.0 for code in tradable_codes}
                else:
                    current_weights = {code: 0.0 for code in tradable_codes}
            else:
                if not regime_today:
                    current_weights = {code: 0.0 for code in tradable_codes}

            for code in tradable_codes:
                weights_per_day[code][i] = current_weights[code]

            prev_month_year = cur_month_year

        for code in tradable_codes:
            signals[code] = pd.Series(weights_per_day[code], index=closes_df.index, name=code)

        signals[self.REGIME_TICKER] = pd.Series(0.0, index=data_map[self.REGIME_TICKER].index)

        for code in data_map:
            if code not in signals:
                signals[code] = pd.Series(0.0, index=data_map[code].index)

        return signals
