# -*- coding: utf-8 -*-
"""Carga el apartado Reporte de resultados (gastos y mantenimiento) de LYSI Reportes desde la línea de comandos.

  python3 cargar_gastos.py <carpeta_con_los_dos_excel>            -> lee y muestra el control. NO publica.
  python3 cargar_gastos.py <carpeta_con_los_dos_excel> --publicar -> además reescribe datos.json.

La carpeta tiene los dos Excel de gastos tal como se generan: el reporte mensual (una hoja por mes) y el de
resultados del año. Se reconocen por sus hojas, no por el nombre. La aplicación los muestra como están.
Contraseñas, solo por variables de entorno (nunca se escriben en el repositorio):
  LYSI_ADMIN   contraseña de administración (obligatoria)
  LYSI_GASTOS  contraseña con la que se abre el Reporte de resultados. Solo hace falta la primera vez o para cambiarla.
Después de --publicar hay que hacer commit y push de datos.json. No toca Combustible."""
import os
import sys
import json
import datetime

from motor import portal as P, gastos as G

AQUI = os.path.dirname(os.path.abspath(__file__))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    publicar = "--publicar" in sys.argv
    if len(args) != 1 or not os.path.isdir(args[0]):
        sys.exit(__doc__)
    clave = os.environ.get("LYSI_ADMIN")
    if not clave:
        sys.exit("Falta la contraseña de administración en la variable de entorno LYSI_ADMIN.")
    ruta = os.path.join(AQUI, "datos.json")
    datos = json.load(open(ruta, encoding="utf-8"))
    try:
        adm = json.loads(P.descifrar(datos["admin"], clave))
    except ValueError:
        sys.exit("La contraseña de administración no corresponde a este datos.json.")

    r = G.procesar(args[0])
    print("Archivos reconocidos:")
    for t, n in (("mensual", "Reporte mensual"), ("resultados", "Resultados del año")):
        print(f"  {n:20s} {r['archivos'].get(t, '— FALTA —')}")
    print("\nCONTROL")
    for x in r["errores"]:
        print("  ERROR:", x)
    if r["html"]:
        print(f"  {r['hojas']} hojas leídas · {r['descripcion']}")
    if r["control"]:
        c = r["control"]
        print("  " + " | ".join(c["cab"][:7]))
        for f in c["filas"]:
            print("  " + " | ".join(f[:7]))
    if r["errores"] or not r["html"]:
        sys.exit("\nNo se publica: hay errores o no hay ningún Excel de gastos reconocido.")
    if len(r["archivos"]) < 2:
        print("\nAVISO: falta uno de los dos Excel; se publicaría solo el que está.")
    if not publicar:
        print("\nSolo control: no se modificó nada. Para publicar, repetir con --publicar.")
        return
    cg = os.environ.get("LYSI_GASTOS") or (adm.get("claves") or {}).get("gastos")
    if not cg:
        sys.exit("\nFalta definir la contraseña de Gastos: pasala en la variable de entorno LYSI_GASTOS.")
    if cg == clave:
        sys.exit("\nLa contraseña de Gastos tiene que ser distinta de la de administración.")
    adm.setdefault("claves", {})["gastos"] = cg
    nuevo = dict(datos)
    nuevo["cajas"] = dict(datos.get("cajas", {}))
    nuevo["cajas"]["gastos"] = P.cifrar(r["html"], cg, z=True)
    nuevo["admin"] = P.cifrar(json.dumps(adm, ensure_ascii=False), clave)
    nuevo["info"] = dict(datos.get("info", {}))
    nuevo["info"]["gastos"] = r["descripcion"]
    nuevo["info"]["gastos_fecha"] = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M")
    # se escribe aparte y se reemplaza de una: si algo se corta, datos.json no queda a medias
    with open(ruta + ".tmp", "w", encoding="utf-8") as fh:
        json.dump(nuevo, fh, ensure_ascii=False)
    os.replace(ruta + ".tmp", ruta)
    print("\ndatos.json actualizado. Falta commit y push para que el sitio lo muestre.")


if __name__ == "__main__":
    main()
