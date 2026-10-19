# -*- coding: utf-8 -*-
"""Control RENPRE desde la consola: el mismo cruce que corre la herramienta de la app.

  python3 control_renpre.py <remitos.xlsx> <declaraciones.xls>            -> imprime el control (texto)
  python3 control_renpre.py <remitos.xlsx> <declaraciones.xls> --html x.html -> además guarda la pantalla como archivo suelto (sin estilos)

No publica nada ni toca datos.json. Requisitos: pandas, openpyxl, xlrd."""
import sys
import json
from motor import renpre


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 2:
        sys.exit(__doc__)
    R = renpre.procesar(args[0], args[1])
    for a in R.get("avisos", []):
        print("AVISO:", a)
    for e in R.get("errores", []):
        print("ERROR:", e)
    if R.get("errores"):
        sys.exit(1)
    print(R["texto"])
    if "--html" in sys.argv:
        out = sys.argv[sys.argv.index("--html") + 1]
        open(out, "w", encoding="utf-8").write(R["html"])
        print("\nHTML:", out)
    if "--json" in sys.argv:
        out = sys.argv[sys.argv.index("--json") + 1]
        json.dump({k: v for k, v in R.items() if k not in ("html", "texto")}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
        print("JSON:", out)


if __name__ == "__main__":
    main()
