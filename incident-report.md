# Informe de incidentes — Terminal Rescue

<!--
Plantilla con el formato obligatorio. Llenen los cinco campos de cada incidente (1 a 10).
- Síntoma, Diagnóstico y Solución: al menos 3 palabras.
- Comandos: al menos un comando entre comillas invertidas, por ejemplo `docker compose ps`.
- Evidencia: ruta de un archivo de evidence/ que exista y no esté vacío, por ejemplo evidence/01-worker.txt.
- Entre todos los incidentes deben aparecer al menos 6 herramientas distintas:
  docker, psql, grep, awk, sed, sort, uniq, wc, find, chmod.
Revisen con: ./validator entregables
-->

## Incidente 1
- **Síntoma:** `docker compose ps` muestra `cierre-worker` en `Exited (1)` poco después de arrancar.
- **Diagnóstico:** el log del worker reporta el código CIE-1107: `WORKER_INTERVAL_SECONDS` debe ser un entero de segundos y recibió '30s'. El worker convierte el valor con `int()` y la `s` final lo rompe; el valor venía así desde `.env.example`.
- **Comandos:** `docker compose ps -a`, `docker compose logs cierre-worker | tail -5`, `grep WORKER_INTERVAL_SECONDS .env`
- **Solución:** se cambió `WORKER_INTERVAL_SECONDS=30s` por `WORKER_INTERVAL_SECONDS=30` en `.env.example` (y en `.env`), y se recreó el worker con `docker compose up -d --force-recreate cierre-worker`. Queda en `running` y sin reinicios.
- **Evidencia:** evidence/01-worker.txt

## Incidente 2
- **Síntoma:** la API responde 503 "base de datos no disponible" a cualquier consulta de afiliado.
- **Diagnóstico:** en el log de la API aparece CIE-2210: no se puede resolver el nombre `cierre-database`. Con `grep DATABASE_HOST .env` se ve que apunta a un host que no existe: el servicio de la base en `docker-compose.yml` se llama `cierre-db`. Entre contenedores se usa el nombre del servicio.
- **Comandos:** `grep DATABASE_HOST .env`, `docker compose logs cierre-api | grep CIE-2210`, `curl -s localhost:8081/afiliados/1098765432`
- **Solución:** se cambió `DATABASE_HOST=cierre-database` por `DATABASE_HOST=cierre-db` en `.env.example` (y en `.env`) y se recreó `cierre-api`. La misma variable usa el worker. La consulta de ejemplo ahora responde 200.
- **Evidencia:** evidence/02-api-conexion.txt

## Incidente 3
- **Síntoma:** `./run.sh` termina con error: el script de cierre no puede leer su archivo de entrada (`awk: cannot open "/opt/cierre/entrada/AFI_MAE.csv"`, código de salida 2).
- **Diagnóstico:** con `grep -n ENTRADA= scripts/cierre.sh` se ve que la entrada era la ruta fija `/opt/cierre/entrada`, que no existe en el servidor (`ls -ld` lo confirma); los CSV están en `data/`. Además el script usaba `mkdir` sin `-p` y fallaba en la segunda corrida, y movía el archivo de entrada con `mv`.
- **Comandos:** `grep -n ENTRADA= scripts/cierre.sh`, `ls -ld /opt/cierre/entrada`, `find scripts -name "*.sh" -exec ls -l {} +`, `chmod +x run.sh scripts/*.sh`, `bash scripts/cierre.sh`
- **Solución:** la entrada pasó a leerse de `data/` con rutas relativas al repositorio, se usa `mkdir -p` y ya no se mueve ningún archivo. Los scripts quedan con permiso de ejecución y `./run.sh` termina con código 0 y genera los cuatro archivos de `output/`.
- **Evidencia:** evidence/03-cierre-falla.txt

## Incidente 4
- **Síntoma:** los tres logs de `logs/` suman miles de líneas de error y no se sabe cuál es el problema más repetido.
- **Diagnóstico:** los errores usan códigos `CIE-####` (los avisos `W-###` no cuentan). Con `grep -o`, `sort` y `uniq -c` se cuenta cada código. Mirando solo `api.log` el más frecuente sería CIE-5003 (700), pero sumando los tres logs el más repetido es CIE-4012 con 1424 ocurrencias (356 en la API y 1068 en el worker).
- **Comandos:** `wc -l logs/*.log`, `cat logs/*.log | grep -o 'CIE-[0-9]*' | sort | uniq -c | sort -rn`, `find scripts -name 'top_error.sh'`, `chmod +x scripts/top_error.sh`, `awk '{print $2}'`
- **Solución:** se creó `scripts/top_error.sh`, que repite ese conteo sobre los tres logs y escribe `output/top_error.txt` con `codigo_error=CIE-4012` y `ocurrencias=1424`. El cierre (`run.sh`) lo invoca como último paso.
- **Evidencia:** evidence/04-top-error.txt

## Incidente 5
- **Síntoma:** Los archivos de entrada presentaban datos sucios con documentos duplicados, códigos de estado inválidos, afiliados sin empresa aportante y beneficiarios huérfanos.
- **Diagnóstico:** Al inspeccionar AFI_MAE.csv y AFI_BEN.csv, se encontraron 20 documentos repetidos, 14 con estados diferentes a A/I, 18 afiliados sin empresa válida y 15 beneficiarios sin afiliado en el maestro.
- **Comandos:** `awk -F',' '{print $2}' output/excepciones.csv | sort | uniq -c`
- **Solución:** Se implementó la lógica en scripts/cierre.py para conservar la primera aparición de duplicados, descartar estados inválidos y empresas inexistentes, reportando cada caso con su respectivo tipo en output/excepciones.csv.
- **Evidencia:** evidence/05-excepciones.txt

## Incidente 6
- **Síntoma:** `GET /afiliados/8871612039` responde 500 "error interno" para afiliados sin segundo nombre.
- **Diagnóstico:** el traceback del log de la API muestra `TypeError: can only concatenate str (not "NoneType")` en `find_member`. Con `psql` se comprobó que `nom2` es NULL para ese documento: `\copy` de un CSV carga el campo vacío como NULL y `nom1 + " " + nom2` no se puede hacer con None. Además el `JOIN` con empresa descartaba afiliados sin empresa y `ESTADOS[est_afi]` fallaría con un estado raro.
- **Comandos:** `docker compose exec cierre-db psql -U cierre -d cierre -tc "select nom2 is null from afi_mae where nro_doc='8871612039'"`, `docker compose logs cierre-api | grep -A12 CIE-5003`, `awk -F, 'NR>1 && $4=="" {print $1; exit}' data/AFI_MAE.csv`
- **Solución:** en `services/api/app.py` el nombre se arma con `" ".join(...)` omitiendo los campos vacíos, el `JOIN` pasó a `LEFT JOIN` y el estado usa `ESTADOS.get(...)`. Ahora el documento responde 200, los existentes siguen igual y uno inexistente da 404.
- **Evidencia:** evidence/06-consulta-500.txt

## Incidente 7
- **Síntoma:** Fechas de afiliación en formatos no estándar (DD/MM/YYYY, YYYYMMDD) y valores con fechas no válidas (2023/02/29, 2025-02-30, SIN FECHA, N/A) que rompen la consistencia del cierre.
- **Diagnóstico:** Existen registros en AFI_MAE.csv con fechas en múltiples formatos y 12 registros con fechas inexistentes o corruptas que deben reportarse sin excluir al afiliado de los totales.
- **Comandos:** `grep "FECHA_INVALIDA" output/excepciones.csv | wc -l`
- **Solución:** Implementación de función normalizar_fecha en scripts/cierre.py que acepta YYYY-MM-DD, DD/MM/YYYY y YYYYMMDD, valida años bisiestos y fechas reales, convierte las válidas a formato ISO y registra las 12 fechas inválidas en output/excepciones.csv sin descartar al afiliado.
- **Evidencia:** evidence/07-fechas.txt

## Incidente 8
- **Síntoma:** El extracto recibido de Caja Oriente no coincidía en formato, presentaba delimitador punto y coma, ceros a la izquierda y estados discordantes con el maestro local.
- **Diagnóstico:** Al cruzar extracto_caja_oriente.csv contra el maestro de afiliados eliminando los ceros del documento, se identificaron 25 discrepancias entre afiliados no encontrados o con situaciones opuestas (VIGENTE vs RETIRADO).
- **Comandos:** `sed -n '1,10p' data/extracto_caja_oriente.csv | grep ";"`
- **Solución:** Se implementó la comparación en scripts/cierre.py normalizando los documentos con lstrip('0') y mapeando situaciones (VIGENTE=A, RETIRADO=I), registrando las 25 diferencias como CRUCE_NO_COINCIDE en output/excepciones.csv sin alterar el formato de afiliados_activos.csv.
- **Evidencia:** evidence/08-cruce.txt

## Incidente 9
- **Síntoma:** Los totales de afiliados activos e inactivos no cuadraban con los valores exigidos por Operaciones en la hoja de control.
- **Diagnóstico:** Faltaba calcular y reportar los afiliados inactivos válidos y el conteo total de excepciones de auditoría según las reglas del diccionario.
- **Comandos:** `diff -u <(sort control/hoja_control.csv) <(grep -E 'total_afiliados|activos|inactivos' output/totales.txt | tr '=' ',' | sort)`
- **Solución:** Se ajustó el cálculo en scripts/cierre.py para generar en output/totales.txt los valores exactos: 1500 afiliados totales, 1194 activos, 274 inactivos y 104 excepciones, cuadrando perfectamente con la hoja de control.
- **Evidencia:** evidence/09-totales.txt

## Incidente 10
- **Síntoma:** El proceso de cierre fallaba al ejecutarse por segunda vez o producía duplicados y datos corruptos acumulados.
- **Diagnóstico:** El script heredado usaba concatenación (>>) sobre los archivos de salida y creaba directorios sin flag -p, impidiendo que el proceso fuera idempotente y repetible.
- **Comandos:** `sha256sum output/*`
- **Solución:** Se reescribió scripts/cierre.sh con mkdir -p y scripts/cierre.py para sobreescribir desde cero los 4 archivos de salida (afiliados_activos.csv, excepciones.csv, totales.txt y top_error.txt), asegurando ejecuciones idénticas y consistentes vía run.sh.
- **Evidencia:** evidence/10-repetibilidad.txt
