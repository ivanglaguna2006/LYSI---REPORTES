# -*- coding: utf-8 -*-
"""Recorre la carpeta de datos, calcula cada mes que tenga su mes anterior y arma el HTML de Combustible.
Lo usan por igual el generador de escritorio y la pantalla de administración (dentro del navegador)."""
import os
import json
import datetime
from . import calculo as K, render as V, config as C

NOMBRES = {"cargas": "cargas de la tarjeta YPF (ReporteConsumos)", "filarus": "km de Filarus (KmRecorridos)",
           "malla": "Informe de combustible de My Scania", "resumen": "Resumen de rendimientos de My Scania"}


def meses_disponibles(base):
    out = []
    for d in sorted(os.listdir(base)):
        p = os.path.join(base, d)
        if os.path.isdir(p) and len(d) == 7 and d[4] == "-" and os.path.exists(os.path.join(p, "cargas.xlsx")):
            out.append((int(d[:4]), int(d[5:]), p))
    return out


def cargar_seguro(a, m, p, errores):
    """Lee un mes archivo por archivo, para poder decir cuál es el que no se pudo leer."""
    from . import fuentes as F
    d = {"carpeta": p}
    lectores = {"cargas": F.leer_cargas, "filarus": F.leer_filarus, "malla": F.leer_malla, "resumen": F.leer_resumen}
    for tipo, fn in lectores.items():
        ruta = os.path.join(p, tipo + ".xlsx")
        d[tipo if tipo != "cargas" else "cargas_crudo"] = None
        if not os.path.exists(ruta):
            continue
        try:
            df = fn(ruta)
            if df is None or len(df) == 0:
                raise ValueError("el archivo no tiene filas")
            d[tipo if tipo != "cargas" else "cargas_crudo"] = df
        except Exception as ex:
            errores.append(f"{C.MESES[m].capitalize()} {a}: no se pudo leer el archivo de {NOMBRES[tipo]}. "
                           f"Revisá que sea el export correcto. Detalle: {type(ex).__name__}: {ex}")
    if d["cargas_crudo"] is not None:
        d["cargas"], d["depuracion"] = F.depurar(d["cargas_crudo"])
        fuera = d["cargas_crudo"][(d["cargas_crudo"].fecha.dt.year != a) | (d["cargas_crudo"].fecha.dt.month != m)]
        if len(fuera) > len(d["cargas_crudo"]) * 0.5:
            errores.append(f"{C.MESES[m].capitalize()} {a}: el archivo de cargas trae fechas de otro mes "
                           f"({d['cargas_crudo'].fecha.min():%d/%m/%Y} a {d['cargas_crudo'].fecha.max():%d/%m/%Y}). Revisá que esté en el mes correcto.")
    if d.get("filarus") is not None:
        f = d["filarus"]
        if ((f.dia.dt.year != a) | (f.dia.dt.month != m)).mean() > 0.5:
            errores.append(f"{C.MESES[m].capitalize()} {a}: el archivo de Filarus trae fechas de otro mes "
                           f"({f.dia.min():%d/%m/%Y} a {f.dia.max():%d/%m/%Y}).")
    aj = os.path.join(p, "ajustes.json")
    d["ajustes"] = json.load(open(aj, encoding="utf-8")) if os.path.exists(aj) else {}
    return d


def calcular_todo(base):
    """Devuelve (resultados, errores, pendientes)."""
    errores, pendientes = [], []
    disp = meses_disponibles(base)
    cache = {(a, m): cargar_seguro(a, m, p, errores) for a, m, p in disp}
    res = []
    for a, m, p in disp:
        pa, pm = (a, m - 1) if m > 1 else (a - 1, 12)
        mes = cache[(a, m)]
        nombre = f"{C.MESES[m]} {a}"
        if mes.get("cargas") is None:
            continue
        if (pa, pm) not in cache or cache[(pa, pm)].get("cargas") is None:
            pendientes.append(f"{nombre}: queda como mes de arranque (falta cargar {C.MESES[pm]} para poder medir sus ventanas).")
            continue
        if mes.get("filarus") is None:
            pendientes.append(f"{nombre}: falta el archivo de Filarus; no se puede calcular.")
            continue
        try:
            res.append(K.calcular(mes, cache[(pa, pm)], a, m))
        except Exception as ex:
            errores.append(f"{nombre}: el cálculo se interrumpió. Detalle: {type(ex).__name__}: {ex}")
    return res, errores, pendientes


def html_combustible(res):
    anios = sorted({r["anio"] for r in res})
    partes, tabs = [], []
    for a in anios:
        ms = [r for r in res if r["anio"] == a]
        for i, r in enumerate(ms):
            prev = ms[i - 1] if i > 0 and ms[i - 1]["mes"] == r["mes"] - 1 else None
            partes.append(V.mes_html(r, prev))
            tabs.append(f'<button type="button" data-ir="m{a}{r["mes"]:02d}">{r["nombre_mes"].capitalize()} {a}</button>')
        cargados = {r["mes"] for r in ms}
        hoy = datetime.date.today()
        hasta = 12 if a < hoy.year else max(max(cargados), hoy.month - 1)
        falt = [C.MESES[m] for m in range(1, hasta + 1) if m not in cargados]
        partes.append(V.anual_html(ms, a, falt))
        tabs.append(f'<span class="sep"></span><button type="button" data-ir="a{a}">Evaluación {a}</button>')
    ultimo = res[-1]
    inicio = f'm{ultimo["anio"]}{ultimo["mes"]:02d}'
    return f'<template data-tabs>{"".join(tabs)}</template><div data-inicio="{inicio}"></div>' + "".join(partes)


def procesar(base):
    """Punto de entrada único. Devuelve un JSON con el HTML de Combustible y un resumen de control por mes."""
    res, errores, pendientes = calcular_todo(base)
    out = {"errores": errores, "pendientes": pendientes, "meses": [], "html": None,
           "generado": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"), "reglas": C.VERSION_REGLAS}
    for r in res:
        k, U = r["kpis"], r["unidades"]
        inv = U[U.estado == "A INVESTIGAR"]
        out["meses"].append({
            "id": f'{r["anio"]}-{r["mes"]:02d}', "nombre": f'{r["nombre_mes"]} {r["anio"]}',
            "km": k["km"], "gasoil": k["gasoil_medible"], "coef": k["coef"], "operativas": k["operativas"], "totales": k["totales"],
            "criticas": k["criticas"], "atencion": k["atencion"], "normales": k["normales"], "coef_bajo": k["coef_bajo"],
            "investigar": [{"unidad": x.unidad, "motivo": x.motivo, "manual": bool(x.get("manual", False) is True)} for _, x in inv.iterrows()],
            "cierra_ypf": bool(r["conciliacion_ypf"]["cierra"]), "total_ypf": r["conciliacion_ypf"]["total_archivo_l"],
            "anulatorios": len(r["depuracion"]["pares_anulatorios"]), "malla_anterior": bool(k["hay_malla_anterior"]),
            "fuente_odo": k["fuente_odo"], "fuente_filarus": k["fuente_filarus"],
            "unidades": sorted(U.unidad.tolist()),
        })
    if res:
        out["html"] = html_combustible(res)
    return json.dumps(out, ensure_ascii=False)
