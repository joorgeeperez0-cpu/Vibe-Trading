# v1_stopfix · resultados (2026-09-13)

Experimento: corregir el trailing stop "mismo día" de v1.5 cripto. Motor: `mi_sistema/signal_engine_v1_stopfix.py`. Pine: `mi_sistema/pine/v15_stopfix.pine`.

**Estado: APROBADO y en operativa desde 2026-09-13** (decisión del usuario). `signal_engine_v1.py` y `pine/v15_donchian.pine` quedan deprecados. `paper_log.csv` reconstruido con stopfix: 7 trades, exactamente los previstos en la tabla de impacto de abajo.

## Metodología
- Harness `mi_sistema/scripts/run_backtest_local.py`: el mismo `CryptoEngine` de `agent/backtest` (sin modificar), sobre los OHLCV archivados de `results/v15_cripto_top7_in_sample` y `results/v15_cripto_top7_walkforward`, con las configs `configs/v15_cripto_top7_{in_sample,walkforward}.json`.
- Motivo: Docker parado y CCXT-Binance bloqueado desde España; además, usar los mismos OHLCV aísla el efecto del cambio de motor.
- Validación: `repro_v1_*` reproduce v1 con métricas idénticas y `trades.csv` / `equity.csv` / `positions.csv` idénticos línea a línea a los archivados.
- Cada carpeta de run incluye `run_info.json` (hashes de config y motor, origen de los OHLCV, versiones).

## Carpetas y archivos
| Ruta | Contenido |
|---|---|
| `is_2018_2022/artifacts/` | stopfix in-sample: metrics, trades, equity, positions, OHLCV |
| `wf_2023_2026/artifacts/` | stopfix walk-forward |
| `repro_v1_is_2018_2022/`, `repro_v1_wf_2023_2026/` | reproducción de v1 con el harness (prueba de paridad) |
| `comparison.md` | tablas v1 vs stopfix, año a año, gates (generado por `scripts/analyze_v1_stopfix.py`) |
| `comparison_summary.csv`, `comparison_yearly.csv` | lo mismo en CSV |
| `v1_exit_types_is_2018_2022.csv`, `v1_exit_types_wf_2023_2026.csv` | cada salida de v1 clasificada (generado por `scripts/diag_v1_exit_types.py`) |

## Diagnóstico de salidas de v1
| Periodo | Tipo | N | Retorno medio trade | Ganadores | Día de salida alcista |
|---|---|---|---|---|---|
| IS | stop fantasma | 40 | +26.6 % | 100 % | 100 % |
| IS | stop real | 80 | −0.6 % | 36 % | 14 % |
| WF | stop fantasma | 30 | +21.1 % | 100 % | 100 % |
| WF | stop real | 62 | −1.2 % | 34 % | 13 % |

"Stop fantasma" = salida que solo existe porque el stop se subió con el close del mismo día. Con el engine ejecutando en la apertura siguiente, estas salidas eran tomas de beneficio en días de mucho rango, no un lookahead que inflara el resultado. (No hubo salidas por Donchian: el stop ATR siempre salta antes.)

## Impacto sobre el paper 2026 (yfinance, desde 2026-05-01)
| Ticker | v1 | stopfix |
|---|---|---|
| BTC | IN 08-19, OUT 08-20, IN 08-21 [abierta] | IN 08-19 [abierta] |
| ETH | IN 08-19, OUT 08-21 | IN 08-19, OUT 08-23 |
| SOL | IN 08-19, OUT 08-21, IN 08-27, OUT 08-30 | IN 08-19, OUT 08-30 |
| XRP | IN 08-21, OUT 08-26 | igual |
| ADA | IN 08-21, OUT 08-25 | igual |
| BNB | IN 08-19, OUT 08-20, IN 08-21, OUT 09-01, IN 09-05, OUT 09-10 | IN 08-19, OUT 09-01, IN 09-05, OUT 09-10 |
| AVAX | — | — |

10 trades (v1) → 7 trades (stopfix).

## Reproducir
```powershell
python mi_sistema/scripts/run_backtest_local.py --config mi_sistema/configs/v15_cripto_top7_in_sample.json --data mi_sistema/results/v15_cripto_top7_in_sample/artifacts --engine signal_engine_v1_stopfix --out mi_sistema/results/v1_stopfix/is_2018_2022
python mi_sistema/scripts/run_backtest_local.py --config mi_sistema/configs/v15_cripto_top7_walkforward.json --data mi_sistema/results/v15_cripto_top7_walkforward/artifacts --engine signal_engine_v1_stopfix --out mi_sistema/results/v1_stopfix/wf_2023_2026
python mi_sistema/scripts/analyze_v1_stopfix.py
python mi_sistema/scripts/diag_v1_exit_types.py
```
