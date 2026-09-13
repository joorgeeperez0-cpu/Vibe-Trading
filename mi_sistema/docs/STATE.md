# Estado actual del proyecto

**Última actualización**: 2026-09-13

## Hito 2026-09-13 · Corrección de bugs de datos y reconstrucción de paper_log.csv

Proyecto en stand-by (modo B, paper sin capital real) desde 2026-05-28. Binance España bloqueado desde 2026-07-01.

**Qué pasó**: el `paper_log.csv` de v1.5 estaba corrupto por 4 bugs en `check_v15_cripto.py` (fecha desplazada un día, velas repetidas, días sin ejecución sin entradas/salidas, sin persistencia ni backfill). El log original queda como evidencia en `mi_sistema/paper_log_corrupto_2026-09-13.csv.bak`.

**Qué se hizo**:
- Fase 1: fixes de fecha real de vela, `end = hoy + 2`, aviso de datos rancios y backfill en `check_v15_cripto.py` y `check_v2_etfs.py`.
- Fase 2: se añadieron 2 fixes más (descartar la vela UTC en curso y deduplicar velas) y se reconstruyó `paper_log.csv` desde 2026-05-01 → **135 filas (2026-05-01 a 2026-09-12)**, sin fechas duplicadas ni huecos.
- Validación contra FMP: divergencia máxima yfinance vs FMP en las velas de señal 0.77 % (ADA, en high/low). Ninguna > 1 %.
- Fase 3: estado persistente en `mi_sistema/positions_state.json`, validación cruzada semanal yfinance vs FMP (domingos, `data_quality_check.py`, requiere `FMP_API_KEY`).

**Track record reconstruido v1.5 (2026-05-01 → 2026-09-12)**:
- Sin señales hasta el 2026-08-19 (mercado bajo SMA 200 / sin breakout).
- 10 trades: 9 cerrados + BTC abierto (entrada 2026-08-21 a 78 335, stop 75 958).
- Con precios de entrada FMP y precios de stop registrados: 4 ganadores / 9 cerrados (44 %). 8 de las 9 salidas son stops subidos con el close del mismo día en que se tocaron (precio de stop > close del día) (ver DECISIONS_LOG 2026-09-13, punto abierto).

**Decisiones abiertas**: comportamiento del trailing stop en la misma vela (Python y Pine lo hacen igual; afecta al backtest validado). Ver DECISIONS_LOG.

## Resumen ejecutivo

**Dos sistemas validados y listos para paper trading.**

**v1.5 cripto** (Donchian breakout 55/20 + SMA(200)): operando en paper desde 2026-05-01 sobre 7 cripto vía TradingView. Sin señales aún (BTC bajo SMA 200).

**v2 ETFs** (cross-sectional momentum top 3 + regime filter SPY): validado hoy 2026-05-05. Pendiente de plan de paper trading (mensual, manual).

## Métricas de los dos sistemas

### v1.5 cripto

| Métrica | IS 2018-2022 | WF 2023-2026 |
|---|---|---|
| Sharpe | 1.72 | 1.71 |
| Calmar | 2.51 | 2.26 |
| Max DD | 7.2 % | 7.8 % |
| Profit factor | 3.16 | 2.66 |
| Trades | 120 | 92 |
| Annual return | 18.1 % | 17.7 % |

**Universo**: BTC-USDT, ETH-USDT, SOL-USDT, XRP-USDT, ADA-USDT, BNB-USDT, AVAX-USDT.

### v2 ETFs

| Métrica | IS 2018-2022 | WF 2023-2026 |
|---|---|---|
| Sharpe | 0.64 | 1.10 |
| Calmar | 0.43 | 1.40 |
| Max DD | 12.2 % | 7.9 % |
| Profit factor | 2.44 | 9.11 |
| Trades | 35 | 21 |
| Annual return | 5.2 % | 11.1 % |

**Universo**: SPY (regime ref), QQQ, IWM, EFA, EEM, GLD, TLT (6 tradeables).

## Hecho

- Setup Docker, OpenRouter, fork personal en GitHub.
- v1 mixto (15 activos) descartado: acciones blue chip eran lastre activo (-59 € PnL en WF).
- v1 cripto-only (5), v1 cripto expandido (10) descartados.
- **v1.5 cripto top 7** validado con Sharpe WF 1.71 y degradación IS→WF de -0.6 %.
- Sweep SMA confirmó SMA(200) como elección robusta (alternativas 100/150/250 se desploman en WF).
- Parche del loader cripto OKX→CCXT integrado en imagen Docker (persistente).
- Pine Script v6 cargado en TradingView para los 7 cripto.
- v2 acciones probado en 4 universos: 10 stocks (Sharpe 0.96 WF), 10 stocks 12m skip-1 (peor), 30 NDX (peor), **7 ETFs (Sharpe 1.10 WF) ← elegido**.
- ETFs gana por: diversificación entre clases de activos, sin sesgo de supervivencia, GLD+TLT como hedges naturales en bear de equity.

## En curso

- Paper trading v1.5 cripto en TradingView. Empezó 2026-05-01. Llevamos 5 días sin señales (mercado bajo SMA 200 mayoritariamente).
- Documentación de v2 ETFs como sistema validado: `mi_sistema/docs/STRATEGY_V2.md`.

## Pendiente para futuras sesiones

- **Plan paper trading v2 ETFs**: definir capital asignado (propuesta 50/50 con v1.5), método de revisión mensual (TradingView Pine Script vs hoja de cálculo), columnas adicionales en paper_log.csv para rebalanceos mensuales.
- **Tras 1 mes de paper de v1.5**: revisión parcial, comparación con backtest.
- **Tras 3 meses de paper de v1.5**: decisión sobre ir a real con capital pequeño.
- **Sweep RISK_PER_TRADE (deferido)**: NO tocar hasta tener 3 meses de paper validado.

## Cartera proyectada cuando ambos sistemas estén en real

| Sistema | Universo | Capital | Trades/año | Sharpe esperado |
|---|---|---|---|---|
| v1.5 cripto | BTC, ETH, SOL, XRP, ADA, BNB, AVAX | 50 % | ~28 | 1.5-1.7 |
| v2 ETFs | SPY (ref), QQQ, IWM, EFA, EEM, GLD, TLT | 50 % | ~6 | 1.0-1.2 |
| **Total** | 14 instrumentos | 100 % | **~34** | combinado por descorrelación |

Sistemas estructuralmente descorrelacionados (cripto vs equity/bonos/commodities). El combinado debería tener Sharpe similar o algo superior al mejor de los dos individuales por reducción de varianza.

## Workflow operativo

**Backtests**:
- `docker compose --profile frontend up -d` (parche persistente, no requiere reaplicar).
- `mi_sistema/scripts/run_backtest.ps1 -ConfigName "X" [-SignalEngine "Y"]`.

**Paper trading**:
- v1.5: revisión diaria de 7 gráficos en TradingView, anotar en `paper_log.csv`.
- v2 ETFs: revisión mensual (último día hábil), rebalanceo, anotar en `paper_log.csv` (columnas a definir).

## Decisiones abiertas

Ninguna. Cartera definitiva fijada el 2026-05-05.

## Cartera operativa (paper trading)

- **v1.5 cripto**: 500 € capital de referencia, daily, 7 cripto, automatizado vía `mi_sistema/scripts/check_v15_cripto.py`. Empezó 2026-05-01.
- **v2 ETFs**: 500 € capital de referencia, mensual, 7 ETFs (3 tradeables al mes), automatizado vía `mi_sistema/scripts/check_v2_etfs.py`. Empezó 2026-05-05 con apertura inicial EEM/IWM/GLD.

## Descartes documentados

- v1 mixto (15 activos): acciones eran lastre.
- v1 cripto-only (5) y v1 cripto expandido (10): subóptimos vs v1.5 top 7.
- v2 acciones original (10 stocks): IS falla criterios.
- v2b (12m skip-1): peor que v2 base.
- v2 Nasdaq 30: peor que ETFs en todas las dimensiones.
- **v3 4h cripto**: WF Sharpe 0.55, Calmar 0.42, MDD 23.6 %. Falla 4/5 criterios. Comisiones eaten 2/3 del bruto.
