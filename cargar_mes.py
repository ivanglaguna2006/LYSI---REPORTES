# -*- coding: utf-8 -*-
"""Carga un mes en LYSI Reportes desde la línea de comandos, igual que la pantalla de Administración.

  python3 cargar_mes.py 2026-10 <carpeta_con_los_archivos>            -> calcula y muestra el control. NO publica.
  python3 cargar_mes.py 2026-10 <carpeta_con_los_archivos> --publicar -> además reescribe datos.json.

La contraseña de administración se lee de la variable de entorno LYSI_ADMIN (nunca se escribe en el repositorio).
Los archivos se reconocen por el nombre: ReporteConsumos, KmRecorridos/Filarus, Informe de combustible, Resumen.
Después de --publicar hay que hacer commit y push de datos.json para que el sitio se actualice."""
import os
import sys
import json
import base64
import shutil
import tempfile
import datetime

from motor import portal as P, armado

AQUI = os.path.dirname(os.path.abspath(__file__))
TIPOS = ["cargas", "filarus", "malla", "resumen"]


def clasificar(nombre):
    n = nombre.lower()
    if "consumo" in n and "informe" not in n:
        return "cargas"
    if "km" in n or "filarus" in n:
        return "filarus"
    if "informe" in n or "combustible" in n or "malla" in n:
        return "malla"
    if "resumen" in n or "rendimiento" in n:
        return "resumen"
    return None


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    publicar = "--publicar" in sys.argv
    if len(args) != 2 or len(args[0]) != 7 or args[0][4] != "-":
        sys.exit(__doc__)
    mes, carpeta = args
    clave = os.environ.get("LYSI_ADMIN")
    if not clave:
        sys.exit("Falta la contraseña de administración en la variable de entorno LYSI_ADMIN.")
    ruta = os.path.join(AQUI, "datos.json")
    datos = json.load(open(ruta, encoding="utf-8"))
    try:
        adm = json.loads(P.descifrar(datos["admin"], clave))
    except ValueError:
        sys.exit("La contraseña de administración no corresponde a este datos.json.")
    adm.setdefault("fuentes", {}); adm.setdefault("ajustes", {})

    nuevos, sin = {}, []
    for f in sorted(os.listdir(carpeta)):
        if not f.lower().endswith((".xlsx", ".xls")) or f.startswith("~$"):
            continue
        t = clasificar(f)
        if t is None or t in nuevos:
            sin.append(f)
            continue
        nuevos[t] = {"n": f, "b": base64.b64encode(open(os.path.join(carpeta, f), "rb").read()).decode()}
    print(f"Mes {mes}. Archivos reconocidos:")
    for t in TIPOS:
        print(f"  {t:8s} {nuevos[t]['n'] if t in nuevos else '— FALTA —'}")
    if sin:
        print("  No reconocidos o repetidos (no se usan):", ", ".join(sin))
    if not nuevos:
        sys.exit("No hay archivos para cargar.")
    adm["fuentes"].setdefault(mes, {}).update(nuevos)

    tmp = tempfile.mkdtemp(prefix="lysi_")
    try:
        for mid, fs in adm["fuentes"].items():
            d = os.path.join(tmp, mid)
            os.makedirs(d)
            for t, x in fs.items():
                open(os.path.join(d, t + ".xlsx"), "wb").write(base64.b64decode(x["b"]))
            if adm["ajustes"].get(mid):
                json.dump(adm["ajustes"][mid], open(os.path.join(d, "ajustes.json"), "w", encoding="utf-8"), ensure_ascii=False)
        for mid, imp in (adm.get("importados") or {}).items():
            d = os.path.join(tmp, mid)
            os.makedirs(d, exist_ok=True)
            json.dump(imp, open(os.path.join(d, "importado.json"), "w", encoding="utf-8"), ensure_ascii=False)
        r = json.loads(armado.procesar(tmp))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("\nCONTROL")
    for e in r["errores"]:
        print("  ERROR:", e)
    for p in r["pendientes"]:
        print("  Pendiente:", p)
    for m in r["meses"]:
        if m.get("importado"):
            print(f"  {m['nombre']}: {m['km']:,.0f} km · {m['gasoil']:,.2f} L · coef {m['coef']:.2f} · importado de un reporte ({m['metodo']})")
            continue
        print(f"  {m['nombre']}: {m['km']:,.0f} km · {m['gasoil']:,.2f} L · coef {m['coef']:.2f} · {m['operativas']} de {m['totales']} operativas · "
              f"{m['criticas']} crít. / {m['atencion']} atenc. / {m['normales']} norm. / {m['coef_bajo']} bajo / {len(m['investigar'])} invest. · "
              f"YPF {'cierra' if m['cierra_ypf'] else 'NO CIERRA'} · km: {m['fuente_odo']} odómetro, {m['fuente_filarus']} Filarus"
              + ("" if m["malla_anterior"] else " · sin malla del mes anterior"))
        if m["id"] == mes:
            for x in m["investigar"]:
                print(f"      a investigar {x['unidad']}: {x['motivo']}" + (" [decisión registrada]" if x["manual"] else ""))
    if r["errores"] or not r["html"]:
        sys.exit("\nNo se publica: hay errores o no hay ningún mes calculable.")
    if mes not in [m["id"] for m in r["meses"]]:
        print(f"\nAVISO: {mes} quedó cargado pero todavía no se puede calcular (ver pendientes).")
    if not publicar:
        print("\nSolo control: no se modificó nada. Para publicar, repetir con --publicar.")
        return
    nuevo = dict(datos)
    nuevo["cajas"] = dict(datos.get("cajas", {}))
    nuevo["cajas"]["combustible"] = P.cifrar(r["html"], adm["claves"]["combustible"])
    nuevo["admin"] = P.cifrar(json.dumps(adm, ensure_ascii=False), clave)
    nuevo["info"] = {"meses": [m["nombre"] for m in r["meses"]], "ids": [m["id"] for m in r["meses"] if not m.get("importado")],
                     "generado": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M"),
                     "reglas": r["reglas"]}
    for k in ("gastos", "gastos_fecha", "gastos_orig"):
        if (datos.get("info") or {}).get(k):
            nuevo["info"][k] = datos["info"][k]
    # se escribe aparte y se reemplaza de una: si algo se corta, datos.json no queda a medias
    with open(ruta + ".tmp", "w", encoding="utf-8") as fh:
        json.dump(nuevo, fh, ensure_ascii=False)
    os.replace(ruta + ".tmp", ruta)
    print("\ndatos.json actualizado. Falta commit y push para que el sitio lo muestre.")


if __name__ == "__main__":
    main()
