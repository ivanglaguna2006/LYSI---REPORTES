# -*- coding: utf-8 -*-
"""Datos fijos del Prompt Maestro LYSI v4.7. Todo lo que es criterio vive acá, no en el código."""

VERSION_REGLAS = "4.7"

# Regla 5 — unidades excluidas de todo el procesamiento
EXCLUIDAS = {
    "AA130XU": "Auto de la empresa",
    "AD831JQ": "Auto de la empresa",
    "AF963XJ": "Auto de la empresa",
    "AG812UT": "Auto de la empresa",
    "PBC613": "Utilitario liviano",
}

PRODUCTOS_GASOIL = ["D.DIESEL 500", "INFINIA", "INFINIA DIESEL"]
# Regla 17 — factor de conversión a litros
PRODUCTOS_UREA = {"AZUL 32 BIDON 10 L": 10, "AZUL 32 BIDON 20 L": 20, "AZUL 32 GRANEL": 1}

# Ideales por modelo (L/100 km)
IDEAL_MB = 32.6
IDEALES_SCANIA = {"360": 30.0, "410": 30.0, "420": 26.0}
# Regla 18 — modelos sin análogo razonable: van a "A investigar"
MODELOS_SIN_IDEAL = ["ATEGO"]

# Regla 13 — capacidad nominal de tanque (L)
CAPACIDAD = {"360": 425.0, "410": 440.0, "420": 465.0}

# Clasificación por diferencia contra el ideal
UMBRAL_CRITICO = 3.0
UMBRAL_ATENCION = 1.0
UMBRAL_COEF_BAJO = -3.0

# Urea
UREA_EXCESO = 8.0
UREA_BAJO = 4.0

# Regla 4 — emparejamiento carga ↔ evento de malla para el odómetro
VENTANA_ODO_HORAS = 24
# Regla 19 — emparejamiento carga ↔ suba de malla
VENTANA_SUBA_HORAS = 3
TOLERANCIA_LITROS = 2.0
DOS_EN_UNO_HORAS = 2
# Regla 11 — control de sanidad ODO vs Filarus
SANIDAD_PCT = 50.0

# Pares gemelos con telemetría cruzada: se miden con Filarus y se leen como par
PARES_GEMELOS = [("AE162MR", "AE162MN")]

# Equipos de My Scania sin patente cargada → patente. Se miden con Filarus.
EQUIPOS_SIN_PATENTE = {
    "4112518": "AI282LR",
    "4112569": "AI183ZP",
    "4121659": "AI331KW",
    "4121842": "AI415RL",
    "4122472": "AI415RM",
    "4122533": "AI415RK",
}

MESES = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

# Regla 21 — un coeficiente por encima de este múltiplo del ideal no es consumo físicamente posible:
# el KM de esa ventana se declara no confiable y la unidad va a "A investigar".
COEF_IMPOSIBLE_FACTOR = 2.0

# Regla 19 — piso de suba real: por debajo es ruido del sensor
SUBA_PISO_PCT = 4.0
# Subas de tanque sin carga de tarjeta: se listan desde este porcentaje
SUBA_SIN_CARGA_PCT = 10.0
# Dos eventos de malla son un mismo llenado si el nivel continúa (± puntos) y están a menos de estas horas
SUBA_CONTINUIDAD_PTS = 1.0
SUBA_CONTINUIDAD_HORAS = 4.0

# Evaluación anual — para entrar al ranking de mejor/peor hay que tener, en promedio, al menos estos km por mes cargado
EVAL_MIN_KM_MES = 3000
