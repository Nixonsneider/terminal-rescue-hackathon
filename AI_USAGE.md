# Uso de inteligencia artificial

Usamos Claude Code (modelo Sonnet 5.5) como asistente durante el reto. Todo lo que generó se ejecutó y se revisó en el entorno Docker antes de subirlo: los dos integrantes pueden explicar el código entregado.

## Uso 1
- Herramienta: Claude Code (Claude Sonnet 5.5)
- Para qué se usó: analizar el kit del reto y evaluar el estado inicial: qué fallaba en el worker, la API, el script de cierre y los datos.
- Prompt principal (resumido): "analiza esto, es un reto de un hackathon" sobre el ZIP del kit.
- Qué produjo: una lista de las causas probables de cada incidente (intervalo '30s', host cierre-database, nombres NULL en la API, `mkdir` sin `-p`, `mv` del archivo de entrada) y una estimación de que el error más frecuente era CIE-4012 con 1424 ocurrencias.
- Qué modificó o corrigió el equipo: la IA solo había leído el código y no había ejecutado nada, así que reprodujimos cada falla en Docker y contamos los códigos de los logs con grep, sort y uniq antes de aceptar el diagnóstico.

## Uso 2
- Herramienta: Claude Code (Claude Sonnet 5.5)
- Para qué se usó: implementar la parte de infraestructura y API (incidentes 1, 2, 4 y 6) y generar la evidencia de cada incidente.
- Prompt principal (resumido): "haz la parte A, un commit por error corregido" en el repositorio clonado.
- Qué produjo: los cambios en `.env.example` y `services/api/app.py` (`LEFT JOIN`, nombre armado sin campos NULL, `ESTADOS.get`), el script `scripts/top_error.sh` y los archivos de `evidence/` con la salida real de Docker.
- Qué modificó o corrigió el equipo: pedimos que cada commit usara el formato "feat:" con una descripción corta y nuestra propia identidad de Git, y que el push se hiciera solo después de revisar los cambios y probarlos con Docker.

## Uso 3
- Herramienta: Claude Code (Claude Sonnet 5.5)
- Para qué se usó: evaluar el trabajo del compañero y hacer pruebas de punta a punta con `./reset.sh`, `./validator check` y `./validator entregables`.
- Prompt principal (resumido): "vuelve a probar todo y asegúrate que esté perfecto".
- Qué produjo: la confirmación de que los totales coinciden con la hoja de control y de que el cierre es repetible, y el hallazgo de 378 nombres con doble espacio en `afiliados_activos.csv` cuando NOM2 o APE2 venían vacíos.
- Qué modificó o corrigió el equipo: revisamos el hallazgo, aprobamos el arreglo en `nombre_completo` de `scripts/cierre.py` y repetimos las pruebas hasta obtener 625 de 625 puntos en el validador.
