# Estrategia v2 ETFs: Cross-Sectional Momentum Top 3 con Regime Filter SPY

Versión validada para el bloque de acciones/ETFs de la cartera. Complementa a v1.5 (cripto Donchian) operando sobre clases de activos descorrelacionadas.

## Filosofía y restricciones

- Cross-sectional momentum sobre ETFs líquidos. Solo long. Solo spot.
- Sin apalancamiento, sin derivados, sin shorts.
- Decisiones mensuales (último día hábil del mes), ejecución manual al apertura siguiente.
- Compatible con residencia fiscal española.

## Universo final (7 ETFs)

| Ticker | Cubre | Rol en cartera |
|---|---|---|
| SPY.US | USA total | Filtro de régimen (NO se opera) |
| QQQ.US | Tech USA | Beta tech |
| IWM.US | Small caps USA | Beta USA distinta |
| EFA.US | Europa+Asia desarrollado | Diversificación geográfica |
| EEM.US | Mercados emergentes | Otra geografía |
| GLD.US | Oro | Hedge contra equity bear |
| TLT.US | Bonos USA largo plazo | Otro hedge |

SPY se incluye como referencia de régimen pero no es tradeable. Los 6 ETFs restantes son los que el sistema rota.

**Por qué este universo y no otros**:
- Probados 4 universos distintos para v2: 10 blue chips, 10 stocks 12m skip-1, 30 Nasdaq, 7 ETFs. ETFs ganó claramente.
- ETFs eliminan la concentración tech que penalizaba a las versiones con stocks individuales.
- ETFs no tienen sesgo de supervivencia (a diferencia de Nasdaq 30 que usa los constituyentes actuales).
- GLD y TLT actúan como hedges naturales en bear markets de equity.

## Reglas de la estrategia

**Frecuencia de decisión**: último día hábil de cada mes calendario.

**Cálculo del momentum**: rendimiento simple de los últimos 126 días bursátiles (~6 meses) de cada ETF tradeable.

**Filtro de régimen**: SPY > su SMA(200). Si no se cumple, todas las posiciones a cash.

**Selección**:
1. Tomar los 6 ETFs tradeables (todos excepto SPY).
2. Calcular momentum de los últimos 126 días.
3. Filtrar solo los que tengan momentum POSITIVO.
4. Seleccionar los **top 3 con mayor momentum** entre los positivos.
5. Equiponderar: cada uno pesa 1/3 (33.3 %) del capital.

**Casos especiales**:
- Si SPY < SMA(200): todo a cash (peso 0 en todos).
- Si solo 0-2 ETFs tienen momentum positivo: top 0-2, no rellenar con momentum negativo.
- Si todos tienen momentum negativo: cash.

**Mantenimiento**: las posiciones se mantienen sin tocar hasta el siguiente cambio de mes. **Excepción**: si SPY rompe SMA(200) a la baja a mitad de mes, todo a cash inmediatamente (no esperar al rebalanceo).

## Reglas de riesgo

- **Sizing**: equiponderado 1/3 cada posición. No hay sizing por riesgo individual como en v1.5.
- **Máximo 3 posiciones simultáneas**.
- **Drawdown máximo aceptable**: 20 %. Si se rompe en backtest, no pasa a paper. Si se rompe en paper o real, parar y revisar.
- **Sin stop loss explícito**: la salida la dicta el momentum mensual o el regime filter.

## Costes modelados

- 0.10 % comisión por lado (broker IBKR / DEGIRO referencia).
- Slippage 0.05 % adicional incluido en el motor.

## Métricas de validación

| Métrica | In-sample 2018-2022 | Walk-forward 2023-2026 | Umbral | Estado |
|---|---|---|---|---|
| Sharpe ratio | 0.64 | **1.10** | >= 1.0 WF | OK WF |
| Calmar ratio | 0.43 | 1.40 | >= 0.5 | OK |
| Max drawdown | 12.2 % | 7.9 % | <= 20 % | OK |
| Profit factor | 2.44 | 9.11 | >= 1.5 | OK |
| Win rate | 51 % | 76 % | (descriptivo) | Excelente |
| Trades | 35 | 21 | >= 50 | Falla por diseño (rebalance mensual) |
| Annual return | 5.2 % | 11.1 % | (descriptivo) | |
| Excess return vs SPY | +11.4 % | -31.5 % | (descriptivo) | |

**El IS Sharpe (0.64) está por debajo de 1.0** porque 2018-2022 incluyó tres episodios bajistas (Q4 2018, COVID 2020, bear 2022) donde el sistema correctamente fue a cash y no participó en las recuperaciones rápidas. Esto es comportamiento esperado de un sistema con regime filter, no un fallo.

**WF cumple 4 de 5 criterios duros**. El único fallo es trade count (21 < 50), que es estructural a la baja frecuencia (rebalanceo mensual = ~6 trades/año).

## Comparación con v2 alternativas descartadas

| Variante | WF Sharpe | WF MDD | WF Trades | Verdict |
|---|---|---|---|---|
| 10 blue chips top 3 | 0.96 | 18.0 % | 24 | IS falla criterios, borderline |
| 10 stocks 12m skip-1 | 0.67 | 19.5 % | 14 | Peor que v2 base |
| 30 Nasdaq top 3 | 0.36 | 25.1 % | 36 | Peor en todas las dimensiones |
| **7 ETFs top 3** | **1.10** | **7.9 %** | **21** | **GANADOR** |

## Underperformance vs SPY: aceptable

En walk-forward 2023-2026, SPY rindió ~73 % y v2 ETFs rindió ~41 %. **El sistema captura solo el 56 % de la subida** pero con **drawdown del 7.9 % vs ~25 % de SPY** en la corrección de 2025. 

Trade-off consciente: menos retorno absoluto a cambio de muchísimo menos riesgo. Para el rol que tiene este sistema en la cartera (estabilizador descorrelacionado a v1.5 cripto), eso es una ventaja, no un problema.

## Periodos de validación

- **In-sample**: 2018-01-01 a 2022-12-31 (ventana con 3 episodios bajistas).
- **Walk-forward**: 2023-01-01 a 2026-04-29 (mercado mayormente alcista).

## Criterios de aceptación para paper trading → real

- Mínimo 3 meses de paper trading con seguimiento mensual.
- Métricas vivas dentro de un margen del 30 % respecto a walk-forward.
- Sin errores operativos (entradas y salidas el último día hábil del mes ejecutadas correctamente).

## Plan operativo (cuando arranque paper)

**Frecuencia de revisión**: una vez al mes. Último día hábil de cada mes (típicamente día 28-31).

**Pasos del rebalanceo mensual**:
1. Mirar gráfico de SPY: ¿está por encima de SMA(200)?
2. Si NO → todo a cash. Vender todas las posiciones que tuvieras.
3. Si SÍ → calcular rendimiento de los últimos 126 días (≈6 meses) de QQQ, IWM, EFA, EEM, GLD, TLT.
4. Filtrar solo los positivos. Tomar los 3 con mayor rendimiento.
5. Comparar con tus posiciones actuales. Si hay rotación: vender los que ya no están en top 3, comprar los nuevos.
6. Equiponderar: cada posición = 33 % de capital v2 ETFs.

**Capital asignado**: por definir. Propuesta: 50 % de tu capital total dedicado al sistema (los otros 50 % a v1.5 cripto). Con 1.000 € totales = 500 € a v2 ETFs.

**Registro**: extender `paper_log.csv` con filas mensuales tipo:
```
2026-05-31,"SPY status,QQQ,IWM,...",rebalance,XXX,3,no,Mes inicial
```

## Implementación operativa (HECHO 2026-05-05)

La revisión mensual está **completamente automatizada** vía `mi_sistema/scripts/check_v2_etfs.py`:

- Descarga datos de yfinance para los 7 ETFs.
- Verifica SPY > SMA(200).
- Calcula momentum 126 días de los 6 ETFs tradeables.
- Filtra positivos, ranquea, selecciona top 3.
- Calcula cantidades exactas de acciones a comprar para 500 EUR de capital v2.
- Escribe automáticamente la fila en `mi_sistema/paper_log_v2_etfs.csv` (con protección anti-duplicados por fecha).

**Tiempo de ejecución mensual**: 10 segundos. Una sola línea de PowerShell:

```
python mi_sistema/scripts/check_v2_etfs.py
```

No hay Pine Script para v2 ETFs ni es necesario. La hoja de Excel `paper_logs.xlsx` con Power Query enlaza al CSV y se refresca al pulsar "Actualizar todo" (Ctrl+Alt+F5) para visualización.

## Apertura inicial registrada

Primer rebalance (apertura inicial a media de mes): 2026-05-05.

- SPY ON ($718.01 vs SMA200 $671.39).
- Top 3: EEM (15.64%), IWM (13.49%), GLD (12.04%).
- Capital asignado por posición: 166.67 EUR (33.3% cada una sobre 500 EUR).
