# Terminal Rescue — Alonso Esteban García Sandoval y Nixon Sneider Villamizar Sarmiento

## Descripción

Este proyecto repara el proceso de cierre mensual de afiliados de una Caja de Compensación Familiar. El cierre genera el archivo de afiliados activos que usa el área de Subsidios, reporta en un archivo de excepciones los datos que no se pueden usar (duplicados, afiliados sin empresa, fechas inválidas, cruces que no coinciden con Caja Oriente) y ofrece una API para consultar un afiliado por su documento. Está pensado para el equipo de Operaciones y Auditoría.

## Integrantes

- Alonso Esteban García Sandoval (GitHub: chipitaps)
- Nixon Sneider Villamizar Sarmiento (GitHub: nixonsneider)

## Requisitos

- Docker Desktop o Docker Engine con el plugin `docker compose`.
- Python 3 (solo la librería estándar) y Bash para ejecutar `run.sh`.
- Git, `curl` y las utilidades estándar de Linux (`grep`, `awk`, `sort`, `uniq`).
- Probado en Windows 11 con Docker Desktop y WSL (Ubuntu); el cierre corre igual en cualquier Linux.

## Instalación y ejecución

Desde una copia limpia del repositorio, en este orden:

```bash
cp .env.example .env
docker compose up -d --build
docker compose ps
./run.sh
```

`docker compose up -d --build` construye la API y el worker y carga los CSV de `data/` en PostgreSQL. `./run.sh` ejecuta el cierre y escribe los resultados en `output/`. Para volver al estado inicial se usa `./reset.sh`, que borra contenedores, volúmenes y `output/` y levanta todo de nuevo.

## Configuración

Las variables viven en `.env` (que no se versiona) y se copian desde `.env.example`:

- `POSTGRES_DB`: nombre de la base que crea PostgreSQL. Ejemplo: `cierre`.
- `POSTGRES_USER`: usuario administrador de la base. Ejemplo: `cierre`.
- `POSTGRES_PASSWORD`: contraseña de ese usuario. Ejemplo: `cambiar-por-una-clave`.
- `DATABASE_HOST`: host con el que la API y el worker se conectan; debe ser el nombre del servicio de la base. Ejemplo: `cierre-db`.
- `DATABASE_PORT`: puerto de PostgreSQL. Ejemplo: `5432`.
- `DATABASE_NAME`: base a la que se conectan la API y el worker. Ejemplo: `cierre`.
- `DATABASE_USER`: usuario de conexión de la API y el worker. Ejemplo: `cierre`.
- `DATABASE_PASSWORD`: contraseña de conexión de la API y el worker. Ejemplo: `cambiar-por-una-clave`.
- `API_PORT`: puerto del equipo donde se publica la API. Ejemplo: `8081`.
- `WORKER_INTERVAL_SECONDS`: cada cuántos segundos concilia el worker; debe ser un entero, sin letras. Ejemplo: `30`.

## Arquitectura

El sistema tiene tres servicios definidos en `docker-compose.yml`. `cierre-db` es PostgreSQL 16 y carga al arrancar los CSV de `data/` en las tablas `afi_mae`, `afi_ben`, `empresa` y `aportes`. `cierre-api` es un servidor HTTP en Python que consulta esa base por el nombre del servicio. `cierre-worker` es un proceso en Python que cada cierto tiempo cuenta los afiliados en la base y lo escribe en su log. El cierre mensual no corre en un contenedor: `run.sh` llama a `scripts/cierre.sh`, que ejecuta `scripts/cierre.py` (lee los CSV de `data/` y escribe `output/`), y después a `scripts/top_error.sh`, que cuenta los errores de `logs/`.

## Uso

Consultar un afiliado por la API con `GET /afiliados/{documento}`:

```bash
curl localhost:8081/afiliados/1098765432
```

Responde `{"documento": "1098765432", "nombre": "JUAN CARLOS PEREZ GOMEZ", "estado": "ACTIVO", "empresa": "EMPRESA ABC"}`. Un documento que no existe responde 404.

`./run.sh` genera en `output/`:

- `afiliados_activos.csv`: un registro por afiliado activo con empresa válida, con sus beneficiarios y su último aporte.
- `excepciones.csv`: los registros que no se pueden usar y su tipo (`DUPLICADO`, `SIN_EMPRESA`, `BENEFICIARIO_HUERFANO`, `CODIGO_INVALIDO`, `FECHA_INVALIDA`, `CRUCE_NO_COINCIDE`).
- `totales.txt`: `total_afiliados`, `activos`, `inactivos` y `excepciones`.
- `top_error.txt`: el código de error más frecuente de los logs y cuántas veces aparece.

## Pruebas

Con el entorno levantado se ejecuta `./validator check`, que debe mostrar las 10 pruebas en PASS (625 de 625 puntos), y `./validator entregables`, que revisa el informe, la evidencia, los scripts y el historial Git. Para comprobar la repetibilidad se corre `./run.sh` dos veces seguidas y las salidas de `output/` deben ser idénticas. Los totales de `output/totales.txt` deben coincidir con `control/hoja_control.csv`: 1500 afiliados, 1194 activos y 274 inactivos.

## Documentación

- [incident-report.md](incident-report.md): los 10 incidentes con síntoma, diagnóstico, comandos, solución y evidencia.
- [evidence/](evidence/): la salida real de terminal que demuestra cada incidente.
- [AI_USAGE.md](AI_USAGE.md): cómo usamos la inteligencia artificial y qué corregimos.
- [docs/diccionario.md](docs/diccionario.md): diccionario de datos y reglas del cierre.

## Qué resolvimos

Encontramos y reparamos las diez fallas del kit. El worker caía porque el intervalo era `30s` y no un entero. La API apuntaba a un host de base que no existía y respondía 500 con afiliados sin segundo nombre. El script de cierre leía una ruta inexistente y solo corría una vez. Contamos los errores de los logs y reescribimos el cierre para reportar duplicados, códigos y fechas inválidos, huérfanos y el cruce con Caja Oriente. Hoy los totales coinciden con la hoja de control y el cierre es repetible.

## Limitaciones y pendientes

El cierre usa rutas fijas dentro del repositorio y no recibe parámetros. La API no tiene autenticación ni paginación. El worker solo registra el conteo en su log y no corrige datos.
