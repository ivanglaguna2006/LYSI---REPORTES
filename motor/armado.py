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
        if os.path.isdir(p) and len(d) == 7 and d[4] == "-" and (
                os.path.exists(os.path.join(p, "cargas.xlsx")) or os.path.exists(os.path.join(p, "importado.json"))):
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


def importado_a_R(d, a, m):
    """Mes importado de un reporte ya hecho: arma un resultado con la misma forma que el del motor."""
    import pandas as pd
    met = d.get("metodo", "calendario")
    filas = []
    for x in d["unidades"]:
        km, gas, ideal = x.get("km"), float(x.get("gasoil") or 0), x.get("ideal")
        conf = bool(x.get("km_confiable")) and bool(km)
        coef = gas * 100 / km if conf else None
        dif = (coef - ideal) if (coef is not None and ideal) else None
        est = x.get("estado")
        if met != "ventana":
            est = "HISTORICO" if conf else "SIN KM"
        urea = float(x.get("urea") or 0)
        filas.append({"unidad": x["unidad"], "modelo": x.get("modelo") or "", "chofer": x.get("chofer") or "",
                      "t0": pd.Timestamp(x["t0"]) if x.get("t0") else pd.NaT, "t1": pd.Timestamp(x["t1"]) if x.get("t1") else pd.NaT,
                      "dias": x.get("dias"), "fuente": x.get("fuente") or "Filarus", "km": km, "km_confiable": conf, "gasoil": gas, "urea": urea,
                      "n_cargas": x.get("cargas"), "coef": coef, "ideal": ideal, "dif": dif, "estado": est,
                      "motivo": x.get("motivo") or "", "obs": x.get("obs") or "",
                      "ratio_urea": urea / gas * 100 if gas else None})
    U = pd.DataFrame(filas)
    med = U[U.km_confiable]
    km, gm, go, ur = float(med.km.sum()), float(med.gasoil.sum()), float(U.gasoil.sum()), float(U.urea.sum())
    ex = d.get("extra", {})
    est = U.estado.value_counts().to_dict()
    precio = ex["importe_gasoil"] / go if ex.get("importe_gasoil") and go else None

    def sobre(estados):
        x = U[U.estado.isin(estados) & U.km_confiable]
        return float((x.gasoil - x.ideal * x.km / 100).sum()) if len(x) else 0.0
    vent = met == "ventana"
    k = {"km": km, "gasoil_medible": gm, "gasoil_operativa": go, "urea": ur, "coef": gm * 100 / km if km else None,
         "ratio_urea": ur / go * 100 if (go and vent) else None, "km_prom": km / len(med) if len(med) else None, "n_medibles": int(len(med)),
         "totales": ex.get("totales", int(len(U))), "operativas": int(len(U)), "sin_cargas": ex.get("sin_cargas", 0),
         "criticas": int(est.get("CRITICO", 0)) if vent else None, "atencion": int(est.get("ATENCION", 0)) if vent else None,
         "normales": int(est.get("NORMAL", 0)) if vent else None, "coef_bajo": int(est.get("COEF BAJO", 0)) if vent else None,
         "investigar": int(est.get("A INVESTIGAR", 0)) if vent else None,
         "exceso_urea": int((U.ratio_urea > C.UREA_EXCESO).sum()) if vent else None,
         "precio_gasoil": precio, "precio_min": ex.get("precio_min"), "precio_max": ex.get("precio_max"),
         "importe_gasoil": ex.get("importe_gasoil") or 0.0,
         "sobre_ideal_criticas": sobre(["CRITICO"]) if vent else None, "sobre_ideal_crit_atencion": sobre(["CRITICO", "ATENCION"]) if vent else None,
         "fuente_odo": int((U.fuente == "ODO malla").sum()), "fuente_filarus": int((U.fuente == "Filarus").sum()),
         "hay_malla_anterior": False, "gasoil_no_medible": go - gm}
    k["costo_criticas"] = k["sobre_ideal_criticas"] * precio if (vent and precio) else None
    k["costo_crit_atencion"] = k["sobre_ideal_crit_atencion"] * precio if (vent and precio) else None
    A = pd.DataFrame(d.get("atribucion") or [], columns=["unidad", "chofer", "litros", "part", "km", "ideal", "estado", "medible"])
    return {"anio": a, "mes": m, "nombre_mes": C.MESES[m], "version_reglas": C.VERSION_REGLAS, "importado": True, "metodo": met,
            "comparable": vent, "nota": d.get("nota", ""), "origen": d.get("origen", ""), "kpis": k, "unidades": U, "atribucion": A,
            "conc_agregado": pd.DataFrame(), "subas_sin_carga": pd.DataFrame(), "consumo_real": pd.DataFrame()}


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
        imp = os.path.join(p, "importado.json")
        motivo = None
        if mes.get("cargas") is None:
            motivo = ""
        elif (pa, pm) not in cache or cache[(pa, pm)].get("cargas") is None:
            motivo = f"{nombre}: queda como mes de arranque (falta cargar {C.MESES[pm]} para poder medir sus ventanas)."
        elif mes.get("filarus") is None:
            motivo = f"{nombre}: falta el archivo de Filarus; no se puede calcular."
        if motivo is None:
            try:
                res.append(K.calcular(mes, cache[(pa, pm)], a, m))
                continue
            except Exception as ex:
                errores.append(f"{nombre}: el cálculo se interrumpió. Detalle: {type(ex).__name__}: {ex}")
                continue
        # sin archivos suficientes para calcular: si hay un reporte importado, se muestra ese
        if os.path.exists(imp):
            try:
                res.append(importado_a_R(json.load(open(imp, encoding="utf-8")), a, m))
            except Exception as ex:
                errores.append(f"{nombre}: no se pudo leer el reporte importado. Detalle: {type(ex).__name__}: {ex}")
        elif motivo:
            pendientes.append(motivo)
    return res, errores, pendientes


def html_combustible(res):
    anios = sorted({r["anio"] for r in res})
    partes, tabs = [], []
    for a in anios:
        ms = [r for r in res if r["anio"] == a]
        for i, r in enumerate(ms):
            if r.get("importado"):
                partes.append(V.mes_importado_html(r))
            else:
                prev = ms[i - 1] if i > 0 and ms[i - 1]["mes"] == r["mes"] - 1 and not ms[i - 1].get("importado") else None
                partes.append(V.mes_html(r, prev))
            tabs.append(f'<button type="button" data-ir="m{a}{r["mes"]:02d}">{r["nombre_mes"].capitalize()} {a}</button>')
        cargados = {r["mes"] for r in ms}
        hoy = datetime.date.today()
        hasta = 12 if a < hoy.year else max(max(cargados), hoy.month - 1)
        falt = [C.MESES[m] for m in range(1, hasta + 1) if m not in cargados]
        comp = [r for r in ms if r.get("comparable", True)]
        hist = [r for r in ms if not r.get("comparable", True)]
        if comp:
            partes.append(V.anual_html(comp, a, falt, hist))
            tabs.append(f'<span class="sep"></span><button type="button" data-ir="a{a}">Evaluación {a}</button>')
    calc = [r for r in res if not r.get("importado")] or res
    ultimo = calc[-1]
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
        imp = bool(r.get("importado"))
        out["meses"].append({
            "id": f'{r["anio"]}-{r["mes"]:02d}', "nombre": f'{r["nombre_mes"]} {r["anio"]}',
            "importado": imp, "metodo": r.get("metodo", "ventana"),
            "km": k["km"], "gasoil": k["gasoil_medible"], "coef": k["coef"], "operativas": k["operativas"], "totales": k["totales"],
            "criticas": k["criticas"], "atencion": k["atencion"], "normales": k["normales"], "coef_bajo": k["coef_bajo"],
            "investigar": [] if imp else [{"unidad": x.unidad, "motivo": x.motivo, "manual": bool(x.get("manual", False) is True)} for _, x in inv.iterrows()],
            "n_investigar": k["investigar"],
            "cierra_ypf": None if imp else bool(r["conciliacion_ypf"]["cierra"]), "total_ypf": None if imp else r["conciliacion_ypf"]["total_archivo_l"],
            "anulatorios": 0 if imp else len(r["depuracion"]["pares_anulatorios"]), "malla_anterior": bool(k["hay_malla_anterior"]),
            "fuente_odo": k["fuente_odo"], "fuente_filarus": k["fuente_filarus"],
        })
    if res:
        out["html"] = html_combustible(res)
    return json.dumps(out, ensure_ascii=False)
