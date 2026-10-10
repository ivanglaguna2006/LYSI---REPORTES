# LYSI Reportes — instrucciones para Claude

Este repositorio aloja la app de reportes de LYSI (GitHub Pages):
https://ivanglaguna2006.github.io/LYSI---REPORTES/

- `index.html`: la app (pantalla de acceso, consulta y Administración). No tiene datos.
- `datos.json`: los reportes y los archivos fuente, **cifrados**. Nunca editarlo a mano ni reemplazarlo por otra cosa: la app deja de abrir.
- `motor/`: el código de cálculo (reglas del Prompt Maestro v4.7). Es el mismo que la app lleva adentro.
- `cargar_mes.py`: carga un mes desde acá, con el mismo resultado que la pantalla de Administración.
- `cargar_gastos.py`: carga el apartado Reporte de resultados a partir de los dos Excel de gastos.
- `motor/gastos.py`: pasa esos dos Excel a página, tal como están (no recalcula nada).
- `regenerar.py`: vuelve a armar Combustible con los archivos ya cargados, sin sumar ninguno. Se usa después de un cambio de software en `motor/`.

## Cargar un mes cuando Ivo pasa los archivos

Ivo adjunta los cuatro archivos del mes tal como bajan de cada plataforma:
ReporteConsumos (tarjeta YPF), KmRecorridos (Filarus), Informe de combustible y Resumen de rendimientos (My Scania).

1. `git pull` de este repositorio antes de empezar (Ivo también puede publicar desde la app).
2. Copiar los cuatro archivos a una carpeta vacía, sin renombrarlos.
3. Pedirle a Ivo la contraseña de administración si no la dio en este chat. Usarla solo como variable de entorno; no escribirla en ningún archivo ni en un commit.
4. Control, sin publicar:
   `LYSI_ADMIN='<contraseña>' python3 cargar_mes.py AAAA-MM <carpeta>`
5. Mostrarle a Ivo el control tal como sale: km, litros, coeficiente, estados, si cierra la conciliación con YPF y la lista de unidades a investigar con su motivo. Es el checkpoint: **esperar su OK antes de publicar**.
6. Con su OK: repetir el comando con `--publicar`, y después commit y push de `datos.json` a `main`. El sitio se actualiza en uno o dos minutos.
7. Confirmarle qué meses quedaron publicados.

Requisitos de Python: pandas, openpyxl, cryptography.

## Cargar el Reporte de resultados (gastos y mantenimiento)

En la app el apartado se llama «Reporte de resultados»; tiene su propia contraseña y no toca Combustible. La app muestra los dos Excel que Ivo ya genera:
el reporte mensual (una hoja por mes, `REPORTE_MENSUAL_LYSI_...xlsx`) y el de resultados del año
(`REPORTE_RESULTADOS_LYSI_...xlsx`). Cada carga reemplaza lo anterior: van siempre los dos archivos completos.

1. `git pull`.
2. Copiar los dos Excel a una carpeta vacía.
3. Control, sin publicar: `LYSI_ADMIN='<contraseña>' python3 cargar_gastos.py <carpeta>`
4. Mostrarle a Ivo el control (el resumen de cada mes tal como figura en el Excel) y **esperar su OK**.
5. Con su OK: repetir con `--publicar`, y después commit y push de `datos.json` a `main`.
   La primera vez, o para cambiar la contraseña de Resultados, agregar `LYSI_GASTOS='<contraseña de gastos>'`.
6. Si el control avisa que hay hojas sin contenido, el Excel se guardó sin valores calculados: pedirle a Ivo
   que lo abra y lo guarde en Excel, y volver a cargarlo. No se publica así.

## Reglas

- No inventar ni corregir datos: si el control muestra un error de archivo (export equivocado, fechas de otro mes), se lo informa a Ivo y no se publica.
- Si falta alguno de los cuatro archivos, avisar cuál. Con solo cargas + Filarus el mes sirve de arranque para el siguiente, pero no se calcula completo.
- Para medir un mes tiene que estar cargado el mes anterior.
- Las decisiones de criterio (mandar una unidad a investigar por un motivo que las reglas no detectan) las toma Ivo y se registran desde Administración en la app, no acá.
- No cambiar `motor/` ni `index.html` en una carga mensual. Si hay que cambiar una regla, es un cambio de software: se hace aparte, se valida contra agosto y septiembre 2026 (484 888 km / 30,41 y 535 206 km / 30,60), se regenera `index.html` (`python3 -c "from motor import app; open('index.html','w',encoding='utf-8').write(app.cascara())"`) y, si cambia cómo se arma Combustible, se vuelve a armar lo publicado con `LYSI_ADMIN='<contraseña>' python3 regenerar.py` (control) y después `--publicar`.
- Este repositorio es público: nunca subir contraseñas, tokens ni archivos fuente sin cifrar. Los archivos de Ivo se copian a una carpeta **fuera** del repositorio, y al publicar se agrega solo lo necesario (`git add datos.json`), nunca `git add -A`.
- Antes de publicar, `git pull`: si alguien publicó desde la app mientras tanto, hay que volver a correr el control sobre la versión nueva.
- Volver atrás una publicación: `git revert` del commit de `datos.json`. Esa versión abre con las contraseñas que tenía en ese momento.
