# Estrategia v1 — Vibe Trading

**Versión:** 1.0
**Fecha:** 2026-04-29
**Responsable:** Jorge
**Estado:** Draft inicial para fase 2 (backtest y paper trading)

---

## Resumen ejecutivo

Sistema de seguimiento de tendencia diario sobre 15 activos (5 cripto + 10 blue chips USA), riesgo de 1% por operación, validación walk-forward antes de pasar a real. Este documento es la guía cerrada para la fase 2 del proyecto y se actualiza solo cuando una decisión cambia con justificación escrita.

---

## 1. Objetivos y restricciones

**Objetivo de fase 2:** validar que el sistema cumple Sharpe walk-forward ≥ 1.0 y Calmar ≥ 0.5 antes de plantear ejecución con capital real.

**Capital de referencia:** 1.000€. La estrategia escala linealmente con el capital, así que los porcentajes son lo importante, no las cifras absolutas.

**Restricciones operativas firmes:**
- Solo spot, sin apalancamiento, sin derivados, sin posiciones cortas.
- Sin VPS. Decisiones al cierre del día, ejecución manual al apertura siguiente.
- Una decisión al día por activo.
- Operativa compatible con residencia fiscal en España.

---

## 2. Universo de activos

15 activos en total: 5 cripto + 10 blue chips USA. Universo cerrado, sin cambios durante la fase de validación salvo pérdida de cotización o quiebra del activo.

### Cripto (5 activos)

| Ticker | Nombre | Histórico fiable desde |
|--------|--------|------------------------|
| BTC | Bitcoin | 2014 |
| ETH | Ethereum | 2016 |
| SOL | Solana | 2020 |
| XRP | Ripple | 2014 |
| ADA | Cardano | 2018 |

### Blue chips USA (10 activos)

| Ticker | Nombre | Sector |
|--------|--------|--------|
| AAPL | Apple | Tecnología |
| MSFT | Microsoft | Tecnología |
| GOOGL | Alphabet | Tecnología |
| NVDA | Nvidia | Tecnología |
| META | Meta Platforms | Tecnología |
| JPM | JPMorgan Chase | Financiero |
| V | Visa | Pagos |
| JNJ | Johnson & Johnson | Salud |
| UNH | UnitedHealth | Salud |
| PG | Procter & Gamble | Consumo defensivo |

### Fuentes de datos

- Cripto: Binance, datos diarios al cierre UTC.
- Acciones: Yahoo Finance, ajustado por splits y dividendos.
- Periodo mínimo de backtest: 2018-01-01 hasta fecha actual.

---

## 3. Reglas de riesgo

### Riesgo por operación

1% del capital total en el momento de la entrada. Con 1.000€, eso equivale a 10€ máximos perdidos por trade si salta el stop.

Esta cifra se revisará tras la validación walk-forward y los primeros 3 meses de paper trading.

### Drawdown máximo

20% sobre capital total. Si se rompe en backtest, la estrategia no pasa a paper. Si se rompe en paper o real, se detiene la operativa hasta revisión completa de hipótesis.

### Posiciones simultáneas

Máximo 5 posiciones abiertas a la vez. Si hay más señales válidas que cupo libre, priorizamos las de mayor fuerza relativa (rendimiento de los últimos 90 días).

Dentro del bloque cripto la correlación es alta, así que limitamos a 3 posiciones cripto abiertas simultáneamente. El resto del cupo se reserva a blue chips.

### Stop loss

- Cripto: 2x ATR(20) por debajo del precio de entrada.
- Blue chips: 1.5x ATR(20) por debajo del precio de entrada.

El stop solo se mueve a favor (trailing tipo Turtle). Nunca se relaja.

### Costes modelados en backtest

- Cripto: 0.10% ida + 0.10% vuelta (Binance spot estándar).
- Acciones: 0.05% ida + 0.05% vuelta (referencia IBKR / DEGIRO).
- Slippage adicional: 0.05% por trade en cripto, 0.02% en acciones.

---

## 4. Estrategia v1: Donchian Breakout (Turtle modificado)

### Tipo

Trend following por ruptura, sistema mecánico sin discrecionalidad.

### Señal de entrada (long)

Se abre posición larga cuando se cumplen las dos condiciones siguientes en el cierre del día:

1. El precio de cierre rompe el máximo de los últimos **55 días**.
2. El precio está por encima de su **SMA(200)**.

El segundo filtro evita rupturas dentro de mercados bajistas estructurales y reduce drásticamente el número de falsas señales.

### Señal de salida

Se cierra la posición cuando ocurre cualquiera de estas dos cosas:

1. El precio cierra por debajo del mínimo de los últimos **20 días**.
2. Salta el stop loss inicial (2x ATR cripto, 1.5x ATR acciones).

### Position sizing

Cantidad de unidades a comprar:

```
unidades = (capital_total × 0.01) / (precio_entrada − stop_inicial)
```

El resultado se redondea a la baja según la unidad mínima del activo.

**Ejemplo numérico con BTC:**

- Capital total: 1.000€
- Precio entrada: 60.000€
- ATR(20): 1.500€
- Stop inicial: 60.000 − (2 × 1.500) = 57.000€
- Riesgo por unidad: 3.000€
- Cantidad: (1.000 × 0.01) / 3.000 = 0.0033 BTC
- Exposición resultante: ≈ 200€ (20% del capital, riesgo controlado en 10€)

### Cadencia operativa

- Cierre del día (UTC en cripto, 22:00 CET en acciones USA): cálculo de señales.
- Apertura del día siguiente: ejecución de órdenes pendientes.
- Una sola revisión por sesión y por activo.

---

## 5. Métricas de aceptación

### Para pasar de backtest a paper trading

- Sharpe ratio walk-forward (out-of-sample): ≥ 1.0
- Calmar ratio: ≥ 0.5
- Max drawdown: ≤ 20%
- Profit factor: ≥ 1.5
- Mínimo 50 trades en el periodo de validación
- Sin concentración extrema: ningún año aporta más del 50% del retorno total

### Para pasar de paper trading a real

- Mínimo 3 meses de paper trading continuo.
- Métricas vivas dentro de un margen del 30% respecto al backtest.
- Sin errores operativos significativos (saltos de orden, mal cálculo de tamaño, etc.).

---

## 6. Criterios de descarte

La estrategia se descarta o se replantea si se cumple alguna de estas condiciones:

- Retornos concentrados en un único régimen (por ejemplo, solo funciona en cripto 2020-2021).
- Alta sensibilidad a parámetros: cambiar el periodo Donchian de 55 a 50 días destruye los resultados.
- Max drawdown supera el 25% en cualquier ventana.
- Menos de 30 trades totales en 5 años (sin material estadístico).
- Sharpe in-sample muy superior al out-of-sample (ej. 1.8 vs 0.3): señal clara de overfitting.

---

## 7. Esquema de validación walk-forward

### Datos

Histórico desde 2018-01-01 hasta fecha actual para los 15 activos.

### Particiones

- Train inicial: 2018-2022 (5 años).
- Test rolling: 2023, 2024, 2025, 2026 cada año como bloque fuera de muestra.
- Re-optimización de parámetros al final de cada año de test.

### Parámetros optimizables

- Periodo Donchian de entrada: rango 30-90 días.
- Periodo Donchian de salida: rango 10-30 días.
- Multiplicador de ATR para stop: rango 1-3.

### Parámetros fijos (no optimizables)

- Filtro SMA(200) para entradas.
- Riesgo por trade del 1%.
- Universo cerrado.

Mantener estos parámetros fuera del proceso de optimización evita curve fitting trivial.

---

## 8. Próximos pasos

1. Implementar el motor de backtest en Python con estas reglas. Librerías candidatas: vectorbt (rápido, pythónico) o backtrader (más completo, más lento).
2. Recopilar histórico limpio de los 15 activos desde 2018 (Binance API + Yahoo Finance).
3. Correr backtest in-sample 2018-2022 y revisar comportamiento cualitativo (curva de equity, distribución de trades, drawdowns).
4. Ejecutar walk-forward 2023-2026 con re-optimización anual.
5. Si pasa las métricas de aceptación: traducir las reglas a Pine Script para TradingView paper trading (Caja 3 del plan).
6. Si no pasa: documentar en este mismo archivo bajo "Iteración 2" qué parámetro o componente cambia y por qué, y volver al paso 3.

---

## Registro de cambios

| Versión | Fecha | Cambio |
|---------|-------|--------|
| 1.0 | 2026-04-29 | Versión inicial. Trend following diario, 1% riesgo, 15 activos. |
