# -*- coding: utf-8 -*-
"""Arma el archivo único del software: pantalla de acceso + apartados cifrados con contraseña.

Cifrado: PBKDF2-HMAC-SHA256 -> clave AES-256-CTR + clave HMAC-SHA256 (cifrar y después autenticar).
Sin la contraseña el archivo no contiene ningún dato legible."""
import os
import re
import gzip
import base64
import hmac
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# Iteraciones de PBKDF2. 600 000 es la recomendación vigente de OWASP para PBKDF2-HMAC-SHA256 (2023).
# Cada caja guarda sus propias iteraciones ("n"), así que lo ya publicado sigue abriendo.
ITER = 600000

# Política de contraseñas. La seguridad del sitio es exactamente la fuerza de las contraseñas: el archivo
# cifrado es público y se puede atacar sin límite de intentos, así que una contraseña corta o previsible
# no sirve por más cifrado que haya. Misma regla en la app (motor/app.py, función fuerza).
MINIMO = 14
PROHIBIDAS = ["lysi", "logistica", "combustible", "mantenimiento", "admin", "reporte", "informe", "gastos",
              "contrase", "password", "clave", "camion", "scania", "ypf", "filarus", "renpre", "qwerty", "asdf",
              "123456", "abcdef", "transporte", "empresa"]
PALABRAS = """abeja abrigo aceite acero acorde agua aguila ajo alamo alba alce alfombra alga almendra altar alto amapola ambar anillo anis antena arado arbol arco arena arpa arroz asado astro atlas aurora avena azul bahia balcon ballena balsa banco bandera barco barro baston bata batuta bebida becerro beso biblia bigote bisagra blanco bloque boca bola bolsa bombilla bonito bosque bota botella brazo breve brillo brisa bronce bruma buey bufanda buho burbuja buzon caballo cabana cabello cabra cacao cadena cafe caja calle calma camino campana campo canasta cancion canela canoa cantera capa carbon carpa carreta carro carta casa cascada castor cebolla cedro ceniza centro cepillo cera cerca cereza cerro cesta chaleco chicle chimenea chispa ciclo cielo cinta circo ciruela cisne clavo cobre coche cocina codo cohete cola colina collar color cometa comida concha conejo copa coral corcho cordero corona corral correo cortina cosecha costa crema cristal cuadro cubo cuchara cuello cuenco cuerda cuerno cuervo cueva cumbre cuna dado dama danza dardo datil dedal dedo delfin delta diente dique disco doble domingo dorado dragon duende dulce duna edificio elefante enano encina eneldo enero envase equipo erizo escala escoba escudo esfera espejo espiga espuma estatua estrella estufa fabrica faro farol felpa feria fiesta figura filtro final firma flauta flecha flor foca fogata fondo foro fosforo fragua fraile frasco fresa fresco frio fruta fuego fuente fuerte gacela galaxia galleta gallo ganso garza gato gaviota gemelo girasol globo gorra gota granizo grillo grua grupo guante guinda guitarra habano hacha hada halcon harina hebilla helado helecho heno hermano hielo hierro higo hilo himno hoja hongo hormiga horno huerta hueso huevo humo iglesia iman imperio indice insecto invierno isla jabon jade jamon jardin jarra jazmin jinete jirafa joya juego jueves jugo junco junio laguna lampara lana lancha lapiz laurel lava lazo leche lechuza lengua leon letra libro licor lima limon lince lino lirio llama llanta llave lluvia lobo lomo loro lucero luna lupa luz madera madre maiz maleta mango manta manzana mapa mar marfil marmol martes martillo melon mente mesa metal miel miercoles mimbre mirlo mochila moneda monte morado mosca motor muelle mundo muro musgo musica nacar naranja nave nevada nido niebla nieve nogal norte nota nube nudo nuez oasis oboe ocaso oceano olivo olla olmo onda oro orquidea oruga oso ostra oveja padre paja pajaro paleta palma paloma pan panal pantano papel parra pasto pato pavo pecho peine pelota pera perla perro pez piano piedra pierna pimienta pino pintura pipa pista plata plato playa pluma polen polvo pomelo portal pozo pradera prisma puente puerta puerto pulpo puma punto quemado queso quilla quinua radio raiz rama rana rastro raton rayo red regalo reina reloj remo repollo reptil resina reto rienda rio risa roble roca rocio rodilla rojo ropa rosa rueda ruido rumbo sabana sabio sal salon salto sandia sapo sardina sauce seda sello selva semana semilla senda siesta silla sirena sol sombra sopa sorbete suela sueno sur tabaco tabla taller tambor tapa taza teatro techo tela templo tenedor tierra tigre tijera timon tinta toalla tomate tomillo torre tortuga trebol tren trigo trompa trueno tulipan tunel turbina umbral unicornio urbano uva vaca valle vapor vela velero venado verano verde vereda vidrio viento vinagre vino violin visera volcan vuelo yegua yema yunque yute zafiro zanja zapato zorro zumo""".split()


def _plano(t):
    import unicodedata
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()


def fuerza(pw):
    """Evalúa una contraseña: (sirve, nivel, motivo). nivel: debil | aceptable | fuerte."""
    import math
    pw = pw or ""
    if len(pw) < MINIMO:
        return False, "debil", "Tiene que tener al menos %d caracteres: lo más cómodo es una frase de 5 o 6 palabras." % MINIMO
    p = _plano(pw)
    for x in PROHIBIDAS:
        if x in p.replace(" ", "").replace("-", "").replace("_", ""):
            return False, "debil", "No puede contener palabras previsibles como «%s»." % x
    if re.search(r"(19|20)\d\d", p):
        return False, "debil", "Evitá años y fechas: son lo primero que se prueba."
    if re.search(r"(.)\1{3,}", p) or len(set(p)) <= 4:
        return False, "debil", "Tiene demasiados caracteres repetidos."
    partes = [x for x in re.split(r"[\s\-_.,/]+", p) if len(x) >= 2]
    if len(partes) >= 4:
        # frase: ~10 bits por palabra (vocabulario de unas mil palabras), más algo por números y mayúsculas
        bits = len(partes) * 10 + (4 if re.search(r"\d", pw) else 0) + (2 if re.search(r"[A-Z]", pw) else 0)
    else:
        # contraseña "de caracteres": tamaño del alfabeto usado, descontado porque nadie elige al azar
        pool = sum([26 if re.search(r"[a-z]", pw) else 0, 26 if re.search(r"[A-Z]", pw) else 0,
                    10 if re.search(r"\d", pw) else 0, 33 if re.search(r"[^A-Za-z0-9]", pw) else 0]) or 26
        bits = len(pw) * math.log2(pool) * 0.8
    if bits < 42:
        return False, "debil", "Es previsible: sumá palabras o caracteres, o generá una frase."
    if bits < 60:
        return True, "aceptable", "Sirve. Una palabra más la haría fuerte."
    return True, "fuerte", "Fuerte."


def avisar(nombre, pw):
    """Imprime un aviso si la contraseña no cumple la política (no corta el proceso: la cambia Ivo desde la app)."""
    ok, nivel, motivo = fuerza(pw)
    if not ok:
        print("AVISO: la contraseña %s es débil (%s). Conviene cambiarla desde Administración en la app." % (nombre, motivo))
    return ok


def frase():
    """Genera una frase de 6 palabras al azar más dos dígitos (~61 bits de entropía)."""
    import secrets
    return "-".join(secrets.choice(PALABRAS) for _ in range(6)) + "-" + str(secrets.randbelow(90) + 10)


def _derivar(clave, salt, n):
    """clave str -> PBKDF2 con n iteraciones; clave bytes (64) -> se usa directa, n = 0 (clave maestra al azar)."""
    if isinstance(clave, (bytes, bytearray)):
        if len(clave) != 64:
            raise ValueError("la clave maestra tiene que tener 64 bytes")
        return bytes(clave)
    return hashlib.pbkdf2_hmac("sha256", clave.encode("utf-8"), salt, n, 64)


def cifrar(texto, clave, z=False):
    """z=True: comprime (gzip) antes de cifrar; se usa en los apartados pesados (Gastos).
    clave: contraseña (str) o clave maestra (bytes de 64)."""
    if not clave:
        raise ValueError("clave vacía: no se cifra nada sin contraseña")
    salt, iv = os.urandom(16), os.urandom(16)
    n = 0 if isinstance(clave, (bytes, bytearray)) else ITER
    dk = _derivar(clave, salt, n)
    enc = Cipher(algorithms.AES(dk[:32]), modes.CTR(iv)).encryptor()
    datos = texto.encode("utf-8")
    if z:
        datos = gzip.compress(datos, 9, mtime=0)
    ct = enc.update(datos) + enc.finalize()
    tag = hmac.new(dk[32:], iv + ct, hashlib.sha256).digest()
    b = lambda x: base64.b64encode(x).decode()
    caja = {"s": b(salt), "i": b(iv), "t": b(tag), "c": b(ct), "n": n}
    if z:
        caja["z"] = 1
    return caja



def descifrar(caja, clave):
    """Inverso de cifrar(). Lanza ValueError si la contraseña no corresponde."""
    b = base64.b64decode
    salt, iv, tag, ct = b(caja["s"]), b(caja["i"]), b(caja["t"]), b(caja["c"])
    n = int(caja.get("n", ITER))
    if (n == 0) != isinstance(clave, (bytes, bytearray)):
        raise ValueError("contraseña incorrecta")
    dk = _derivar(clave, salt, n)
    if not hmac.compare_digest(hmac.new(dk[32:], iv + ct, hashlib.sha256).digest(), tag):
        raise ValueError("contraseña incorrecta")
    dec = Cipher(algorithms.AES(dk[:32]), modes.CTR(iv)).decryptor()
    datos = dec.update(ct) + dec.finalize()
    if caja.get("z"):
        datos = gzip.decompress(datos)
    return datos.decode("utf-8")


# ── Accesos por mail ───────────────────────────────────────────────────────────────────────
# Cada reporte se cifra con una clave maestra al azar (64 bytes). Esa clave se guarda, por cada mail
# habilitado, envuelta con PBKDF2(mail + "\n" + contraseña del reporte). Sin un par mail + contraseña
# válido no hay forma de descifrar nada, ni editando la app: el mail no es un chequeo, es parte de la llave.
# adm["usuarios"] = {mail: ["combustible", "gastos"]}; adm["maestras"] = {reporte: clave maestra en base64}.
# Si adm no tiene "usuarios", se sigue cifrando a la antigua (solo contraseña): es el modo previo a la migración.

def mail_plano(m):
    return (m or "").strip().lower()


def id_mail(m):
    """Identificador público del mail dentro de datos.json (no deja el mail legible)."""
    return base64.urlsafe_b64encode(hashlib.sha256(("lysi-acceso:" + mail_plano(m)).encode("utf-8")).digest()).decode()[:22]


def maestra(adm, reporte):
    """Clave maestra NUEVA del reporte (bytes). Se rota en cada publicación: quien tuvo la anterior
    (por ejemplo alguien dado de baja) no puede abrir lo que se publique de ahora en más."""
    m = adm.setdefault("maestras", {})
    m[reporte] = base64.b64encode(os.urandom(64)).decode()
    return base64.b64decode(m[reporte])


def maestra_actual(adm, reporte):
    """Clave maestra con la que está cifrado lo publicado (bytes) o None en modo antiguo."""
    v = (adm.get("maestras") or {}).get(reporte)
    return base64.b64decode(v) if v else None


def accesos(adm, reporte):
    """Cajas de acceso del reporte: una por mail habilitado, con la clave maestra envuelta en mail + contraseña."""
    pw = (adm.get("claves") or {}).get(reporte)
    if not pw:
        raise ValueError("falta la contraseña del reporte %s" % reporte)
    k = adm["maestras"][reporte]
    out = {}
    for mail, reps in (adm.get("usuarios") or {}).items():
        if reporte in (reps or []):
            out[id_mail(mail)] = cifrar(k, mail_plano(mail) + "\n" + pw)
    # el mail es parte de la llave, no un chequeo; pero la contraseña del reporte es compartida:
    # dar de baja a alguien = quitar su mail Y cambiar la contraseña del reporte (la maestra rota sola)
    return out


def sellar(nuevo, adm, reporte, texto, z=False):
    """Cifra el contenido de un reporte y arma sus accesos. Devuelve la clave maestra usada (bytes) o None en modo antiguo."""
    nuevo.setdefault("cajas", {})
    if not adm.get("usuarios"):
        adm.pop("usuarios", None)
        adm.pop("maestras", None)
        nuevo["cajas"][reporte] = cifrar(texto, adm["claves"][reporte], z)
        nuevo.pop("accesos", None)
        nuevo["v"] = 2
        return None
    k = maestra(adm, reporte)
    nuevo["cajas"][reporte] = cifrar(texto, k, z)
    acc = accesos(adm, reporte)
    if not acc:
        raise ValueError("no hay ningún mail habilitado para %s: nadie podría entrar. Habilitalos desde Administración en la app." % reporte)
    nuevo.setdefault("accesos", {})[reporte] = acc
    nuevo["v"] = 3
    return k


def abrir_reporte(datos, reporte, mail, pw):
    """Abre un reporte como lo hace la app: con accesos por mail, o con la contraseña sola si todavía no migró."""
    acc = (datos.get("accesos") or {}).get(reporte)
    if not acc:
        return descifrar(datos["cajas"][reporte], pw)
    caja = acc.get(id_mail(mail))
    if not caja:
        raise ValueError("mail no habilitado")
    k = base64.b64decode(descifrar(caja, mail_plano(mail) + "\n" + pw))
    return descifrar(datos["cajas"][reporte], k)


CSS = r"""
:root{--ink:#1A1A1A;--lima:#94C337;--lima2:#4B7010;--lima0:#F1F7E4;--v1:#4B7010;--v2:#94C337;--v3:#94C337;--v0:#F1F7E4;--ng:#1A1A1A;--tx:#1A1A1A;--tx2:#5A6055;--ln:#DFE2D8;--bg:#fff;--bg2:#F6F7F3;--ti:Jost,"Century Gothic","Avenir Next",Futura,sans-serif;--cu:Barlow,"Segoe UI",system-ui,sans-serif}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--tx);font:15px/1.5 var(--cu);-webkit-text-size-adjust:100%}
h1,h2,h3,.kv,.pn,figcaption{font-family:var(--ti)}
[hidden]{display:none!important}
.saltar{position:absolute;left:-999px;top:8px;z-index:50;background:#fff;color:var(--ink);padding:8px 12px;border-radius:8px;font-weight:600}
.saltar:focus{left:12px}
h1:focus,h2:focus,main:focus{outline:none}
.lgm{display:block;color:var(--ink)}
:focus-visible{outline:3px solid var(--lima2);outline-offset:2px}
/* acceso: página clara, barra con el logo y una tarjeta por reporte */
#acceso{min-height:100vh;background:#F7F8F5;display:flex;flex-direction:column}
.barra{background:#fff;border-bottom:1px solid var(--ln);display:flex;align-items:center;gap:22px;padding:12px clamp(20px,6vw,88px)}
.marca{margin:0;-webkit-tap-highlight-color:transparent;user-select:none;-webkit-user-select:none}
.marca .lgm{width:72px;height:auto}
.razon{font:400 14px/2.4 var(--ti);letter-spacing:.2em;text-transform:uppercase;color:var(--ink);padding-left:22px;border-left:1px solid var(--ln)}
.priv{margin-left:auto;display:flex;align-items:center;gap:9px;color:var(--tx2);font-size:15px;white-space:nowrap}
.priv svg,.pie svg{width:20px;height:20px;flex:none}
.acc{width:100%;max-width:1348px;margin:0 auto;padding:clamp(28px,6vh,60px) 24px 30px;flex:1}
.ceja{text-align:center;font:600 14px var(--ti);letter-spacing:.34em;text-transform:uppercase;color:var(--lima2);margin:0 0 10px}
.acc h1{text-align:center;font:600 clamp(38px,5vw,60px)/1.05 var(--ti);letter-spacing:-.025em;margin:0}
.sub{text-align:center;font-size:clamp(17px,1.7vw,22px);color:var(--tx2);margin:14px 0 clamp(30px,6vh,54px)}
.rdh{display:flex;justify-content:space-between;align-items:baseline;gap:12px;margin:0 0 20px}
.rdh h2{font:600 25px var(--ti);letter-spacing:-.01em;margin:0}
.rdh span{color:var(--tx2);font-size:17px}
.puertas{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,420px),1fr));gap:30px}
.puerta{background:#fff;border:1px solid var(--ln);border-radius:12px;box-shadow:0 1px 2px rgba(26,26,26,.04);padding:32px 34px 12px;display:flex;flex-direction:column}
.pc{display:flex;gap:28px;align-items:flex-start;flex:1;padding-bottom:24px;border-bottom:1px solid var(--ln);margin-bottom:22px}
.ico{flex:none;width:104px;height:104px;border-radius:14px;background:var(--lima0);color:var(--lima2);display:grid;place-items:center}
.ico svg{width:48px;height:48px}
.puerta h3{font:600 27px/1.15 var(--ti);letter-spacing:-.015em;margin:16px 0 8px}
.pc p{margin:0;color:var(--tx2);font-size:18px;line-height:1.45;max-width:23em}
.per{display:inline-flex;align-items:center;gap:10px;margin-top:14px;background:var(--lima0);color:#2C3A14;border-radius:22px;padding:8px 18px;font-size:15.5px}
.per svg{width:18px;height:18px;color:var(--lima2)}
.fm{display:flex;flex-direction:column;gap:10px}
.fm label{font-weight:500;font-size:16px}
.campo{position:relative;margin-bottom:10px}
.campo input{font:inherit;font-size:16.5px;width:100%;padding:15px 54px 15px 20px;border:1px solid #8A8F84;border-radius:8px;background:#fff;color:var(--tx)}
.campo input::placeholder{color:#6B7066}
input[aria-invalid=true]{border-color:#C62828!important;box-shadow:0 0 0 1px #C62828}
.ojo{position:absolute;right:5px;top:50%;transform:translateY(-50%);width:44px;height:44px;border:0;border-radius:6px;background:none;color:var(--tx2);cursor:pointer;display:grid;place-items:center}
.ojo svg{width:24px;height:24px}
.ojo[aria-pressed=true]{color:var(--lima2)}
.entrar{font:600 18px var(--ti);padding:16px 22px;border:0;border-radius:8px;background:var(--lima);color:var(--ink);cursor:pointer;display:flex;align-items:center;justify-content:center;gap:12px}
.entrar svg{width:20px;height:20px}
.entrar:hover{background:#A9D64F}
.entrar[disabled]{opacity:.6;cursor:wait}
.msj{min-height:1.5em;margin:8px 0 0;font-size:14.5px;color:#C62828}
.pronto{align-self:flex-start;color:var(--tx2);font:500 15px var(--ti);border:1px solid var(--ln);padding:9px 14px;border-radius:8px;margin-bottom:8px}
.pie{display:flex;justify-content:center;align-items:center;gap:12px;color:var(--tx2);font-size:15px;margin:42px 0 0}
.pie.err{color:#B3261E;font-weight:600;flex-wrap:wrap}
.fin{display:flex;justify-content:space-between;gap:8px 16px;flex-wrap:wrap;border-top:1px solid var(--ln);margin:0 clamp(20px,4vw,60px);padding:22px 4px 26px;color:var(--tx2);font-size:14px}
/* aplicación: misma barra clara que el inicio */
.cab{position:sticky;top:0;z-index:30;background:#fff;color:var(--ink);border-bottom:1px solid var(--ln)}
.cab .in{display:flex;align-items:center;gap:16px;padding:9px 20px 3px;max-width:1680px;margin:0 auto}
.cab .logo{display:flex;align-items:center}
.cab .logo .lgm{width:46px;height:auto;color:var(--ink)}
.cab .donde{font:600 20px/1.2 var(--ti);letter-spacing:-.01em;padding-left:16px;border-left:1px solid var(--ln)}
.bt,#salir,#salir-adm{font:500 14.5px var(--cu);background:#fff;color:var(--ink);border:1px solid #8A8F84;border-radius:8px;padding:7px 14px;cursor:pointer;white-space:nowrap}
.bt:hover,#salir:hover,#salir-adm:hover{border-color:var(--ink)}
#salir-adm{margin-left:auto}
.imp{margin-left:auto;position:relative}
.imp .bt{display:flex;align-items:center;gap:8px}
.imp .bt svg{width:17px;height:17px}
#imp-menu{position:absolute;right:0;top:calc(100% + 6px);background:#fff;border:1px solid var(--ln);border-radius:10px;box-shadow:0 8px 24px rgba(26,26,26,.12);padding:6px;min-width:250px;z-index:40;display:flex;flex-direction:column}
#imp-menu button{font:500 15px var(--cu);text-align:left;background:none;border:0;border-radius:6px;padding:9px 12px;cursor:pointer;color:var(--ink)}
#imp-menu button:hover{background:var(--lima0)}
#imp-menu small{display:block;font-weight:400;color:var(--tx2);font-size:13px}
.tabs{display:flex;gap:2px;overflow-x:auto;padding:0 20px;max-width:1680px;margin:0 auto;scrollbar-width:none}
.tabs::-webkit-scrollbar{display:none}
.tabs button{font:500 15.5px var(--ti);background:none;border:0;color:var(--tx2);padding:9px 12px 8px;cursor:pointer;white-space:nowrap;border-bottom:3px solid transparent}
.tabs button:hover{color:var(--ink)}
.tabs button[aria-current="true"]{color:var(--ink);font-weight:600;border-bottom-color:var(--lima)}
.tabs .sep{flex:none;width:1px;background:var(--ln);margin:9px 8px}
.imp-cab{display:none}
main{max-width:1680px;margin:0 auto;padding:0 20px 90px}
.aph{padding:34px 0 6px}
.aph h1{font-size:clamp(34px,4.6vw,54px);font-weight:600;line-height:1.02;margin:0;letter-spacing:-.015em}
.aph p{margin:10px 0 0;color:var(--tx2);max-width:80ch}
.subnav{position:sticky;top:var(--cabh,96px);z-index:20;background:var(--bg);display:flex;gap:0;overflow-x:auto;border-bottom:1px solid var(--ln);margin:16px -20px 0;padding:0 12px;scrollbar-width:none}
.subnav::-webkit-scrollbar{display:none}
.subnav a{font:500 14.5px var(--cu);color:var(--tx2);text-decoration:none;padding:11px 9px 9px;white-space:nowrap;border-bottom:3px solid transparent}
.subnav a:hover{color:var(--ink)}
.subnav a[aria-current="true"]{color:var(--ink);font-weight:600;border-bottom-color:var(--lima)}
section{padding-top:46px;scroll-margin-top:calc(var(--cabh,96px) + 46px)}
section>h2{font-size:29px;font-weight:600;line-height:1.1;letter-spacing:-.01em;margin:0 0 12px;padding-left:13px;border-left:5px solid var(--lima)}
h3{font-size:19px;font-weight:600;margin:30px 0 10px}
.lead{font-size:18.5px;line-height:1.5;max-width:74ch;margin:8px 0 18px}
.nota{color:var(--tx2);max-width:100ch;margin:6px 0 12px;font-size:14.5px}
.aviso{background:#FFF7E0;border-left:4px solid #E65100;border-radius:0 6px 6px 0;padding:10px 14px;max-width:100ch;font-size:14.5px}
.franja{display:flex;height:14px;gap:2px;border-radius:7px;overflow:hidden;max-width:980px}
.ley{display:flex;flex-wrap:wrap;gap:4px 20px;margin:10px 0 4px;font-size:14px;color:var(--tx2)}
.le i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px}
.le b{color:var(--tx)}
/* indicadores: una regla arriba y el número; el dato principal va primero y más grande */
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:22px 26px;margin:14px 0 6px}
.kpi{border-top:2px solid var(--ink);padding:10px 0 0;min-width:0}
.kv{font-size:27px;font-weight:500;line-height:1.08;letter-spacing:-.01em;font-variant-numeric:tabular-nums;white-space:nowrap}
.kl{font-size:14.5px;font-weight:600;margin-top:4px}
.kn{font-size:13px;color:var(--tx2);line-height:1.35}
/* variación contra el mes anterior: flecha y signo dicen el sentido; el color, si es mejor o peor */
.kd{font-size:13px;font-weight:600;color:var(--tx2);margin-top:5px;white-space:nowrap}
.kd-p{color:#B3261E}.kd-m{color:#2E7D32}
.kd-p::after{content:" · peor"}.kd-m::after{content:" · mejor"}
.kpi.kpi-h .kd{font-size:15.5px;margin-top:7px}
.kpi.kpi-h{order:-1;grid-column:span 2;border-top:5px solid var(--lima)}
.kpi.kpi-h .kv{font-size:58px;font-weight:600;line-height:1}
.kpi.kpi-h .kl{font-size:16px}
.kpi[data-e]{border-top-width:4px}
.kpi[data-e=c]{border-top-color:#C62828}.kpi[data-e=a]{border-top-color:#E65100}.kpi[data-e=n]{border-top-color:#2E7D32}.kpi[data-e=b]{border-top-color:#1565C0}.kpi[data-e=i]{border-top-color:#455A64}
.tw{overflow:auto;border:1px solid var(--ln);border-radius:6px;max-width:100%;max-height:calc(100vh - var(--cabh,96px) - 64px);max-height:calc(100dvh - var(--cabh,96px) - 64px)}
.tw.mas{-webkit-mask-image:linear-gradient(90deg,#000 calc(100% - 34px),transparent);mask-image:linear-gradient(90deg,#000 calc(100% - 34px),transparent)}
thead{position:sticky;top:0;z-index:3}
table{border-collapse:collapse;width:100%;font-size:13.5px;font-variant-numeric:tabular-nums}
th{background:var(--ink);color:#fff;font:600 13px/1.25 var(--cu);letter-spacing:.01em;padding:9px 9px;white-space:nowrap;text-align:left}
td{padding:6px 9px;border-top:1px solid var(--ln);vertical-align:top;white-space:nowrap}
td.r,th.r{text-align:right}
tbody tr:nth-child(even) td{background:var(--bg2)}
tbody tr:hover td{background:var(--lima0)}
tr.tot td{font-weight:700;background:var(--lima0)!important;border-top:2px solid var(--ink)}
td .obs{white-space:normal;display:inline-block;min-width:240px;max-width:520px;color:var(--tx2);font-size:13px;line-height:1.35}
.est[style*="E65100"]{background:#B84A00!important}
.est{display:inline-block;color:#fff;font:600 12.5px/1.3 var(--cu);padding:2px 8px;border-radius:3px;white-space:nowrap}
.tag{display:inline-block;background:var(--ink);color:#fff;font-size:12px;font-weight:500;padding:1px 6px;border-radius:3px}
.bd{width:110px;height:11px;display:block;margin-top:4px}
.nc{color:#8a5a00}
.sm{color:var(--tx2);font-weight:400;font-size:14px}
.vac{color:#6B7066}
.mz{padding-left:13px}
details.hist{border:1px solid var(--ln);border-radius:6px;margin:6px 0;overflow:hidden}
details.hist>summary{cursor:pointer;padding:10px 13px;font-size:15px;list-style-position:inside}
details.hist>summary:hover{background:var(--bg2)}
details.hist[open]>summary{background:var(--lima0);border-bottom:1px solid var(--ln)}
details.hist .tw{border:0;border-radius:0}
ul.hechos{margin:6px 0;padding-left:20px;max-width:100ch}
ul.hechos li{margin:6px 0}
ul.hechos li::marker{color:var(--lima2)}
.pods{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:22px 28px;margin:16px 0 12px}
.pod{border-top:2px solid var(--ink);padding:11px 0 4px}
.pt{font-size:14px;font-weight:600;color:var(--tx2)}
.pn{font-size:26px;font-weight:600;line-height:1.1;letter-spacing:-.01em;margin:5px 0 3px}
.pl{font-weight:600;font-variant-numeric:tabular-nums}
.pd{font-size:13.5px;color:var(--tx2);margin-top:6px;line-height:1.4}
.dos{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:26px;margin:16px 0 20px}
figure{margin:0}
figcaption{font-size:16px;font-weight:600;margin-bottom:6px}
.chart{width:100%;height:auto;display:block}
.chart .ax{font:12px var(--cu);fill:#5A6055}
.chart .dl{font:600 13px var(--cu);fill:#1A1A1A}
.chart .in{font:600 12px var(--cu);fill:#fff}
@media (max-width:900px){
 .tabs{-webkit-mask-image:linear-gradient(90deg,transparent 0,#000 18px,#000 calc(100% - 30px),transparent);mask-image:linear-gradient(90deg,transparent 0,#000 18px,#000 calc(100% - 30px),transparent)}
}
@media (max-width:640px){
 .barra{gap:12px;padding:10px 16px}.marca .lgm{width:52px}.razon{font-size:10.5px;letter-spacing:.14em;line-height:1.5;padding-left:12px}.priv span{display:none}
 .acc{padding:26px 16px 24px}.ceja{font-size:12px}.rdh h2{font-size:21px}.rdh span{font-size:15px}.puertas{gap:18px}
 .puerta{padding:20px 18px 8px}.pc{gap:16px;padding-bottom:18px;margin-bottom:18px}.ico{width:64px;height:64px;border-radius:10px}.ico svg{width:32px;height:32px}
 .puerta h3{font-size:22px;margin:2px 0 6px}.pc p{font-size:15.5px}.per{font-size:14px;padding:6px 14px}.pie{margin-top:28px;font-size:14px;text-align:center}.fin{margin:0 16px;font-size:13px}
 main{padding:0 16px 70px}.cab .in{padding:9px 16px 2px}.tabs{padding:0 8px}.subnav{margin:14px -16px 0;padding:0 8px}
 .aph{padding-top:24px}.aph h1{font-size:34px}
 section{padding-top:36px}section>h2{font-size:24px}.lead{font-size:17px}
 .kpis{grid-template-columns:1fr 1fr;gap:18px 18px}.kv{font-size:24px}.kl{font-size:13.5px}.kn{font-size:12.5px}
 .kpi.kpi-h .kv{font-size:50px}
 .cab .donde{font-size:17px;padding-left:12px}.cab .in{gap:10px}.cab .logo .lgm{width:38px}.imp .bt span{display:none}.imp .bt{padding:7px 10px}
 .apartado:not(.gst) td:first-child,.apartado:not(.gst) th:first-child{position:sticky;left:0;z-index:1}
 .apartado:not(.gst) th:first-child{z-index:2}
 .apartado:not(.gst) td:first-child{background:#fff;border-right:1px solid var(--ln)}
 .apartado:not(.gst) table.c1l td:first-child{white-space:normal;min-width:44vw;max-width:44vw}
 .apartado:not(.gst) tbody tr:nth-child(even) td:first-child{background:var(--bg2)}
}
/* dedos: nada que se toque mide menos de 44 px */
@media (pointer:coarse){
 .chips button{min-height:44px;padding:9px 14px}.bt,#salir,#salir-adm{min-height:44px;min-width:44px}.cab .in{gap:12px}
 .subnav a{padding-top:13px;padding-bottom:11px}.tabs button{padding-top:11px;padding-bottom:10px}.lnk{display:inline-block;padding:11px 6px;margin:-9px 0}
}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
@media print{
 @page{size:A4 landscape;margin:11mm 10mm 12mm}
 *{-webkit-print-color-adjust:exact;print-color-adjust:exact}
 html{scroll-behavior:auto}body{background:#fff;font-size:11.5px}
 .cab,.subnav,.chips,#acceso,#adm,#previa{display:none!important}
 .imp-cab{display:flex;align-items:center;gap:12px;border-bottom:2px solid var(--ink);padding-bottom:8px}
 .imp-cab .lgm{width:46px;height:auto}
 .imp-cab b{display:block;font:600 14px var(--ti);letter-spacing:.14em;text-transform:uppercase}
 .imp-cab span{color:var(--tx2);font-size:11px}
 .imp-cab .f{margin-left:auto;text-align:right}
 main{max-width:none;padding:0}
 .aph{padding:10px 0 0}.aph h1,.gst .aph h1{font-size:24px}.aph p{margin-top:4px}
 section{padding-top:14px}section>h2,.gst section>h2{font-size:16px;margin-bottom:6px;break-after:avoid}
 h3{font-size:13px;margin:12px 0 5px;break-after:avoid}
 .lead{font-size:13px;max-width:none;margin:4px 0 10px}.nota,.aviso,ul.hechos,.gp{max-width:none;font-size:11px}
 .kpis{grid-template-columns:repeat(7,1fr);gap:10px 14px;margin:8px 0 4px}.gk{grid-template-columns:repeat(4,1fr)}
 .kpi{padding-top:6px}.kv,.gk .kv{font-size:17px}.kpi.kpi-h .kv{font-size:32px}.kl,.kpi.kpi-h .kl{font-size:10.5px}.gk .kl{font-size:9px}.kn,.kd,.kpi.kpi-h .kd{font-size:9.5px}
 .pods{grid-template-columns:repeat(4,1fr);gap:10px 14px}.pn{font-size:16px}.pd,.pt{font-size:10px}
 .tw{overflow:visible;max-height:none;border:0;border-radius:0;-webkit-mask-image:none;mask-image:none}thead{position:static}table{font-size:9.5px}
 th,.gst th{position:static;padding:4px 5px;font-size:9px}td,.gst td{padding:2.5px 5px;white-space:normal;font-size:9.5px}
 td .obs,.gst td .obs{min-width:0;max-width:none;font-size:9px}
 thead{display:table-header-group}tr,.kpi,.pod,figure,.aviso{break-inside:avoid}
 .gst[data-grupo]{display:block}
 details.hist{border:0;margin:8px 0}details.hist>summary{padding:4px 0;list-style:none;font-weight:600}
 body[data-imp=resumen] .imp-o{display:none}
}
"""

JS = r"""
(function(){
"use strict";
// ── SHA-256, HMAC, PBKDF2 y AES-256-CTR en JavaScript puro: el archivo abre igual sin conexión
//    y en visores donde el navegador no ofrece crypto.subtle. ──
var K=new Uint32Array([0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2]);
var W=new Int32Array(64);
function comp(H,b,o){var i,a=H[0],bb=H[1],c=H[2],d=H[3],e=H[4],f=H[5],g=H[6],h=H[7],t1,t2,s0,s1;
 for(i=0;i<16;i++)W[i]=(b[o+4*i]<<24)|(b[o+4*i+1]<<16)|(b[o+4*i+2]<<8)|b[o+4*i+3];
 for(i=16;i<64;i++){s0=W[i-15];s0=((s0>>>7)|(s0<<25))^((s0>>>18)|(s0<<14))^(s0>>>3);s1=W[i-2];s1=((s1>>>17)|(s1<<15))^((s1>>>19)|(s1<<13))^(s1>>>10);W[i]=(W[i-16]+s0+W[i-7]+s1)|0;}
 for(i=0;i<64;i++){t1=(h+(((e>>>6)|(e<<26))^((e>>>11)|(e<<21))^((e>>>25)|(e<<7)))+((e&f)^(~e&g))+K[i]+W[i])|0;
  t2=((((a>>>2)|(a<<30))^((a>>>13)|(a<<19))^((a>>>22)|(a<<10)))+((a&bb)^(a&c)^(bb&c)))|0;h=g;g=f;f=e;e=(d+t1)|0;d=c;c=bb;bb=a;a=(t1+t2)|0;}
 H[0]=(H[0]+a)|0;H[1]=(H[1]+bb)|0;H[2]=(H[2]+c)|0;H[3]=(H[3]+d)|0;H[4]=(H[4]+e)|0;H[5]=(H[5]+f)|0;H[6]=(H[6]+g)|0;H[7]=(H[7]+h)|0;}
function ini(){return new Int32Array([0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19]);}
function fin(H,msg,pre){// msg: bytes restantes; pre: bytes ya procesados
 var l=msg.length,tot=(pre+l),n=((l+9+63)>>6)<<6,b=new Uint8Array(n),i;b.set(msg);b[l]=0x80;
 var bits=tot*8,hi=Math.floor(tot/0x20000000);b[n-8]=hi>>>24;b[n-7]=hi>>>16;b[n-6]=hi>>>8;b[n-5]=hi;b[n-4]=bits>>>24;b[n-3]=bits>>>16;b[n-2]=bits>>>8;b[n-1]=bits;
 for(i=0;i<n;i+=64)comp(H,b,i);var o=new Uint8Array(32);for(i=0;i<8;i++){o[4*i]=H[i]>>>24;o[4*i+1]=H[i]>>>16;o[4*i+2]=H[i]>>>8;o[4*i+3]=H[i];}return o;}
function sha256(m){var H=ini(),i,n=m.length-(m.length%64);for(i=0;i<n;i+=64)comp(H,m,i);return fin(H,m.subarray(n),n);}
function hmacEst(key){if(key.length>64)key=sha256(key);var ip=new Uint8Array(64),op=new Uint8Array(64),i;for(i=0;i<64;i++){var k=key[i]||0;ip[i]=k^0x36;op[i]=k^0x5c;}
 var a=ini(),b=ini();comp(a,ip,0);comp(b,op,0);return{a:a,b:b};}
function hmac(est,m){var H=new Int32Array(est.a),i,n=m.length-(m.length%64);for(i=0;i<n;i+=64)comp(H,m,i);var d=fin(H,m.subarray(n),64+n);var G=new Int32Array(est.b);return fin(G,d,64);}
function pbkdf2(pw,salt,it,len){var est=hmacEst(pw),out=new Uint8Array(len),bl,i,j,off=0;
 for(bl=1;off<len;bl++){var s=new Uint8Array(salt.length+4);s.set(salt);s[salt.length+3]=bl;var u=hmac(est,s),t=new Uint8Array(u);
  for(i=1;i<it;i++){u=hmac(est,u);for(j=0;j<32;j++)t[j]^=u[j];}out.set(t.subarray(0,Math.min(32,len-off)),off);off+=32;}return out;}
// AES
var SB=new Uint8Array(256),T0=new Uint32Array(256),T1=new Uint32Array(256),T2=new Uint32Array(256),T3=new Uint32Array(256);
(function(){var p=1,q=1,i;do{p=p^(p<<1)^(p&0x80?0x11b:0);p&=255;q^=q<<1;q^=q<<2;q^=q<<4;q&=255;if(q&0x80)q^=0x09;var x=q^((q<<1)|(q>>>7))^((q<<2)|(q>>>6))^((q<<3)|(q>>>5))^((q<<4)|(q>>>4));SB[p]=(x^0x63)&255;}while(p!==1);SB[0]=0x63;
 for(i=0;i<256;i++){var s=SB[i],s2=((s<<1)^(s&0x80?0x11b:0))&255,s3=s2^s;T0[i]=((s2<<24)|(s<<16)|(s<<8)|s3)>>>0;T1[i]=((s3<<24)|(s2<<16)|(s<<8)|s)>>>0;T2[i]=((s<<24)|(s3<<16)|(s2<<8)|s)>>>0;T3[i]=((s<<24)|(s<<16)|(s3<<8)|s2)>>>0;}})();
function expandir(k){var w=new Uint32Array(60),i,t,rc=1;for(i=0;i<8;i++)w[i]=((k[4*i]<<24)|(k[4*i+1]<<16)|(k[4*i+2]<<8)|k[4*i+3])>>>0;
 for(i=8;i<60;i++){t=w[i-1];if(i%8===0){t=((SB[(t>>>16)&255]<<24)|(SB[(t>>>8)&255]<<16)|(SB[t&255]<<8)|SB[t>>>24])>>>0;t=(t^(rc<<24))>>>0;rc=((rc<<1)^(rc&0x80?0x11b:0))&255;}
  else if(i%8===4){t=((SB[t>>>24]<<24)|(SB[(t>>>16)&255]<<16)|(SB[(t>>>8)&255]<<8)|SB[t&255])>>>0;}w[i]=(w[i-8]^t)>>>0;}return w;}
function bloque(w,inp,out){var s0=(((inp[0]<<24)|(inp[1]<<16)|(inp[2]<<8)|inp[3])^w[0])>>>0,s1=(((inp[4]<<24)|(inp[5]<<16)|(inp[6]<<8)|inp[7])^w[1])>>>0,s2=(((inp[8]<<24)|(inp[9]<<16)|(inp[10]<<8)|inp[11])^w[2])>>>0,s3=(((inp[12]<<24)|(inp[13]<<16)|(inp[14]<<8)|inp[15])^w[3])>>>0,t0,t1,t2,t3,r,k=4;
 for(r=1;r<14;r++){t0=T0[s0>>>24]^T1[(s1>>>16)&255]^T2[(s2>>>8)&255]^T3[s3&255]^w[k];t1=T0[s1>>>24]^T1[(s2>>>16)&255]^T2[(s3>>>8)&255]^T3[s0&255]^w[k+1];t2=T0[s2>>>24]^T1[(s3>>>16)&255]^T2[(s0>>>8)&255]^T3[s1&255]^w[k+2];t3=T0[s3>>>24]^T1[(s0>>>16)&255]^T2[(s1>>>8)&255]^T3[s2&255]^w[k+3];s0=t0>>>0;s1=t1>>>0;s2=t2>>>0;s3=t3>>>0;k+=4;}
 t0=((SB[s0>>>24]<<24)|(SB[(s1>>>16)&255]<<16)|(SB[(s2>>>8)&255]<<8)|SB[s3&255])^w[k];t1=((SB[s1>>>24]<<24)|(SB[(s2>>>16)&255]<<16)|(SB[(s3>>>8)&255]<<8)|SB[s0&255])^w[k+1];t2=((SB[s2>>>24]<<24)|(SB[(s3>>>16)&255]<<16)|(SB[(s0>>>8)&255]<<8)|SB[s1&255])^w[k+2];t3=((SB[s3>>>24]<<24)|(SB[(s0>>>16)&255]<<16)|(SB[(s1>>>8)&255]<<8)|SB[s2&255])^w[k+3];
 out[0]=t0>>>24;out[1]=t0>>>16;out[2]=t0>>>8;out[3]=t0;out[4]=t1>>>24;out[5]=t1>>>16;out[6]=t1>>>8;out[7]=t1;out[8]=t2>>>24;out[9]=t2>>>16;out[10]=t2>>>8;out[11]=t2;out[12]=t3>>>24;out[13]=t3>>>16;out[14]=t3>>>8;out[15]=t3;}
function ctr(key,iv,data){var w=expandir(key),c=new Uint8Array(iv),ks=new Uint8Array(16),out=new Uint8Array(data.length),i,j;
 for(i=0;i<data.length;i+=16){bloque(w,c,ks);for(j=0;j<16&&i+j<data.length;j++)out[i+j]=data[i+j]^ks[j];for(j=15;j>=0;j--){c[j]=(c[j]+1)&255;if(c[j])break;}}return out;}
function b64(s){var bin=atob(s),o=new Uint8Array(bin.length),i;for(i=0;i<bin.length;i++)o[i]=bin.charCodeAt(i);return o;}
function utf8(s){if(window.TextEncoder)return new TextEncoder().encode(s);var u=unescape(encodeURIComponent(s)),o=new Uint8Array(u.length),i;for(i=0;i<u.length;i++)o[i]=u.charCodeAt(i);return o;}
function derivar(pw,salt,it){
 if(pw instanceof Uint8Array){if(it!==0||pw.length!==64)return Promise.reject(new Error("clave"));return Promise.resolve(pw);}
 if(it===0)return Promise.reject(new Error("clave"));
 return new Promise(function(ok){var listo=false;function puro(){if(listo)return;listo=true;ok(pbkdf2(utf8(pw),salt,it,64));}
  try{if(window.crypto&&crypto.subtle&&crypto.subtle.importKey){var t=setTimeout(puro,2500+Math.round(it/100));
   crypto.subtle.importKey("raw",utf8(pw),"PBKDF2",false,["deriveBits"]).then(function(k){return crypto.subtle.deriveBits({name:"PBKDF2",salt:salt,iterations:it,hash:"SHA-256"},k,512);})
   .then(function(b){if(listo)return;listo=true;clearTimeout(t);ok(new Uint8Array(b));},function(){clearTimeout(t);puro();});return;}}catch(e){}
  puro();});}
function mailPlano(m){return String(m||"").trim().toLowerCase();}
function idMail(m){var h=sha256(utf8("lysi-acceso:"+mailPlano(m))),s="",i;for(i=0;i<h.length;i++)s+=String.fromCharCode(h[i]);return btoa(s).replace(/\+/g,"-").replace(/\//g,"_").slice(0,22);}
// Abre un reporte: con accesos por mail (la clave maestra viene envuelta en mail + contraseña) o, si todavía no migró, con la contraseña sola.
function abrirReporte(datos,id,mail,pw){var acc=datos.accesos&&datos.accesos[id];
 if(!acc)return abrir(datos.cajas[id],pw).then(function(h){return{h:h,k:null};});
 var caja=acc[idMail(mail)];if(!caja)return Promise.reject(new Error("mail"));
 return abrir(caja,mailPlano(mail)+"\n"+pw).then(function(kb){var k=b64(kb);return abrir(datos.cajas[id],k).then(function(h){return{h:h,k:k};});});}
function abrir(caja,pw){var salt=b64(caja.s),iv=b64(caja.i),tag=b64(caja.t),ct=b64(caja.c);
 return derivar(pw,salt,caja.n).then(function(dk){var m=new Uint8Array(16+ct.length);m.set(iv);m.set(ct,16);var t=hmac(hmacEst(dk.subarray(32)),m),d=0,i;for(i=0;i<32;i++)d|=t[i]^tag[i];
  if(d)throw new Error("clave");var o=ctr(dk.subarray(0,32),iv,ct);return caja.z?inflar(o):new TextDecoder().decode(o);});}
function inflar(u){if(!window.DecompressionStream)return Promise.reject(new Error("viejo"));
 return new Response(new Blob([u]).stream().pipeThrough(new DecompressionStream("gzip"))).text();}
window.__lysi={sha256:sha256,pbkdf2:pbkdf2,ctr:ctr,hmac:hmac,hmacEst:hmacEst,abrir:abrir};

// ── Interfaz: lo único que hace el JavaScript es abrir con la contraseña y mostrar u ocultar apartados ──
var CAJAS=window.LYSI_CAJAS||{};
var acceso=document.getElementById("acceso"),app=document.getElementById("app"),cont=document.getElementById("contenido"),donde=document.getElementById("donde");
function medir(){var c=document.querySelector(".cab");if(c)document.documentElement.style.setProperty("--cabh",c.offsetHeight+"px");}
function mostrar(id){var aps=cont.querySelectorAll(".apartado"),i,ok=false;for(i=0;i<aps.length;i++){var v=aps[i].id===id;aps[i].hidden=!v;ok=ok||v;}
 if(!ok&&aps.length){aps[aps.length-1].hidden=false;id=aps[aps.length-1].id;}
 var bs=document.querySelectorAll(".tabs button");for(i=0;i<bs.length;i++)bs[i].setAttribute("aria-current",bs[i].getAttribute("data-ir")===id?"true":"false");
 window.scrollTo(0,0);medir();}
document.addEventListener("click",function(ev){var b=ev.target.closest&&ev.target.closest("[data-ir]");if(b){mostrar(b.getAttribute("data-ir"));}});
var forms=document.querySelectorAll("[data-caja]");
Array.prototype.forEach.call(forms,function(fm){
 var id=fm.getAttribute("data-caja"),inp=fm.querySelector("input"),btn=fm.querySelector("button"),msj=document.getElementById("msj-"+id);
 function entrar(){
  var pw=(inp.value||"").trim();
  if(!pw){msj.style.color="";msj.textContent="Escribí la contraseña.";return;}
  btn.disabled=true;msj.style.color="#c9d2cb";msj.textContent="Abriendo…";
  setTimeout(function(){
   var pr;try{pr=abrir(CAJAS[id],pw);}catch(err){pr=Promise.reject(err);}
   pr.then(function(htmlTxt){cont.innerHTML=htmlTxt;var t=cont.querySelector("template[data-tabs]");
     document.getElementById("tabs").innerHTML=t?t.innerHTML:"";donde.textContent=fm.getAttribute("data-nombre");
     acceso.hidden=true;app.hidden=false;inp.value="";msj.textContent="";btn.disabled=false;
     var ini=(cont.querySelector("[data-inicio]")||{getAttribute:function(){return"";}}).getAttribute("data-inicio");mostrar(ini);})
    .catch(function(err){btn.disabled=false;msj.style.color="";
     if(err&&err.message==="clave"){msj.textContent="Contraseña incorrecta. Probá de nuevo.";inp.select();}
     else{msj.textContent="No se pudo abrir en este visor ("+(err&&err.message?err.message:err)+"). Abrí el archivo con Chrome o Edge.";}});
  },40);}
 btn.addEventListener("click",entrar);
 inp.addEventListener("keydown",function(ev){if(ev.key==="Enter"||ev.keyCode===13){ev.preventDefault();entrar();}});
});
document.getElementById("salir").addEventListener("click",function(){cont.innerHTML="";document.getElementById("tabs").innerHTML="";app.hidden=true;acceso.hidden=false;window.scrollTo(0,0);});
window.addEventListener("resize",medir);
})();
"""


def armar(cajas, generado, pie=""):
    """cajas: lista de dicts {id, nombre, descripcion, html (o None si todavía no existe), clave}."""
    import json
    puertas, datos = [], {}
    for c in cajas:
        if c.get("html") is None:
            puertas.append(f'<div class="puerta"><div><h2>{c["nombre"]}</h2><p>{c["descripcion"]}</p></div><span class="pronto">En preparación</span></div>')
            continue
        datos[c["id"]] = cifrar(c["html"], c["clave"])
        puertas.append(f'''<div class="puerta"><div><h2>{c["nombre"]}</h2><p>{c["descripcion"]}</p></div>
<div class="fm" data-caja="{c["id"]}" data-nombre="{c["nombre"]}"><label class="vh" for="pw-{c["id"]}" hidden>Contraseña de {c["nombre"]}</label>
<input id="pw-{c["id"]}" type="password" placeholder="Contraseña" aria-label="Contraseña de {c["nombre"]}" autocomplete="off"><button type="button">Entrar</button></div>
<p class="msj" id="msj-{c["id"]}" role="status"></p></div>''')
    return f'''<!doctype html>
<html lang="es-AR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>LYSI Reportes</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700&family=Jost:wght@400;500;600&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>
<div id="acceso"><div class="cinta"></div><div class="acc">
<p class="marca">LYSI<b>.</b></p>
<p class="sub">Reportes de flota de Logística y Servicios Integrales S.A. Cada reporte se abre con su propia contraseña.</p>
{"".join(puertas)}</div>
<p class="pie">{pie} Generado el {generado}. Este archivo no guarda ni envía la contraseña: sin ella, el contenido no se puede leer.</p></div>
<div id="app" hidden><div class="cab"><div class="in"><span class="logo">LYSI<b>.</b></span><span class="donde" id="donde"></span><button id="salir" type="button">Cerrar</button></div>
<div class="tabs" id="tabs" role="navigation" aria-label="Apartados"></div></div><main id="contenido"></main></div>
<script>window.LYSI_CAJAS={json.dumps(datos)};</script><script>{JS}</script></body></html>'''
