# -*- coding: utf-8 -*-
"""Arma la primera versión de la aplicación a partir de una carpeta de datos.
Uso: python3 construir.py <carpeta_datos> <salida.html> <claves.json>   (claves: combustible y admin)"""
import sys, json
from motor import app
base, salida, claves = sys.argv[1], sys.argv[2], json.load(open(sys.argv[3], encoding="utf-8"))
import os
html, r = app.sitio(base, claves, os.path.join(os.path.dirname(salida), "sitio"))
open(salida, "w", encoding="utf-8").write(html)
print("OK", salida, round(len(html) / 1024), "KB;", [m["nombre"] for m in r["meses"]], r["errores"], r["pendientes"])
