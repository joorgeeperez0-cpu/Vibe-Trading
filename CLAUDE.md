# Vibe-Trading — Sistema sistemático personal (sobre fork HKUDS/Vibe-Trading)

## Qué es este proyecto
Sistema de **trading sistemático personal** construido encima de un fork de **HKUDS/Vibe-Trading**.
La plataforma upstream (FastAPI + React/TS, carpetas `agent/`, `frontend/`, `assets/`, `Dockerfile`, `docker-compose.yml`, `pyproject.toml`) **no es código propio** — solo se usa como infraestructura.

**Todo el código propio vive en `mi_sistema/`.** Trabajar ahí salvo que el usuario diga lo contrario.

## Estrategias en operación (paper trading)
1. **v1.5** — Donchian breakout 55/20 + filtro SMA200 + ATR stop. 7 cripto, frecuencia diaria.
2. **v2 ETFs** — Cross-sectional momentum top 3 con regime filter SPY. 7 ETFs, frecuencia mensual.

Ambas validadas con:
- Backtest in-sample 2018–2022.
- Walk-forward 2023–2026.
- Criterios de aceptación: **Sharpe ≥ 1.0, Calmar ≥ 0.5, MDD ≤ 20%, PF ≥ 1.5**.

**Estado:** paper trading. Plan: pasar a real con capital pequeño tras 3 meses de validación.

## Stack
- **Python**: `pandas`, `numpy`, `yfinance` (lógica de señales y backtests)
- **Pine Script v6** (TradingView) — versiones equivalentes de las estrategias
- **PowerShell** — orquestación y scheduling local
- **Docker** — entorno reproducible (heredado del upstream)

## Estructura — qué es propio y qué no
```
Vibe-Trading/
├── mi_sistema/                    ← TODO EL CÓDIGO PROPIO
│   ├── signal_engine_v1.py
│   ├── signal_engine_v15_sma{100,150,250}.py
│   ├── signal_engine_v2_acciones.py
│   ├── signal_engine_v2b_acciones.py
│   ├── signal_engine_v3_4h.py
│   ├── paper_log.csv              ← log v1.5 cripto
│   ├── paper_log_v2_etfs.csv      ← log v2 ETFs
│   ├── paper_logs.xlsx
│   ├── paper_trading_guia.md
│   ├── paper_trading_guia_v2.md
│   ├── configs/
│   ├── pine/                      ← versiones Pine Script v6
│   ├── scripts/
│   ├── results/
│   └── docs/
│
├── estrategia_v1.md               ← documentación raíz (propia)
│
└── (resto: agent/, frontend/, Dockerfile, pyproject.toml, README*.md, etc.)
    ↑ UPSTREAM HKUDS/Vibe-Trading — NO modificar salvo petición explícita
```

## Convenciones
- **Versionar estrategias por archivo, no por edición destructiva**: si se cambia v1.5 SMA200 a SMA150, crear `signal_engine_v15_sma150.py` (patrón ya existente). No sobrescribir versiones validadas.
- Los logs de paper trading (`paper_log*.csv`, `paper_logs.xlsx`) son **append-only**. No reescribir histórico — cada fila es una señal real ya emitida.
- Pine Script y Python deben mantenerse **alineados**: un cambio de lógica en una estrategia debe replicarse en ambas versiones (`mi_sistema/*.py` y `mi_sistema/pine/*.pine`). Si solo se actualiza una, dejarlo explícito en el commit.
- Criterios de aceptación (Sharpe/Calmar/MDD/PF) son **gates** — un cambio de estrategia que no los cumpla no se promociona a paper trading; queda en `results/` como experimento.

## Reglas de seguridad
- **No tocar** `agent/`, `frontend/`, `Dockerfile`, `docker-compose.yml`, `pyproject.toml`, ni los `README*.md` del upstream sin pedirlo. Son código de terceros y mezclar cambios propios ahí complica futuras actualizaciones del fork. **Excepción documentada**: `agent/backtest/runner.py` y `agent/backtest/loaders/registry.py` tienen patch propio (OKX → CCXT en routing cripto y reorden de fallback chain), persistente en la imagen Docker. **NO revertir** estos cambios aunque parezcan divergencias respecto al upstream.
- Cualquier paso de "paper → real" requiere confirmación explícita del usuario. Por defecto, todo es paper.
- No commitear claves de broker, API keys ni archivos con datos de cuenta real.

## Convención clave de signal engines
Los archivos `signal_engine_*.py` son **clases que implementan el contrato `SignalEngine`**, NO scripts ejecutables. No tienen `__main__` y lanzarlos con `python <archivo>.py` no produce señal. Para generar señales se usan los scripts en `mi_sistema/scripts/`.

Estado de cada variante:
- `signal_engine_v1.py` (SMA=200) → **VALIDADO Y OPERATIVO** para v1.5 cripto. Sharpe walk-forward 1.71.
- `signal_engine_v2_acciones.py` (cross-sectional momentum 6m, top 3) → **VALIDADO Y OPERATIVO** para v2 ETFs (universo SPY/QQQ/IWM/EFA/EEM/GLD/TLT). Sharpe walk-forward 1.10. Pese al nombre histórico "acciones", el motor se usa con ETFs.
- `signal_engine_v15_sma{100,150,250}.py` → variantes del sweep SMA, **descartadas**. SMA(200) ganó por estabilidad IS→WF.
- `signal_engine_v2b_acciones.py` → variante 12m skip-1 momentum, **descartada**. Peor que v2 base.
- `signal_engine_v3_4h.py` → Donchian breakout intradía 4h, **descartado por datos**. Walk-forward Sharpe 0.55, MDD 23.6 %, comisiones se comen el edge.

## Comandos típicos
```powershell
# Señal diaria v1.5 cripto (auto-escribe a paper_log.csv, con anti-duplicados por fecha)
python mi_sistema/scripts/check_v15_cripto.py

# Forzar reescritura de la fila de hoy (si quieres regenerar tras un error o tras un cambio intra-día)
python mi_sistema/scripts/check_v15_cripto.py --force

# Señal mensual v2 ETFs, último día hábil (auto-escribe a paper_log_v2_etfs.csv)
python mi_sistema/scripts/check_v2_etfs.py
python mi_sistema/scripts/check_v2_etfs.py --force

# Backtest configurable
powershell -ExecutionPolicy Bypass -File mi_sistema/scripts/run_backtest.ps1 -ConfigName "<config>" [-SignalEngine "<engine>"]

# Levantar entorno Docker (patch CCXT persistente en la imagen)
docker compose --profile frontend up -d
```

## Automatización operativa
- **Tarea programada de Windows** (registrada con `mi_sistema/scripts/setup_tarea_diaria.ps1`) lanza `check_v15_cripto.py` diariamente a las 09:00 hora local. Output en `mi_sistema/scripts/schedule_log.txt`. Si el PC estaba apagado, se ejecuta al encenderlo (StartWhenAvailable).
- Verificar estado: `Get-ScheduledTask -TaskName "Vibe v1.5 daily check"`.
- Forzar ejecución manual: `Start-ScheduledTask -TaskName "Vibe v1.5 daily check"`.
- Desinstalar tarea: `Unregister-ScheduledTask -TaskName "Vibe v1.5 daily check" -Confirm:$false`.
- v2 ETFs NO está automatizado (frecuencia mensual, el usuario lo lanza a mano cada último día hábil).

## Documentación a consultar
- `estrategia_v1.md` (raíz) — diseño original de la estrategia v1 (histórico, ya superado por STRATEGY_V1.md).
- `mi_sistema/paper_trading_guia.md` — guía operativa v1.5 (cripto diario).
- `mi_sistema/paper_trading_guia_v2.md` — guía operativa v2 ETFs (mensual).
- `mi_sistema/docs/STATE.md` — estado actual del proyecto, **se actualiza después de cada hito**.
- `mi_sistema/docs/DECISIONS_LOG.md` — log cronológico de decisiones con justificación.
- `mi_sistema/docs/STRATEGY_V1.md` — especificación cerrada de v1.5 cripto (Donchian + SMA).
- `mi_sistema/docs/STRATEGY_V2.md` — especificación cerrada de v2 ETFs (momentum + regime).
- `mi_sistema/docs/SYSTEM.md` — instrucciones del rol y división de capas (Claude AI / Cowork / agente Vibe-Trading).
- `mi_sistema/docs/PLATFORM_INTERNALS.md` — cómo funciona Vibe-Trading por dentro (regex de market detection, FALLBACK_CHAINS, etc.).
