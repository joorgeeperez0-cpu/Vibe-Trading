# Log de decisiones

Decisiones importantes en orden cronológico. Cada entrada: qué se decidió, por qué, qué se descartó.

## 2026-04-29 · Estrategia v1: Donchian breakout 55/20 con filtro SMA(200)

**Decidido**: trend following clásico tipo Turtle modificado, daily, 1 % riesgo por trade, 5 cripto + 10 blue chips USA.

**Por qué**: la estrategia más estudiada de la literatura, fácil de validar walk-forward, robusta a sobreajuste si se mantiene simple.

**Descartado**: mean reversion en blue chips, momentum cross-sectional, buy & hold rebalanceado.

## 2026-04-29 · Universo cerrado de 15 activos (después modificado)

**Decidido inicialmente**: 5 cripto (BTC, ETH, SOL, XRP, ADA) + 10 blue chips USA (AAPL, MSFT, GOOGL, NVDA, META, JPM, V, JNJ, UNH, PG).

**Modificado el 2026-04-30**: tras descubrir que las acciones eran lastre (-59 € en walk-forward) y que cripto cargaba el 87 % del PnL, se redujo el universo a 7 cripto. Detalles abajo.

## 2026-04-29 · Riesgo del 1 % por trade

**Decidido**: 1 % del capital por operación, con stop ATR adaptativo (2x cripto, 1.5x acciones).

**Por qué**: estándar de literatura, deja margen para 20 trades perdedores antes de tocar drawdown del 20 %.

**Descartado**: 0.5 % (demasiado conservador), 2 % (solo justificable post-validación walk-forward), Kelly fraction (prematuro).

## 2026-04-29 · Verificación obligatoria de outputs del agente Vibe-Trading

**Decidido**: para cualquier número del agente integrado, exigir el comando bash o python que lo generó y los archivos crudos correspondientes.

**Por qué**: el primer informe del agente tenía cifras por activo fabricadas. Las métricas globales del `metrics.csv` real sí eran fiables, pero las tablas por activo eran alucinaciones.

## 2026-04-29 · Bypass del agente para backtests deterministas

**Decidido**: ejecutar `python -m backtest.runner` directamente dentro del contenedor, sin pasar por el agente DeepSeek.

**Por qué**: el agente añade variabilidad innecesaria (interpretación de prompt, posible alucinación) cuando lo que queremos es ejecutar reglas exactas. El motor de backtest funciona perfecto en solitario.

**Cómo**: scripts en `mi_sistema/scripts/run_backtest.ps1` que copian config + signal_engine al contenedor y lanzan el runner.

## 2026-04-30 · Universo final v1.5: top 7 cripto, eliminadas las acciones

**Decidido**: BTC-USDT, ETH-USDT, SOL-USDT, XRP-USDT, ADA-USDT, BNB-USDT, AVAX-USDT.

**Por qué**: 
1. Las 10 acciones blue chip generaron solo 80 € de PnL en in-sample y -59 € en walk-forward. Eran lastre activo, no diversificación.
2. Probamos 4 universos cripto distintos. El de 7 (sumando BNB y AVAX a las 5 originales, eliminando DOT/LINK/DOGE marginales) dio Sharpe walk-forward 1.71 vs 1.45 de cripto-only y 1.39 de cripto-expandido (10).
3. AVAX fue la sorpresa: profit factor individual 5.34, mejor que BTC.

**Descartado**: 
- 15 activos mixto (Sharpe 0.88 walk-forward).
- 5 cripto only (Sharpe 1.45, retorno menor).
- 10 cripto expandido (Sharpe 1.39, drawdown mayor por DOT y LINK marginales).

## 2026-04-30 · Patch del loader cripto OKX→CCXT, ahora persistente

**Decidido**: modificar directamente `agent/backtest/runner.py` y `agent/backtest/loaders/registry.py` en el fork, e incluir los cambios en la imagen Docker reconstruida.

**Por qué**: el patch en runtime se perdía con cada `docker compose down + up`, requiriendo re-aplicar manualmente. Tras el rebuild, el patch queda baked-in y persiste.

**Trade-off**: divergencia con upstream HKUDS. Si en el futuro pulleamos cambios de upstream que toquen estos archivos, hay que resolver conflicto manteniendo nuestras líneas con "ccxt" en vez de "okx".

## 2026-04-30 · Test de sensibilidad SMA: confirmado SMA(200) robusto

**Decidido**: mantener SMA(200) como filtro de régimen.

**Por qué**: sweep con SMA = 100, 150, 200, 250 sobre el universo v1.5. Resultados:

| SMA | Sharpe IS | Sharpe WF | Degradación |
|---|---|---|---|
| 100 | 1.65 | 1.18 | -28.5 % |
| 150 | 1.75 | 1.35 | -22.9 % |
| 200 | 1.72 | 1.71 | **-0.6 %** |
| 250 | 1.55 | 1.32 | -14.8 % |

SMA(200) tuvo la menor degradación in-sample → walk-forward (-0.6 %), señal de un parámetro genuinamente robusto. SMA(150) tenía Sharpe IS marginalmente mejor (1.75) pero se desplomó a 1.35 en out-of-sample, indicando overfit al periodo de entrenamiento.

**Importancia metodológica**: el sweep no era para optimizar, era para **verificar robustez**. Si SMA(200) hubiera tenido degradación similar a las otras (~20 %), tendríamos que asumir suerte. La estabilidad demuestra que es una elección genuina.

## 2026-04-30 · Diferir el sweep de RISK_PER_TRADE hasta después del paper

**Decidido**: empezar paper trading con RISK_PER_TRADE = 1 % (lo validado). NO subir a 2 % o 3 % hasta acumular al menos 3 meses de paper.

**Por qué**: subir el sizing antes de validar en directo es saltarse un paso de aprendizaje crítico. Tres meses de paper con 1 % nos enseñan:
1. Si el sistema da los retornos esperados en datos reales.
2. Si emocionalmente aguantas un drawdown del 7-8 % sin desviarte.
3. Si estás listo para más exposición.

Si tras 3 meses de paper todo va bien, ENTONCES correremos sweep de RISK y consideraremos subir a 1.5 % o 2 %. Subir a 3 % casi seguro rompería el umbral de drawdown del 20 %.

## 2026-04-30 · Cowork tiene acceso directo al repo

**Decidido**: a partir de esta fecha, Cowork (Claude en modo agente local) edita archivos directamente en `C:\Users\user\Desktop\PROYECTOS\VIBE-TRADING\Vibe-Trading` sin pasar por scripts de deploy.

**Por qué**: el flujo anterior (outputs/ + deploy_to_repo.ps1) tenía un bug: el deploy borraba los resultados de backtests recién generados. Con acceso directo, Cowork edita y crea archivos en su sitio, sin overhead.

**Implicación**: el deploy script `desplegar_a_repo.ps1` queda obsoleto. Tampoco se usa más.

## 2026-05-05 · v2 ETFs elegido como segundo sistema, descartadas alternativas

**Decidido**: el bloque de "acciones/diversificación" de la cartera se opera con **v2 ETFs** (cross-sectional momentum top 3 con regime filter SPY sobre SPY/QQQ/IWM/EFA/EEM/GLD/TLT). Resto de universos probados rechazados.

**Por qué**: comparación walk-forward entre 4 universos con el mismo motor:

| Universo | WF Sharpe | WF MDD | WF Trades | Verdict |
|---|---|---|---|---|
| 10 blue chips top 3 | 0.96 | 18.0 % | 24 | IS falla, borderline |
| 10 stocks 12m skip-1 | 0.67 | 19.5 % | 14 | Peor que v2 base |
| 30 Nasdaq top 3 | 0.36 | 25.1 % | 36 | Peor en todas dimensiones |
| **7 ETFs top 3** | **1.10** | **7.9 %** | 21 | **Ganador, pasa criterios** |

ETFs gana por:
1. Diversificación entre clases de activos (equity USA, internacional, oro, bonos).
2. GLD y TLT actúan como hedges naturales: cuando equity cae, suelen subir, y el sistema rota a ellos.
3. Sin sesgo de supervivencia (a diferencia de Nasdaq 30).
4. Sin concentración tech excesiva (que era el problema de las versiones con stocks).

**Descartado**:
- 10 blue chips top 3 (v2 original): IS Sharpe 0.60 falla criterios. WF mejor pero borderline.
- 10 stocks con momentum 12m skip-1: la iteración no mejoró nada, empeoró WF. Hipótesis de literatura no aplicó al universo pequeño.
- 30 stocks Nasdaq: más tickers no compensa, sigue tech-concentrado, además sesgo de supervivencia.

**Trade-off conocido y aceptado**: v2 ETFs WF rinde 11.1 % anual vs SPY 73 % en walk-forward. Captura solo ~56 % de la subida de SPY. PERO con drawdown 7.9 % vs ~25 % de SPY en correcciones. Para el rol de estabilizador descorrelacionado a v1.5 cripto, ese trade-off es deseable.

## 2026-05-05 · No optimizar trade frequency

**Decidido**: aceptar v2 ETFs con ~6 trades/año (rebalanceo mensual). NO sustituir por sistemas de mayor frecuencia que dieron peores métricas.

**Por qué**: se planteó si "más trades = más ganancia con capital pequeño". Los datos del sweep desmontan esta intuición:
- Nasdaq 30 hizo 71 % más trades que ETFs y rindió ~la mitad.
- Comisiones del 0.2 % round-trip se acumulan: 21 trades/año = 0.4 % anual de drag, 100 trades/año = 2 % de drag.

Lo que maximiza retorno con capital pequeño es **Sharpe ratio**, no frequency.

## 2026-05-05 · v3 4h cripto descartado tras backtest

**Decidido**: NO operar Donchian breakout sobre cripto en timeframe 4h. La cartera definitiva queda en v1.5 (daily cripto) + v2 ETFs (mensual).

**Por qué**: backtest in-sample y walk-forward de v3 4h sobre los 7 cripto de v1.5:

| Métrica | v3 4h IS | v3 4h WF | v1.5 daily WF (referencia) |
|---|---|---|---|
| Sharpe | 1.17 | 0.55 | 1.71 |
| Calmar | 1.21 | 0.42 | 2.26 |
| Max DD | 20.5 % | 23.6 % | 7.8 % |
| Profit factor | 1.40 | 1.20 | 2.66 |
| Trades | 772 | 593 | 92 |
| Annual return | 24.8 % | 9.9 % | 17.7 % |

**Walk-forward falla 4 de 5 criterios** (Sharpe, Calmar, MDD, PF). Solo pasa "trades ≥ 50".

**Estabilidad muy mala**: degradación IS → WF de Sharpe del -53 %. Para comparar, v1.5 tuvo -0.6 %.

**Causa raíz**: 593 trades en 3.3 años = ~180 trades/año = ~36 % de drag anual por comisiones (0.2 % round-trip). Las comisiones se comen casi todo el edge. El sistema bruto generaba ~46 % anual antes de costes y los costes se llevaron las dos terceras partes.

**Lección operativa documentada**: bajar el timeframe NO es palanca para ganar más con capital pequeño. Es lo contrario. Cualquier futura tentación de operar 1h, 15m o scalping debe enfrentarse a estos números.

**Implicación**: v3 4h queda en el repo (signal_engine, configs, results) como evidencia documentada de un experimento fallido, no como sistema operativo.

## 2026-09-13 · Corrección de bugs en checks diarios y reconstrucción de paper_log.csv

**Contexto**: se detectó que `paper_log.csv` (v1.5 cripto) tenía histórico corrupto. Causas en `check_v15_cripto.py` (versión original en `check_v15_cripto.py.bak`):
1. **Lag de fecha**: `end` de yfinance es exclusivo; la fila etiquetada con hoy llevaba datos del día anterior.
2. **Velas repetidas**: yfinance a veces devolvía la misma vela varias veces.
3. **Días sin ejecución**: si la tarea no corría, las entradas/salidas de esos días nunca se registraban.
4. **Sin persistencia ni backfill**: cada ejecución re-simulaba todo y solo escribía la fila de hoy.

**Decidido**:
- **Fase 1**: fila etiquetada con la fecha real de la última vela, `end = hoy + 2`, aviso si la última vela tiene ≥ 2 días, backfill de fechas huérfanas. Aplicado también a `check_v2_etfs.py` (fecha real de vela + aviso).
- **Fase 2**: al revisar la Fase 1 antes de reconstruir se vio que (a) el bug 2 no tenía corrección real, solo un comentario, y (b) `end = hoy + 2` metía la **vela UTC del día en curso, incompleta**, que quedaría congelada en un log append-only. Se añadió deduplicación del índice y descarte de la vela UTC en curso. Con eso se reconstruyó `paper_log.csv` desde 2026-05-01: 135 filas. El log corrupto se guarda como `paper_log_corrupto_2026-09-13.csv.bak`.
- **Fase 3**: estado persistente `mi_sistema/positions_state.json` (entry_date, entry_price, stop_price, weight por ticker + última vela procesada). La simulación se reanuda desde el estado; los indicadores se siguen calculando sobre el histórico completo descargado, así que el resultado es idéntico al de simular desde 2026-05-01. Al arrancar se comprueba el entry_price guardado contra el close actual de la vela de entrada (aviso si > 1 %). `--rebuild-state` fuerza la simulación completa.
- **Validación cruzada semanal**: los domingos, `check_v15_cripto.py` lanza `data_quality_check.py`, que compara el cierre yfinance vs FMP de BTC, ETH y SPY. Si difiere > 0.5 %, escribe un WARNING en `mi_sistema/scripts/data_quality_log.txt`. Usa la API REST de FMP con `FMP_API_KEY` en variable de entorno (el conector FMP de Claude no está disponible para la tarea programada). Sin clave, registra SKIP y no bloquea las señales.

**Validación de la reconstrucción contra FMP** (velas de señal, OHLC): divergencia máxima 0.77 % (ADA, low-priced), resto < 0.6 %. Ninguna > 1 %. Los precios del log son fiables.

**Punto abierto (no se ha cambiado nada, requiere decisión)**: el trailing stop se sube con el **close** de la vela y se compara con el **low** de esa misma vela. Como el low suele ocurrir antes que el close, se producen "salidas" a un precio de stop que puede ser superior al close del día (BTC 2026-08-20: stop 70 094, close 73 033, low 68 868). Pasa en 8 de las 9 salidas reconstruidas. `signal_engine_v1.py` y `pine/v15_donchian.pine` hacen lo mismo, así que el backtest validado (Sharpe WF 1.71) incluye este sesgo. Opción a evaluar: comparar el low contra el stop de la vela anterior y actualizar el trailing después. Si se cambia, sería un motor nuevo (`signal_engine_v15_trailfix.py` + Pine) con backtest IS/WF y gates antes de promocionar.

**Por qué no se tocó**: la convención del proyecto exige versionar por archivo y pasar gates antes de cambiar la lógica en paper.

## 2026-09-13 · Backtest de signal_engine_v1_stopfix (trailing stop sin mismo día)

**Qué se probó**: `mi_sistema/signal_engine_v1_stopfix.py` (+ `pine/v15_stopfix.pine`). Único cambio respecto a v1: en la vela X se evalúa `low_X <= stop` con el stop que quedó al cierre de X-1; solo si no hay salida se sube el trailing con `close_X - 2·ATR_X` para X+1. Parámetros idénticos (55/20/200/20/2.0/1 %).

**Metodología**:
- Docker no estaba arrancado y CCXT-Binance está bloqueado desde España, así que se creó `mi_sistema/scripts/run_backtest_local.py`: ejecuta el **mismo** `CryptoEngine` de `agent/backtest` (sin modificarlo) sobre los **OHLCV archivados** de `results/v15_cripto_top7_{in_sample,walkforward}`, con las mismas configs `v15_cripto_top7_*.json`.
- Validación del harness: la reproducción de v1 da métricas idénticas al decimal y `trades.csv`, `equity.csv` y `positions.csv` idénticos línea a línea (IS y WF).
- WF = ejecución separada 2023-01-01 → 2026-04-29, sin reoptimización (igual que el WF original).

**Números crudos** (`results/v1_stopfix/comparison.md`):

| Métrica | v1 IS | v1 WF | stopfix IS | stopfix WF |
|---|---|---|---|---|
| Sharpe | 1.7246 | 1.7111 | 1.6588 | 1.7450 |
| Calmar | 2.5106 | 2.2623 | 2.4906 | 2.7740 |
| Max DD | 7.19 % | 7.80 % | 10.23 % | 8.23 % |
| Profit factor | 3.1607 | 2.6620 | 5.0130 | 3.3790 |
| Trades | 120 | 92 | 95 | 74 |
| Retorno anual | 18.05 % | 17.65 % | 25.48 % | 22.83 % |
| Win rate | 57.5 % | 55.4 % | 61.1 % | 52.7 % |
| Ganancia/pérdida media | 2.34 | 2.14 | 3.20 | 3.03 |
| Días medios en posición | 7.8 | 7.1 | 10.8 | 9.9 |

WF año a año (retorno / Sharpe): 2023 v1 35.1 % / 3.00 vs sf 35.8 % / 2.67 · 2024 v1 20.6 % / 1.52 vs sf 41.9 % / 2.13 · 2025 v1 6.9 % / 0.99 vs sf 4.2 % / 0.56 · 2026 (hasta 29-abr) idénticos, −1.3 %.

**Gates**: stopfix pasa 4/4 en IS y en WF. En WF es ≥ v1 en Sharpe, Calmar y PF; peor en MDD (+0.43 pp). Regla automática → **candidato a sustitución**.

**Interpretación (diagnóstico `results/v1_stopfix/v1_exit_types_*.csv`)**: de las salidas de v1, 40/120 (IS) y 30/92 (WF) son "stop fantasma" (solo saltan porque el stop se subió con el close del mismo día). El 100 % de ellas fueron ganadoras (+26.6 % IS, +21.1 % WF de media) y ocurrieron en días alcistas. En el backtest el engine ejecuta en la apertura siguiente, así que v1 no tenía lookahead de precio: el sesgo **no inflaba** el Sharpe 1.71. Lo que hacía la regla era cerrar tendencias ganadoras en días de mucho rango intradía (una toma de beneficios involuntaria). stopfix las mantiene: más retorno y PF, algo más de drawdown, Sharpe equivalente. El Sharpe 1.71 original sigue siendo creíble como medida de la estrategia; la regla del stop era distinta a la documentada, no fraudulenta.

**Limitaciones pendientes**:
1. Ningún motor modela el fill intradía del stop: el engine vende en la apertura del día siguiente. Afecta a ambos por igual, pero los números absolutos de las salidas por stop real no son exactos.
2. El engine ignora `commission: 0.001` de la config: aplica 0.05 % taker (apertura), 0.02 % maker (cierre), 0.05 % slippage y funding de perpetuo 0.01 %/8 h sobre longs. STRATEGY_V1.md documenta 0.10 % + 0.05 %. Igual para v1 y stopfix.
3. 2025 fue peor con stopfix (Sharpe 0.56 vs 0.99): la mejora se concentra en 2024.
4. `pine/v15_stopfix.pine` no se ha compilado en TradingView.

**Impacto en el paper 2026 (datos yfinance)**: stopfix habría registrado 7 trades en lugar de 10. BTC seguiría en posición desde 2026-08-19 (sin la salida del 08-20 y reentrada del 08-21), BNB sin el ciclo 08-19→08-20→08-21, ETH saldría el 08-23 (v1: 08-21) y SOL tendría un único trade 08-19→08-30.

**Decisión**: pendiente del usuario. v1 sigue siendo el motor operativo; no se ha tocado `signal_engine_v1.py`, `v15_donchian.pine`, `check_v15_cripto.py` ni configs.

## 2026-09-13 · Sustitución de v1 por v1_stopfix en operativa (aprobada por el usuario)

**Decidido**: el motor operativo de v1.5 cripto pasa a ser `signal_engine_v1_stopfix.py` / `pine/v15_stopfix.pine`. `signal_engine_v1.py` y `pine/v15_donchian.pine` quedan **deprecados** (docstring de aviso, sin cambios de lógica, se conservan por trazabilidad: reproducen los resultados archivados).

**Números que lo justifican** (backtest del mismo día, mismos OHLCV y engine):

| WF 2023-2026 | v1 | v1_stopfix |
|---|---|---|
| Sharpe | 1.71 | 1.75 |
| Calmar | 2.26 | 2.77 |
| Max DD | 7.8 % | 8.2 % |
| Profit factor | 2.66 | 3.38 |
| Trades | 92 | 74 |
| Retorno anual | 17.7 % | 22.8 % |

IS 2018-2022 stopfix: Sharpe 1.66, Calmar 2.49, MDD 10.2 %, PF 5.01. Pasa 4/4 gates en IS y WF. En rentabilidad ajustada por riesgo son equivalentes; el motivo de fondo es de **corrección**: stopfix implementa la regla escrita en STRATEGY_V1.md, es ejecutable con una orden stop real y elimina las salidas "fantasma" que el paper registraba a precios inalcanzables.

**Migración ejecutada**:
1. `check_v15_cripto.py`: en `_simulate` las salidas se evalúan con el stop del cierre anterior y el trailing se actualiza solo si no hay salida. Precio de salida por stop registrado como `min(stop, open)`. Se mantiene toda la infraestructura (fecha real de vela, descarte de vela UTC en curso, deduplicación, backfill, `positions_state.json`, validación FMP de los domingos). Backup: `check_v15_cripto.py.pre_stopfix.bak`.
2. Tests antes de tocar el log real: señales de `check_v15_cripto.py` idénticas a `signal_engine_v1_stopfix.py` día a día; reanudar desde estado == simular desde 2026-05-01; rebuild en seco correcto.
3. `paper_log.csv` reconstruido con `--rebuild-state`: 135 filas (2026-05-01 → 2026-09-12), sin duplicados ni huecos. Log de v1 en `paper_log_v1_2026-09-13.csv.bak`.

**Resultado del paper reconstruido** — 7 trades (6 cerrados + BTC abierto), igual que lo previsto en el reporte del backtest:

| Ticker | Entrada | Salida | Fill salida | Ret. (entrada FMP) |
|---|---|---|---|---|
| ETH | 2026-08-19 | 2026-08-23 stop | 2372.13 | +5.35 % |
| SOL | 2026-08-19 | 2026-08-30 stop | 100.86 | +18.18 % |
| XRP | 2026-08-21 | 2026-08-26 stop | 1.3959 | −4.00 % |
| ADA | 2026-08-21 | 2026-08-25 stop | 0.2079 | −9.23 % |
| BNB | 2026-08-19 | 2026-09-01 stop | 675.71 | +7.70 % |
| BNB | 2026-09-05 | 2026-09-10 stop | 718.26 | −6.33 % |
| BTC | 2026-08-19 | abierta (stop 75 958) | — | +11.49 % no realizado a 09-12 |

Hit ratio con precios FMP: 3/6 = 50 %. Todos los fills de salida caen dentro del rango low–high de la vela FMP (con v1, 8 de 9 salidas quedaban por encima del close). Divergencia máxima yfinance vs FMP: 0.77 % (ADA).

**Pendiente del usuario**: compilar `pine/v15_stopfix.pine` en TradingView y sustituir el script en los 7 gráficos (nota en `paper_trading_guia.md`).
