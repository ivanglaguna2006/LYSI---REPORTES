# -*- coding: utf-8 -*-
"""Motor de cálculo del reporte mensual de combustible LYSI (Prompt Maestro v4.7).

Entrada: los archivos fuente del mes analizado y del mes anterior.
Salida: un diccionario con todas las tablas del reporte. Mismos archivos -> mismos números, siempre.
"""
import os
import json
import pandas as pd
import numpy as np
from . import config as C
from . import fuentes as F

H = pd.Timedelta(hours=1)


# ───────────────────────── utilidades ─────────────────────────
def familia(marca, modelo):
    """Familia de modelo para ideal y capacidad: '360', '410', '420', 'MB' o None."""
    marca = (marca or "").upper()
    modelo = (modelo or "").upper()
    if "BENZ" in marca or "MERCEDES" in marca:
        return "MB"
    for k in ("360", "410", "420"):
        if k in modelo:
            return k
    return None


def ideal_de(marca, modelo):
    """Devuelve (ideal, tiene_ideal_validado)."""
    fam = familia(marca, modelo)
    if fam == "MB":
        if any(m in (modelo or "").upper() for m in C.MODELOS_SIN_IDEAL):
            return C.IDEAL_MB, False
        return C.IDEAL_MB, True
    if fam in C.IDEALES_SCANIA:
        return C.IDEALES_SCANIA[fam], True
    return None, False


def unir_2en1(g):
    """Paso 2.1 — cargas de la misma unidad, mismo día y a menos de 2 h: se suman. Queda la hora de la última."""
    g = g.sort_values("fecha").reset_index(drop=True)
    grupos, actual = [], []
    for _, r in g.iterrows():
        if actual and r.fecha.normalize() == actual[-1].fecha.normalize() \
                and (r.fecha - actual[-1].fecha) < C.DOS_EN_UNO_HORAS * H:
            actual.append(r)
        else:
            if actual:
                grupos.append(actual)
            actual = [r]
    if actual:
        grupos.append(actual)
    filas = []
    for grp in grupos:
        ult = grp[-1]
        filas.append({
            "unidad": ult.unidad, "fecha": ult.fecha, "fecha_ini": grp[0].fecha,
            "litros": float(sum(x.litros for x in grp)), "dos_en_uno": len(grp) > 1,
            "n": len(grp), "chofer": ult.chofer, "localidad": ult.localidad,
            "provincia": ult.provincia, "establecimiento": ult.establecimiento,
        })
    return pd.DataFrame(filas)


def evento_cercano(eventos, t, horas, usados=None):
    """Evento de malla más cercano a t dentro de ±horas. Devuelve la fila o None."""
    if eventos is None or len(eventos) == 0 or pd.isna(t):
        return None
    d = (eventos.hora - t).abs()
    if usados:
        d = d[~d.index.isin(usados)]
    if d.empty:
        return None
    i = d.idxmin()
    return eventos.loc[i] if d.loc[i] <= horas * H else None


def km_filarus(fil_u, t_desde, t_hasta):
    """Regla 4 — Filarus: días posteriores a la fecha de t_desde y hasta la fecha de t_hasta inclusive."""
    if fil_u is None or len(fil_u) == 0:
        return 0.0
    m = (fil_u.dia > t_desde.normalize()) & (fil_u.dia <= t_hasta.normalize())
    return float(fil_u.loc[m, "km"].sum())


def unir_subas(ev):
    """La malla a veces parte un mismo llenado en dos eventos: si el nivel de un evento arranca donde terminó
    el anterior (± SUBA_CONTINUIDAD_PTS) y están a menos de SUBA_CONTINUIDAD_HORAS, es una sola suba."""
    ev = ev.sort_values("hora")
    grupos, actual = [], []
    for _, e in ev.iterrows():
        if actual and abs(e.nivel_de - actual[-1].nivel_a) <= C.SUBA_CONTINUIDAD_PTS \
                and (e.hora - actual[-1].hora) <= C.SUBA_CONTINUIDAD_HORAS * H:
            actual.append(e)
        else:
            if actual:
                grupos.append(actual)
            actual = [e]
    if actual:
        grupos.append(actual)
    out = []
    for g in grupos:
        out.append({"equipo": g[0].equipo, "hora": g[0].hora, "horas": [x.hora for x in g],
                    "suba": float(sum(x.suba for x in g)), "nivel_de": g[0].nivel_de, "nivel_a": g[-1].nivel_a,
                    "cambios": f"{g[0].nivel_de:.0f} % -> {g[-1].nivel_a:.0f} %", "odo": g[0].odo,
                    "lugar": g[0].lugar, "partes": len(g), "sin_patente": bool(g[0].sin_patente)})
    return out


# ───────────────────────── carga de un mes ─────────────────────────
def cargar_mes(carpeta):
    """Lee lo que haya en la carpeta de un mes (cargas, filarus, malla, resumen)."""
    d = {"carpeta": carpeta}
    p = lambda n: os.path.join(carpeta, n)
    d["cargas_crudo"] = F.leer_cargas(p("cargas.xlsx")) if os.path.exists(p("cargas.xlsx")) else None
    d["filarus"] = F.leer_filarus(p("filarus.xlsx")) if os.path.exists(p("filarus.xlsx")) else None
    d["malla"] = F.leer_malla(p("malla.xlsx")) if os.path.exists(p("malla.xlsx")) else None
    d["resumen"] = F.leer_resumen(p("resumen.xlsx")) if os.path.exists(p("resumen.xlsx")) else None
    if d["cargas_crudo"] is not None:
        d["cargas"], d["depuracion"] = F.depurar(d["cargas_crudo"])
    aj = p("ajustes.json")
    d["ajustes"] = json.load(open(aj, encoding="utf-8")) if os.path.exists(aj) else {}
    return d


# ───────────────────────── cálculo principal ─────────────────────────
def calcular(mes, ant, anio, nmes):
    """mes / ant: diccionarios de cargar_mes() del mes analizado y del anterior."""
    R = {"anio": anio, "mes": nmes, "nombre_mes": C.MESES[nmes], "version_reglas": C.VERSION_REGLAS}
    cargas, dep = mes["cargas"], mes["depuracion"]
    crudo = mes["cargas_crudo"]
    ajustes = mes.get("ajustes", {}) or {}
    aj_unidades = ajustes.get("unidades", {})
    avisos = []

    gas = cargas[cargas.tipo == "GAS"]
    urea = cargas[cargas.tipo == "UREA"]
    gas_ant = ant["cargas"][ant["cargas"].tipo == "GAS"] if ant and ant.get("cargas") is not None else None

    # Filarus de los dos meses (cola de la ventana)
    fils = [x["filarus"] for x in (ant, mes) if x and x.get("filarus") is not None]
    fil = pd.concat(fils) if fils else pd.DataFrame(columns=["unidad", "dia", "km", "marca", "modelo", "interno"])
    fil_mes = mes["filarus"] if mes.get("filarus") is not None else fil.iloc[0:0]
    # Malla de los dos meses, solo eventos de combustible para odómetro
    mallas = [x["malla"] for x in (ant, mes) if x and x.get("malla") is not None]
    malla = pd.concat(mallas).sort_values(["unidad", "hora"]).reset_index(drop=True) if mallas else None
    malla_mes = mes.get("malla")
    resumen = mes.get("resumen")
    hay_malla_ant = bool(ant and ant.get("malla") is not None)

    # Ficha de cada unidad (marca / modelo / interno) desde Filarus
    ficha = {}
    for u, g in fil.sort_values("dia").groupby("unidad"):
        ult = g.iloc[-1]
        ficha[u] = {"marca": ult.marca, "modelo": ult.modelo, "interno": ult.interno}
    if resumen is not None:
        for _, r in resumen.iterrows():
            if r.unidad not in ficha and r.modelo_scania:
                hp = "".join(ch for ch in r.modelo_scania if ch.isdigit())[:3]
                ficha[r.unidad] = {"marca": "SCANIA", "modelo": "P" + hp, "interno": None}

    # ── Conciliación con el total del archivo YPF ──
    anul_idx = set()
    crudo_sin_anul = crudo.copy()
    for par in dep["pares_anulatorios"]:
        m = (crudo_sin_anul.fecha == par["fecha"]) & (crudo_sin_anul.remito == par["remito"]) \
            & (crudo_sin_anul.producto == par["producto"])
        crudo_sin_anul = crudo_sin_anul[~m]
    crudo_sin_anul = crudo_sin_anul[crudo_sin_anul.crudo >= 0]
    gas_archivo = crudo_sin_anul[crudo_sin_anul.tipo == "GAS"]
    exc = dep["excluidas"]
    exc_gas = exc[exc.tipo == "GAS"]
    conc = {
        "total_archivo_l": float(gas_archivo.litros.sum()), "total_archivo_cargas": int(len(gas_archivo)),
        "excluidas": [], "operativa_l": float(gas.litros.sum()), "operativa_cargas": int(len(gas)),
        "operativa_unidades": int(cargas.unidad.nunique()),
    }
    for motivo, g in exc_gas.groupby(exc_gas.unidad.map(C.EXCLUIDAS)):
        conc["excluidas"].append({
            "motivo": motivo, "litros": float(g.litros.sum()), "cargas": int(len(g)),
            "unidades": int(g.unidad.nunique()), "productos": sorted(g.producto.unique().tolist()),
        })
    conc["cierra"] = abs(conc["total_archivo_l"] - sum(e["litros"] for e in conc["excluidas"]) - conc["operativa_l"]) < 0.001
    conc["excluidas_total_l"] = float(exc[exc.tipo.isin(["GAS"])].litros.sum())
    R["conciliacion_ypf"] = conc

    nocomb = dep["no_combustibles"]
    R["depuracion"] = {
        "pares_anulatorios": [{**p, "fecha": p["fecha"].isoformat()} for p in dep["pares_anulatorios"]],
        "negativas_sueltas": [{**p, "fecha": p["fecha"].isoformat()} for p in dep["negativas_sueltas"]],
        "no_combustibles": [
            {"unidad": u, "producto": pr, "cargas": int(len(g)), "cantidad": float(g.crudo.sum())}
            for (u, pr), g in nocomb.groupby(["unidad", "producto"])],
        "filas_archivo": int(len(crudo)), "filas_depuradas": int(len(cargas)),
    }

    # ── Ventanas, KM y coeficientes por unidad ──
    unidades = []
    tramos_todos = []
    comparativo = []
    pares = {a: b for a, b in C.PARES_GEMELOS}
    pares.update({b: a for a, b in C.PARES_GEMELOS})

    for u in sorted(cargas.unidad.unique()):
        g_u = gas[gas.unidad == u]
        f = ficha.get(u, {"marca": "", "modelo": "", "interno": None})
        fam = familia(f["marca"], f["modelo"])
        ideal, ideal_ok = ideal_de(f["marca"], f["modelo"])
        fil_u = fil[fil.unidad == u]
        mc = malla[(malla.unidad == u) & (malla.evento == "Combustible")] if malla is not None else None
        res_u = resumen[resumen.unidad == u] if resumen is not None else None
        row = {
            "unidad": u, "interno": f["interno"], "marca": f["marca"], "modelo": f["modelo"], "familia": fam,
            "t0": None, "t1": None, "dias": None, "fuente": None, "km": None, "km_confiable": False,
            "gasoil": float(g_u.litros.sum()), "urea": float(urea[urea.unidad == u].litros.sum()),
            "n_cargas": int(len(g_u)), "coef": None, "ideal": ideal, "dif": None,
            "estado": None, "motivo": "", "obs": [], "km_odo": None, "km_fil": None,
        }
        row["ratio_urea"] = row["urea"] / row["gasoil"] * 100 if row["gasoil"] > 0 else None
        t1 = g_u.fecha.max() if len(g_u) else pd.NaT
        t0 = pd.NaT
        if gas_ant is not None:
            ga = gas_ant[gas_ant.unidad == u]
            t0 = ga.fecha.max() if len(ga) else pd.NaT
        row["t0"], row["t1"] = t0, t1

        investigar = None  # (motivo, km_confiable)
        odo0_forzado = None
        if pd.isna(t1):
            row["estado"] = "SIN GASOIL"
            row["motivo"] = "Solo cargó urea en el mes"
            unidades.append(row)
            continue
        if pd.isna(t0):
            row["fuente"] = "Sin t0"
            investigar = ("Sin t0: no cargó gasoil en el mes anterior", False)
        else:
            row["dias"] = (t1 - t0) / pd.Timedelta(days=1)
            # sin la malla del mes anterior no hay odómetro en t0: no se empareja contra eventos del mes analizado
            e0 = evento_cercano(mc, t0, C.VENTANA_ODO_HORAS) if hay_malla_ant else None
            e1 = evento_cercano(mc, t1, C.VENTANA_ODO_HORAS)
            kf = km_filarus(fil_u, t0, t1)
            row["km_fil"] = kf
            ko = float(e1.odo - e0.odo) if (e0 is not None and e1 is not None) else None
            row["km_odo"] = ko
            usar_odo = ko is not None and ko > 0
            odo0_forzado = None
            ajk = aj_unidades.get(u, {})
            if ajk.get("km_ventana") is not None and ajk.get("fuente") == "ODO malla" and e1 is not None:
                # falta la malla del mes anterior: el km de la ventana se toma del reporte ya circulado
                ko = float(ajk["km_ventana"])
                odo0_forzado = float(e1.odo) - ko
                row["km_odo"] = ko
                usar_odo = True
                row["obs"].append(ajk.get("origen", "KM de ventana tomado del reporte circulado."))
            if u in pares:
                usar_odo = False
                row["obs"].append(f"Par cruzado con {pares[u]}: se usa Filarus.")
            if ko is not None and ko <= 0:
                row["obs"].append("Odómetro de malla no avanza entre t0 y t1 → Filarus.")
            if usar_odo:
                row["fuente"], row["km"] = "ODO malla", ko
                d0 = (e0.hora - t0) / H if e0 is not None else 0.0
                d1 = (e1.hora - t1) / H
                if abs(d0) > C.VENTANA_SUBA_HORAS or abs(d1) > C.VENTANA_SUBA_HORAS:
                    row["obs"].append(
                        "Cargas de borde sin suba de tanque a la hora de la tarjeta: "
                        f"t0 empareja {abs(d0):.0f} h {'después' if d0 > 0 else 'antes'}, "
                        f"t1 {abs(d1):.0f} h {'después' if d1 > 0 else 'antes'}.")
                if kf > 0:
                    difp = (kf - ko) / ko * 100
                    if abs(difp) > 9:
                        row["obs"].append(f"ODO ventana {ko:,.0f} vs Filarus {kf:,.0f} ({difp:+.1f}%).".replace(",", " "))
            else:
                row["fuente"], row["km"] = "Filarus", kf
                if u not in pares:
                    if mc is not None and len(mc) and e0 is None and e1 is not None:
                        row["obs"].append("Malla sin evento ±24 h de t0 → Filarus.")
                    elif mc is not None and len(mc) and e1 is None:
                        row["obs"].append("Malla sin evento ±24 h de t1 → Filarus.")
            row["km_confiable"] = True

            # Ajuste manual registrado para esta unidad (decisión del analista): va antes que las reglas automáticas
            aj = aj_unidades.get(u)
            if aj and aj.get("estado") == "A INVESTIGAR":
                investigar = (aj.get("motivo", "Decisión del analista"), bool(aj.get("km_confiable", True)))
                row["manual"] = True

            # Regla 11 — control de sanidad sobre el mes calendario (Resumen vs Filarus)
            if investigar is None and res_u is not None and len(res_u) and u not in pares:
                km_res = float(res_u.km.iloc[0]) if pd.notna(res_u.km.iloc[0]) else None
                km_fm = float(fil_mes[fil_mes.unidad == u].km.sum())
                if km_res and km_res > 0:
                    difp = abs(km_fm - km_res) / km_res * 100
                    if difp > C.SANIDAD_PCT:
                        if row["fuente"] == "Filarus" and km_fm < km_res:
                            investigar = (f"Regla 11: sin odómetro de malla en la ventana y Filarus sin señal "
                                          f"({km_fm:,.0f} vs {km_res:,.0f} km del Resumen). Sin fuente confiable.".replace(",", " "), False)
                        elif row["fuente"] == "Filarus":
                            row["obs"].append(f"Regla 11: telemetría parcial (Resumen {km_res:,.0f} vs Filarus {km_fm:,.0f} km) → se usa Filarus.".replace(",", " "))
                        else:
                            row["obs"].append(f"Regla 11: Resumen {km_res:,.0f} vs Filarus {km_fm:,.0f} km en el mes; se mantiene el odómetro.".replace(",", " "))

            if investigar is None and (row["km"] is None or row["km"] <= 0):
                investigar = ("Sin km en la ventana", False)
            if investigar is None and not ideal_ok:
                investigar = (f"{f['modelo'] or 'Modelo desconocido'} sin ideal validado ni análogo (Regla 18)", True)
        if investigar is None and ideal and row["km"]:
            coef = row["gasoil"] * 100 / row["km"]
            if coef > C.COEF_IMPOSIBLE_FACTOR * ideal:
                txt = (f"{coef:.2f}".replace(".", ",") + " L/100 km no es consumo físicamente posible "
                       f"(más de {C.COEF_IMPOSIBLE_FACTOR:g} veces el ideal). KM medido por {row['fuente']}: "
                       + f"{row['km']:,.0f}".replace(",", " ") + " (no confiable, fuera del coeficiente).")
                investigar = (txt, False)

        if investigar is not None:
            row["estado"] = "A INVESTIGAR"
            row["motivo"] = investigar[0]
            row["km_confiable"] = bool(investigar[1]) and row["km"] is not None and row["km"] > 0
            if row["km_confiable"] and ideal:
                row["coef"] = row["gasoil"] * 100 / row["km"]
                row["dif"] = row["coef"] - ideal
        else:
            row["coef"] = row["gasoil"] * 100 / row["km"]
            row["dif"] = row["coef"] - ideal
            d = round(row["dif"], 2)  # se clasifica con la diferencia que se muestra (2 decimales)
            row["estado"] = ("CRITICO" if d > C.UMBRAL_CRITICO else "ATENCION" if d > C.UMBRAL_ATENCION
                             else "COEF BAJO" if d < C.UMBRAL_COEF_BAJO else "NORMAL")

        # Comparativo Filarus vs My Scania sobre la ventana
        if row["km_odo"] and row["km_odo"] > 0 and row["km_fil"] and row["km_fil"] > 0 and row["fuente"] == "ODO malla":
            c_o = row["gasoil"] * 100 / row["km_odo"]
            c_f = row["gasoil"] * 100 / row["km_fil"]
            delta = abs(c_f - c_o)
            cat = "COINCIDE" if delta < 1 else "LEVE" if delta < 3 else "MODERADA" if delta < 6 else "GRANDE"
            comparativo.append({"unidad": u, "km_odo": row["km_odo"], "km_fil": row["km_fil"],
                                "dif_km_pct": (row["km_odo"] - row["km_fil"]) / row["km_fil"] * 100,
                                "gasoil": row["gasoil"], "coef_odo": c_o, "coef_fil": c_f,
                                "delta": c_f - c_o, "categoria": cat})

        # Tramos carga a carga dentro de la ventana (Regla 2 y Regla 8)
        if pd.notna(t0) and row["km"]:
            cg = unir_2en1(g_u)
            prev_t, prev_odo = t0, None
            if row["fuente"] == "ODO malla":
                prev_odo = odo0_forzado if odo0_forzado is not None else float(evento_cercano(mc, t0, C.VENTANA_ODO_HORAS).odo)
            suma = 0.0
            pend_l = 0.0
            for _, c in cg.iterrows():
                tr = {"unidad": u, "desde": prev_t, "hasta": c.fecha, "dos_en_uno": bool(c.dos_en_uno),
                      "litros": c.litros, "km": None, "coef": None, "chofer": c.chofer,
                      "localidad": c.localidad, "fuente": "ODO" if row["fuente"] == "ODO malla" else "Filarus",
                      "nota": ""}
                if row["fuente"] == "ODO malla":
                    e = evento_cercano(mc, c.fecha, C.VENTANA_ODO_HORAS)
                    if e is None:
                        tr["nota"] = "Sin evento de malla ±24 h: sus km quedan en el tramo siguiente."
                        tramos_todos.append(tr)
                        prev_t = c.fecha
                        continue
                    km_t = float(e.odo) - prev_odo
                    if km_t < 0:
                        tr["nota"] = "Odómetro de malla retrocede respecto de la carga anterior: tramo no medible."
                        tramos_todos.append(tr)
                        prev_t = c.fecha
                        continue
                    prev_odo = float(e.odo)
                else:
                    km_t = km_filarus(fil_u, prev_t, c.fecha)
                tr["km"] = km_t
                tr["coef"] = c.litros * 100 / km_t if km_t > 0 else None
                if km_t == 0:
                    tr["nota"] = ("Tramo de 0 km: Filarus corta por día entero." if tr["fuente"] == "Filarus"
                                  else "Tramo de 0 km: el mismo evento de malla empareja con dos cargas seguidas.")
                suma += km_t
                tramos_todos.append(tr)
                prev_t = c.fecha
            row["tramos_suma"] = suma
            row["tramos_cierra"] = abs(suma - row["km"]) < 0.5

        row["obs"] = " ".join(row["obs"])
        unidades.append(row)

    U = pd.DataFrame(unidades)
    orden = {"CRITICO": 0, "ATENCION": 1, "NORMAL": 2, "COEF BAJO": 3, "A INVESTIGAR": 4, "SIN GASOIL": 5}
    U["_o"] = U.estado.map(orden)
    U = U.sort_values(["_o", "dif", "gasoil"], ascending=[True, False, False]).drop(columns="_o").reset_index(drop=True)
    R["unidades"] = U
    R["tramos"] = pd.DataFrame(tramos_todos)
    R["comparativo"] = pd.DataFrame(comparativo).sort_values("delta", key=lambda s: s.abs(), ascending=False) \
        if comparativo else pd.DataFrame()

    # ── Urea ──
    desg = []
    for prod, factor in C.PRODUCTOS_UREA.items():
        g = urea[urea.producto == prod]
        desg.append({"producto": prod, "cargas": int(len(g)), "crudo": float(g.crudo.sum()),
                     "unidad_crudo": "litros" if factor == 1 else "bidones", "factor": factor,
                     "litros": float(g.litros.sum())})
    R["urea_desglose"] = desg
    Ug = U[U.gasoil > 0].copy()
    red = resumen.set_index("unidad").reductor_l.to_dict() if resumen is not None else {}
    en_res = set(resumen.unidad) if resumen is not None else set()
    def reductor(u):
        if u not in en_res:
            return "sin telemetría"
        v = red.get(u)
        return "sin dato" if (v is None or pd.isna(v) or v == 0) else float(v)
    Ug["reductor"] = Ug.unidad.map(reductor)
    R["urea_exceso"] = Ug[Ug.ratio_urea > C.UREA_EXCESO].sort_values("ratio_urea", ascending=False)
    R["urea_bajo"] = Ug[Ug.ratio_urea < C.UREA_BAJO].sort_values(["ratio_urea", "gasoil"], ascending=[True, False])

    # ── Regla 19: conciliación carga de tarjeta ↔ suba de malla ──
    # Cada suba de combustible (≥ piso) se asigna a la carga más cercana dentro de ±3 h; una carga puede
    # recibir más de una suba (la malla a veces parte un mismo llenado en dos eventos) y se suman.
    conc_det, conc_agr, subas_sin = [], [], []
    if malla_mes is not None:
        mm = malla_mes[(malla_mes.evento == "Combustible") & (malla_mes.suba >= C.SUBA_PISO_PCT)]
        gemelas = set(pares.keys())
        for u in sorted(set(mm.unidad) & set(gas.unidad)):
            if u in gemelas:
                continue
            f = ficha.get(u, {})
            fam = familia(f.get("marca"), f.get("modelo"))
            cap = C.CAPACIDAD.get(fam)
            if cap is None:
                continue
            ev = unir_subas(mm[mm.unidad == u])
            cg = unir_2en1(gas[gas.unidad == u]).reset_index(drop=True)
            # pares (carga, suba) dentro de ±3 h, del más cercano al más lejano; cada uno se usa una sola vez
            asign = {i: [] for i in cg.index}
            cand = []
            for k, e in enumerate(ev):
                for j, c in cg.iterrows():
                    d = min(min(abs((h - c.fecha) / H), abs((h - c.fecha_ini) / H)) for h in e["horas"])
                    if d <= C.VENTANA_SUBA_HORAS:
                        cand.append((d, j, k))
            ev_usados = set()
            for d, j, k in sorted(cand):
                if k in ev_usados or asign[j]:
                    continue
                asign[j].append(ev[k])
                ev_usados.add(k)
            libres = []
            for k, e in enumerate(ev):
                if k not in ev_usados:
                    dist = cg.apply(lambda c: min(abs((e["hora"] - c.fecha) / H), abs((e["hora"] - c.fecha_ini) / H)), axis=1)
                    libres.append((e, dist.idxmin() if len(dist) else None))
            for j, c in cg.iterrows():
                evs = asign[j]
                pct = float(sum(e["suba"] for e in evs))
                sl = pct * cap / 100
                fila = {"unidad": u, "modelo": f.get("modelo"), "capacidad": cap, "fecha": c.fecha_ini,
                        "dos_en_uno": bool(c.dos_en_uno), "litros": c.litros, "suba_pct": pct, "suba_l": sl,
                        "n_subas": sum(e["partes"] for e in evs), "dif": c.litros - sl,
                        "equivale": ("sin suba" if not evs else
                                     "equivale" if abs(c.litros - sl) <= C.TOLERANCIA_LITROS else "marcada"),
                        "chofer": c.chofer, "localidad": c.localidad,
                        "hora_suba": evs[0]["hora"] if evs else None,
                        "lugar_suba": evs[0]["lugar"] if evs else "",
                        "niveles": " + ".join(e["cambios"] for e in evs),
                        "sin_patente": bool(ev and ev[0]["sin_patente"])}
                conc_det.append(fila)
            for e, j in libres:
                if e["suba"] >= C.SUBA_SIN_CARGA_PCT:
                    cerca = cg.loc[j] if j is not None else None
                    dh = ((e["hora"] - cerca.fecha) / H) if cerca is not None else None
                    subas_sin.append({"unidad": u, "equipo": e["equipo"], "fecha": e["hora"], "niveles": e["cambios"],
                                      "suba_pct": e["suba"], "suba_l": e["suba"] * cap / 100,
                                      "odo": e["odo"], "lugar": e["lugar"],
                                      "carga_cercana": cerca.fecha if cerca is not None else None,
                                      "carga_cercana_l": float(cerca.litros) if cerca is not None else None,
                                      "carga_cercana_loc": cerca.localidad if cerca is not None else "",
                                      "horas": float(dh) if dh is not None else None})
        CD = pd.DataFrame(conc_det)
        if len(CD):
            for u, g in CD[CD.equivale != "sin suba"].groupby("unidad"):
                t, m_ = g.litros.sum(), g.suba_l.sum()
                conc_agr.append({"unidad": u, "modelo": g.modelo.iloc[0], "cargas": int(len(g)), "tarjeta": t,
                                 "malla": m_, "dif": t - m_, "desv_pct": (t - m_) / m_ * 100 if m_ else None,
                                 "cap_implicita": t / g.suba_pct.sum() * 100 if g.suba_pct.sum() else None,
                                 "cap_nominal": g.capacidad.iloc[0],
                                 "sin_suba": int((CD[CD.unidad == u].equivale == "sin suba").sum())})
    R["conc_detalle"] = pd.DataFrame(conc_det)
    R["conc_agregado"] = pd.DataFrame(conc_agr).sort_values("desv_pct", ascending=False) if conc_agr else pd.DataFrame()
    R["subas_sin_carga"] = pd.DataFrame(subas_sin)

    # ── Regla 20: consumo real del motor, mes calendario ──
    cr = []
    if resumen is not None:
        gas_u = gas.groupby("unidad").litros.sum().to_dict()
        ideales = U.set_index("unidad").ideal.to_dict()
        modelos = U.set_index("unidad").modelo.to_dict()
        fil_mes_u = fil_mes.groupby("unidad").km.sum().to_dict()
        for _, r in resumen.iterrows():
            u = r.unidad
            if u in C.EXCLUIDAS or u not in gas_u:
                continue
            nota = ""
            fuera = False
            if pd.isna(r.km) or r.km <= 0 or pd.isna(r.motor_l):
                continue
            kf = fil_mes_u.get(u)
            if u in pares:
                nota = f"Leer como par con {pares[u]} (telemetría cruzada)."
            elif kf and abs(kf - r.km) / max(kf, r.km) * 100 > C.SANIDAD_PCT and r.km < kf:
                nota = f"Telemetría parcial ({r.km:,.0f} km vs {kf:,.0f} de Filarus): fuera de comparación.".replace(",", " ")
                fuera = True
            t = gas_u[u]
            cr.append({"unidad": u, "modelo": modelos.get(u), "km": float(r.km), "tarjeta": t,
                       "motor": float(r.motor_l), "dif_l": t - float(r.motor_l),
                       "compra": t * 100 / r.km, "real": float(r.motor_l) * 100 / r.km,
                       "compra_menos_real": (t - float(r.motor_l)) * 100 / r.km,
                       "ideal": ideales.get(u), "real_vs_ideal": (float(r.motor_l) * 100 / r.km - ideales[u]) if ideales.get(u) else None,
                       "nota": nota, "fuera": fuera,
                       "ralenti_pct": r.ralenti_pct, "ralenti_l": r.ralenti_l, "ralenti_hm": r.ralenti_hm})
    R["consumo_real"] = pd.DataFrame(cr).sort_values("compra_menos_real", ascending=False) if cr else pd.DataFrame()

    # ── Choferes: atribución completa y ranking (Regla 10) ──
    multi, atrib = [], []
    Uidx = U.set_index("unidad")
    for u, g in gas.groupby("unidad"):
        tot = g.litros.sum()
        ru = Uidx.loc[u]
        km_u = ru.km if (ru.km_confiable and ru.km) else None
        por = g.groupby("chofer").litros.sum().sort_values(ascending=False)
        for ch, l in por.items():
            part = l / tot
            atrib.append({"chofer": ch, "unidad": u, "litros": l, "part": part,
                          "km": km_u * part if km_u else None, "ideal": ru.ideal,
                          "estado": ru.estado, "medible": ru.estado != "A INVESTIGAR" and km_u is not None})
        if len(por) > 1:
            for ch, l in por.items():
                multi.append({"unidad": u, "chofer": ch, "litros": l, "total_unidad": tot, "part": l / tot * 100,
                              "km": km_u * l / tot if km_u else None, "estado": ru.estado,
                              "compartida": por.iloc[0] / tot <= 0.5, "n_choferes": len(por)})
    A = pd.DataFrame(atrib)
    chof = []
    for ch, g in A.groupby("chofer"):
        med = g[g.medible]
        fila = {"chofer": ch, "unidades": ", ".join(sorted(g.unidad.unique())), "n_unidades": int(g.unidad.nunique()),
                "litros_total": float(g.litros.sum()), "km": None, "litros": None, "coef": None,
                "ideal": None, "dif": None, "aviso": ""}
        inv = sorted(g[~g.medible].unidad.unique())
        if len(med):
            km, l = med.km.sum(), med.litros.sum()
            fila.update({"km": km, "litros": l, "coef": l * 100 / km if km else None,
                         "ideal": float((med.ideal * med.km).sum() / km) if km else None})
            fila["dif"] = fila["coef"] - fila["ideal"] if fila["coef"] is not None else None
            if inv:
                fila["aviso"] = "Cargó también en unidad(es) a investigar: " + ", ".join(inv)
        else:
            fila["aviso"] = "Solo cargó en unidad(es) a investigar: " + ", ".join(inv)
        chof.append(fila)
    R["choferes"] = pd.DataFrame(chof).sort_values("dif", ascending=False, na_position="last").reset_index(drop=True)
    R["multichofer"] = pd.DataFrame(multi)
    R["atribucion"] = A

    # ── Cargas detalle ──
    R["cargas"] = cargas

    # ── Unidades sin cargas (están en Filarus, no cargaron) ──
    todas = (set(fil_mes.unidad) | set(cargas.unidad)) - set(C.EXCLUIDAS)
    sin_cargas = sorted(todas - set(cargas.unidad))
    R["sin_cargas"] = [{"unidad": u, "km_filarus": float(fil_mes[fil_mes.unidad == u].km.sum()),
                        "modelo": ficha.get(u, {}).get("modelo", "")} for u in sin_cargas]

    # ── KPIs: totales de suma exacta de cargas, nunca de valores redondeados ──
    med = U[U.km_confiable & U.km.notna() & (U.km > 0)]
    km_tot = float(med.km.sum())
    gas_med = float(med.gasoil.sum())
    gas_op = float(gas.litros.sum())
    urea_tot = float(urea.litros.sum())
    est = U.estado.value_counts().to_dict()
    imp = gas.importe_yer.sum()
    precio = float(imp / gas_op) if gas_op else None
    def sobre_ideal(estados):
        s = U[U.estado.isin(estados) & U.km.notna()]
        return float((s.gasoil - s.ideal * s.km / 100).sum())
    R["kpis"] = {
        "km": km_tot, "gasoil_medible": gas_med, "gasoil_operativa": gas_op, "urea": urea_tot,
        "coef": gas_med * 100 / km_tot if km_tot else None,
        "ratio_urea": urea_tot / gas_op * 100 if gas_op else None,
        "km_prom": km_tot / len(med) if len(med) else None, "n_medibles": int(len(med)),
        "totales": len(todas), "operativas": int(U.unidad.nunique()), "sin_cargas": len(sin_cargas),
        "criticas": int(est.get("CRITICO", 0)), "atencion": int(est.get("ATENCION", 0)),
        "normales": int(est.get("NORMAL", 0)), "coef_bajo": int(est.get("COEF BAJO", 0)),
        "investigar": int(est.get("A INVESTIGAR", 0)), "sin_gasoil": int(est.get("SIN GASOIL", 0)),
        "exceso_urea": int(len(R["urea_exceso"])), "urea_bajo": int(len(R["urea_bajo"])),
        "fuente_odo": int((U.fuente == "ODO malla").sum()), "fuente_filarus": int((U.fuente == "Filarus").sum()),
        "precio_gasoil": precio,
        "precio_min": float(gas.precio_yer.min()) if len(gas) else None,
        "precio_max": float(gas.precio_yer.max()) if len(gas) else None,
        "importe_gasoil": float(imp),
        "importe_urea": float(urea.importe_yer.sum()),
        "sobre_ideal_criticas": sobre_ideal(["CRITICO"]),
        "sobre_ideal_crit_atencion": sobre_ideal(["CRITICO", "ATENCION"]),
        "gasoil_no_medible": gas_op - gas_med,
        "hay_malla_anterior": hay_malla_ant,
    }
    k = R["kpis"]
    k["costo_criticas"] = k["sobre_ideal_criticas"] * precio if precio else None
    k["costo_crit_atencion"] = k["sobre_ideal_crit_atencion"] * precio if precio else None
    R["avisos"] = avisos
    R["ajustes"] = ajustes
    return R
