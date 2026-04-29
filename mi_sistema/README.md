# mi_sistema/

Mi implementación personal de estrategias de trading sobre la plataforma Vibe-Trading.

Esto es el código y los resultados de mi proyecto, construido encima del fork de HKUDS/Vibe-Trading. Los `signal_engines/` definen la lógica, los `configs/` parametrizan cada run, los `scripts/` automatizan la ejecución, y `results/` guarda los artefactos de cada backtest.

## Estructura

```
mi_sistema/
├── README.md                       Este archivo.
├── signal_engine_v1.py             Estrategia v1: Donchian breakout 55/20 con SMA(200).
├── configs/
│   ├── in_sample_2018_2022.json    Config del backtest in-sample.
│   └── walkforward_2023_2026.json  Config del walk-forward.
├── scripts/
│   ├── patch_loader.py             Cambia el primary loader cripto de OKX a CCXT en el contenedor.
│   ├── parche_loader.ps1           PowerShell que aplica el parche dentro del Docker.
│   ├── run_backtest.ps1            Lanza un backtest. Recibe el nombre del config como argumento.
│   ├── test_data_yfinance.py       Sanity check de datos de yfinance para los 15 activos.
│   └── ejecutar_test.ps1           Runner del sanity check.
└── results/
    ├── in_sample_2018_2022/        Artefactos del backtest 2018-2022.
    └── walkforward_2023_2026/      Artefactos del walk-forward 2023-2026.
```

## Cómo usar

**1. Aplicar el parche del loader cripto** (solo la primera vez, o tras `docker compose down + up`):

```powershell
powershell -ExecutionPolicy Bypass -File mi_sistema\scripts\parche_loader.ps1
```

Esto cambia el routing interno de cripto en el contenedor: en vez de pegarle a OKX (que solo tiene datos desde mayo 2022), va directo a CCXT-Binance (que tiene desde 2017).

**2. Lanzar un backtest**:

```powershell
powershell -ExecutionPolicy Bypass -File mi_sistema\scripts\run_backtest.ps1 -ConfigName "in_sample_2018_2022"
powershell -ExecutionPolicy Bypass -File mi_sistema\scripts\run_backtest.ps1 -ConfigName "walkforward_2023_2026"
```

Los artefactos quedan en `mi_sistema\results\<NombreConfig>\artifacts\`.

**3. Ver métricas**:

```powershell
notepad mi_sistema\results\in_sample_2018_2022\artifacts\metrics.csv
```

## Resumen de resultados

### In-sample 2018-2022

| Métrica | Valor | Umbral | Estado |
|---|---|---|---|
| Sharpe | 0.94 | >= 1.0 | Falla |
| Calmar | 0.69 | >= 0.5 | OK |
| Max DD | 15.0 % | <= 20 % | OK |
| Profit factor | 1.53 | >= 1.5 | OK |
| Trades | 274 | >= 50 | OK |
| Concentración | 60 % en 2021 | <= 50 % | Falla |

### Walk-forward 2023-2026

| Métrica | Valor | Umbral | Estado |
|---|---|---|---|
| Sharpe | 0.88 | >= 1.0 | Falla |
| Calmar | 0.58 | >= 0.5 | OK |
| Max DD | 17.0 % | <= 20 % | OK |
| Profit factor | 1.36 | >= 1.5 | Falla |
| Trades | 207 | >= 50 | OK |

**Conclusión clave**: la estrategia es estable (no overfitting) pero no llega a los criterios de aceptación. Cripto domina el PnL (87 % en in-sample, pendiente de confirmar en walk-forward).

## Decisión pendiente

Iterar a v2 con cambios concretos (eliminar acciones, ajustar parámetros, añadir filtros) o aceptar v1 como sistema cripto-only y hacer paper trading a sabiendas de que falla Sharpe y profit factor por poco.
