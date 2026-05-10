# Guía de paper trading v1.5

Documento operativo para los próximos tres meses de paper trading con la estrategia v1.5 sobre 7 cripto, vía TradingView.

## Setup inicial (una sola vez)

**1. Crear lista de activos en TradingView.**

Abre TradingView y crea una watchlist nueva llamada "Vibe v1.5 paper" con estos 7 símbolos. Usa los pares de Binance porque son los más líquidos y los que cubre nuestro backtest:

- BINANCE:BTCUSDT
- BINANCE:ETHUSDT
- BINANCE:SOLUSDT
- BINANCE:XRPUSDT
- BINANCE:ADAUSDT
- BINANCE:BNBUSDT
- BINANCE:AVAXUSDT

**2. Cargar el script Pine en cada gráfico.**

Abre el primer gráfico (BTCUSDT). Timeframe: **1D** (diario). Sigue estos pasos:

- Pulsa el botón "Pine Editor" abajo en la pantalla.
- Abre el archivo `mi_sistema/pine/v15_donchian.pine` en tu PC, copia todo el contenido y pégalo en el editor de TradingView reemplazando lo que haya.
- Pulsa "Guardar" arriba a la derecha del editor. Le das nombre "v1.5 Donchian".
- Pulsa "Añadir al gráfico".

Ya tienes el script funcionando en BTCUSDT. Para los otros 6 cripto, no hace falta repetir el copy-paste: vas al gráfico, abres el menú de indicadores (icono fx), pestaña "Mis scripts", y pulsas en "v1.5 Donchian" para añadirlo.

**3. Configurar la alerta única.**

Como tienes Free, solo puedes tener una alerta activa. La que más te interesa es **entradas** porque las salidas las verás visualmente cuando revises los gráficos a diario.

- Sobre el gráfico de BTCUSDT con el script aplicado, pulsa el icono del reloj con campana (Alerta).
- Condición: tu script "v1.5 Donchian" → "Entrada Long".
- Frecuencia: "Una vez por barra cierre".
- Notificaciones: pop-up + email opcional.
- Nombre: "v1.5 ENTRY signals".

Esa alerta dispara cuando cualquier vela diaria de BTC cierra por encima del Donchian55 y del SMA200. **Para los otros 6 cripto no hay alerta**, los revisas manualmente al cierre UTC.

## Rutina diaria de revisión

**Hora de revisión: 02:00 hora España en verano (00:00 UTC).**

En verano España va UTC+2, así que 00:00 UTC = 02:00 CEST. En invierno UTC+1, así que 00:00 UTC = 01:00 CET. Como es de madrugada, alternativa: revisar al levantarte (08:00-09:00) y procesar las señales del día anterior. No es ideal pero funcional.

**Si revisas a la hora exacta del cierre UTC**: las señales son en tiempo real, ejecutas a precio de mercado en TradingView paper.

**Si revisas por la mañana siguiente**: la vela del día anterior ya cerró. La señal está confirmada. Tu "ejecución" la registras al precio de cierre de ayer (no al precio actual del live), porque eso es lo que el sistema decidió ese día.

**Pasos de la revisión** (5-10 minutos):

1. Abre la watchlist "Vibe v1.5 paper".
2. Recorre los 7 gráficos uno por uno. Mira el panel superior derecho de cada uno:
   - **Estado FUERA**: nada que hacer en ese activo. Continúa.
   - **Estado EN POSICIÓN**: revisa si en la última vela aparece flecha de salida (roja STOP o naranja D20). Si sí, registra la salida en `paper_log.csv`. Si no, mantén la posición.
   - **Si en la última vela aparece flecha verde de ENTRADA**: anota la entrada en `paper_log.csv` con el precio de cierre, el stop y el peso que muestra el panel.
3. Cuando hayas terminado los 7, ya estás. Hasta mañana.

**No tomes decisiones discrecionales.** El sistema dice qué hacer. Si una entrada te parece mala intuitivamente, da igual, anótala y opérala. Si una salida te parece prematura, da igual, ciérrala. Esa disciplina es exactamente lo que se está midiendo en paper.

## Cómo registrar trades en paper_log.csv

El CSV está en `mi_sistema/paper_log.csv`. Una fila por trade completo (cuando se cierra). Los campos:

- `fecha_entrada`: fecha del cierre cuando saltó la entrada (formato YYYY-MM-DD).
- `activo`: ticker (BTC, ETH, etc.).
- `precio_entrada`: precio de cierre en la vela de entrada.
- `stop_inicial`: precio del stop calculado en la entrada (lo muestra el panel).
- `peso_porcentaje`: el porcentaje que muestra el panel al entrar (ej. 18.5).
- `fecha_salida`: fecha del cierre cuando saltó la salida.
- `precio_salida`: precio de salida (cierre del día para Donchian, stop ATR para STOP).
- `motivo_salida`: "stop" o "donchian".
- `pnl_eur`: cálculo manual sobre 1.000 € de capital de referencia. Fórmula: `(precio_salida / precio_entrada - 1) * peso_porcentaje * 1000 / 100`. Restar comisiones del 0.2 % total (entrada + salida) sobre el peso.
- `notas`: opcional, lo que quieras observar (volatilidad rara, slippage estimado, gap nocturno, etc.).

Ejemplo: entras BTC a 65.000$ con stop a 61.700 (5 % distancia) y peso 20 %. Sales por Donchian a 70.000$. PnL = (70000/65000 - 1) * 0.20 * 1000 - (1000 * 0.20 * 0.002) = 15.38 - 0.40 = 14.98 €.

## Reglas operativas estrictas

**No improvisar.** El sistema dice "compra" o "vende", tú obedeces. Si no obedeces, anota en notas el porqué para luego ver el coste de las desviaciones.

**Una posición por activo máximo.** Si BTC ya está en posición y vuelve a romper Donchian55, no se entra otra vez. Esperas a salir primero.

**Máximo 5 posiciones simultáneas.** Si los 7 cripto disparan entrada el mismo día (improbable pero posible), priorizas las 5 con mejor "fuerza relativa" (rendimiento de los últimos 90 días). El panel del gráfico no calcula esto automáticamente, lo miras a ojo en el gráfico.

**Si te pierdes una sesión de revisión.** Al volver, primero revisas los gráficos como siempre. Cualquier entrada o salida que ya pasó hace dos días, la registras a la fecha y precio reales del backtest (no al precio actual). Anotas en `notas` que la entrada/salida fue retroactiva.

**Si TradingView se cae o tiene un bug visual** (raro): vuelve al backtest engine local y verifica con `run_backtest.ps1` sobre los datos hasta ayer. Las señales tienen que coincidir.

## Métricas de seguimiento del paper

Cada domingo, calcula sobre `paper_log.csv` acumulado:

- Trades cerrados (debería ir creciendo poco a poco, 1-3 por semana).
- Win rate (objetivo a 3 meses: 50-60 %, igual que el backtest).
- PnL acumulado en € sobre 1.000 € de referencia.
- Drawdown máximo desde el inicio.

Te montaré un script de PowerShell que calcule esto automáticamente desde `paper_log.csv` cuando lleves el primer mes de datos.

## Criterios de validación a 3 meses

Cuando hayas completado 3 meses de paper (mínimo 50 trades acumulados), comparas con el backtest walk-forward 2023-2026:

| Métrica | Walk-forward | Tolerancia | Si supera tolerancia |
|---|---|---|---|
| Sharpe estimado | 1.71 | -30 % a +30 % | Investigar |
| Win rate | 55 % | ±10 puntos | Investigar |
| Profit factor | 2.66 | -50 % a +50 % | Investigar |
| Max drawdown | 7.8 % | hasta 12 % | Aceptable |
| Max drawdown | -- | > 15 % | PARAR |

**Si pasas las cuatro primeras, luz verde para ir a real con capital pequeño** (300-500 €), manteniendo paper en paralelo durante otros 3 meses para tener una segunda muestra independiente.

**Si fallas en 2 o más, evaluamos** si el sistema necesita rediseño (v2 cripto), si el problema es de ejecución (te saltaste señales, calculaste mal sizing), o si fue mala suerte y damos otra ronda.

## Trampas mentales que evitar durante paper

**No hacer cherry-picking de señales que te gustan.** Todas o ninguna.

**No cambiar reglas a mitad de camino.** Si el Donchian saca una entrada que crees que es trampa, anótala y ejecútala.

**No mover el stop manualmente.** El stop se mueve con el script. Tú no.

**No mirar el resultado de cada trade emocionalmente.** En 274 trades del in-sample había muchísimas pérdidas pequeñas. Es el coste estructural del trend following. Lo que importa es la suma agregada.

**No dejar de actualizar el log.** Si un día no anotas, mañana habrás perdido contexto. 5 minutos al día.
