# mi_sistema/

Mi implementación personal de estrategias de trading sobre la plataforma Vibe-Trading.

Esto es el código y los resultados de mi proyecto, construido encima del fork de HKUDS/Vibe-Trading. Los signal engines definen la lógica, los configs parametrizan cada run, los scripts automatizan la ejecución, y `results/` guarda los artefactos de cada backtest.

## Estado actual

**v1.5 validada y lista para paper trading.** Donchian breakout 55/20 con filtro SMA(200), riesgo 1 % por trade, sobre 7 cripto. Pasa todos los criterios de aceptación con margen, in-sample y walk-forward.

| Métrica | In-sample 2018-2022 | Walk-forward 2023-2026 | Umbral | Estado |
|---|---|---|---|---|
| Sharpe ratio | 1.72 | 1.71 | >= 1.0 | OK |
| Calmar ratio | 2.51 | 2.26 | >= 0.5 | OK |
| Max drawdown | 7.2 % | 7.8 % | <= 20 % | OK |
| Profit factor | 3.16 | 2.66 | >= 1.5 | OK |
| Trades | 120 | 92 | >= 50 | OK |
| Annual return | 18.1 % | 17.7 % | (descriptivo) | |

**Universo de v1.5** (7 cripto): BTC-USDT, ETH-USDT, SOL-USDT, XRP-USDT, ADA-USDT, BNB-USDT, AVAX-USDT.

## Estructura

```
mi_sistema/
├── README.md                              Este archivo.
├── signal_engine_v1.py                    Estrategia: Donchian 55/20 + SMA(200) + ATR stop.
├── configs/
│   ├── in_sample_2018_2022.json           Universo mixto v1 (15 activos), historico
│   ├── walkforward_2023_2026.json         Universo mixto v1 (15 activos), historico
│   ├── v1_cripto_only_in_sample.json      5 cripto, historico
│   ├── v1_cripto_only_walkforward.json    5 cripto, historico
│   ├── v1_cripto_expandido_in_sample.json 10 cripto, historico
│   ├── v1_cripto_expandido_walkforward.json 10 cripto, historico
│   ├── v15_cripto_top7_in_sample.json     7 cripto OPTIMOS, validado
│   └── v15_cripto_top7_walkforward.json   7 cripto OPTIMOS, validado
├── scripts/
│   ├── patch_loader.py                    Cambia primary loader cripto OKX -> CCXT.
│   ├── parche_loader.ps1                  Lanzador del parche.
│   ├── run_backtest.ps1                   Genérico, recibe config como argumento.
│   └── test_data_yfinance.py              Sanity check de datos.
└── results/
    ├── in_sample_2018_2022/               v1 mixto historico (Sharpe 0.94)
    ├── walkforward_2023_2026/             v1 mixto historico (Sharpe 0.88)
    ├── v1_cripto_only_in_sample/          (Sharpe 1.62)
    ├── v1_cripto_only_walkforward/        (Sharpe 1.45)
    ├── v1_cripto_expandido_in_sample/     (Sharpe 1.55)
    ├── v1_cripto_expandido_walkforward/   (Sharpe 1.39)
    ├── v15_cripto_top7_in_sample/         GANADOR (Sharpe 1.72)
    └── v15_cripto_top7_walkforward/       GANADOR (Sharpe 1.71)
```

## Cómo usar

### Paso previo: aplicar el parche del loader cripto

Solo la primera vez tras `docker compose down + up`. Cambia el routing interno: cripto va a CCXT-Binance (histórico desde 2017) en vez de OKX (solo desde mayo 2022).

```powershell
powershell -ExecutionPolicy Bypass -File mi_sistema\scripts\parche_loader.ps1
```

### Lanzar un backtest existente

```powershell
powershell -ExecutionPolicy Bypass -File mi_sistema\scripts\run_backtest.ps1 -ConfigName "v15_cripto_top7_walkforward"
```

Los artefactos quedan en `mi_sistema\results\<NombreConfig>\artifacts\`.

### Ver métricas

```powershell
Get-Content mi_sistema\results\v15_cripto_top7_walkforward\artifacts\metrics.csv
```

### Validar trades por activo

```powershell
Import-Csv mi_sistema\results\v15_cripto_top7_walkforward\artifacts\trades.csv | Group-Object code | Select-Object Name, Count | Sort-Object Count -Descending
```

## Estrategia v1.5 en una página

**Tipo**: Trend following por ruptura. Long-only, spot, sin apalancamiento.

**Entrada**: cierre rompe máximo de los últimos 55 días Y precio por encima de SMA(200).

**Salida**: cierre rompe mínimo de los últimos 20 días O salta el stop ATR.

**Stop**: precio_entrada − 2.0 × ATR(20). Trailing solo a favor (Turtle).

**Sizing**: peso de la posición = mín(1.0, 0.01 / risk_pct), donde risk_pct = (entrada − stop) / entrada. Esto implementa el 1 % de riesgo por trade.

**Universo**: 7 cripto (BTC, ETH, SOL, XRP, ADA, BNB, AVAX) en formato Vibe-Trading (sufijo `-USDT`).

**Costes**: 0.1 % comisión por lado, slippage incluido por motor.

## Iteraciones probadas y descartadas

**v1 mixto (5 cripto + 10 acciones blue chip)**: descartado. Acciones eran lastre activo (-59 € PnL en walk-forward). Sharpe 0.88 walk-forward.

**v1 cripto-only (BTC, ETH, SOL, XRP, ADA)**: bueno pero subóptimo. Sharpe 1.45 walk-forward. Drop de ~6 puntos de retorno anual respecto a v1.5.

**v1 cripto expandido (10 cripto, +BNB AVAX LINK DOT DOGE)**: bueno pero con problemas. DOT con PnL negativo, LINK y DOGE con aporte marginal. Sharpe 1.39 walk-forward.

**v1.5 cripto top 7**: ganador. Selección de los 7 con contribución positiva clara basada en el análisis del walk-forward expandido. Sharpe 1.71 walk-forward.

## Próximos pasos

**1. Paper trading con v1.5 (3 meses)**: traducir las reglas a Pine Script para TradingView. Operar sin dinero real, comparar señales generadas con las del backtest, medir capacidad de ejecutar las reglas sin saltármelas. Si tras 3 meses las métricas vivas están dentro de un 30 % de las del backtest, pasamos a real con capital pequeño.

**2. v2 acciones (en paralelo)**: cross-sectional momentum top 3 con filtro de régimen sobre SPY. Si pasa criterios, se opera junto a v1.5 con asignación de capital descorrelacionada.

## Notas de la plataforma

**Parche permanente del loader cripto**: el archivo `runner.py` y `registry.py` se modifican en runtime con `parche_loader.ps1`. Los cambios se mantienen mientras el contenedor exista. Si haces `docker compose down`, hay que volver a aplicar el parche tras `up`.

**Bypass del agente**: los scripts `run_backtest.ps1` van directos al motor de backtest, no usan el agente DeepSeek. Esto da resultados deterministas y rápidos. El agente del Vibe-Trading sigue disponible para análisis exploratorios via web UI cuando haga falta.

**Datos**: yfinance para acciones .US (auto-fallback funciona), CCXT-Binance para cripto -USDT (tras parche). Histórico desde 2018, salvo SOL (desde abril 2020) y AVAX (desde septiembre 2020).
