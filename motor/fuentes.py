# -*- coding: utf-8 -*-
"""Lectura y depuración de los archivos fuente. Ningún dato se inventa: todo sale de estos archivos."""
import re
import warnings
import pandas as pd
from . import config as C

warnings.filterwarnings("ignore")


def patente(x):
    """Normaliza una patente: sin prefijo de interno (Regla 16), sin espacios ni guiones."""
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    s = re.sub(r"\(.*?\)", "", str(x))
    return re.sub(r"[^A-Za-z0-9]", "", s).upper()


def interno(x):
    m = re.match(r"\s*\((.*?)\)", str(x))
    return m.group(1).strip() if m else None


def leer_cargas(ruta):
    """Archivo de cargas de la tarjeta YPF. Devuelve todas las filas con tipo y litros convertidos."""
    df = pd.read_excel(ruta, sheet_name="ReporteConsumos", dtype=str)
    df.columns = [c.strip() for c in df.columns]
    out = pd.DataFrame({
        "fecha": pd.to_datetime(df["FECHA"], format="%d/%m/%Y %H:%M:%S"),
        "unidad": df["IDENTIFICACION TARJETA"].map(patente),
        "chofer": df["CONDUCTOR"].fillna("").str.strip().str.replace("#", "Ñ"),
        "producto": df["PRODUCTO"].str.strip(),
        "crudo": df["LITROS UNIDADES"].astype(float),
        "localidad": df["LOCALIDAD"].fillna("").str.strip(),
        "provincia": df["PROVINCIA"].fillna("").str.strip(),
        "establecimiento": df["ESTABLECIMIENTO"].fillna("").str.strip(),
        "remito": df["REMITO"].fillna("").str.strip(),
        "precio_yer": pd.to_numeric(df["PRECIO YER"], errors="coerce"),
        "importe_yer": pd.to_numeric(df["IMP TOT YER"], errors="coerce"),
        "tasa_vial": pd.to_numeric(df.get("TASA VIAL"), errors="coerce"),
    })
    out.loc[out.chofer == "", "chofer"] = "Sin ID conductor"
    out["tipo"] = "OTRO"
    out.loc[out.producto.isin(C.PRODUCTOS_GASOIL), "tipo"] = "GAS"
    out.loc[out.producto.isin(C.PRODUCTOS_UREA.keys()), "tipo"] = "UREA"
    factor = out.producto.map(C.PRODUCTOS_UREA).fillna(1.0)
    out["litros"] = out.crudo * factor
    return out.sort_values("fecha").reset_index(drop=True)


def depurar(cargas):
    """Regla 9 (pares anulatorios y negativas sueltas) + Regla 5 (excluidas) + productos no combustibles.
    Devuelve (base depurada, informe de lo descartado)."""
    df = cargas.copy()
    df["descartada"] = ""
    # Regla 9: mismo timestamp, producto y remito, litros de signo opuesto
    neg = df[df.crudo < 0]
    pares = []
    for i, r in neg.iterrows():
        cand = df[(df.fecha == r.fecha) & (df.producto == r.producto) & (df.remito == r.remito)
                  & (df.unidad == r.unidad) & (df.crudo == -r.crudo) & (df.descartada == "")]
        if len(cand):
            j = cand.index[0]
            df.loc[[i, j], "descartada"] = "par anulatorio"
            pares.append({"unidad": r.unidad, "fecha": r.fecha, "producto": r.producto,
                          "litros": abs(r.crudo), "remito": r.remito, "chofer": r.chofer})
    sueltas = df[(df.crudo < 0) & (df.descartada == "")]
    df.loc[sueltas.index, "descartada"] = "negativa suelta"
    df.loc[df.unidad.isin(C.EXCLUIDAS.keys()) & (df.descartada == ""), "descartada"] = "excluida Regla 5"
    df.loc[(df.tipo == "OTRO") & (df.descartada == ""), "descartada"] = "no combustible"
    informe = {
        "pares_anulatorios": pares,
        "negativas_sueltas": sueltas[["unidad", "fecha", "producto", "crudo"]].to_dict("records"),
        "excluidas": df[df.descartada == "excluida Regla 5"],
        "no_combustibles": df[df.descartada == "no combustible"],
    }
    base = df[df.descartada == ""].drop(columns=["descartada"]).reset_index(drop=True)
    return base, informe


def leer_filarus(ruta):
    df = pd.read_excel(ruta, sheet_name="FilarusXls", dtype=str)
    out = pd.DataFrame({
        "unidad": df["Movil"].map(patente),
        "interno": df["Movil"].map(interno),
        "dia": pd.to_datetime(df["Fecha"]).dt.normalize(),
        "km": pd.to_numeric(df["KmRecorridos"], errors="coerce").fillna(0.0),
        "marca": df["Marca"].fillna("").str.strip(),
        "modelo": df["Modelo"].fillna("").str.strip(),
        "chofer_filarus": df["Chofer"].fillna("").str.strip(),
    })
    return out


def leer_malla(ruta):
    """Informe de combustible de My Scania: eventos de repostaje con nivel de tanque y odómetro."""
    df = pd.read_excel(ruta, sheet_name="Informe", header=3, dtype=str)
    df.columns = [c.strip() for c in df.columns]
    col_odo = [c for c in df.columns if c.startswith("Lectura del cuentakil")][0]
    niveles = df["Cambios"].str.extract(r"(\d+)\s*%\s*->\s*(\d+)\s*%")
    out = pd.DataFrame({
        "equipo": df["Equipo"].str.strip(),
        "hora": pd.to_datetime(df["Hora (repostaje)"], format="%Y/%m/%d, %H:%M"),
        "odo": pd.to_numeric(df[col_odo], errors="coerce"),
        "evento": df["Evento"].str.strip(),
        "cambios": df["Cambios"].str.strip(),
        "nivel_de": pd.to_numeric(niveles[0], errors="coerce"),
        "nivel_a": pd.to_numeric(niveles[1], errors="coerce"),
        "suba": pd.to_numeric(df["Aumentar (%)"], errors="coerce"),
        "conductor": df["Conductor"].fillna("").str.strip(),
        "lugar": df["Dirección"].fillna("").str.strip(),
    })
    out = out.dropna(subset=["equipo", "hora"])
    out["unidad"] = out.equipo.map(lambda e: C.EQUIPOS_SIN_PATENTE.get(e, patente(e)))
    out["sin_patente"] = out.equipo.isin(C.EQUIPOS_SIN_PATENTE.keys())
    return out.sort_values(["unidad", "hora"]).reset_index(drop=True)


def leer_resumen(ruta):
    """Resumen de rendimientos de My Scania (mes calendario)."""
    df = pd.read_excel(ruta, sheet_name="Informe", header=3, dtype=str)
    df.columns = [c.strip() for c in df.columns]
    def num(col):
        return pd.to_numeric(df[col], errors="coerce")
    out = pd.DataFrame({
        "equipo": df["Número de matrícula"].str.strip(),
        "km": num("Distancia recorrida (km)"),
        "motor_l": num("Consumo combustible líquido (litros)"),
        "motor_coef": num("Consumo combustible líquido (l/100 km)"),
        "reductor_l": num("Reductor (litros)"),
        "odo_fin": num("Lectura del cuentakilómetros (km)"),
        "modelo_scania": df["Información del equipo (modelo)"].fillna("").str.strip(),
        "ralenti_hm": df["Ralentí (h:m)"],
        "ralenti_pct": num("Ralentí (% del tiempo de funcionamiento del motor)"),
        "ralenti_l": num("Consumo combustible líquido: ralentí sin toma de fuerza (litros)"),
        "motor_hm": df["Tiempo de funcionamiento del motor (h:m)"],
        "driver_support": num("Scania Driver Support (puntuación media en %)"),
        "vel_media": num("Velocidad de conducción media  (km/h)") if "Velocidad de conducción media  (km/h)" in df.columns else None,
    })
    out = out[out.equipo.notna() & (out.equipo != "Total")]
    out["unidad"] = out.equipo.map(lambda e: C.EQUIPOS_SIN_PATENTE.get(e, patente(e)))
    return out.reset_index(drop=True)
