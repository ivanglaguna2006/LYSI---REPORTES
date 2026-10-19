# -*- coding: utf-8 -*-
"""Vuelve a armar el apartado Combustible con los archivos que ya están cargados. No suma ni cambia ningún archivo.

Sirve después de un cambio de software en motor/ (cómo se muestra o cómo se calcula): los reportes publicados
se arman de nuevo con el código actual.

  python3 regenerar.py            -> calcula y muestra el control. NO publica.
  python3 regenerar.py --publicar -> además reescribe datos.json (solo Combustible; Resultados y administración no se tocan).

La contraseña de administración se lee de la variable de entorno LYSI_ADMIN (nunca se escribe en el repositorio).
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


def armar(adm):
    """Corre el mismo proceso que la pantalla de Administración sobre las fuentes guardadas."""
    tmp = tempfile.mkdtemp(prefix="lysi_")
    try:
        for mid, fs in (adm.get("fuentes") or {}).items():
            d = os.path.join(tmp, mid)
            os.makedirs(d)
            for t, x in fs.items():
                open(os.path.join(d, t + ".xlsx"), "wb").write(base64.b64decode(x["b"]))
            if (adm.get("ajustes") or {}).get(mid):
                json.dump(adm["ajustes"][mid], open(os.path.join(d, "ajustes.json"), "w", encoding="utf-8"), ensure_ascii=False)
        for mid, imp in (adm.get("importados") or {}).items():
            d = os.path.join(tmp, mid)
            os.makedirs(d, exist_ok=True)
            json.dump(imp, open(os.path.join(d, "importado.json"), "w", encoding="utf-8"), ensure_ascii=False)
        return json.loads(armado.procesar(tmp))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    publicar = "--publicar" in sys.argv
    clave = os.environ.get("LYSI_ADMIN")
    if not clave:
        sys.exit("Falta la contraseña de administración en la variable de entorno LYSI_ADMIN.")
    P.avisar("de administración", clave)
    ruta = os.path.join(AQUI, "datos.json")
    datos = json.load(open(ruta, encoding="utf-8"))
    try:
        adm = json.loads(P.descifrar(datos["admin"], clave))
    except ValueError:
        sys.exit("La contraseña de administración no corresponde a este datos.json.")
    r = armar(adm)

    print("CONTROL")
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
              f"YPF {'cierra' if m['cierra_ypf'] else 'NO CIERRA'}")
    if r["errores"] or not r["html"]:
        sys.exit("\nNo se publica: hay errores o no hay ningún mes calculable.")
    antes = (datos.get("info") or {})
    ahora = [m["nombre"] for m in r["meses"]]
    if antes.get("meses") and antes["meses"] != ahora:
        sys.exit(f"\nNo se publica: los meses armados ({ahora}) no coinciden con los publicados ({antes['meses']}).")
    if not publicar:
        print("\nSolo control: no se modificó nada. Para publicar, repetir con --publicar.")
        return
    nuevo = dict(datos)
    nuevo["cajas"] = dict(datos.get("cajas", {}))
    nuevo["cajas"]["combustible"] = P.cifrar(r["html"], adm["claves"]["combustible"])
    nuevo["info"] = dict(antes)
    nuevo["info"].update({"meses": ahora, "ids": [m["id"] for m in r["meses"] if not m.get("importado")],
                          "generado": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M"),
                          "reglas": r["reglas"]})
    # se escribe aparte y se reemplaza de una: si algo se corta, datos.json no queda a medias
    with open(ruta + ".tmp", "w", encoding="utf-8") as fh:
        json.dump(nuevo, fh, ensure_ascii=False)
    os.replace(ruta + ".tmp", ruta)
    print("\ndatos.json actualizado (solo Combustible). Falta commit y push para que el sitio lo muestre.")


if __name__ == "__main__":
    main()
