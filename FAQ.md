Preguntas Frecuentes (FAQ) - Quiniela Pro

1) ¿Cómo empiezo?
- En “Jornada Actual” selecciona temporada, jornada y división, luego carga partidos.
- Calcula probabilidades con “Calcular Pronósticos”.
- En “Pronósticos” rellena automáticamente (dobles/triples) y guarda desde allí.
- Opcional: aplica condiciones y reducción en la pestaña “Reducción” y vuelve a guardar si ajustas.
- Finalmente, en “Análisis” carga tu quiniela guardada, carga resultados y compara.

2) ¿Qué es el modo freemium?
- Existen pagos para desbloquear pasos y quitar anuncios. En desarrollo, el modo DEV permite probar todo sin bloquear. En producción se aplicará el flujo freemium real.

3) ¿Dónde se guarda la quiniela para comparación?
- Los botones “💾 Guardar Quiniela” están en “Pronósticos” y “Reducción”. Guardan en JSON local y actualizan la vista simulada.
- En “Análisis” solo aparece “Cargar Quiniela Guardada” + botones para resultados y comparación.

4) ¿Puedo ver jornadas pasadas?
- Con la pestaña “Histórico” consultas cualquier temporada/jornada (requiere BBDD histórica). Sin BBDD, aparece un aviso premium.

5) ¿Qué es “Pleno al 15”?
- Es el partido 15 donde eliges total de goles por equipo (0/1/2/M). La app estima probabilidades con Poisson (versión ligera si SciPy no está disponible).

6) ¿Cómo se carga la BBDD histórica?
- Desde los recordatorios premium (botones “Obtener BBDD Histórica”). Es un pago único; tras activarla, histórico y análisis avanzado se desbloquean.

7) ¿Cómo guardo mi quiniela?
- En “Pronósticos” o “Reducción” pulsa “💾 Guardar Quiniela”. Siempre que edites, vuelve a guardar para mantener la simulación actualizada.

8) ¿Por qué las reducciones eliminan combinaciones?
- La reducción aplica filtros estadísticos (totales, consecutivos, parejas, tríos, interrupciones) y persigue cubrir aciertos objetivo minimizando apuestas.

9) ¿Hay APK para móvil?
- Sí. En la carpeta `app_android/` hay un esqueleto Kivy en modo mock. Consulta `ANDROID_APK.md` para compilar con Buildozer y probar en Android.

10) ¿Puedo usarlo sin conexión?
- Sí. La app funciona offline con SQLite; scraping/cuotas requieren conexión. La BBDD histórica se guarda localmente.

11) ¿Dónde reporto errores?
- Abre una incidencia en GitHub con logs, versión y pasos para reproducir.


