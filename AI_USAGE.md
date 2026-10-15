# Uso de inteligencia artificial

Usamos Claude Code (modelo Sonnet 5.5) y Antigravity (Gemini) como asistentes durante el reto. Todo lo que generaron se ejecutó y se revisó antes de subirlo: los dos integrantes pueden explicar el código entregado.

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

## Uso 4
- Herramienta: Antigravity (Gemini)
- Para qué se usó: Implementar la detección de datos sucios en AFI_MAE.csv (duplicados, estados inválidos, afiliados sin empresa y beneficiarios huérfanos) y escribirlos en excepciones.csv
- Prompt principal (resumido): "Agrega las reglas del diccionario al cierre: duplicados conservando primera aparición, CODIGO_INVALIDO si EST_AFI no es A/I, SIN_EMPRESA si el activo no tiene empresa válida y BENEFICIARIO_HUERFANO si NRO_DOC_AFI no existe en el maestro"
- Qué produjo: Código Python en scripts/cierre.py con las cuatro reglas en orden, generando excepciones.csv con 20 DUPLICADO, 14 CODIGO_INVALIDO, 18 SIN_EMPRESA y 15 BENEFICIARIO_HUERFANO
- Qué modificó o corrigió el equipo: La IA inicialmente ubicó la validación de huérfanos antes de construir el conjunto documentos_maestro, lo que causaba que nunca detectara ninguno; se reordenó para que el conjunto se construya después de aplicar duplicados y estados

## Uso 5
- Herramienta: Antigravity (Gemini)
- Para qué se usó: Implementar la normalización de fechas de FEC_AFI aceptando YYYY-MM-DD, DD/MM/YYYY y YYYYMMDD, validando fechas reales y reportando FECHA_INVALIDA sin excluir al afiliado
- Prompt principal (resumido): "Agrega la normalización de fechas al cierre. Formatos aceptados: YYYY-MM-DD, DD/MM/YYYY y YYYYMMDD. Convierte las válidas a ISO. Si es inválida como N/A o 2023/02/29 repórtala como FECHA_INVALIDA. FECHA_INVALIDA NO excluye al afiliado"
- Qué produjo: Función normalizar_fecha usando datetime.strptime que valida años bisiestos automáticamente y detectó exactamente los 12 registros inválidos esperados por el validador
- Qué modificó o corrigió el equipo: La IA inicialmente aplicaba la validación de fechas solo sobre los afiliados activos; se corrigió para que recorra todos los unicos sin importar estado, ya que FECHA_INVALIDA no descarta al afiliado de ningún cálculo

## Uso 6
- Herramienta: Antigravity (Gemini)
- Para qué se usó: Implementar el cruce con Caja Oriente, completar los campos empresa/beneficiarios/ultimo_aporte en afiliados_activos.csv, agregar inactivos y excepciones a totales.txt y hacer el cierre repetible
- Prompt principal (resumido): "Haz los incidentes 8, 9 y 10 de Persona B: cruce con extracto de Caja Oriente con separador punto y coma y ceros a la izquierda, cuadre de totales con 1500/1194/274 y repetibilidad del run.sh"
- Qué produjo: Lectura del extracto con delimiter=';', normalización de documentos con lstrip('0'), mapeo VIGENTE/RETIRADO a A/I, escritura de inactivos y excepciones en totales.txt, y corrección de mkdir -p en cierre.sh para idempotencia
- Qué modificó o corrigió el equipo: La IA propuso comparar directamente el string del id_afiliado sin quitar ceros, lo que hacía que ningún documento coincidiera con el maestro; se añadió lstrip('0') antes de la búsqueda para que la comparación funcionara correctamente
