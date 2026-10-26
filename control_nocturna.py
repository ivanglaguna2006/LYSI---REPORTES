#!/usr/bin/env python3
"""Circulación nocturna desde la consola: python3 control_nocturna.py <planilla.xlsx> [salida.xlsx]

Completa las columnas de control (Autorizado, Observaciones, minutos) con las mismas reglas que la
herramienta de la app, valida el resultado contra el original y guarda `<planilla>_procesado.xlsx`
(o la ruta que se indique). No toca el archivo de entrada ni publica nada.
"""
import sys

from motor import nocturna


def main(argv):
    if len(argv) < 2:
        print(__doc__.strip())
        return 2
    entrada = argv[1]
    salida = argv[2] if len(argv) > 2 else nocturna.nombre_salida(entrada)
    try:
        res = nocturna.procesar(entrada, salida)
    except nocturna.ErrorNocturna as e:
        print("No se procesó:", e)
        return 1
    fallas = nocturna.verificar(entrada, salida, res)
    if fallas:
        print("El archivo no pasó la validación y no se entrega:")
        for f in fallas:
            print(" -", f)
        import os
        os.remove(salida)
        return 1
    for linea in nocturna.mensaje(res):
        print(linea)
    if res["borde"]:
        print("Borde 03:30 (fila, inicio, clasificación):")
        for f, h, c in res["borde"]:
            print("  %d  %s  %s" % (f, h, c))
    print("Guardado en:", salida)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
