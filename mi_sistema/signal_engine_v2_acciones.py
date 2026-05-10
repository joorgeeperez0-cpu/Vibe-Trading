"""
Estrategia v2 acciones - Cross-Sectional Momentum Top 3 con Regime Filter SPY.

Logica:
- Cada cambio de mes calendario: ranking de los 10 blue chips USA por rendimiento
  de los ultimos 126 dias bursatiles (~6 meses).
- Seleccionar las 3 con mayor momentum POSITIVO. Equiponderadas (peso 1/3 cada una).
- Mantener hasta el siguiente cambio de mes.
- Regime filter: solo se abren o mantienen posiciones si SPY > SMA(200).
  Si SPY rompe SMA(200) a la baja a mitad de mes, todas las posiciones a cash.

SPY (codigo "SPY.US") debe estar incluido en config.codes como referencia.
SPY no se opera (su signal siempre es 0).

Sigue el contrato SignalEngine de Vibe-Trading: returns Dict[code, Series]
con valores en [0.0, 1.0].
"""

from typing import Dict
import numpy as np
import pandas as pd


class SignalEngine:
    MOMENTUM_WINDOW = 126   # dias bursatiles ~ 6 meses
    TOP_N = 3
    REGIME_TICKER = "SPY.US"
    REGIME_SMA = 200

    def generate(self, data_map: Dict[str, pd.DataFrame]) -> Dict[str, pd.Series]:
        signals: Dict[str, pd.Series] = {}

        # Sin SPY no hay filtro de regimen: todo a cash por seguridad
        if self.REGIME_TICKER not in data_map:
            for code, df in data_map.items():
                signals[code] = pd.Series(0.0, index=df.index)
            return signals

        # Preparar SPY: closes y filtro de regimen
        spy_df = data_map[self.REGIME_TICKER].copy()
        for col in ("open", "high", "low", "close", "volume"):
            if col in spy_df.columns:
                spy_df[col] = pd.to_numeric(spy_df[col], errors="coerce")
        spy_df = spy_df.dropna(subset=["close"])
        spy_close = spy_df["close"]
        spy_sma = spy_close.rolling(self.REGIME_SMA).mean()
        regime_ok = (spy_close > spy_sma).fillna(False)

        # Tickers tradeables: todos menos SPY
        tradable_codes = [c for c in data_map.keys() if c != self.REGIME_TICKER]

        # DataFrame con closes alineados (outer join por fechas)
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

        # Alinear regime_ok al indice de closes_df
        regime_ok_aligned = regime_ok.reindex(closes_df.index, method="ffill").fillna(False)

        # Momentum: rendimiento simple de los ultimos 126 dias
        momentum = closes_df.pct_change(self.MOMENTUM_WINDOW)

        # Iterar dia a dia para gestionar el estado de las weights
        current_weights = {code: 0.0 for code in tradable_codes}
        weights_per_day = {code: np.zeros(len(closes_df), dtype=float) for code in tradable_codes}

        prev_month_year = None
        for i, date in enumerate(closes_df.index):
            cur_month_year = (date.year, date.month)

            # Detectar cambio de mes (no rebalanceamos en el primer dia del backtest)
            is_rebalance_day = (prev_month_year is not None and cur_month_year != prev_month_year)

            regime_today = bool(regime_ok_aligned.loc[date]) if date in regime_ok_aligned.index else False

            if is_rebalance_day:
                if regime_today:
                    # Regime OK: seleccionar top 3 con momentum positivo
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
                        # Sin momentum positivo en ningun activo: todo a cash
                        current_weights = {code: 0.0 for code in tradable_codes}
                else:
                    # Regime roto en dia de rebalanceo: cash
                    current_weights = {code: 0.0 for code in tradable_codes}
            else:
                # Dia normal (no rebalanceo)
                # Si regime se rompe a mitad de mes, salir de todas las posiciones
                if not regime_today:
                    current_weights = {code: 0.0 for code in tradable_codes}

            # Guardar las weights del dia
            for code in tradable_codes:
                weights_per_day[code][i] = current_weights[code]

            prev_month_year = cur_month_year

        # Construir las Series de salida
        for code in tradable_codes:
            signals[code] = pd.Series(weights_per_day[code], index=closes_df.index, name=code)

        # SPY no se opera
        signals[self.REGIME_TICKER] = pd.Series(0.0, index=data_map[self.REGIME_TICKER].index)

        # Cualquier code adicional que pudiera estar en data_map pero no procesamos
        for code in data_map:
            if code not in signals:
                signals[code] = pd.Series(0.0, index=data_map[code].index)

        return signals
