# v1 vs v1_stopfix

Mismos OHLCV archivados, mismo CryptoEngine, mismas configs. v1 = artefactos archivados (reproducidos al decimal con el harness local).

## Walk-forward 2023-01-01 a 2026-04-29 + in-sample stopfix

| Métrica | v1 IS | v1 WF (ref) | stopfix IS | stopfix WF | Delta WF |
|---|---|---|---|---|---|
| Sharpe | 1.72 | 1.71 | 1.66 | 1.75 | +0.03 |
| Calmar | 2.51 | 2.26 | 2.49 | 2.77 | +0.51 |
| MDD % | 7.2 | 7.8 | 10.2 | 8.2 | +0.43 |
| PF | 3.16 | 2.66 | 5.01 | 3.38 | +0.72 |
| # Trades | 120 | 92 | 95 | 74 | -18.00 |
| Retorno anual % | 18.1 | 17.7 | 25.5 | 22.8 | +5.18 |
| Win rate % | 57.5 | 55.4 | 61.1 | 52.7 | -2.73 |
| Ganancia media € | 27.97 | 23.29 | 46.14 | 36.73 | +13.44 |
| Pérdida media € | 11.97 | 10.89 | 14.43 | 12.11 | +1.23 |
| Ganancia/pérdida media | 2.34 | 2.14 | 3.20 | 3.03 | +0.89 |
| Días medios en posición | 7.8 | 7.1 | 10.8 | 9.9 | +2.78 |
| Máx. pérdidas seguidas | 6 | 6 | 6 | 7 | +1.00 |

## Año a año (walk-forward)

| Año | Retorno % v1 | Retorno % sf | Sharpe v1 | Sharpe sf | MDD % v1 | MDD % sf | PF v1 | PF sf | Trades v1 | Trades sf |
|---|---|---|---|---|---|---|---|---|---|---|
| 2023 | 35.1 | 35.8 | 3.00 | 2.67 | 3.1 | 4.6 | 9.25 | 9.69 | 20 | 15 |
| 2024 | 20.6 | 41.9 | 1.52 | 2.13 | 4.8 | 6.4 | 2.28 | 4.12 | 47 | 37 |
| 2025 | 6.9 | 4.2 | 0.99 | 0.56 | 5.4 | 7.4 | 1.75 | 1.55 | 24 | 21 |
| 2026 (hasta 2026-04-29) | -1.3 | -1.3 | -2.26 | -2.26 | 1.4 | 1.4 | 0.00 | 0.00 | 1 | 1 |

## Gates

stopfix WF: 4/4 -> sharpe 1.75 >= 1.0 OK; calmar 2.77 >= 0.5 OK; mdd_pct 8.23 <= 20.0 OK; profit_factor 3.38 >= 1.5 OK

stopfix IS: 4/4 -> sharpe 1.66 >= 1.0 OK; calmar 2.49 >= 0.5 OK; mdd_pct 10.23 <= 20.0 OK; profit_factor 5.01 >= 1.5 OK

stopfix WF >= v1 WF en 3/4 métricas: sharpe sí, calmar sí, mdd_pct no, profit_factor sí

**Regla automática:** CANDIDATO A SUSTITUCIÓN (pasa 4 gates y >= v1 en al menos 3/4 métricas WF)
