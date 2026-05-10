# Guía de paper trading v2 ETFs

Sistema cross-sectional momentum top 3 sobre 7 ETFs. Frecuencia mensual.

## Setup inicial (una sola vez)

**Watchlist en TradingView**: añadir los 7 ETFs en una lista llamada "Vibe v2 ETFs paper":

```
AMEX:SPY    (referencia para regime filter, NO se opera)
NASDAQ:QQQ
AMEX:IWM
AMEX:EFA
AMEX:EEM
AMEX:GLD
NASDAQ:TLT
```

Confirma que el exchange a la derecha del símbolo es AMEX o NASDAQ (los pares correctos). Para SPY puede salir como NYSEARCA, también vale.

**Hoja de cálculo de rebalance**: usar `paper_log_v2_etfs.csv` como plantilla. Cada fila = un rebalance mensual.

## Capital asignado al sistema

500 € de los 1.000 € totales (50 % de la cartera teórica). Los otros 500 € van a v1.5 cripto, ya en marcha desde 2026-05-01.

## Rutina mensual de rebalanceo

**Día**: último día hábil de cada mes (29-31 según mes). En 2026 las fechas serán: 30 mayo, 30 junio, 31 julio, 31 agosto, 30 septiembre, 30 octubre, 30 noviembre, 31 diciembre.

**Hora**: tras el cierre de mercado USA (22:00 hora España en horario de verano CEST). Los datos del día estarán cerrados y las medias serán definitivas.

**Pasos**:

**1. Verificar régimen SPY**:
- Abrir gráfico SPY en TradingView, timeframe diario.
- Mirar si el cierre de hoy está por encima o por debajo de la SMA(200).
- Si **SPY < SMA(200)** → todo a cash. Anotar en log y terminar.
- Si **SPY > SMA(200)** → continuar al paso 2.

**2. Calcular momentum de los 6 ETFs tradeables**:

Para cada uno (QQQ, IWM, EFA, EEM, GLD, TLT):
- Apuntar precio de cierre hoy.
- Apuntar precio de cierre de hace 126 días bursátiles (~6 meses atrás). En TradingView basta con mover el cursor 126 velas hacia atrás.
- Calcular: `momentum_pct = (precio_hoy / precio_hace_126_dias - 1) * 100`.

Atajo en TradingView: añadir indicador "Rate of Change" con length=126 al gráfico, lee el valor actual.

**3. Filtrar y ranquear**:
- Eliminar ETFs con momentum negativo o cero.
- Ordenar los positivos de mayor a menor momentum.
- Tomar los **top 3**.

**4. Comparar con posiciones actuales**:
- Si los top 3 coinciden con tus posiciones actuales → mantener, no vender ni comprar.
- Si hay rotación (uno o más ETFs salen del top 3 y otros entran):
  - **Vender** los ETFs que ya no están en top 3.
  - **Comprar** los nuevos ETFs hasta llegar a 33 % cada uno.
- Si hay menos de 3 ETFs con momentum positivo (raro): solo posicionarse en los que cumplen, el resto cash.

**5. Pesos finales**: cada uno de los top 3 debe pesar ~33.3 % del capital v2 (~165 € sobre 500 €).

**6. Anotar en `paper_log_v2_etfs.csv`** con esta fila:

```
2026-05-30,ON,12.5,8.3,4.1,-2.0,15.7,3.2,"QQQ,GLD,TLT",rebalance,"QQQ=33%,GLD=33%,TLT=33%",Primer rebalance
```

Columnas:
- **fecha_rebalance**: fecha del último día hábil del mes.
- **spy_status**: ON (encima SMA 200) o OFF (debajo).
- **momentum_xxx**: rendimiento % de los últimos 126 días de cada ETF.
- **top3_seleccionados**: los 3 elegidos.
- **accion**: rebalance / hold / all_to_cash.
- **pesos_objetivo**: porcentajes finales.
- **notas**: cualquier observación.

## Regla intra-mes

Si **SPY rompe SMA(200) a la baja durante el mes**, vendes todo inmediatamente (no esperar al rebalance). Anota en el log con accion=`all_to_cash_intra_mes`.

Esta es la única excepción a la frecuencia mensual. El resto del tiempo NO miras nada, dejas correr.

## Cuánto tiempo te lleva al mes

10-15 minutos. Una vez que cojas el ritmo, 5 minutos.

## Capital simulado

Empiezas con 500 € de capital v2. Cada mes:
- Si rebalance: aplicas las nuevas posiciones (vender lo que sale, comprar lo que entra, ajustar pesos al 33 %).
- Apuntas el valor del portfolio total al cierre del último día del mes.
- Calculas drawdown desde el máximo histórico del portfolio.

Al final de cada mes, tienes una métrica clara: capital actual, retorno mensual, drawdown actual.

## Métricas que validar tras 3 meses

| Métrica | Walk-forward backtest | Aceptable en paper |
|---|---|---|
| Sharpe | 1.10 | ≥ 0.7 |
| Annual return | 11.1 % | ≥ 5 % |
| Max drawdown | 7.9 % | ≤ 12 % |
| Win rate | 76 % | ≥ 50 % |

Si tras 3 meses cumples estos umbrales → considera ir a real con capital pequeño.
Si no cumples → analizar si es deriva normal o problema estructural.

## Reglas estrictas

- **No saltarse el regime filter**. Si SPY < SMA(200), todo a cash, da igual lo bonito que pinte el gráfico de QQQ.
- **No anticipar rebalanceos**. Si a media de mes parece que el ranking va a cambiar, no rebalancees. Espera al último día.
- **No cambiar la lista de ETFs**. El universo es cerrado: 6 ETFs tradeables. No improvisar añadir nuevos.
- **No saltarse ningún mes**. Cada último día hábil, revisión obligatoria, aunque pienses "no va a haber cambios".
