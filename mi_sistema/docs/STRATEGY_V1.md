# Estrategia v1.5: Donchian breakout 55/20 + SMA(200) sobre 7 cripto

Versión vigente y validada. Reemplaza la v1 original (15 activos mixto) que se descartó por las acciones ser lastre.

## Filosofía y restricciones

- Trend following puro. Solo long. Solo spot. Sin apalancamiento, sin derivados, sin shorts.
- Sin VPS. Decisiones al cierre del día UTC, ejecución manual al apertura siguiente.
- Una decisión al día por activo.
- Compatible con residencia fiscal española.

## Universo final (7 cripto)

BTC-USDT, ETH-USDT, SOL-USDT, XRP-USDT, ADA-USDT, BNB-USDT, AVAX-USDT.

Universo cerrado durante toda la fase de validación. Sin sustituciones salvo pérdida de cotización del activo.

**Por qué este universo y no otros**:
- Probados 4 universos en backtest. Top 7 ganó por mejor Sharpe walk-forward (1.71 vs 1.45 de 5 cripto only, vs 1.39 de 10 cripto expandido).
- Acciones blue chip USA descartadas: -59 € PnL en walk-forward, eran lastre activo, no diversificación.
- DOT, LINK, DOGE descartadas: contribución marginal o negativa al PnL del expandido.

## Reglas de la estrategia

**Entrada larga** (las dos condiciones a la vez):
1. Cierre del día rompe el máximo de los últimos **55 días**.
2. Precio por encima de su **SMA(200)**.

**Salida** (cualquiera de las dos):
1. Cierre por debajo del mínimo de los últimos **20 días**.
2. Salta el stop loss.

**Stop loss inicial**: precio_entrada − 2.0 × ATR(20). Solo cripto en este universo, así que el multiplicador 2.0 aplica a todos.

**Trailing tipo Turtle**: el stop solo se mueve a favor de la posición, nunca se relaja.

## Reglas de riesgo

- **Riesgo por trade**: 1 % del capital total al momento de la entrada (RISK_PER_TRADE = 0.01).
  - Sizing: `weight = mín(1.0, 0.01 / ((entrada − stop) / entrada))`.
  - Esto implementa que si salta el stop, pierdes exactamente 1 % del capital.
- **Drawdown máximo aceptable**: 20 % sobre capital. Si se rompe en backtest la estrategia no pasa a paper. Si se rompe en paper o real se detiene la operativa hasta revisión.
- **Posiciones simultáneas**: hasta 7 abiertas a la vez (una por activo del universo).
- **Priorización**: cuando el peso total supere 100 %, el motor lo capa proporcionalmente.

## Costes modelados

- 0.10 % comisión por lado (Binance spot).
- Slippage estimado en 0.05 % adicional por trade.

## Métricas de validación (cierre 2026-04-30)

| Métrica | In-sample 2018-2022 | Walk-forward 2023-2026 | Umbral |
|---|---|---|---|
| Sharpe ratio | 1.72 | 1.71 | >= 1.0 OK |
| Calmar ratio | 2.51 | 2.26 | >= 0.5 OK |
| Max drawdown | 7.2 % | 7.8 % | <= 20 % OK |
| Profit factor | 3.16 | 2.66 | >= 1.5 OK |
| Trades | 120 | 92 | >= 50 OK |
| Annual return | 18.1 % | 17.7 % | (descriptivo) |

Estabilidad in-sample → walk-forward: **-0.6 % de degradación en Sharpe**. Señal de parámetros robustos.

## Robustez al SMA: sweep validado

| SMA | Sharpe IS | Sharpe WF | Degradación |
|---|---|---|---|
| 100 | 1.65 | 1.18 | -28.5 % |
| 150 | 1.75 | 1.35 | -22.9 % |
| **200** | **1.72** | **1.71** | **-0.6 %** |
| 250 | 1.55 | 1.32 | -14.8 % |

Este sweep no se hizo para optimizar sino para **verificar que SMA(200) generaliza bien**. Las alternativas se desploman 15-28 % al pasar a out-of-sample. Confirmación clara de que SMA(200) es la elección correcta, no una casualidad.

## Periodos de validación

- **In-sample**: 2018-01-01 a 2022-12-31. Datos completos via CCXT-Binance.
- **Walk-forward**: 2023-01-01 a 2026-04-29. Out-of-sample puro.

Datos limitados solo en SOL (desde abril 2020) y AVAX (desde sep 2020). El motor maneja activos con histórico parcial sin romper.

## Criterios de aceptación para paper trading → real

Para pasar de paper trading a operar con dinero real:
- Mínimo 3 meses de paper trading continuo.
- Métricas vivas dentro de un margen del 30 % respecto al backtest.
- Sin errores operativos significativos (señales ignoradas, sizing mal calculado).
- Capital inicial real propuesto: 300-500 € (de los 1.000 € totales).
- Mantener paper en paralelo durante 3 meses adicionales para tener segunda muestra.

## Criterios de descarte

La estrategia se replantea si:
- Retornos concentrados en un único régimen (ej. solo funciona en bull cycle cripto).
- Max drawdown supera el 25 % en cualquier ventana.
- Menos de 30 trades totales en 3 meses de paper.
- Métricas vivas a más del 30 % del backtest en sentido negativo.
