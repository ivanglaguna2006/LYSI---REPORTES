"""Circulación nocturna: completa las columnas de control de la planilla de circulaciones.

Herramienta «Circulación nocturna» del inicio (Administración y control). Corre en el navegador con
Pyodide y desde la consola con ``control_nocturna.py``. No guarda nada: recibe el Excel que exporta el
sistema satelital y devuelve el mismo archivo con seis columnas completadas (Autorizado, Observaciones y
los minutos), sin tocar nada más.

Reglas (especificación «Clasificación de Circulación Nocturna»):
- Observaciones: TRAFICO si la hora de inicio está entre las 23:00:00 y las 03:29:59 (cruza la
  medianoche); INICIO DE JORNADA en cualquier otro horario. El corte de las 03:30 es estricto.
- Autorizado: siempre SI.
- Duración < 29 → MINUTOS AUTORIZADOS; Duración ≥ 29 → MINUTOS OPERATIVOS. MINUTOS NO AUTORIZADOS
  queda siempre vacía. La duración se usa tal cual viene: nunca se recalcula como fin − inicio.
- Las filas sin inicio válido o sin duración numérica (vacías, «NO HAY REPORTE») quedan intactas.
"""
import base64
import copy
import json
import os
import shutil
import unicodedata
from datetime import datetime, time

import openpyxl

LIMITE_MINUTOS = 29          # estricto: 29 va a MINUTOS OPERATIVOS
CORTE_JORNADA = time(3, 30)  # 03:30:00 inclusive -> INICIO DE JORNADA
CORTE_TRAFICO = time(23, 0)  # 23:00:00 inclusive -> TRAFICO

ENCABEZADOS = {
    "inicio":     "cnfechahorainicio",
    "duracion":   "duracion",
    "chofer":     "chofer",
    "autorizado": "autorizado",
    "obs":        "observaciones",
    "min_aut":    "minutos autorizados",
    "min_noaut":  "minutos no autorizados",
    "min_oper":   "minutos operativos",
}
SALIDA = ["autorizado", "obs", "min_aut", "min_noaut", "min_oper"]


def norm(s):
    """Normaliza un encabezado: sin acentos, sin mayúsculas, sin espacios extra."""
    if s is None:
        return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.lower().split())


class ErrorNocturna(Exception):
    pass


def _hoja(wb):
    for hoja in wb.worksheets:
        mapa = {}
        for c in hoja[1]:
            n = norm(c.value)
            if n and n not in mapa:
                mapa[n] = c.column
        if ENCABEZADOS["inicio"] in mapa and ENCABEZADOS["duracion"] in mapa:
            return hoja, mapa
    raise ErrorNocturna("No se encontró una hoja con las columnas «CNFechaHoraInicio» y «Duración» en la fila 1.")


def _columnas(mapa):
    faltan = [n for n in ENCABEZADOS.values() if n not in mapa]
    if faltan:
        raise ErrorNocturna("Faltan columnas en la fila 1: " + ", ".join("«" + f + "»" for f in faltan) + ".")
    return {k: mapa[n] for k, n in ENCABEZADOS.items()}


def _es_valida(ini, dur):
    if not isinstance(ini, datetime):
        return False
    if isinstance(dur, bool) or not isinstance(dur, (int, float)):
        return False
    return True


def _motivo(ws, fila, ini, dur, col):
    """Por qué se saltea una fila (para el aviso); None si la fila está totalmente vacía."""
    vals = [ws.cell(fila, c).value for c in range(1, ws.max_column + 1)]
    if not any(v is not None and str(v).strip() != "" for v in vals):
        return None
    movil = ws.cell(fila, col["movil"]).value if col.get("movil") else None
    if isinstance(movil, str) and "no hay reporte" in norm(movil):
        return "sin reporte ese día"
    if ini is None or ini == "":
        return "sin fecha y hora de inicio"
    if not isinstance(ini, datetime):
        return "inicio que no es una fecha y hora"
    if dur is None or dur == "":
        return "sin duración"
    return "duración que no es un número"


def _escribir(ws, fila, col_destino, valor, col_modelo):
    """Escribe el valor heredando el formato de la fila si la celda no tenía uno propio."""
    celda = ws.cell(fila, col_destino)
    sin_estilo_propio = celda._style is None or not any(celda._style)
    celda.value = valor
    if sin_estilo_propio:
        modelo = ws.cell(fila, col_modelo)
        if modelo._style is not None:
            celda._style = copy.copy(modelo._style)


def clasificar(hora):
    """TRAFICO entre las 23:00:00 y las 03:29:59; INICIO DE JORNADA en el resto."""
    return "TRAFICO" if (hora >= CORTE_TRAFICO or hora < CORTE_JORNADA) else "INICIO DE JORNADA"


def procesar(entrada, salida):
    """Copia `entrada` en `salida` y completa las columnas de control. Devuelve el resumen."""
    if entrada.lower().endswith(".xlsm"):
        raise ErrorNocturna("El archivo es .xlsm (con macros): se perderían al guardar. Exportalo como .xlsx.")
    shutil.copyfile(entrada, salida)
    try:
        wb = openpyxl.load_workbook(salida)
    except Exception as e:
        raise ErrorNocturna("No se pudo abrir el archivo como Excel (.xlsx): " + str(e))
    ws, mapa = _hoja(wb)
    if getattr(ws, "_charts", None) or getattr(ws, "_images", None):
        raise ErrorNocturna("La hoja tiene gráficos o imágenes que se perderían al guardar. Sacalos y volvé a subir el archivo.")
    col = _columnas(mapa)
    col["movil"] = mapa.get("movil")

    procesadas, salteadas = 0, []
    suma_k = suma_m = suma_dur = 0
    borde = []
    for fila in range(2, ws.max_row + 1):
        ini = ws.cell(fila, col["inicio"]).value
        dur = ws.cell(fila, col["duracion"]).value
        if not _es_valida(ini, dur):
            m = _motivo(ws, fila, ini, dur, col)
            if m:
                salteadas.append((fila, m))
            continue
        hora = ini.time()
        cat = clasificar(hora)
        texto, numero = col["chofer"], col["duracion"]
        _escribir(ws, fila, col["obs"], cat, texto)
        _escribir(ws, fila, col["autorizado"], "SI", texto)
        if dur < LIMITE_MINUTOS:
            _escribir(ws, fila, col["min_aut"], dur, numero)
            _escribir(ws, fila, col["min_oper"], None, numero)
            suma_k += dur
        else:
            _escribir(ws, fila, col["min_oper"], dur, numero)
            _escribir(ws, fila, col["min_aut"], None, numero)
            suma_m += dur
        _escribir(ws, fila, col["min_noaut"], None, numero)
        suma_dur += dur
        procesadas += 1
        if hora.hour == 3:
            borde.append((fila, hora.strftime("%H:%M:%S"), cat))

    if suma_k + suma_m != suma_dur:
        raise ErrorNocturna("Los minutos no se conservan: revisar la clasificación.")
    wb.save(salida)
    return {"hoja": ws.title, "procesadas": procesadas, "salteadas": salteadas,
            "autorizados": suma_k, "operativos": suma_m, "duracion": suma_dur, "borde": borde}


def verificar(original, salida, resumen):
    """Las nueve verificaciones de la especificación, sobre los archivos en disco. Devuelve la lista de fallas."""
    fallas = []
    wo = openpyxl.load_workbook(original)
    ws_ = openpyxl.load_workbook(salida)
    if [h.title for h in wo.worksheets] != [h.title for h in ws_.worksheets]:
        fallas.append("cambió la cantidad o el nombre de las hojas")
        return fallas
    ho, mapa = _hoja(wo)
    hs = ws_[ho.title]
    col = _columnas(mapa)
    col["movil"] = mapa.get("movil")
    cols_salida = {col[k] for k in SALIDA}

    # 1. integridad estructural
    if ho.max_row != hs.max_row or ho.max_column != hs.max_column:
        fallas.append("cambió la cantidad de filas o columnas (%dx%d → %dx%d)" % (ho.max_row, ho.max_column, hs.max_row, hs.max_column))
    # 2. cobertura
    datos = sum(1 for f in range(2, ho.max_row + 1)
                if any(ho.cell(f, c).value is not None and str(ho.cell(f, c).value).strip() != "" for c in range(1, ho.max_column + 1)))
    if resumen["procesadas"] + len(resumen["salteadas"]) != datos:
        fallas.append("cobertura: %d procesadas + %d salteadas ≠ %d filas con datos" % (resumen["procesadas"], len(resumen["salteadas"]), datos))
    suma_k = suma_m = suma_dur = 0
    for f in range(2, hs.max_row + 1):
        ini = ho.cell(f, col["inicio"]).value
        dur = ho.cell(f, col["duracion"]).value
        k, l, m = (hs.cell(f, col[x]).value for x in ("min_aut", "min_noaut", "min_oper"))
        i, j = hs.cell(f, col["autorizado"]).value, hs.cell(f, col["obs"]).value
        if _es_valida(ini, dur):
            # 3. exclusividad
            if (k is None) == (m is None):
                fallas.append("fila %d: K y M %s" % (f, "cargadas a la vez" if k is not None else "vacías las dos"))
            suma_k += k or 0
            suma_m += m or 0
            suma_dur += dur
            # 6. dominio
            if i != "SI":
                fallas.append("fila %d: Autorizado = %r" % (f, i))
            if j not in ("INICIO DE JORNADA", "TRAFICO"):
                fallas.append("fila %d: Observaciones = %r" % (f, j))
            elif j != clasificar(ini.time()):
                fallas.append("fila %d: Observaciones = %s pero el inicio es %s" % (f, j, ini.time().strftime("%H:%M:%S")))
            # 7. borde 03:30
            if ini.time().hour == 3 and j != clasificar(ini.time()):
                fallas.append("fila %d: borde 03:30 mal clasificado" % f)
            if (dur < LIMITE_MINUTOS and k != dur) or (dur >= LIMITE_MINUTOS and m != dur):
                fallas.append("fila %d: la duración %s no quedó en la columna que corresponde" % (f, dur))
        else:
            # 8. filas intactas
            if any(v is not None for v in (i, j, k, l, m)):
                fallas.append("fila %d: fila salteada con columnas de control cargadas" % f)
        # 5. columna L
        if l is not None:
            fallas.append("fila %d: MINUTOS NO AUTORIZADOS con valor" % f)
    # 4. conservación
    if suma_k + suma_m != suma_dur:
        fallas.append("conservación: %s + %s ≠ %s" % (suma_k, suma_m, suma_dur))
    # 9. identidad fuera de las columnas de salida
    difs = 0
    for f in range(1, ho.max_row + 1):
        for c in range(1, ho.max_column + 1):
            if c in cols_salida and f > 1:
                continue
            a, b = ho.cell(f, c), hs.cell(f, c)
            if a.value != b.value or list(a._style or []) != list(b._style or []):
                difs += 1
                if difs <= 5:
                    fallas.append("celda %s cambió fuera de las columnas de control" % a.coordinate)
    if difs > 5:
        fallas.append("… y %d celdas más" % (difs - 5))
    for cd in set(ho.column_dimensions) | set(hs.column_dimensions):
        if ho.column_dimensions[cd].width != hs.column_dimensions[cd].width:
            fallas.append("cambió el ancho de la columna " + cd)
    if (ho.auto_filter.ref or None) != (hs.auto_filter.ref or None):
        fallas.append("cambió el autofiltro")
    if ho.freeze_panes != hs.freeze_panes:
        fallas.append("cambiaron los paneles inmovilizados")
    return fallas


def _plural(n, uno, varios):
    return ("%d " % n) + (uno if n == 1 else varios)


def mensaje(resumen):
    """Texto para la persona: una línea de confirmación y, si hubo, las filas salteadas."""
    lineas = ["Archivo procesado: %s completadas en la hoja «%s» (%s autorizados, %s operativos)." % (
        _plural(resumen["procesadas"], "circulación", "circulaciones"), resumen["hoja"],
        _plural(resumen["autorizados"], "minuto", "minutos"), _plural(resumen["operativos"], "minuto", "minutos"))]
    if resumen["salteadas"]:
        por = {}
        for f, m in resumen["salteadas"]:
            por.setdefault(m, []).append(f)
        partes = ["%s (%s)" % (m, ", ".join(str(f) for f in fs)) for m, fs in por.items()]
        lineas.append("Quedaron sin completar %s: %s." % (_plural(len(resumen["salteadas"]), "fila", "filas"), "; ".join(partes)))
    return lineas


def nombre_salida(nombre):
    base, ext = os.path.splitext(nombre)
    return base + "_procesado" + (ext or ".xlsx")


def procesar_json(ruta, nombre):
    """Para el navegador: procesa `ruta` y devuelve JSON con el archivo en base64 o los errores."""
    salida = os.path.join(os.path.dirname(ruta), "salida.xlsx")
    try:
        res = procesar(ruta, salida)
        fallas = verificar(ruta, salida, res)
        if fallas:
            return json.dumps({"errores": ["El archivo no pasó la validación y no se entrega:"] + fallas[:12]})
        with open(salida, "rb") as f:
            b = base64.b64encode(f.read()).decode("ascii")
        return json.dumps({"nombre": nombre_salida(nombre), "b64": b, "mensaje": mensaje(res),
                           "procesadas": res["procesadas"], "salteadas": len(res["salteadas"]),
                           "autorizados": res["autorizados"], "operativos": res["operativos"]})
    except ErrorNocturna as e:
        return json.dumps({"errores": [str(e)]})
    except Exception as e:
        return json.dumps({"errores": ["No se pudo procesar: " + str(e)]})
