# LYSI Reportes — instrucciones para Claude

Este repositorio aloja la app de reportes de LYSI (GitHub Pages):
https://ivanglaguna2006.github.io/LYSI---REPORTES/

- `index.html`: la app (pantalla de acceso, consulta y Administración). No tiene datos.
- La pantalla de inicio tiene una **hoja por área** (pestañas bajo el título). Hoy hay una sola, «Administración y control», con el Informe de combustible, el Informe de mantenimiento y, en «Herramientas», el procesador de Declaraciones RENPRE y la Circulación nocturna. Para sumar un área se agrega una entrada en `AREAS` (`motor/app.py`) y se regenera `index.html`; las tarjetas de reporte conservan sus ids porque el JavaScript los usa tal cual.
- `originales.json`: los dos Excel del Informe de mantenimiento, **cifrados**; lo escribe `cargar_gastos.py`. La app lo baja solo cuando alguien pide el Excel original.
- `datos.json`: los reportes y los archivos fuente, **cifrados**. Nunca editarlo a mano ni reemplazarlo por otra cosa: la app deja de abrir.
- `motor/`: el código de cálculo (reglas del Prompt Maestro v4.7). Es el mismo que la app lleva adentro.
- `cargar_mes.py`: carga un mes desde acá, con el mismo resultado que la pantalla de Administración.
- `cargar_gastos.py`: carga el apartado Informe de mantenimiento a partir de los dos Excel de gastos.
- `motor/gastos.py`: pasa esos dos Excel a página, tal como están (no recalcula nada).
- `regenerar.py`: vuelve a armar Combustible con los archivos ya cargados, sin sumar ninguno. Se usa después de un cambio de software en `motor/`.
- `motor/renpre.py`: el cruce de remitos contra declaraciones RENPRE (herramienta «Declaraciones RENPRE» del inicio). Corre en el navegador con Pyodide (instala `xlrd` aparte para el .xls) y también desde la consola con `control_renpre.py`.
- `control_renpre.py`: `python3 control_renpre.py <remitos.xlsx> <declaraciones.xls>` imprime el control en texto (`--html x.html` guarda la pantalla). No publica nada.
- `motor/nocturna.py`: completa la planilla de circulación nocturna (herramienta «Circulación nocturna» del inicio). Corre en el navegador con Pyodide y desde la consola con `control_nocturna.py`.
- `control_nocturna.py`: `python3 control_nocturna.py <planilla.xlsx> [salida.xlsx]` guarda `<planilla>_procesado.xlsx` validado contra el original. No publica nada.

## Circulación nocturna

La herramienta no guarda datos ni pide contraseña: la persona sube el Excel de circulaciones nocturnas (encabezados en la
fila 1: Fecha, Movil, Flota, Chofer, CNFechaHoraInicio, CNFechaHoraFin, Duración, Distancia KM, Autorizado, Observaciones,
MINUTOS AUTORIZADOS, MINUTOS NO AUTORIZADOS, MINUTOS OPERATIVOS, OBSERVACIONES2; se ubican por nombre normalizado), toca
«Procesar» y se descarga el mismo archivo con el sufijo `_procesado` y cinco columnas completadas. Reglas: Observaciones =
TRAFICO si el inicio está entre 23:00:00 y 03:29:59 (cruza la medianoche), INICIO DE JORNADA en el resto, corte 03:30 estricto;
Autorizado = SI; Duración < 29 → MINUTOS AUTORIZADOS, ≥ 29 → MINUTOS OPERATIVOS; MINUTOS NO AUTORIZADOS siempre vacía; la
duración se usa tal cual (nunca fin − inicio). Filas vacías, «NO HAY REPORTE» o sin inicio/duración válidos quedan intactas.
Fuera de esas columnas nada cambia (se abre y guarda con openpyxl; se rechazan .xlsm y hojas con gráficos o imágenes) y
`verificar()` compara el resultado con el original antes de entregarlo. Cada ~15 días Ivo vuelve a subir la planilla ya
procesada con filas nuevas: se recalcula completa. La especificación está en el proyecto «LYSI app» (documento «Circulación
nocturna — Especificación»). Si Ivo pasa la planilla por acá, se corre `control_nocturna.py` y se le devuelve el archivo.

## Control RENPRE

La herramienta no guarda datos ni pide contraseña: la persona sube el Excel de remitos del mes (hoja «Remitos»,
encabezados en la fila 6, filas pendientes en amarillo; el archivo original, porque Google Drive y las
conversiones pierden los colores) y el export de transacciones del RENPRE (.xls), toca «Procesar» y el
resultado se abre como un reporte con pestañas Resumen, Con problemas, Para revisar, Bien declarados y Sin
remito. Las reglas (origen esperado por cliente, familias de producto, stopwords, aliases, tolerancia de
cantidad) están en `REGLAS` dentro de `motor/renpre.py`; la especificación completa está en el chat del
proyecto «LYSI app» (documento «Control RENPRE — Especificación del cruce remitos vs. declaraciones»).
Si Ivo pasa los dos archivos por acá, se corre `control_renpre.py` y se le muestra el texto tal como sale;
no se corrigen datos ni se toca el archivo de remitos.

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

## Cargar el Informe de mantenimiento (gastos y mantenimiento)

En la app el apartado se llama «Informe de mantenimiento»; tiene su propia contraseña y no toca Combustible. La app muestra los dos Excel que Ivo ya genera:
el reporte mensual (una hoja por mes, `REPORTE_MENSUAL_LYSI_...xlsx`) y el de resultados del año
(`REPORTE_RESULTADOS_LYSI_...xlsx`). Cada carga reemplaza lo anterior: van siempre los dos archivos completos.

1. `git pull`.
2. Copiar los dos Excel a una carpeta vacía.
3. Control, sin publicar: `LYSI_ADMIN='<contraseña>' python3 cargar_gastos.py <carpeta>`
4. Mostrarle a Ivo el control (el resumen de cada mes tal como figura en el Excel) y **esperar su OK**.
5. Con su OK: repetir con `--publicar`, y después commit y push de `datos.json` y `originales.json` a `main`
   (`git add datos.json originales.json`). `originales.json` son los dos Excel cifrados con la contraseña del
   apartado: es lo que la app ofrece como «Excel original».
   La primera vez, o para cambiar la contraseña del Informe, agregar `LYSI_GASTOS='<contraseña de gastos>'`.
   Si hay mails habilitados, al menos uno tiene que tener permiso de «gastos» (si no, `sellar` corta con un aviso).
6. Si el control avisa que hay hojas sin contenido, el Excel se guardó sin valores calculados: pedirle a Ivo
   que lo abra y lo guarde en Excel, y volver a cargarlo. No se publica así.

## Seguridad

- GitHub Pages sirve solo texto cifrado: `datos.json` y `originales.json` van con AES-256-CTR + HMAC-SHA256 (`motor/portal.py`). Cada caja guarda sus iteraciones en `n`; `n = 0` significa que la caja está cifrada con una **clave maestra** (64 bytes al azar), no con una contraseña.
- **Accesos por mail** (`datos.json` v3): cada reporte se cifra con su clave maestra, y en `datos["accesos"][reporte]` esa clave va envuelta, por cada mail habilitado, con PBKDF2(600 000) de `mail + "\n" + contraseña del reporte`. El id de cada acceso es un hash del mail (no queda el mail legible). El mail es parte de la llave, no un chequeo: sin mail + contraseña válidos no hay forma de descifrar nada. Los mails y permisos viven en la caja admin (`adm["usuarios"] = {mail: ["combustible","gastos"]}`, `adm["maestras"]`). Se administran desde «Quién puede entrar» en la app.
- **La maestra rota en cada publicación** (app y scripts): quien tuvo la anterior no abre lo nuevo. Como la contraseña del reporte es compartida, **dar de baja a alguien = quitar su mail y cambiar la contraseña del reporte** en la misma publicación. Los accesos se re-envuelven todos en cada publicación; `cargar_gastos.py` re-cifra `originales.json` con la maestra nueva y la app lo hace también (sube los dos archivos).
- Sin mails habilitados (`adm` sin `usuarios`) todo sigue en modo antiguo: solo contraseña, `v = 2`. Es el estado de lo publicado hasta octubre 2026 y la app lo abre igual.
- **La fuerza de las contraseñas sigue siendo la seguridad del sitio**: el archivo cifrado es público y se ataca sin límite de intentos. Política única en `P.fuerza` (Python) y `fuerza` (JavaScript): mínimo 14 caracteres, sin palabras previsibles ni años, estimación de entropía. La app no publica con una contraseña que no cumpla; «Generar» arma una frase de 6 palabras (`P.frase()` en consola). Los scripts avisan si la de administración es débil; una `LYSI_GASTOS` nueva débil se rechaza.
- Sesión en el navegador: los campos se vacían al entrar; al cerrar un reporte o Administración se borra todo lo descifrado de memoria; cierre automático a los 15 minutos sin actividad (también al volver de una pestaña en segundo plano). Los campos llevan `autocomplete="one-time-code"` y las marcas de los gestores de contraseñas para que no ofrezcan guardarla.
- Cambiar una contraseña o rotar la maestra no protege las versiones anteriores de `datos.json`, que quedan en el historial público del repositorio cifradas con las llaves de ese momento.
- Pendientes: Pyodide en un Web Worker aislado con integridad (SRI) y CSP; token de GitHub fine-grained acotado a este repositorio; contraseña propia por persona (haría que quitar un mail alcance para dar de baja); eventualmente una capa de acceso externa (Cloudflare Access o repositorio privado) para tener bloqueo de intentos y auditoría.

## Reglas

- No inventar ni corregir datos: si el control muestra un error de archivo (export equivocado, fechas de otro mes), se lo informa a Ivo y no se publica.
- Si falta alguno de los cuatro archivos, avisar cuál. Con solo cargas + Filarus el mes sirve de arranque para el siguiente, pero no se calcula completo.
- Para medir un mes tiene que estar cargado el mes anterior.
- Las decisiones de criterio (mandar una unidad a investigar por un motivo que las reglas no detectan) las toma Ivo y se registran desde Administración en la app, no acá.
- No cambiar `motor/` ni `index.html` en una carga mensual. Si hay que cambiar una regla, es un cambio de software: se hace aparte, se valida contra agosto y septiembre 2026 (484 888 km / 30,41 y 535 206 km / 30,60), se regenera `index.html` (`python3 -c "from motor import app; open('index.html','w',encoding='utf-8').write(app.cascara())"`) y, si cambia cómo se arma Combustible, se vuelve a armar lo publicado con `LYSI_ADMIN='<contraseña>' python3 regenerar.py` (control) y después `--publicar`.
- Este repositorio es público: nunca subir contraseñas, tokens ni archivos fuente sin cifrar. Los archivos de Ivo se copian a una carpeta **fuera** del repositorio, y al publicar se agrega solo lo necesario (`git add datos.json`), nunca `git add -A`.
- Antes de publicar, `git pull`: si alguien publicó desde la app mientras tanto, hay que volver a correr el control sobre la versión nueva.
- Volver atrás una publicación: `git revert` del commit de `datos.json`. Esa versión abre con las contraseñas que tenía en ese momento.
