#!/usr/bin/env python3
"""Cierre mensual de afiliados activos."""
import csv
from datetime import datetime
import os
import re
from collections import OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTRADA = os.path.join(ROOT, "data")
SALIDA = os.path.join(ROOT, "output")


def leer_csv(nombre):
    ruta = os.path.join(ENTRADA, nombre)
    with open(ruta, encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def escribir_csv(nombre, campos, filas):
    ruta = os.path.join(SALIDA, nombre)
    with open(ruta, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=campos, lineterminator="\n")
        writer.writeheader()
        writer.writerows(filas)


def nombre_completo(fila):
    return "{0} {1} {2} {3}".format(
        fila.get("NOM1", ""),
        fila.get("NOM2", ""),
        fila.get("APE1", ""),
        fila.get("APE2", ""),
    )


def normalizar_fecha(valor):
    """Normaliza fecha a YYYY-MM-DD (ISO) aceptando YYYY-MM-DD, DD/MM/YYYY y YYYYMMDD.

    Valida fechas reales (ej. 29 de febrero solo en año bisiesto).
    Devuelve la fecha en formato YYYY-MM-DD o None si es inválida.
    """
    if not valor:
        return None
    val = valor.strip()
    # 1. Formato YYYY-MM-DD (ISO)
    if re.match(r"^\d{4}-\d{2}-\d{2}$", val):
        try:
            dt = datetime.strptime(val, "%Y-%m-%d")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            return None
    # 2. Formato DD/MM/YYYY
    if re.match(r"^\d{2}/\d{2}/\d{4}$", val):
        try:
            dt = datetime.strptime(val, "%d/%m/%Y")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            return None
    # 3. Formato YYYYMMDD
    if re.match(r"^\d{8}$", val):
        try:
            dt = datetime.strptime(val, "%Y%m%d")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            return None
    return None


def main():
    os.makedirs(SALIDA, exist_ok=True)

    maestro = leer_csv("AFI_MAE.csv")
    empresas_por_codigo = {
        fila["COD_EMP"]: fila for fila in leer_csv("EMPRESA.csv")
    }
    beneficiarios = leer_csv("AFI_BEN.csv")

    print("Leyendo afiliados desde {0}/AFI_MAE.csv".format(ENTRADA.replace("\\", "/")))

    # 1. Duplicados: se conserva la primera aparición; DUPLICADO una vez por documento.
    unicos = OrderedDict()
    duplicados = OrderedDict()
    for fila in maestro:
        documento = (fila.get("NRO_DOC") or "").strip()
        if documento in unicos:
            duplicados[documento] = True
            continue
        unicos[documento] = fila

    excepciones = []
    for documento in duplicados:
        excepciones.append(
            {
                "documento": documento,
                "tipo": "DUPLICADO",
                "detalle": "Documento repetido en AFI_MAE; se conserva la primera aparicion",
            }
        )

    # 2. Estado: solo A e I. Otro valor => CODIGO_INVALIDO (no activo ni inactivo).
    validos = OrderedDict()
    for documento, fila in unicos.items():
        estado = (fila.get("EST_AFI") or "").strip()
        if estado not in ("A", "I"):
            excepciones.append(
                {
                    "documento": documento,
                    "tipo": "CODIGO_INVALIDO",
                    "detalle": "EST_AFI={0}".format(estado or "(vacio)"),
                }
            )
            continue
        validos[documento] = fila

    # 3. Empresa de activos: vacía o inexistente => SIN_EMPRESA (no entra a activos).
    activos = []
    for documento, fila in validos.items():
        estado = (fila.get("EST_AFI") or "").strip()
        if estado != "A":
            continue
        cod_emp = (fila.get("COD_EMP") or "").strip()
        if not cod_emp or cod_emp not in empresas_por_codigo:
            excepciones.append(
                {
                    "documento": documento,
                    "tipo": "SIN_EMPRESA",
                    "detalle": "COD_EMP={0}".format(cod_emp or "(vacio)"),
                }
            )
            continue
        activos.append(
            {
                "documento": documento,
                "nombre": nombre_completo(fila),
                "estado": "ACTIVO",
                "cod_empresa": cod_emp,
                "empresa": "",
                "beneficiarios": "0",
                "ultimo_aporte": "",
            }
        )

    # 4. Fechas: YYYY-MM-DD, DD/MM/YYYY y YYYYMMDD se normalizan a ISO (YYYY-MM-DD).
    # Si la fecha es inválida (N/A, 2023/02/29, etc.) se reporta FECHA_INVALIDA.
    # IMPORTANTE: FECHA_INVALIDA NO excluye al afiliado, sigue contando normal.
    for documento, fila in unicos.items():
        fec_raw = (fila.get("FEC_AFI") or "").strip()
        fec_iso = normalizar_fecha(fec_raw)
        if fec_iso is not None:
            fila["FEC_AFI"] = fec_iso
        else:
            excepciones.append(
                {
                    "documento": documento,
                    "tipo": "FECHA_INVALIDA",
                    "detalle": "FEC_AFI={0}".format(fec_raw or "(vacio)"),
                }
            )

    # 5. Huérfanos: el afiliado del beneficiario no está en el maestro (tras duplicados).
    documentos_maestro = set(unicos)
    for fila in beneficiarios:
        doc_afi = (fila.get("NRO_DOC_AFI") or "").strip()
        if doc_afi in documentos_maestro:
            continue
        excepciones.append(
            {
                "documento": (fila.get("NRO_DOC_BEN") or "").strip(),
                "tipo": "BENEFICIARIO_HUERFANO",
                "detalle": "NRO_DOC_AFI={0} no existe en AFI_MAE".format(doc_afi or "(vacio)"),
            }
        )

    escribir_csv(
        "afiliados_activos.csv",
        [
            "documento",
            "nombre",
            "estado",
            "cod_empresa",
            "empresa",
            "beneficiarios",
            "ultimo_aporte",
        ],
        activos,
    )
    escribir_csv("excepciones.csv", ["documento", "tipo", "detalle"], excepciones)

    # TODO: nombre de la empresa desde EMPRESA.csv
    # TODO: contar beneficiarios desde AFI_BEN.csv
    # TODO: último aporte desde APORTES.csv (YYYY-MM)
    # TODO: cruce con el extracto de Caja Oriente

    totales_path = os.path.join(SALIDA, "totales.txt")
    with open(totales_path, "w", encoding="utf-8") as handle:
        handle.write("total_afiliados={0}\n".format(len(unicos)))
        handle.write("activos={0}\n".format(len(activos)))

    print("Cierre terminado")


if __name__ == "__main__":
    main()
