# -*- coding: utf-8 -*-
"""Arma el HTML de cada apartado. Todo el contenido queda como HTML estático (Regla 6):
ningún dato se calcula ni se inserta en el navegador."""
import html
import pandas as pd
from . import config as C

NB = "&#160;"
COL = {"CRITICO": "#C62828", "ATENCION": "#E65100", "NORMAL": "#2E7D32", "COEF BAJO": "#1565C0",
       "A INVESTIGAR": "#455A64", "SIN GASOIL": "#8a8a8a"}
ETIQ = {"CRITICO": "Crítico", "ATENCION": "Atención", "NORMAL": "Normal", "COEF BAJO": "Coef. bajo",
        "A INVESTIGAR": "A investigar", "SIN GASOIL": "Sin gasoil"}
ORDEN = ["CRITICO", "ATENCION", "NORMAL", "COEF BAJO", "A INVESTIGAR"]


def nulo(v):
    return v is None or (isinstance(v, float) and pd.isna(v)) or v is pd.NaT


def n(v, dec=0, signo=False):
    """Número con separador de miles (espacio duro) y coma decimal."""
    if nulo(v):
        return "—"
    s = f"{v:+,.{dec}f}" if signo else f"{v:,.{dec}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", NB).replace("-", "−")


def e(s):
    return html.escape("" if nulo(s) else str(s))


def f(t, hora=True):
    if nulo(t):
        return "—"
    return t.strftime("%d/%m %H:%M") if hora else t.strftime("%d/%m")


def badge(estado):
    return f'<span class="est" style="background:{COL.get(estado, "#777")}">{ETIQ.get(estado, estado)}</span>'


def tabla(cols, filas, clase=""):
    """cols: lista de (titulo, alineacion 'l'|'r'). filas: lista de listas de HTML ya formateado."""
    th = "".join(f'<th class="{a}">{t}</th>' for t, a in cols)
    trs = []
    for fila in filas:
        cls = ""
        if isinstance(fila, dict):
            cls, fila = f' class="{fila["cls"]}"', fila["c"]
        trs.append(f"<tr{cls}>" + "".join(f'<td class="{cols[i][1]}">{c}</td>' for i, c in enumerate(fila)) + "</tr>")
    return f'<div class="tw"><table class="{clase}"><thead><tr>{th}</tr></thead><tbody>{"".join(trs)}</tbody></table></div>'


def barra_dif(dif, maxabs=12.0):
    """Barra estática centrada en el ideal: a la derecha consume de más, a la izquierda de menos."""
    if nulo(dif):
        return ""
    w = min(abs(dif), maxabs) / maxabs * 50
    col = COL["CRITICO"] if dif > 3 else COL["ATENCION"] if dif > 1 else COL["COEF BAJO"] if dif < -3 else COL["NORMAL"]
    x = 50 if dif >= 0 else 50 - w
    return (f'<svg class="bd" viewBox="0 0 100 10" preserveAspectRatio="none" aria-hidden="true">'
            f'<rect x="{x:.1f}" y="2" width="{max(w, 0.8):.1f}" height="6" fill="{col}"/>'
            f'<rect x="49.6" y="0" width="0.8" height="10" fill="#111"/></svg>')


def kpi(valor, rotulo, nota=""):
    nt = f'<div class="kn">{nota}</div>' if nota else ""
    return f'<div class="kpi"><div class="kv">{valor}</div><div class="kl">{rotulo}</div>{nt}</div>'


def franja_estados(k):
    tot = k["operativas"]
    partes, ley = [], []
    datos = [("CRITICO", k["criticas"]), ("ATENCION", k["atencion"]), ("NORMAL", k["normales"]),
             ("COEF BAJO", k["coef_bajo"]), ("A INVESTIGAR", k["investigar"])]
    for est, c in datos:
        if c:
            partes.append(f'<div style="flex:{c};background:{COL[est]}" title="{ETIQ[est]}: {c}"></div>')
        ley.append(f'<div class="le"><i style="background:{COL[est]}"></i><b>{c}</b> {ETIQ[est].lower()}</div>')
    return f'<div class="franja" role="img" aria-label="Estado de las {tot} unidades operativas">{"".join(partes)}</div><div class="ley">{"".join(ley)}</div>'


# ───────────────────────── apartado de un mes ─────────────────────────
def mes_html(R, prev=None):
    k = R["kpis"]
    U = R["unidades"]
    mes = R["nombre_mes"].capitalize()
    anio = R["anio"]
    pid = f"m{anio}{R['mes']:02d}"
    S = []  # secciones (id, titulo, html)

    # 1 ── Resumen
    cy = R["conciliacion_ypf"]
    filas = [["Total de gasoil del archivo YPF", n(cy["total_archivo_l"], 2), n(cy["total_archivo_cargas"]), "Sin pares anulatorios"]]
    for x in cy["excluidas"]:
        filas.append([f"menos: excluidas por Regla 5 — {e(x['motivo']).lower()} ({x['unidades']})", n(-x["litros"], 2), n(x["cargas"]), e(", ".join(x["productos"]))])
    filas.append({"cls": "tot", "c": ["Gasoil de la flota operativa", n(cy["operativa_l"], 2), n(cy["operativa_cargas"]),
                                      "Cierra al milésimo" if cy["cierra"] else "NO CIERRA — revisar"]})
    if k["gasoil_no_medible"] > 0.005:
        filas.append(["de eso, en unidades sin km confiable (fuera del coeficiente general)", n(k["gasoil_no_medible"], 2), "", ""])
    t_conc = tabla([("Concepto", "l"), ("Litros", "r"), ("Cargas", "r"), ("Detalle", "l")], filas)
    t_urea = tabla([("Producto", "l"), ("Cargas", "r"), ("Valor crudo", "r"), ("Factor", "r"), ("Litros", "r")],
                   [[e(d["producto"]), n(d["cargas"]), n(d["crudo"], 0 if d["factor"] > 1 else 2) + " " + d["unidad_crudo"],
                     "×" + str(d["factor"]), n(d["litros"], 2)] for d in R["urea_desglose"]]
                   + [{"cls": "tot", "c": ["Total", n(sum(d["cargas"] for d in R["urea_desglose"])), "", "", n(k["urea"], 2)]}])
    dep = R["depuracion"]
    li = []
    if dep["pares_anulatorios"]:
        for p in dep["pares_anulatorios"]:
            li.append(f"Par anulatorio descartado (Regla 9): {e(p['unidad'])}, {pd.Timestamp(p['fecha']).strftime('%d/%m/%Y %H:%M:%S')}, "
                      f"{e(p['producto'])}, +{n(p['litros'], 0)} y −{n(p['litros'], 0)}, remito {e(p['remito'])}, {e(p['chofer'])}.")
    else:
        li.append("Sin pares anulatorios en el mes (Regla 9).")
    for p in dep["no_combustibles"]:
        li.append(f"Producto no combustible, fuera de todo cálculo: {e(p['unidad'])}, {p['cargas']} carga(s) de {e(p['producto'])} ({n(p['cantidad'], 2)}).")
    li.append(f"Las {len(C.EXCLUIDAS)} unidades excluidas por Regla 5 suman {n(cy['excluidas_total_l'], 2)} L de gasoil y no entran en ningún cálculo.")
    li.append(f"Fuente de km: {k['fuente_odo']} unidades por odómetro de malla Scania y {k['fuente_filarus']} por Filarus.")
    sc = R["sin_cargas"]
    if sc:
        li.append("Sin cargas en el mes: " + ", ".join(f"{e(x['unidad'])} ({n(x['km_filarus'])} km en Filarus)" for x in sc) + ".")
    aj = (R.get("ajustes") or {})
    if aj.get("nota"):
        li.append("Ajuste registrado: " + e(aj["nota"]))
    manual = U[U.get("manual", False) == True] if "manual" in U.columns else U.iloc[0:0]
    for _, r in manual.iterrows():
        li.append(f"Decisión del analista registrada: {e(r.unidad)} a investigar — {e(r.motivo)}")
    comp = ""
    if prev is not None:
        comp = f" ({prev['nombre_mes']}: {n(prev['kpis']['coef'], 2)})"
    resumen = f"""
<p class="lead">{k['operativas']} unidades operativas de {k['totales']} totales, {k['sin_cargas']} sin cargas.
{n(k['km'])} km en las ventanas de {k['n_medibles']} unidades y {n(k['gasoil_medible'], 2)} L de gasoil:
coeficiente general <strong>{n(k['coef'], 2)} L/100 km</strong>{comp}.</p>
{franja_estados(k)}
<h3>Actividad de la flota</h3>
<div class="kpis">
{kpi(n(k['km']), 'km de las ventanas', f"{k['n_medibles']} unidades medibles")}
{kpi(n(k['gasoil_medible'], 2), 'litros de gasoil', 'de las unidades medibles')}
{kpi(n(k['coef'], 2), 'coeficiente general', 'gasoil × 100 / km')}
{kpi(n(k['urea'], 2), 'litros de urea', 'bidones convertidos (Regla 17)')}
{kpi(n(k['ratio_urea'], 2) + NB + '%', 'ratio urea / gasoil', 'sobre la flota operativa')}
{kpi(n(k['km_prom']), 'km promedio por unidad', 'por ventana medible')}
</div>
<h3>Estado de la flota</h3>
<div class="kpis">
{kpi(f"{k['operativas']} de {k['totales']}", 'operativas', f"{k['sin_cargas']} sin cargas")}
{kpi(k['criticas'], 'críticas', 'diferencia mayor a 3')}
{kpi(k['atencion'], 'en atención', 'diferencia de 1 a 3')}
{kpi(k['normales'], 'normales', 'diferencia hasta 1')}
{kpi(k['coef_bajo'], 'coeficiente bajo', 'diferencia menor a −3')}
{kpi(k['investigar'], 'a investigar', 'Regla 21')}
{kpi(k['exceso_urea'], 'exceso de urea', 'ratio mayor a 8 %')}
</div>
<h3>Conciliación con el total del archivo YPF</h3>{t_conc}
<h3>Desglose de urea</h3>{t_urea}
<h3>Depuración previa</h3><ul class="hechos">{''.join(f'<li>{x}</li>' for x in li)}</ul>"""
    S.append(("resumen", "Resumen", resumen))

    # 2 ── Consumo por unidad vs ideal
    filas = []
    for _, r in U.iterrows():
        vent = f"{f(r.t0)} → {f(r.t1)}" if not nulo(r.t0) else f"sin arranque → {f(r.t1)}"
        km = n(r.km) if (r.km_confiable and not nulo(r.km)) else (f'<span class="nc" title="No confiable, fuera del coeficiente">{n(r.km)}*</span>' if not nulo(r.km) and r.km > 0 else "—")
        obs = " ".join(x for x in [r.motivo, r.obs] if x)
        filas.append([f"<b>{e(r.unidad)}</b>", e(r.modelo), vent, n(r.dias, 1), e(r.fuente), km, n(r.gasoil, 2),
                      n(r.coef, 2), n(r.ideal, 1), n(r.dif, 2, True) if not nulo(r.dif) else "—",
                      barra_dif(r.dif) if r.estado != "A INVESTIGAR" else "", badge(r.estado), f'<span class="obs">{e(obs)}</span>'])
    S.append(("unidades", "Consumo por unidad vs ideal", f"""
<p class="nota">Ventana: de la última carga de gasoil de {C.MESES[R['mes'] - 1 or 12]} a la última de {R['nombre_mes']}. La carga de arranque no cuenta como litros,
solo marca desde dónde se miden los km. Coeficiente = litros × 100 / km de la ventana. La barra muestra la diferencia contra el ideal de cada unidad.</p>
""" + tabla([("Unidad", "l"), ("Modelo", "l"), ("Ventana", "l"), ("Días", "r"), ("Fuente km", "l"), ("km", "r"), ("Gasoil L", "r"),
             ("Coef", "r"), ("Ideal", "r"), ("Dif", "r"), ("", "l"), ("Estado", "l"), ("Observación", "l")], filas, "unid")))

    # 3 ── Urea
    def filas_urea(df):
        return [[f"<b>{e(r.unidad)}</b>", e(r.modelo), n(r.gasoil, 2), n(r.urea, 2), n(r.ratio_urea, 2) + NB + "%",
                 n(r.reductor) if not isinstance(r.reductor, str) else r.reductor, badge(r.estado)] for _, r in df.iterrows()]
    cu = [("Unidad", "l"), ("Modelo", "l"), ("Gasoil L", "r"), ("Urea L", "r"), ("Ratio", "r"), ("Reductor Scania L", "r"), ("Estado", "l")]
    cero = int((R["urea_bajo"].urea == 0).sum())
    S.append(("urea", "Urea", f"""
<p class="nota">Ratio = litros de urea / litros de gasoil × 100, los dos de la tarjeta YPF (Regla 3). La columna Reductor de My Scania va solo como referencia.</p>
<h3>Exceso, ratio mayor a {C.UREA_EXCESO:g} % — {len(R['urea_exceso'])} unidades</h3>{tabla(cu, filas_urea(R['urea_exceso']))}
<h3>Ratio bajo, menor a {C.UREA_BAJO:g} % — {len(R['urea_bajo'])} unidades</h3>
<p class="nota">{cero} de las {len(R['urea_bajo'])} cargaron cero urea en todo el mes.</p>{tabla(cu, filas_urea(R['urea_bajo']))}"""))

    # 4 ── Historial de cargas de las críticas
    T = R["tramos"]
    crit = U[U.estado == "CRITICO"]
    bloques = []
    for _, r in crit.iterrows():
        t = T[T.unidad == r.unidad]
        filas = []
        for _, x in t.iterrows():
            filas.append([f(x.desde), f(x.hasta) + (' <span class="tag">2en1</span>' if x.dos_en_uno else ""), n(x.litros, 2),
                          n(x.km) if not nulo(x.km) else "—", e(x.fuente), n(x.coef, 2) if not nulo(x.coef) else "—",
                          e(x.chofer), e(x.localidad) + (f' <span class="obs">{e(x.nota)}</span>' if x.nota else "")])
        cierre = "cierra exacto" if r.tramos_cierra else f"diferencia de {n(r.km - r.tramos_suma)} km contra la ventana"
        filas.append({"cls": "tot", "c": ["Total de la ventana", "", n(r.gasoil, 2), n(r.tramos_suma), "", n(r.coef, 2), "", f"km de la ventana: {n(r.km)}, {cierre}"]})
        bloques.append(f'<details class="hist"><summary><b>{e(r.unidad)}</b> {e(r.modelo)} <span class="sm">coef {n(r.coef, 2)} contra ideal {n(r.ideal, 1)} ({n(r.dif, 2, True)}), {len(t)} tramos</span></summary>'
                       + tabla([("Desde", "l"), ("Hasta", "l"), ("Litros", "r"), ("km tramo", "r"), ("Fuente", "l"), ("Coef tramo", "r"), ("Chofer", "l"), ("Localidad", "l")], filas) + "</details>")
    ncierra = int(crit.tramos_cierra.sum()) if len(crit) else 0
    S.append(("historial", "Historial de cargas de las críticas", f"""
<p class="nota">Tramos de carga a carga dentro de la ventana. Coeficiente de tramo = litros de esa carga × 100 / km del tramo (Regla 2).
En {ncierra} de las {len(crit)} críticas la suma de los tramos es igual al km de la ventana (Regla 8). Tocá cada unidad para ver sus tramos.</p>{''.join(bloques)}"""))

    # 5 ── Conciliación carga ↔ malla
    CA, CD, SS = R["conc_agregado"], R["conc_detalle"], R["subas_sin_carga"]
    if len(CA):
        filas = [[f"<b>{e(r.unidad)}</b>", e(r.modelo), n(r.cargas), n(r.tarjeta, 2), n(r.malla, 2), n(r.dif, 2, True), n(r.desv_pct, 1, True) + NB + "%",
                  n(r.cap_implicita), n(r.cap_nominal), n(r.sin_suba) if r.sin_suba else ""] for _, r in CA.iterrows()]
        tt, tm = CA.tarjeta.sum(), CA.malla.sum()
        filas.append({"cls": "tot", "c": ["Flota", "", n(CA.cargas.sum()), n(tt, 2), n(tm, 2), n(tt - tm, 2, True), n((tt - tm) / tm * 100, 1, True) + NB + "%", "", "", n(CA.sin_suba.sum())]})
        t_agr = tabla([("Unidad", "l"), ("Modelo", "l"), ("Cargas", "r"), ("Tarjeta L", "r"), ("Malla L", "r"), ("Diferencia L", "r"), ("Desvío", "r"),
                       ("Cap. implícita L", "r"), ("Cap. nominal L", "r"), ("Sin suba", "r")], filas)
        filas = [[f"<b>{e(r.unidad)}</b>", f(r.fecha) + (' <span class="tag">2en1</span>' if r.dos_en_uno else ""), n(r.litros, 2),
                  (n(r.suba_pct) + NB + "%") if r.equivale != "sin suba" else "—", n(r.suba_l, 2) if r.equivale != "sin suba" else "—",
                  n(r.dif, 2, True), e(r.equivale), e(r.chofer), e(r.localidad)] for _, r in CD.iterrows()]
        t_det = tabla([("Unidad", "l"), ("Carga", "l"), ("Tarjeta L", "r"), ("Suba", "r"), ("Suba L", "r"), ("Diferencia", "r"), ("¿Equivalen?", "l"), ("Chofer", "l"), ("Localidad", "l")], filas)
        vc = CD.equivale.value_counts().to_dict()
        filas = [[f"<b>{e(r.unidad)}</b>", f(r.fecha), e(r.niveles), n(r.suba_pct) + NB + "%", n(r.suba_l), e(r.lugar),
                  (f"{f(r.carga_cercana)}, {n(r.carga_cercana_l, 2)} L en {e(r.carga_cercana_loc)} ({n(abs(r.horas), 1)} h {'antes' if r.horas > 0 else 'después'})" if not nulo(r.carga_cercana) else "—")]
                 for _, r in SS.sort_values(["unidad", "fecha"]).iterrows()] if len(SS) else []
        t_ss = tabla([("Unidad", "l"), ("Suba", "l"), ("Niveles", "l"), ("%", "r"), ("≈ L", "r"), ("Lugar según My Scania", "l"), ("Carga de tarjeta más cercana", "l")], filas)
        sinpat = sorted(CD[CD.sin_patente].unidad.unique())
        S.append(("malla", "Conciliación tarjeta vs malla", f"""
<p class="nota">Regla 19: por cada carga de gasoil se busca la suba de nivel de tanque dentro de ±{C.VENTANA_SUBA_HORAS} h y se convierte a litros con la capacidad nominal del modelo.
Tolerancia ±{C.TOLERANCIA_LITROS:g} L. Ese corte está por debajo de la resolución de la malla (1 % del tanque son 4,25 a 4,65 L), así que el detalle marca casi todas las filas por aritmética: la señal está en el agregado por unidad.
{('Equipos sin patente en My Scania, asignados por configuración: ' + ', '.join(sinpat) + '.') if sinpat else ''}</p>
<h3>Agregado por unidad — {len(CA)} unidades</h3>{t_agr}
<details class="hist"><summary><b>Detalle por carga</b> <span class="sm">{len(CD)} cargas: {vc.get('equivale', 0)} equivalen, {vc.get('marcada', 0)} marcadas, {vc.get('sin suba', 0)} sin suba</span></summary>{t_det}</details>
<h3>Subas de tanque sin carga de tarjeta — {len(SS)}</h3>
<p class="nota">Subas de {C.SUBA_SIN_CARGA_PCT:g} % o más sin una carga de tarjeta dentro de ±{C.VENTANA_SUBA_HORAS} h. Al lado, la carga de tarjeta más cercana de esa unidad.</p>{t_ss}"""))

    # 6 ── Consumo real del motor
    CR = R["consumo_real"]
    if len(CR):
        filas = [[f"<b>{e(r.unidad)}</b>", e(r.modelo), n(r.km), n(r.tarjeta, 2), n(r.motor), n(r.dif_l, 2, True), n(r.compra, 2), n(r["real"], 2),
                  n(r.compra_menos_real, 2, True), n(r.ideal, 1), n(r.real_vs_ideal, 2, True), f'<span class="obs">{e(r.nota)}</span>'] for _, r in CR.iterrows()]
        ok = CR[~CR.fuera]
        filas.append({"cls": "tot", "c": [f"{len(ok)} comparables", "", n(ok.km.sum()), n(ok.tarjeta.sum(), 2), n(ok.motor.sum()), n(ok.tarjeta.sum() - ok.motor.sum(), 2, True),
                                          n(ok.tarjeta.sum() * 100 / ok.km.sum(), 2), n(ok.motor.sum() * 100 / ok.km.sum(), 2),
                                          n((ok.tarjeta.sum() - ok.motor.sum()) * 100 / ok.km.sum(), 2, True), "", "", ""]})
        S.append(("motor", "Consumo real del motor", f"""
<p class="nota"><b>Esta sección va sobre el mes calendario, no sobre la ventana</b> (Regla 20): el Resumen de My Scania informa km y litros inyectados del 1 al último día del mes.
Por eso el consumo por compra de acá difiere del coeficiente de la tabla principal. Diferencia positiva: se compró más de lo que quemó el motor. Negativa: el motor quemó más de lo comprado. Tres datos crudos, sin umbral.</p>
""" + tabla([("Unidad", "l"), ("Modelo", "l"), ("km calendario", "r"), ("Tarjeta L", "r"), ("Motor L", "r"), ("Dif. L", "r"), ("Por compra", "r"), ("Real", "r"),
             ("Compra − real", "r"), ("Ideal", "r"), ("Real vs ideal", "r"), ("Nota", "l")], filas)))

    # 7 ── Choferes
    CH, MC = R["choferes"], R["multichofer"]
    filas = [[str(i + 1) if not nulo(r.dif) else "", f"<b>{e(r.chofer)}</b>", e(r.unidades), n(r.km), n(r.litros, 2), n(r.coef, 2), n(r.ideal, 2),
              n(r.dif, 2, True) if not nulo(r.dif) else "—", barra_dif(r.dif), f'<span class="obs">{e(r.aviso)}</span>'] for i, (_, r) in enumerate(CH.iterrows())]
    t_ch = tabla([("#", "r"), ("Chofer", "l"), ("Unidad(es)", "l"), ("km prorrateados", "r"), ("Gasoil L", "r"), ("Coef", "r"), ("Ideal pond.", "r"), ("Dif", "r"), ("", "l"), ("Aviso", "l")], filas)
    t_mc = ""
    if len(MC):
        filas = [[f"<b>{e(r.unidad)}</b>" + (f' <span class="tag">Compartida, {r.n_choferes} choferes</span>' if r.compartida else ""), e(r.chofer), n(r.litros, 2),
                  n(r.total_unidad, 2), n(r.part, 1) + NB + "%", n(r.km), badge(r.estado)] for _, r in MC.iterrows()]
        t_mc = f"<h3>Unidades manejadas por más de un chofer — {MC.unidad.nunique()}</h3>" + tabla(
            [("Unidad", "l"), ("Chofer", "l"), ("Litros del chofer", "r"), ("Total unidad L", "r"), ("Participación", "r"), ("km prorrateados", "r"), ("Estado de la unidad", "l")], filas)
    S.append(("choferes", "Choferes", f"""
<p class="nota">El chofer sale de la columna CONDUCTOR de la tarjeta (Regla 1). Los km de la ventana de cada unidad se reparten entre sus choferes según los litros que cargó cada uno;
el ideal del chofer es el promedio de los ideales de sus unidades ponderado por km. Figuran los {len(CH)} choferes con cargas en el mes.</p>{t_ch}{t_mc}"""))

    # 8 ── Comparativo Filarus vs My Scania
    CP = R["comparativo"]
    if len(CP):
        filas = [[f"<b>{e(r.unidad)}</b>", n(r.km_odo), n(r.km_fil), n(r.dif_km_pct, 1, True) + NB + "%", n(r.gasoil, 2), n(r.coef_odo, 2), n(r.coef_fil, 2),
                  n(r.delta, 2, True), e(r.categoria.capitalize())] for _, r in CP.iterrows()]
        vc = CP.categoria.value_counts().to_dict()
        S.append(("comparativo", "Filarus vs My Scania", f"""
<p class="nota">Coeficiente que daría cada unidad con el km de cada fuente sobre la misma ventana. Coincide: menos de 1. Leve: 1 a 3. Moderada: 3 a 6. Grande: más de 6.
En el mes: {vc.get('COINCIDE', 0)} coinciden, {vc.get('LEVE', 0)} leves, {vc.get('MODERADA', 0)} moderadas, {vc.get('GRANDE', 0)} grandes.</p>
""" + tabla([("Unidad", "l"), ("km odómetro", "r"), ("km Filarus", "r"), ("Dif. km", "r"), ("Gasoil L", "r"), ("Coef con odómetro", "r"), ("Coef con Filarus", "r"), ("Δ", "r"), ("Categoría", "l")], filas)))

    # 9 ── Conclusión (solo hechos, Regla 7)
    S.append(("conclusion", "Conclusión", conclusion_html(R, prev)))

    nav = "".join(f'<a href="#{pid}-{sid}">{tit}</a>' for sid, tit, _ in S)
    cuerpo = "".join(f'<section id="{pid}-{sid}"{" data-kpis=\"resumen\"" if sid == "resumen" else ""}><h2>{tit}</h2>{h}</section>' for sid, tit, h in S)
    return f"""<article class="apartado" id="{pid}" data-ap="{pid}" hidden>
<header class="aph"><h1>{mes} {anio}</h1><p>Análisis mensual de flota, ventana carga a carga. Reglas v{R['version_reglas']}.</p></header>
<nav class="subnav" aria-label="Secciones de {mes}">{nav}</nav>{cuerpo}</article>"""


def conclusion_html(R, prev):
    k, U = R["kpis"], R["unidades"]
    P = []
    P.append(("10.1 Resumen", [
        f"{k['operativas']} unidades operativas de {k['totales']} totales, {k['sin_cargas']} sin cargas. {n(k['km'])} km en las ventanas de {k['n_medibles']} unidades, "
        f"{n(k['gasoil_medible'], 2)} L de gasoil, coeficiente general {n(k['coef'], 2)} L/100 km"
        + (f" ({prev['nombre_mes']}: {n(prev['kpis']['coef'], 2)})." if prev else "."),
        f"{k['criticas']} críticas, {k['atencion']} en atención, {k['normales']} normales, {k['coef_bajo']} con coeficiente bajo y {k['investigar']} a investigar. "
        f"Urea {n(k['urea'], 2)} L, ratio {n(k['ratio_urea'], 2)} %, {k['exceso_urea']} unidades sobre {C.UREA_EXCESO:g} %."]))
    crit = U[U.estado == "CRITICO"]
    if prev is not None:
        pe = prev["unidades"].set_index("unidad").estado.to_dict()
        ae = U.set_index("unidad").estado.to_dict()
        rep = [u for u in crit.unidad if pe.get(u) == "CRITICO"]
        nue = [u for u in crit.unidad if pe.get(u) != "CRITICO"]
        dej = [f"{u} → {ETIQ.get(ae[u], ae[u]).lower()}" for u, s in pe.items() if s == "CRITICO" and u in ae and ae[u] != "CRITICO"]
        P[0][1].append(f"Críticas que repiten de {prev['nombre_mes']} ({len(rep)}): {', '.join(rep) or 'ninguna'}. Nuevas ({len(nue)}): {', '.join(nue) or 'ninguna'}. "
                       f"Dejan de ser críticas ({len(dej)}): {', '.join(dej) or 'ninguna'}.")
    # 10.2 hallazgos: un hecho por unidad crítica, con todo lo que el mes muestra de ella
    CR = R["consumo_real"].set_index("unidad") if len(R["consumo_real"]) else None
    CA = R["conc_agregado"].set_index("unidad") if len(R["conc_agregado"]) else None
    SS = R["subas_sin_carga"]
    A = R["atribucion"]
    hall = []
    for _, r in crit.iterrows():
        ch = A[A.unidad == r.unidad].sort_values("litros", ascending=False)
        quien = (ch.chofer.iloc[0].title() if ch.part.iloc[0] > 0.5 else f"compartida entre {len(ch)} choferes") if len(ch) else ""
        t = f"<b>{e(r.unidad)}</b>, {e(quien)}. Coeficiente de ventana {n(r.coef, 2)} contra ideal {n(r.ideal, 1)} ({n(r.dif, 2, True)}), {n(r.gasoil, 2)} L en {n(r.km)} km por {e(r.fuente)}."
        if CR is not None and r.unidad in CR.index and not CR.loc[r.unidad].fuera:
            c = CR.loc[r.unidad]
            t += f" El motor quemó {n(c['real'], 2)} L/100 km según My Scania; en el mes calendario compró {n(abs(c.dif_l), 2)} L {'más' if c.dif_l > 0 else 'menos'} de lo que quemó."
        if CA is not None and r.unidad in CA.index:
            c = CA.loc[r.unidad]
            t += f" Tarjeta contra malla: {n(c.desv_pct, 1, True)} % ({n(c.tarjeta, 2)} L de tarjeta, {n(c.malla, 2)} L de subas)" + (f", {int(c.sin_suba)} carga(s) sin suba." if c.sin_suba else ".")
        if len(SS):
            s = SS[SS.unidad == r.unidad]
            if len(s):
                t += f" {len(s)} suba(s) de tanque sin carga de tarjeta: " + "; ".join(f"{f(x.fecha)} {e(x.niveles)} en {e(x.lugar.split(',')[0])}" for _, x in s.iterrows()) + "."
        if prev is not None and prev["unidades"].set_index("unidad").estado.to_dict().get(r.unidad) == "CRITICO":
            t += f" También fue crítica en {prev['nombre_mes']}."
        hall.append(t)
    P.append(("10.2 Hallazgos críticos del mes", hall or ["Sin unidades críticas."]))
    # 10.3 patrones
    pat = []
    if CA is not None:
        R_ = R["conc_agregado"]
        for fam, cap in C.CAPACIDAD.items():
            g = R_[R_.cap_nominal == cap]
            if len(g) >= 3:
                pat.append(f"P{fam}: {len(g)} unidades con malla, desvío tarjeta vs malla entre {n(g.desv_pct.min(), 1, True)} % y {n(g.desv_pct.max(), 1, True)} %; "
                           f"capacidad implícita del grupo {n(g.tarjeta.sum() / (g.malla.sum() / cap), 0)} L contra {n(cap)} nominales.")
    if len(SS):
        lug = SS.assign(l=SS.lugar.str.split(",").str[0]).groupby("l").agg(nn=("unidad", "size"), us=("unidad", lambda s: ", ".join(sorted(set(s)))))
        for l, x in lug[lug.nn >= 2].sort_values("nn", ascending=False).head(5).iterrows():
            pat.append(f"Subas sin carga de tarjeta en {e(l)}: {x.nn} ({e(x.us)}).")
        ext = SS[SS.lugar.str.contains("Chile", na=False)]
        if len(ext):
            pat.append(f"Subas de tanque en Chile sin carga de tarjeta YPF: {len(ext)} ({', '.join(sorted(ext.unidad.unique()))}), ≈ {n(ext.suba_l.sum())} L. En esas unidades el coeficiente de ventana queda por debajo del consumo real.")
    bajos = U[U.estado == "COEF BAJO"]
    if len(bajos):
        pat.append("Coeficiente bajo: " + ", ".join(f"{r.unidad} ({n(r.coef, 2)}, {r.n_cargas} carga{'s' if r.n_cargas != 1 else ''})" for _, r in bajos.iterrows()) + ".")
    P.append(("10.3 Patrones", pat or ["Sin patrones para informar."]))
    CH = R["choferes"]
    med = CH[CH.dif.notna()]
    P.append(("10.4 Choferes", [
        "Mayor diferencia contra el ideal: " + "; ".join(f"{e(r.chofer)} {n(r.dif, 2, True)} ({e(r.unidades)})" for _, r in med.head(5).iterrows()) + ".",
        "Menor: " + "; ".join(f"{e(r.chofer)} {n(r.dif, 2, True)} ({e(r.unidades)})" for _, r in med.tail(3).iterrows()) + ".",
    ] + ([("Cargaron solo en unidades a investigar: " + "; ".join(f"{e(r.chofer)} ({e(r.unidades)})" for _, r in CH[CH.dif.isna()].iterrows()) + ".")] if CH.dif.isna().any() else [])))
    inv = U[U.estado == "A INVESTIGAR"]
    obs = [f"A investigar ({len(inv)}): " + " ".join(f"<b>{e(r.unidad)}</b>: {e(r.motivo)}" + ("" if str(r.motivo).endswith(".") else ".") for _, r in inv.iterrows())] if len(inv) else []
    nc = crit[~crit.tramos_cierra.astype(bool)] if len(crit) else crit
    obs.append(f"Cierre de tramos: en {len(crit) - len(nc)} de las {len(crit)} críticas la suma de tramos es igual al km de la ventana."
               + ("".join(f" {r.unidad}: diferencia de {n(r.km - r.tramos_suma)} km." for _, r in nc.iterrows())))
    cero = R["tramos"][(R["tramos"].km == 0) & R["tramos"].unidad.isin(crit.unidad)]
    for _, x in cero.iterrows():
        obs.append(f"{x.unidad}: tramo de 0 km el {f(x.hasta, False)}. {e(x.nota)}")
    for a, b in C.PARES_GEMELOS:
        if a in set(U.unidad) or b in set(U.unidad):
            obs.append(f"{a} / {b}: telemetría cruzada; medidas con Filarus y leídas como par.")
    P.append(("10.5 Observaciones operativas", obs))
    if k["precio_gasoil"]:
        P.append(("10.6 Costos", [
            f"Precio promedio de gasoil del archivo YPF: $ {n(k['precio_gasoil'], 2)} por litro (precio YER, rango $ {n(k['precio_min'], 2)} a $ {n(k['precio_max'], 2)}).",
            f"Litros por encima del ideal en las críticas: {n(k['sobre_ideal_criticas'], 1)} L ≈ $ {n(k['costo_criticas'])}. Críticas más atención: {n(k['sobre_ideal_crit_atencion'], 1)} L ≈ $ {n(k['costo_crit_atencion'])}."]))
    pend = []
    sinid = U[(U.estado == "A INVESTIGAR") & U.motivo.str.contains("sin ideal", na=False)]
    for _, r in sinid.iterrows():
        pend.append(f"Ideal de {e(r.modelo)} ({r.unidad}).")
    pend.append(f"Confirmación del ideal Mercedes Benz {n(C.IDEAL_MB, 1)}.")
    pend.append("Capacidad real de tanque por modelo (Regla 13).")
    if len(R["conc_detalle"]) and R["conc_detalle"].sin_patente.any():
        pend.append("Patente de los equipos de My Scania sin matrícula cargada.")
    pend.append("Programación YPF + ACERO del mes, para cruzar la atribución de choferes.")
    if not k["hay_malla_anterior"]:
        pend.append("Informe de combustible (malla) del mes anterior: sin ese archivo el odómetro de arranque no se puede leer.")
    P.append(("10.7 Información pendiente", pend))
    notas = (R.get("ajustes") or {}).get("notas_analista") or []
    if notas:
        P.append(("Notas del analista", [e(x) for x in notas]))
    return '<p class="nota">Solo hechos (Regla 7). Las decisiones las toma la dirección.</p>' + "".join(
        f'<h3>{t}</h3><ul class="hechos">{"".join(f"<li>{x}</li>" for x in items)}</ul>' for t, items in P)


# ───────────────────────── evaluación anual ─────────────────────────
def svg_linea(etqs, vals, alto=180, unidad=""):
    """Línea estática de una sola serie con etiqueta directa en cada punto (son pocos meses)."""
    W, Hh, ml, mr, mt, mb = 640, alto, 46, 20, 22, 30
    vs = [v for v in vals if v is not None]
    if not vs:
        return ""
    lo, hi = min(vs), max(vs)
    pad = (hi - lo) * 0.35 or 0.5
    lo, hi = lo - pad, hi + pad
    nx = max(len(vals) - 1, 1)
    X = lambda i: ml + 40 + (W - ml - mr - 80) * (i / nx if len(vals) > 1 else 0.5)
    Y = lambda v: mt + (Hh - mt - mb) * (1 - (v - lo) / (hi - lo))
    g = []
    for j in range(4):
        v = lo + (hi - lo) * j / 3
        g.append(f'<line x1="{ml}" x2="{W - mr}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="#e3e6e3"/>'
                 f'<text x="{ml - 6}" y="{Y(v) + 4:.1f}" text-anchor="end" class="ax">{n(v, 1)}</text>')
    pts = [(X(i), Y(v), v) for i, v in enumerate(vals) if v is not None]
    path = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y, _ in pts)
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="#1B5E20" stroke="#fff" stroke-width="2"><title>{n(v, 2)} {unidad}</title></circle>'
                   f'<text x="{x:.1f}" y="{y - 10:.1f}" text-anchor="middle" class="dl">{n(v, 2)}</text>' for x, y, v in pts)
    xl = "".join(f'<text x="{X(i):.1f}" y="{Hh - 8}" text-anchor="middle" class="ax">{e(t)}</text>' for i, t in enumerate(etqs))
    return f'<svg class="chart" viewBox="0 0 {W} {Hh}" role="img">{"".join(g)}<path d="{path}" fill="none" stroke="#1B5E20" stroke-width="2"/>{dots}{xl}</svg>'


def svg_estados(etqs, conteos, alto=200):
    """Barras apiladas por estado, una por mes, con separador de 2 px y el total arriba."""
    W, ml, mr, mt, mb = 640, 46, 20, 22, 30
    mx = max(sum(c.values()) for c in conteos) or 1
    bw = min(64, (W - ml - mr) / max(len(conteos), 1) * 0.55)
    out = []
    for j in range(5):
        v = mx * j / 4
        y = mt + (alto - mt - mb) * (1 - v / mx)
        out.append(f'<line x1="{ml}" x2="{W - mr}" y1="{y:.1f}" y2="{y:.1f}" stroke="#e3e6e3"/><text x="{ml - 6}" y="{y + 4:.1f}" text-anchor="end" class="ax">{n(v)}</text>')
    for i, c in enumerate(conteos):
        cx = ml + (W - ml - mr) * ((i + 0.5) / len(conteos))
        y = alto - mb
        for est in ORDEN:
            v = c.get(est, 0)
            if not v:
                continue
            h = (alto - mt - mb) * v / mx
            y -= h
            out.append(f'<rect x="{cx - bw / 2:.1f}" y="{y + 1:.1f}" width="{bw:.1f}" height="{max(h - 2, 1):.1f}" fill="{COL[est]}"><title>{etqs[i]}: {v} {ETIQ[est].lower()}</title></rect>')
            if h > 14:
                out.append(f'<text x="{cx:.1f}" y="{y + h / 2 + 4:.1f}" text-anchor="middle" class="in">{v}</text>')
        out.append(f'<text x="{cx:.1f}" y="{y - 5:.1f}" text-anchor="middle" class="dl">{sum(c.values())}</text>')
        out.append(f'<text x="{cx:.1f}" y="{alto - 8}" text-anchor="middle" class="ax">{e(etqs[i])}</text>')
    ley = "".join(f'<div class="le"><i style="background:{COL[x]}"></i>{ETIQ[x]}</div>' for x in ORDEN)
    return f'<svg class="chart" viewBox="0 0 {W} {alto}" role="img">{"".join(out)}</svg><div class="ley">{ley}</div>'


def celda_estado(r):
    if r is None:
        return '<td class="r vac">—</td>'
    col = COL.get(r["estado"], "#777")
    txt = n(r["dif"], 2, True) if not nulo(r["dif"]) and r["estado"] != "A INVESTIGAR" else ETIQ[r["estado"]].lower()
    return f'<td class="r mz" style="box-shadow:inset 4px 0 0 {col}" title="{ETIQ[r["estado"]]}">{txt}</td>'


def anual_html(meses, anio, faltantes):
    """meses: lista de resultados R ordenados por mes."""
    etq = [m["nombre_mes"][:3].capitalize() for m in meses]
    nombres = [m["nombre_mes"].capitalize() for m in meses]
    pid = f"a{anio}"
    S = []
    # 1 ── Panorama del año
    km = sum(m["kpis"]["km"] for m in meses)
    gas = sum(m["kpis"]["gasoil_medible"] for m in meses)
    gas_op = sum(m["kpis"]["gasoil_operativa"] for m in meses)
    urea = sum(m["kpis"]["urea"] for m in meses)
    sob = sum(m["kpis"]["sobre_ideal_criticas"] for m in meses)
    costo = sum((m["kpis"]["costo_criticas"] or 0) for m in meses)
    sob2 = sum(m["kpis"]["sobre_ideal_crit_atencion"] for m in meses)
    costo2 = sum((m["kpis"]["costo_crit_atencion"] or 0) for m in meses)
    imp = sum(m["kpis"]["importe_gasoil"] for m in meses)
    filas = []
    for m in meses:
        k = m["kpis"]
        filas.append([f"<b>{m['nombre_mes'].capitalize()}</b>", n(k["km"]), n(k["gasoil_medible"], 2), n(k["coef"], 2), n(k["urea"], 2), n(k["ratio_urea"], 2) + NB + "%",
                      f"{k['operativas']} de {k['totales']}", n(k["criticas"]), n(k["atencion"]), n(k["normales"]), n(k["coef_bajo"]), n(k["investigar"]),
                      "$" + NB + n(k["precio_gasoil"], 2), n(k["sobre_ideal_criticas"], 1), "$" + NB + n(k["costo_criticas"])])
    filas.append({"cls": "tot", "c": [f"Acumulado ({len(meses)} meses)", n(km), n(gas, 2), n(gas * 100 / km, 2), n(urea, 2), n(urea / gas_op * 100, 2) + NB + "%",
                                      "", "", "", "", "", "", "$" + NB + n(imp / gas_op, 2), n(sob, 1), "$" + NB + n(costo)]})
    t_pan = tabla([("Mes", "l"), ("km", "r"), ("Gasoil L", "r"), ("Coef", "r"), ("Urea L", "r"), ("Urea/gasoil", "r"), ("Operativas", "r"), ("Crít.", "r"), ("Atenc.", "r"),
                   ("Norm.", "r"), ("Bajo", "r"), ("Invest.", "r"), ("Precio gasoil", "r"), ("L sobre ideal (crít.)", "r"), ("Costo estimado", "r")], filas)
    falt = ""
    if faltantes:
        falt = f'<p class="aviso">Meses de {anio} todavía sin cargar en el software: {", ".join(faltantes)}. La evaluación cubre solo los meses cargados y se completa a medida que se suman.</p>'
    S.append(("panorama", "Panorama del año", f"""
<p class="lead">{len(meses)} meses cargados: {', '.join(nombres)}. {n(km)} km y {n(gas, 2)} L de gasoil en las ventanas medibles:
coeficiente acumulado <strong>{n(gas * 100 / km, 2)} L/100 km</strong>.</p>{falt}
<div class="dos"><figure><figcaption>Coeficiente general por mes, L/100 km</figcaption>{svg_linea(etq, [m['kpis']['coef'] for m in meses], unidad='L/100 km')}</figure>
<figure><figcaption>Unidades operativas por estado, por mes</figcaption>{svg_estados(etq, [{x: int((m['unidades'].estado == x).sum()) for x in ORDEN} for m in meses])}</figure></div>
{t_pan}
<p class="nota">Costo estimado = litros por encima del ideal en las unidades críticas × precio promedio YER del mes. Sumando también las unidades en atención: {n(sob2, 1)} L ≈ $ {n(costo2)} en los meses cargados.</p>"""))

    # 2 ── Evaluación por unidad
    reg = {}
    for i, m in enumerate(meses):
        for _, r in m["unidades"].iterrows():
            reg.setdefault(r.unidad, {"modelo": r.modelo, "ideal": r.ideal, "m": [None] * len(meses)})
            reg[r.unidad]["m"][i] = {"estado": r.estado, "dif": r.dif, "coef": r.coef, "km": r.km if r.km_confiable and r.estado != "A INVESTIGAR" else None,
                                     "gasoil": r.gasoil if r.km_confiable and r.estado != "A INVESTIGAR" else None}
            reg[r.unidad]["modelo"], reg[r.unidad]["ideal"] = r.modelo, r.ideal
    filas_u = []
    for u, d in reg.items():
        med = [x for x in d["m"] if x and x["km"]]
        kmu = sum(x["km"] for x in med)
        gu = sum(x["gasoil"] for x in med)
        coef = gu * 100 / kmu if kmu else None
        dif = coef - d["ideal"] if coef is not None and d["ideal"] else None
        ncrit = sum(1 for x in d["m"] if x and x["estado"] == "CRITICO")
        est = None
        if dif is not None:
            dr = round(dif, 2)
            est = "CRITICO" if dr > C.UMBRAL_CRITICO else "ATENCION" if dr > C.UMBRAL_ATENCION else "COEF BAJO" if dr < C.UMBRAL_COEF_BAJO else "NORMAL"
        sobre = (gu - d["ideal"] * kmu / 100) if kmu and d["ideal"] else None
        filas_u.append({"u": u, "d": d, "km": kmu, "gas": gu, "coef": coef, "dif": dif, "ncrit": ncrit, "est": est, "sobre": sobre, "nmed": len(med)})
    filas_u.sort(key=lambda x: (x["dif"] is None, -(x["dif"] or 0)))
    cols = [("Unidad", "l"), ("Modelo", "l")] + [(t, "r") for t in etq] + [("Meses crítica", "r"), ("km acum.", "r"), ("Gasoil acum. L", "r"), ("Coef acum.", "r"), ("Ideal", "r"), ("Dif", "r"), ("", "l"), ("Evaluación", "l"), ("L sobre ideal", "r")]
    th = "".join(f'<th class="{a}">{t}</th>' for t, a in cols)
    trs = []
    for x in filas_u:
        d = x["d"]
        trs.append(f'<tr><td class="l"><b>{e(x["u"])}</b></td><td class="l">{e(d["modelo"])}</td>' + "".join(celda_estado(c) for c in d["m"])
                   + f'<td class="r">{x["ncrit"] or ""}</td><td class="r">{n(x["km"]) if x["km"] else "—"}</td><td class="r">{n(x["gas"], 2) if x["km"] else "—"}</td>'
                   f'<td class="r">{n(x["coef"], 2)}</td><td class="r">{n(d["ideal"], 1)}</td><td class="r">{n(x["dif"], 2, True) if x["dif"] is not None else "—"}</td>'
                   f'<td class="l">{barra_dif(x["dif"])}</td><td class="l">{badge(x["est"]) if x["est"] else badge("A INVESTIGAR")}</td>'
                   f'<td class="r">{n(x["sobre"], 1, True) if x["sobre"] is not None else "—"}</td></tr>')
    t_u = f'<div class="tw"><table class="unid"><thead><tr>{th}</tr></thead><tbody>{"".join(trs)}</tbody></table></div>'
    siempre = [x["u"] for x in filas_u if x["ncrit"] == len(meses) and len(meses) > 1]
    S.append(("unidades", "Evaluación por unidad", f"""
<p class="nota">Cada mes muestra la diferencia de esa unidad contra su ideal; el color del borde es el estado de ese mes. La evaluación del año usa el acumulado: todos los litros y todos los km
de las ventanas medibles de los meses cargados, contra el mismo ideal y con los mismos cortes del reporte mensual.
{('Críticas en todos los meses cargados (' + str(len(siempre)) + '): ' + ', '.join(siempre) + '.') if siempre else ''}</p>{t_u}"""))

    # 3 ── Evaluación por chofer
    regc = {}
    for i, m in enumerate(meses):
        A = m["atribucion"]
        for ch, g in A[A.medible].groupby("chofer"):
            d = regc.setdefault(ch, {"km": 0.0, "l": 0.0, "idkm": 0.0, "m": [None] * len(meses), "us": set()})
            kmc, lc = g.km.sum(), g.litros.sum()
            d["km"] += kmc; d["l"] += lc; d["idkm"] += (g.ideal * g.km).sum(); d["us"].update(g.unidad)
            d["m"][i] = lc * 100 / kmc - (g.ideal * g.km).sum() / kmc if kmc else None
    fc, fcd = [], []
    for ch, d in regc.items():
        if d["km"] <= 0:
            continue
        coef, ideal = d["l"] * 100 / d["km"], d["idkm"] / d["km"]
        fcd.append({"ch": ch, "dif": coef - ideal, "km": d["km"], "l": d["l"], "coef": coef, "ideal": ideal, "m": d["m"], "us": sorted(d["us"])})
        fc.append((coef - ideal, [f"<b>{e(ch)}</b>", e(", ".join(sorted(d["us"])))] + [n(x, 2, True) if x is not None else "—" for x in d["m"]]
                   + [n(sum(1 for x in d["m"] if x is not None)), n(d["km"]), n(d["l"], 2), n(coef, 2), n(ideal, 2), n(coef - ideal, 2, True), barra_dif(coef - ideal)]))
    fc.sort(key=lambda x: -x[0])
    S.append(("choferes", "Evaluación por chofer", f"""
<p class="nota">Diferencia contra el ideal de cada chofer por mes y acumulada, con los km prorrateados por litros cargados. Solo entran los km de unidades medibles.</p>
""" + tabla([("Chofer", "l"), ("Unidades del año", "l")] + [(t, "r") for t in etq] + [("Meses", "r"), ("km acum.", "r"), ("Gasoil acum. L", "r"), ("Coef", "r"), ("Ideal pond.", "r"), ("Dif", "r"), ("", "l")],
            [x[1] for x in fc], "unid")))

    # 4 ── Urea
    regu = {}
    for i, m in enumerate(meses):
        for _, r in m["unidades"].iterrows():
            if r.gasoil > 0:
                d = regu.setdefault(r.unidad, {"g": 0.0, "u": 0.0, "m": [None] * len(meses), "modelo": r.modelo})
                d["g"] += r.gasoil; d["u"] += r.urea; d["m"][i] = r.ratio_urea
    fu = []
    for u, d in regu.items():
        ratio = d["u"] / d["g"] * 100
        nex = sum(1 for x in d["m"] if x is not None and x > C.UREA_EXCESO)
        if ratio > C.UREA_EXCESO or nex:
            fu.append((ratio, [f"<b>{e(u)}</b>", e(d["modelo"])] + [(n(x, 2) + NB + "%") if x is not None else "—" for x in d["m"]] + [n(nex), n(d["g"], 2), n(d["u"], 2), n(ratio, 2) + NB + "%"]))
    fu.sort(key=lambda x: -x[0])
    S.append(("urea", "Urea", f"""
<p class="nota">Unidades con ratio urea / gasoil por encima de {C.UREA_EXCESO:g} % en algún mes o en el acumulado. Ratio de la flota en los meses cargados: {n(urea / gas_op * 100, 2)} %.</p>
""" + tabla([("Unidad", "l"), ("Modelo", "l")] + [(t, "r") for t in etq] + [("Meses en exceso", "r"), ("Gasoil acum. L", "r"), ("Urea acum. L", "r"), ("Ratio acum.", "r")], [x[1] for x in fu])))

    # 5 ── Tarjeta vs malla
    regm = {}
    for i, m in enumerate(meses):
        CA = m["conc_agregado"]
        for _, r in (CA.iterrows() if len(CA) else []):
            d = regm.setdefault(r.unidad, {"t": 0.0, "m_": 0.0, "m": [None] * len(meses), "modelo": r.modelo, "ss": 0})
            d["t"] += r.tarjeta; d["m_"] += r.malla; d["m"][i] = r.desv_pct
        SS = m["subas_sin_carga"]
        for u, c in (SS.unidad.value_counts().items() if len(SS) else []):
            regm.setdefault(u, {"t": 0.0, "m_": 0.0, "m": [None] * len(meses), "modelo": "", "ss": 0})["ss"] += int(c)
    fm = []
    for u, d in regm.items():
        if d["m_"] > 0:
            dv = (d["t"] - d["m_"]) / d["m_"] * 100
            fm.append((dv, [f"<b>{e(u)}</b>", e(d["modelo"])] + [(n(x, 1, True) + NB + "%") if x is not None else "—" for x in d["m"]]
                       + [n(d["t"], 2), n(d["m_"], 2), n(d["t"] - d["m_"], 2, True), n(dv, 1, True) + NB + "%", n(d["ss"]) if d["ss"] else ""]))
    fm.sort(key=lambda x: -x[0])
    S.append(("malla", "Tarjeta vs malla", f"""
<p class="nota">Desvío de los litros de tarjeta contra las subas de tanque de la malla, por mes y acumulado, con las subas de tanque sin carga de tarjeta que acumula cada unidad.
Vale la advertencia de la Regla 13: con la capacidad nominal las P420 dan negativo por el divisor, no por la unidad.</p>
""" + tabla([("Unidad", "l"), ("Modelo", "l")] + [(t, "r") for t in etq] + [("Tarjeta acum. L", "r"), ("Malla acum. L", "r"), ("Diferencia L", "r"), ("Desvío acum.", "r"), ("Subas sin carga", "r")], [x[1] for x in fm])))

    S.insert(0, ("resumen", "Resumen del año", resumen_anual(meses, filas_u, fcd, regu, urea / gas_op * 100)))
    nav = "".join(f'<a href="#{pid}-{sid}">{tit}</a>' for sid, tit, _ in S)
    cuerpo = "".join(f'<section id="{pid}-{sid}"><h2>{tit}</h2>{h}</section>' for sid, tit, h in S)
    return f"""<article class="apartado" id="{pid}" data-ap="{pid}" hidden>
<header class="aph"><h1>Evaluación {anio}</h1><p>Lectura del año con los meses cargados. Mismas reglas y mismos cortes que el reporte mensual.</p></header>
<nav class="subnav" aria-label="Secciones de la evaluación">{nav}</nav>{cuerpo}</article>"""


def resumen_anual(meses, filas_u, fcd, regu, ratio_urea):
    """Resumen escrito de la evaluación: se arma solo con los meses cargados y se actualiza al sumar un mes.
    Solo hechos (Regla 7): quién lidera, quién cierra, y qué mejoró o empeoró."""
    nm = len(meses)
    minkm = C.EVAL_MIN_KM_MES * nm
    ult = meses[-1]
    nombres = [m["nombre_mes"] for m in meses]
    periodo = nombres[0] if nm == 1 else f"{nombres[0]} a {nombres[-1]}"
    B = []  # bloques (titulo, [parrafos])

    def tarj(titulo, nombre, linea, detalle):
        return f'<div class="pod"><div class="pt">{titulo}</div><div class="pn">{nombre}</div><div class="pl">{linea}</div><div class="pd">{detalle}</div></div>'

    # choferes
    ch = sorted([x for x in fcd if x["km"] >= minkm], key=lambda x: x["dif"])
    us = sorted([x for x in filas_u if x["dif"] is not None and x["km"] >= minkm], key=lambda x: x["dif"])
    us_ok = [x for x in us if x["est"] != "COEF BAJO"]
    pods = []
    ch_ok = [x for x in ch if round(x["dif"], 2) >= C.UMBRAL_COEF_BAJO]
    if ch_ok:
        a, z = ch_ok[0], ch[-1]
        pods.append(tarj("Mejor chofer hasta ahora", e(a["ch"].title()), f"{n(a['dif'], 2, True)} contra su ideal",
                         f"{n(a['coef'], 2)} L/100 km sobre {n(a['km'])} km, ideal {n(a['ideal'], 2)}. Unidades: {e(', '.join(a['us']))}."))
        pods.append(tarj("Chofer con mayor consumo", e(z["ch"].title()), f"{n(z['dif'], 2, True)} contra su ideal",
                         f"{n(z['coef'], 2)} L/100 km sobre {n(z['km'])} km, ideal {n(z['ideal'], 2)}. Unidades: {e(', '.join(z['us']))}."))
    if us_ok:
        a, z = us_ok[0], us[-1]
        pods.append(tarj("Mejor unidad hasta ahora", e(a["u"]), f"{n(a['dif'], 2, True)} contra su ideal",
                         f"{e(a['d']['modelo'])}. {n(a['coef'], 2)} L/100 km sobre {n(a['km'])} km, ideal {n(a['d']['ideal'], 1)}."))
        pods.append(tarj("Unidad con mayor consumo", e(z["u"]), f"{n(z['dif'], 2, True)} contra su ideal",
                         f"{e(z['d']['modelo'])}. {n(z['coef'], 2)} L/100 km sobre {n(z['km'])} km, ideal {n(z['d']['ideal'], 1)}. "
                         f"{n(z['sobre'], 1)} L por encima del ideal; crítica en {z['ncrit']} de {nm} meses."))
    out = f'<p class="lead">Lectura de {periodo} con {nm} {"mes cargado" if nm == 1 else "meses cargados"}. Este resumen se vuelve a escribir solo cada vez que se suma un mes.</p>'
    out += f'<div class="pods">{"".join(pods)}</div>'
    out += (f'<p class="nota">Posiciones por diferencia acumulada contra el ideal (litros y km de todas las ventanas medibles). Entran choferes y unidades con al menos '
            f'{n(minkm)} km acumulados ({n(C.EVAL_MIN_KM_MES)} por mes cargado). El mejor chofer y la mejor unidad se eligen entre los que no quedaron con coeficiente bajo '
            f'(diferencia menor a {n(C.UMBRAL_COEF_BAJO, 0)}): un coeficiente bajo puede venir de cargas hechas fuera de la tarjeta YPF.</p>')

    def podio(lst, clave, top=3):
        return "; ".join(f"{e(clave(x))} ({n(x['dif'], 2, True)})" for x in lst[:top])

    hechos = []
    if len(ch) >= 6:
        hechos.append("Choferes con menor diferencia: " + podio(ch_ok, lambda x: x["ch"].title()) + ". Con mayor diferencia: " + podio(ch[::-1], lambda x: x["ch"].title()) + ".")
    if len(us_ok) >= 6:
        hechos.append("Unidades con menor diferencia: " + podio(us_ok, lambda x: x["u"]) + ". Con mayor diferencia: " + podio(us[::-1], lambda x: x["u"]) + ".")
    bajos = [x for x in us if x["est"] == "COEF BAJO"]
    if bajos:
        hechos.append("Unidades con coeficiente bajo en el acumulado, fuera de la elección: " + ", ".join(f"{x['u']} ({n(x['dif'], 2, True)})" for x in bajos) + ".")
    chb = [x for x in ch if x not in ch_ok]
    if chb:
        hechos.append("Choferes con coeficiente bajo en el acumulado, fuera de la elección: " + ", ".join(f"{e(x['ch'].title())} ({n(x['dif'], 2, True)}, {', '.join(x['us'])})" for x in chb) + ".")
    crit_ac = [x for x in us if x["est"] == "CRITICO"]
    siempre = [x["u"] for x in filas_u if x["ncrit"] == nm]
    hechos.append(f"{len(crit_ac)} unidades quedan críticas en el acumulado" + (f"; {len(siempre)} fueron críticas en los {nm} meses: {', '.join(siempre)}." if nm > 1 and siempre else "."))
    out += f'<h3>Posiciones</h3><ul class="hechos">{"".join(f"<li>{x}</li>" for x in hechos)}</ul>'

    # resultados: último mes contra el anterior
    if nm >= 2:
        prev = meses[-2]
        ka, kp = ult["kpis"], prev["kpis"]
        ma, mp = ult["nombre_mes"], prev["nombre_mes"]

        def cmp_(txt, va, vp, dec, menor_es_mejor=True, unidad="", pref=""):
            d = va - vp
            T = txt[0].upper() + txt[1:]
            if abs(d) < 10 ** -dec / 2:
                return f"<b>{T}</b>: sin cambio, {pref}{n(va, dec)}{unidad}."
            mejora = (d < 0) == menor_es_mejor
            return f"<b>{T}</b>: {'mejoró' if mejora else 'empeoró'}, de {pref}{n(vp, dec)}{unidad} en {mp} a {pref}{n(va, dec)}{unidad} en {ma} ({n(d, dec, True)})."
        res = [
            cmp_("coeficiente general de la flota", ka["coef"], kp["coef"], 2, unidad=" L/100 km"),
            cmp_("unidades críticas", ka["criticas"], kp["criticas"], 0),
            cmp_("unidades en atención", ka["atencion"], kp["atencion"], 0),
            cmp_("unidades normales", ka["normales"], kp["normales"], 0, menor_es_mejor=False),
            cmp_("litros por encima del ideal en las críticas", ka["sobre_ideal_criticas"], kp["sobre_ideal_criticas"], 1, unidad=" L"),
            cmp_("unidades con exceso de urea", ka["exceso_urea"], kp["exceso_urea"], 0),
        ]
        res.append(f"Actividad: {n(ka['km'])} km en {ma} contra {n(kp['km'])} en {mp} ({n((ka['km'] / kp['km'] - 1) * 100, 1, True)} %); "
                   f"gasoil {n(ka['gasoil_medible'], 2)} L contra {n(kp['gasoil_medible'], 2)} L ({n((ka['gasoil_medible'] / kp['gasoil_medible'] - 1) * 100, 1, True)} %). "
                   f"Ratio urea / gasoil: {n(ka['ratio_urea'], 2)} % contra {n(kp['ratio_urea'], 2)} %. "
                   f"Precio promedio del gasoil: $ {n(ka['precio_gasoil'], 2)} contra $ {n(kp['precio_gasoil'], 2)}.")
        out += f'<h3>Resultados: {ma} contra {mp}</h3><ul class="hechos">{"".join(f"<li>{x}</li>" for x in res)}</ul>'

        # movimientos de unidades y choferes entre los dos últimos meses
        mov = []
        for x in filas_u:
            a, p = x["d"]["m"][-1], x["d"]["m"][-2]
            if a and p and a["km"] and p["km"] and a["dif"] is not None and p["dif"] is not None:
                mov.append((a["dif"] - p["dif"], x["u"], p, a))
        mov.sort()
        mv = []
        if mov:
            mv.append("Unidades que más mejoraron: " + "; ".join(f"{u} (de {n(p['dif'], 2, True)} a {n(a['dif'], 2, True)})" for d, u, p, a in mov[:5] if d < 0) + ".")
            mv.append("Unidades que más empeoraron: " + "; ".join(f"{u} (de {n(p['dif'], 2, True)} a {n(a['dif'], 2, True)})" for d, u, p, a in mov[::-1][:5] if d > 0) + ".")
            sal = [u for d, u, p, a in mov if p["estado"] == "CRITICO" and a["estado"] != "CRITICO"]
            ent = [u for d, u, p, a in mov if p["estado"] != "CRITICO" and a["estado"] == "CRITICO"]
            mv.append(f"Dejaron de ser críticas ({len(sal)}): {', '.join(sal) or 'ninguna'}. Pasaron a críticas ({len(ent)}): {', '.join(ent) or 'ninguna'}.")
        movc = sorted([(x["m"][-1] - x["m"][-2], x) for x in fcd if x["m"][-1] is not None and x["m"][-2] is not None and x["km"] >= minkm], key=lambda t: t[0])
        if movc:
            mv.append("Choferes que más mejoraron: " + "; ".join(f"{e(x['ch'].title())} (de {n(x['m'][-2], 2, True)} a {n(x['m'][-1], 2, True)})" for d, x in movc[:3] if d < 0) + ".")
            mv.append("Choferes que más empeoraron: " + "; ".join(f"{e(x['ch'].title())} (de {n(x['m'][-2], 2, True)} a {n(x['m'][-1], 2, True)})" for d, x in movc[::-1][:3] if d > 0) + ".")
        out += f'<h3>Quién se movió</h3><ul class="hechos">{"".join(f"<li>{x}</li>" for x in mv)}</ul>'
        if nm >= 3:
            c0, c1 = meses[0]["kpis"]["coef"], ult["kpis"]["coef"]
            mejor = min(meses, key=lambda m: m["kpis"]["coef"]); peor = max(meses, key=lambda m: m["kpis"]["coef"])
            out += (f'<h3>Tendencia del año</h3><ul class="hechos"><li>El coeficiente general pasó de {n(c0, 2)} en {nombres[0]} a {n(c1, 2)} en {nombres[-1]} ({n(c1 - c0, 2, True)}). '
                    f'Mejor mes: {mejor["nombre_mes"]} ({n(mejor["kpis"]["coef"], 2)}). Peor mes: {peor["nombre_mes"]} ({n(peor["kpis"]["coef"], 2)}).</li></ul>')
    else:
        out += '<p class="nota">Con un solo mes cargado todavía no hay comparación: los resultados de mejora o empeoramiento aparecen desde el segundo mes.</p>'
    return out
