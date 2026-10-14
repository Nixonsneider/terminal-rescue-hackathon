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
- **Síntoma:**
- **Diagnóstico:**
- **Comandos:**
- **Solución:**
- **Evidencia:**

## Incidente 4
- **Síntoma:** los tres logs de `logs/` suman miles de líneas de error y no se sabe cuál es el problema más repetido.
- **Diagnóstico:** los errores usan códigos `CIE-####` (los avisos `W-###` no cuentan). Con `grep -o`, `sort` y `uniq -c` se cuenta cada código. Mirando solo `api.log` el más frecuente sería CIE-5003 (700), pero sumando los tres logs el más repetido es CIE-4012 con 1424 ocurrencias (356 en la API y 1068 en el worker).
- **Comandos:** `wc -l logs/*.log`, `cat logs/*.log | grep -o 'CIE-[0-9]*' | sort | uniq -c | sort -rn`, `find scripts -name 'top_error.sh'`, `chmod +x scripts/top_error.sh`, `awk '{print $2}'`
- **Solución:** se creó `scripts/top_error.sh`, que repite ese conteo sobre los tres logs y escribe `output/top_error.txt` con `codigo_error=CIE-4012` y `ocurrencias=1424`. El cierre (`run.sh`) lo invoca como último paso.
- **Evidencia:** evidence/04-top-error.txt

## Incidente 5
- **Síntoma:**
- **Diagnóstico:**
- **Comandos:**
- **Solución:**
- **Evidencia:**

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
- **Síntoma:**
- **Diagnóstico:**
- **Comandos:**
- **Solución:**
- **Evidencia:**

## Incidente 9
- **Síntoma:**
- **Diagnóstico:**
- **Comandos:**
- **Solución:**
- **Evidencia:**

## Incidente 10
- **Síntoma:**
- **Diagnóstico:**
- **Comandos:**
- **Solución:**
- **Evidencia:**
