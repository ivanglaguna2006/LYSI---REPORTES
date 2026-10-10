# -*- coding: utf-8 -*-
"""Arma la aplicación LYSI Reportes: un único archivo web con
  · acceso de consulta por contraseña (Combustible y Resultados, cada uno con la suya),
  · acceso de administración con otra contraseña: subir los archivos del mes, procesar y publicar.
El cálculo de la administración corre en el navegador con este mismo código Python (Pyodide)."""
import os
import json
import base64
from . import portal as P

PYODIDE = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/"

CSS_ADM = r"""
.adm-door{border-top:1px solid #2c2f2d;padding:16px 0 0;margin-top:26px;display:flex;gap:10px 18px;align-items:center;flex-wrap:wrap;color:#8d968f;font-size:14px}
.adm-door span{flex:1 1 220px}
.adm-door input{font:inherit;padding:7px 10px;border:1px solid #3a403c;background:#0b0b0b;color:#fff;border-radius:3px;width:190px}
.adm-door button{font:500 15px Barlow,sans-serif;padding:7px 14px;border:1px solid #4a514c;border-radius:3px;background:none;color:#d7ded9;cursor:pointer}
.adm-door .msj{flex-basis:100%;margin:0}
#previa{background:#FFF8E1;border-bottom:2px solid #E65100;padding:8px 20px;display:flex;gap:14px;align-items:center;flex-wrap:wrap;font-size:14.5px}
#previa button,.btn{font:600 16px "Barlow Condensed","Arial Narrow",sans-serif;padding:7px 16px;border-radius:3px;border:1px solid var(--v1);background:#fff;color:var(--v1);cursor:pointer}
.btn.pri{background:var(--v2);color:#fff;border-color:var(--v2);font-size:18px;padding:9px 22px}
.btn.pri:hover{background:var(--v1)}
.btn[disabled]{opacity:.5;cursor:not-allowed}
.btn.mini{font-size:14px;padding:3px 10px}
.btn:focus-visible,#previa button:focus-visible,.mesb:focus-visible,.adm-door button:focus-visible,.adm-door input:focus-visible,.adm input:focus-visible,.adm select:focus-visible{outline:3px solid var(--v3);outline-offset:2px}
.adm section{padding-top:30px}
.adm .pasos{counter-reset:p}
.adm section>h2{counter-increment:p}
.adm section>h2:before{content:counter(p) ". "}
.adm label{font-weight:600;font-size:14.5px}
.adm input[type=text],.adm input[type=password],.adm select{font:inherit;padding:7px 9px;border:1px solid #b9c2bb;border-radius:3px;background:#fff;color:var(--tx)}
.anio{display:flex;gap:10px;align-items:center;margin:8px 0 12px}
.meses{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px;max-width:1100px}
.mesb{text-align:left;font:inherit;border:1px solid var(--ln);background:#fff;border-radius:3px;padding:9px 11px;cursor:pointer;border-left:6px solid #c9cfca}
.mesb b{display:block;font:600 19px "Barlow Condensed","Arial Narrow",sans-serif}
.mesb span{font-size:13px;color:var(--tx2)}
.mesb.ok{border-left-color:var(--v2)}
.mesb.arr{border-left-color:#E65100}
.mesb[aria-pressed=true]{background:var(--v0);border-color:var(--v2)}
.panel{border:1px solid var(--ln);border-radius:3px;padding:14px 16px 16px;margin-top:14px;max-width:1100px}
.panel h3{margin-top:0;font-size:26px}
.slot{display:grid;grid-template-columns:minmax(210px,1.2fr) minmax(180px,1.4fr) auto auto;gap:6px 14px;align-items:center;padding:8px 0;border-top:1px solid var(--ln)}
.slot .q{font-weight:600}
.slot .q small{display:block;font-weight:400;color:var(--tx2);font-size:13px}
.slot .e{font-size:14px;color:var(--tx2);overflow-wrap:anywhere}
.slot .e.si{color:var(--v1);font-weight:600}
.fila{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:8px 0}
.estado{padding:10px 12px;border-left:4px solid var(--v2);background:var(--v0);max-width:1100px;margin:10px 0;font-size:14.5px}
.estado.err{border-left-color:#C62828;background:#FDECEA}
.estado.av{border-left-color:#E65100;background:#FFF8E1}
.sucio{display:inline-block;background:#E65100;color:#fff;font:600 14px "Barlow Condensed","Arial Narrow",sans-serif;padding:1px 9px 2px;border-radius:2px;margin-left:10px;vertical-align:middle}
@media (max-width:700px){.slot{grid-template-columns:1fr}}
"""

CSS_GAS = r"""
.gst .tw{margin:8px 0 14px}
.gst th{white-space:normal;text-align:center;vertical-align:bottom;min-width:62px;position:static;font-size:14px;line-height:1.15}
.gst td.c{text-align:center}
.gst th.gap{background:#fff}
.gst .aph h1{font-size:clamp(30px,4.4vw,54px);line-height:1}
.gst .tw.sl{border:0;margin:14px 0 0}
.gst .tw.sl td{border:0;font:600 20px "Barlow Condensed","Arial Narrow",sans-serif;padding:2px 0}
.gst .gr{color:var(--tx2)}
.gst td .obs{min-width:220px;max-width:460px;color:inherit}
.gst tbody tr:nth-child(even) td{background:transparent}
.gst td{font-size:13.5px}
.gk{margin:10px 0 6px;grid-template-columns:repeat(auto-fit,minmax(235px,1fr))}
.gk .kl{font-size:13px;color:var(--tx2);margin:0 0 3px;text-transform:uppercase;letter-spacing:.02em}
.gk .kv{font-size:29px;white-space:nowrap}
h3.barra{color:#fff;padding:7px 12px;margin:24px 0 8px;font-size:21px;border-radius:3px}
h3.barra.b2{font-size:17px;margin:14px 0 4px}
details.gd>summary{font-weight:600}
details.gd .pt{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:8px}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:14px 0 4px}
.chips button{font:500 15px Barlow,sans-serif;border:1px solid #c5ccc6;background:#fff;color:var(--tx);border-radius:16px;padding:4px 12px;cursor:pointer}
.chips button:hover{background:var(--v0)}
.chips button[aria-current=true]{background:var(--v1);color:#fff;border-color:var(--v1)}
.chips button:focus-visible,.lnk:focus-visible{outline:3px solid var(--v3);outline-offset:2px}
.lnk{font:inherit;font-weight:600;color:var(--v1);background:none;border:0;padding:0;cursor:pointer;text-decoration:underline}
.gfig{margin:12px 0 18px;max-width:1000px}
.gfig img{max-width:100%;height:auto;display:block;border:1px solid var(--ln)}
.gp{max-width:86em;margin:6px 0}
.gst p.aviso{margin:8px 0}
@media (max-width:640px){.gk .kv{font-size:24px}.chips{flex-wrap:nowrap;overflow-x:auto;margin:12px -20px 0;padding:0 20px 6px}.chips button{font-size:14px;padding:4px 11px;white-space:nowrap;flex:none}}
"""

HTML_CUERPO = r"""
<div id="acceso"><div class="cinta"></div><div class="acc">
<p class="marca">LYSI<b>.</b></p>
<p class="sub">Reportes de flota de Logística y Servicios Integrales S.A. Cada reporte se abre con su propia contraseña.</p>
<div class="puerta"><div><h2>Combustible</h2><p id="desc-combustible">Reporte mensual de la flota y evaluación del año.</p></div>
<div class="fm" data-caja="combustible" data-nombre="Combustible"><input id="pw-combustible" type="password" placeholder="Contraseña" aria-label="Contraseña de Combustible" autocomplete="off"><button type="button">Entrar</button></div>
<p class="msj" id="msj-combustible" role="status"></p></div>
<div class="puerta"><div><h2>Reporte de resultados</h2><p id="desc-gastos">Compras y proveedores: resultados del año y gasto de cada mes en mantenimiento, gomería y residuos.</p></div>
<div class="fm" data-caja="gastos" data-nombre="Reporte de resultados" id="fm-gastos" hidden><input id="pw-gastos" type="password" placeholder="Contraseña" aria-label="Contraseña de Reporte de resultados" autocomplete="off"><button type="button">Entrar</button></div><span class="pronto" id="pronto-gastos">En preparación</span>
<p class="msj" id="msj-gastos" role="status"></p></div>
<div class="adm-door" id="adm-door" hidden><span>Administración: cargar los archivos de un mes y publicar.</span>
<input id="pw-admin" type="password" placeholder="Contraseña de administración" aria-label="Contraseña de administración" autocomplete="off"><button type="button" id="btn-admin">Administrar</button>
<p class="msj" id="msj-admin" role="status"></p></div>
</div>
<p class="pie" id="pie">Este archivo no guarda ni envía las contraseñas: sin ellas, el contenido no se puede leer.</p></div>

<div id="app" hidden><div class="cab"><div class="in"><span class="logo">LYSI<b>.</b></span><span class="donde" id="donde"></span><button id="salir" type="button">Cerrar</button></div>
<div class="tabs" id="tabs" role="navigation" aria-label="Apartados"></div>
<div id="previa" hidden><b>Vista previa.</b> Así va a quedar; todavía no está publicado. <button type="button" id="volver-adm">Volver a administración</button></div></div>
<main id="contenido"></main></div>

<div id="adm" class="adm" hidden><div class="cab"><div class="in"><span class="logo">LYSI<b>.</b></span><span class="donde">Administración</span><button id="salir-adm" type="button" style="margin-left:auto;font:500 15px Barlow,sans-serif;background:none;color:#fff;border:1px solid #555;border-radius:3px;padding:6px 12px;cursor:pointer">Cerrar</button></div></div>
<main class="pasos">
<header class="aph"><h1>Administración <span class="sucio" id="sucio" hidden>Cambios sin publicar</span></h1>
<p>Subís los archivos del mes, el software calcula con las reglas v<span id="reglas"></span> y publicás. Nadie más entra acá.</p></header>
<section><h2>Elegí el mes y subí sus archivos</h2>
<p class="nota">Cada mes lleva cuatro archivos tal como bajan de cada plataforma. Para medir un mes también tiene que estar cargado el mes anterior: de ahí sale el arranque de cada ventana.</p>
<div class="anio"><label for="anio">Año</label><select id="anio"></select></div>
<div class="meses" id="meses"></div>
<div class="panel" id="panel" hidden></div></section>
<section><h2>Reporte de resultados</h2>
<p class="nota">Subí juntos los dos Excel del reporte de resultados tal como los generás: el reporte mensual (una hoja por mes) y el de resultados del año. La aplicación los muestra como están, no recalcula nada. Si no subís nada, Resultados queda como está publicado.</p>
<div class="fila"><label for="gas-arch">Excel de resultados</label><input type="file" id="gas-arch" multiple accept=".xlsx,.xlsm"></div>
<div id="gas-estado" role="status"></div></section>
<section><h2>Procesá y revisá</h2>
<p class="nota">El cálculo corre en esta computadora y necesita internet la primera vez de cada sesión (unos segundos). Los archivos no salen de acá.</p>
<div class="fila"><button type="button" class="btn pri" id="procesar">Procesar todo</button><button type="button" class="btn" id="ver-previa" disabled>Ver vista previa</button><button type="button" class="btn" id="ver-previa-g" disabled>Vista previa de Resultados</button></div>
<div id="proc-estado" role="status"></div><div id="proc-res"></div></section>
<section><h2>Publicá</h2>
<p class="nota" id="pub-nota"></p>
<div class="fila"><label for="cl-comb">Contraseña de Combustible</label><input type="text" id="cl-comb" autocomplete="off"><label for="cl-gas">Contraseña de Resultados</label><input type="text" id="cl-gas" autocomplete="off"><label for="cl-adm">Contraseña de administración</label><input type="text" id="cl-adm" autocomplete="off"></div>
<div class="fila"><button type="button" class="btn pri" id="publicar" disabled>Publicar</button><button type="button" class="btn" id="copia" disabled>Guardar una copia en archivo</button></div>
<div id="pub-estado" role="status"></div></section>
<section><h2>Dónde se publica</h2>
<p class="nota" id="gh-nota"></p>
<div class="fila"><label for="gh-o">Cuenta de GitHub</label><input type="text" id="gh-o" size="18" autocomplete="off"><label for="gh-r">Repositorio</label><input type="text" id="gh-r" size="18" autocomplete="off"><label for="gh-t">Token</label><input type="password" id="gh-t" size="30" autocomplete="off"></div>
<div class="fila"><button type="button" class="btn" id="gh-probar">Guardar y probar la conexión</button></div>
<div id="gh-estado" role="status"></div></section>
</main></div>
"""

JS_UI = r"""
function b64(s){var bin=atob(s),o=new Uint8Array(bin.length),i;for(i=0;i<bin.length;i++)o[i]=bin.charCodeAt(i);return o;}
function a64(u){var s="",i;for(i=0;i<u.length;i+=0x8000)s+=String.fromCharCode.apply(null,u.subarray(i,i+0x8000));return btoa(s);}
function azar(n){var o=new Uint8Array(n);if(window.crypto&&crypto.getRandomValues)crypto.getRandomValues(o);else for(var i=0;i<n;i++)o[i]=Math.floor(Math.random()*256);return o;}
function cifrar(texto,pw,z){var salt=azar(16),iv=azar(16),n=LYSI.iter||120000;
 var pd=z?new Response(new Blob([texto]).stream().pipeThrough(new CompressionStream("gzip"))).arrayBuffer().then(function(b){return new Uint8Array(b);}):Promise.resolve(utf8(texto));
 return pd.then(function(datos){return derivar(pw,salt,n).then(function(dk){var ct=ctr(dk.subarray(0,32),iv,datos),m=new Uint8Array(16+ct.length);m.set(iv);m.set(ct,16);
  var c={s:a64(salt),i:a64(iv),t:a64(hmac(hmacEst(dk.subarray(32)),m)),c:a64(ct),n:n};if(z)c.z=1;return c;});});}
window.__lysi={sha256:sha256,pbkdf2:pbkdf2,ctr:ctr,hmac:hmac,hmacEst:hmacEst,abrir:abrir,cifrar:cifrar};

var $=function(id){return document.getElementById(id);};
var acceso=$("acceso"),app=$("app"),adm=$("adm"),cont=$("contenido");
var MESES=["","enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"];
var TIPOS=[["cargas","Cargas de la tarjeta YPF","ReporteConsumos"],["filarus","Km de Filarus","KmRecorridos"],["malla","Malla de tanque de My Scania","Informe de combustible"],["resumen","Resumen de My Scania","Resumen de rendimientos"]];
function esc(s){return String(s==null?"":s).replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c];});}
function num(v,d){if(v==null)return"—";var p=Number(v).toFixed(d||0).split(".");p[0]=p[0].replace(/\B(?=(\d{3})+(?!\d))/g," ");return p.join(",");}
function pintarInfo(){var inf=LYSI.info||{};if(inf.meses&&inf.meses.length)$("desc-combustible").textContent="Reporte mensual de la flota y evaluación del año. Meses cargados: "+inf.meses.join(", ")+".";
 $("pie").textContent="Reglas de cálculo v"+(inf.reglas||"")+". Publicado el "+(inf.generado||"—")+". Este archivo no guarda ni envía las contraseñas: sin ellas, el contenido no se puede leer.";$("reglas").textContent=inf.reglas||"";}
function pintarGastos(){var hay=!!(LYSI.cajas&&LYSI.cajas.gastos),inf=LYSI.info||{};$("fm-gastos").hidden=!hay;$("pronto-gastos").hidden=hay;
 $("desc-gastos").textContent="Compras y proveedores: resultados del año y gasto de cada mes en mantenimiento, gomería y residuos."+(hay&&inf.gastos?" Cargado: "+inf.gastos+".":"");}
pintarGastos();pintarInfo();
// El acceso de administración no se muestra en el inicio: aparece solo entrando con #admin al final de la dirección.
function verPuertaAdm(){var v=/^#admin$/i.test(location.hash);$("adm-door").hidden=!v;if(v)setTimeout(function(){try{$("pw-admin").focus();}catch(e){}},50);}
verPuertaAdm();window.addEventListener("hashchange",verPuertaAdm);
// Mismo link para todos: el acceso aparece tocando cinco veces seguidas el punto verde del logo.
(function(){var p=document.querySelector("#acceso .marca b"),n=0,t=null;if(!p)return;
 p.addEventListener("click",function(){n++;clearTimeout(t);t=setTimeout(function(){n=0;},2500);
  if(n>=5){n=0;var d=$("adm-door");d.hidden=!d.hidden;if(!d.hidden){d.scrollIntoView({block:"center"});setTimeout(function(){try{$("pw-admin").focus();}catch(e){}},50);}}});})();
var LISTO=Promise.resolve();
if(LYSI.remoto){$("pie").textContent="Cargando los reportes…";
 LISTO=fetch(LYSI.remoto+"?t="+Date.now(),{cache:"no-store"}).then(function(r){if(!r.ok)throw new Error("http "+r.status);return r.json();})
  .then(function(d){d.remoto=LYSI.remoto;LYSI=d;window.LYSI=d;pintarInfo();pintarGastos();})
  .catch(function(e){$("pie").textContent="No se pudieron cargar los reportes ("+(e&&e.message||e)+"). Revisá la conexión y recargá la página.";throw new Error("sin datos");});}
function medir(){var cs=document.querySelectorAll(".cab"),i;for(i=0;i<cs.length;i++)if(cs[i].offsetHeight)document.documentElement.style.setProperty("--cabh",cs[i].offsetHeight+"px");}
function mostrar(id){var aps=cont.querySelectorAll(".apartado"),i,ok=false;for(i=0;i<aps.length;i++){var v=aps[i].id===id;aps[i].hidden=!v;ok=ok||v;}
 if(!ok&&aps.length){aps[aps.length-1].hidden=false;id=aps[aps.length-1].id;}
 var ap=document.getElementById(id),gr=ap&&ap.getAttribute("data-grupo");
 var bs=document.querySelectorAll(".tabs button");for(i=0;i<bs.length;i++){var on=bs[i].getAttribute("data-ir")===id||(gr&&bs[i].getAttribute("data-grupo")===gr);bs[i].setAttribute("aria-current",on?"true":"false");if(on&&bs[i].scrollIntoView)try{bs[i].scrollIntoView({block:"nearest",inline:"nearest"});}catch(e){}}
 window.scrollTo(0,0);medir();}
function verReporte(htmlTxt,nombre,previa){cont.innerHTML=htmlTxt;var t=cont.querySelector("template[data-tabs]");$("tabs").innerHTML=t?t.innerHTML:"";$("donde").textContent=nombre;
 $("previa").hidden=!previa;acceso.hidden=true;adm.hidden=true;app.hidden=false;
 mostrar((cont.querySelector("[data-inicio]")||{getAttribute:function(){return"";}}).getAttribute("data-inicio"));}
document.addEventListener("click",function(ev){var b=ev.target.closest&&ev.target.closest("[data-ir]");if(b){mostrar(b.getAttribute("data-ir"));}});
function puerta(inp,btn,msj,accion){
 function entrar(){var pw=(inp.value||"").trim();if(!pw){msj.style.color="";msj.textContent="Escribí la contraseña.";return;}
  btn.disabled=true;msj.style.color="#c9d2cb";msj.textContent="Abriendo…";
  setTimeout(function(){var pr;try{pr=LISTO.then(function(){return accion(pw);});}catch(err){pr=Promise.reject(err);}
   pr.then(function(){inp.value="";msj.textContent="";btn.disabled=false;})
    .catch(function(err){btn.disabled=false;msj.style.color="";
     if(err&&err.message==="clave"){msj.textContent="Contraseña incorrecta. Probá de nuevo.";inp.select();}
     else if(err&&err.message==="sin datos"){msj.textContent="Todavía no se pudieron cargar los reportes. Recargá la página.";}
     else{msj.textContent="No se pudo abrir en este visor ("+(err&&err.message?err.message:err)+"). Abrí el archivo con Chrome o Edge.";}});},40);}
 btn.addEventListener("click",entrar);inp.addEventListener("keydown",function(ev){if(ev.key==="Enter"||ev.keyCode===13){ev.preventDefault();entrar();}});}
Array.prototype.forEach.call(document.querySelectorAll("[data-caja]"),function(fm){var id=fm.getAttribute("data-caja");
 puerta(fm.querySelector("input"),fm.querySelector("button"),$("msj-"+id),function(pw){
  if(!LYSI.cajas||!LYSI.cajas[id])return Promise.reject(new Error("todavía no hay reportes publicados"));
  return abrir(LYSI.cajas[id],pw).then(function(h){verReporte(h,fm.getAttribute("data-nombre"),false);});});});
function cerrarTodo(){cont.innerHTML="";$("tabs").innerHTML="";app.hidden=true;adm.hidden=true;acceso.hidden=false;ADM=null;RES=null;window.scrollTo(0,0);}
$("salir").addEventListener("click",function(){if(!$("previa").hidden){volverAdm();return;}cerrarTodo();});
window.addEventListener("resize",medir);

// ───────────── Administración ─────────────
var ADM=null,RES=null,SUCIO=false,MES=null,PYO=null,GAS=[];
function sucio(v){SUCIO=v;$("sucio").hidden=!v;}
window.addEventListener("beforeunload",function(ev){if(SUCIO){ev.preventDefault();ev.returnValue="";}});
puerta($("pw-admin"),$("btn-admin"),$("msj-admin"),function(pw){
 return abrir(LYSI.admin,pw).then(function(txt){ADM=JSON.parse(txt);ADM.fuentes=ADM.fuentes||{};ADM.ajustes=ADM.ajustes||{};ADM.importados=ADM.importados||{};ADM.claves=ADM.claves||{};ADM.claves.admin=pw;abrirAdm();});});
function abrirAdm(){acceso.hidden=true;app.hidden=true;adm.hidden=false;$("cl-comb").value=ADM.claves.combustible||"";$("cl-adm").value=ADM.claves.admin||"";$("cl-gas").value=ADM.claves.gastos||"";GAS=[];$("gas-arch").value="";pintarGas();$("ver-previa-g").disabled=true;
 var hoy=new Date(),y0=hoy.getFullYear(),ys={},k,sel=$("anio"),o="";ys[y0]=1;for(k in ADM.fuentes)ys[k.slice(0,4)]=1;ys[y0-1]=1;
 Object.keys(ys).sort().forEach(function(y){o+='<option value="'+y+'"'+(String(y)===String(y0)?" selected":"")+">"+y+"</option>";});sel.innerHTML=o;
 MES=null;$("panel").hidden=true;pintarMeses();pintarDestino();$("gh-estado").innerHTML="";$("copia").disabled=!LYSI.cajas;$("proc-estado").innerHTML="";$("proc-res").innerHTML="";$("pub-estado").innerHTML="";$("ver-previa").disabled=true;$("publicar").disabled=true;sucio(false);window.scrollTo(0,0);medir();}
function volverAdm(){app.hidden=true;adm.hidden=false;$("previa").hidden=true;cont.innerHTML="";window.scrollTo(0,0);medir();}
$("volver-adm").addEventListener("click",volverAdm);
$("salir-adm").addEventListener("click",function(){if(SUCIO&&!window.confirm("Hay cambios sin publicar. Si cerrás, se pierden. ¿Cerrar igual?"))return;sucio(false);cerrarTodo();});
$("anio").addEventListener("change",function(){MES=null;$("panel").hidden=true;pintarMeses();});
function estadoMes(id){var f=ADM.fuentes[id]||{},n=0;TIPOS.forEach(function(t){if(f[t[0]])n++;});
 var pub=(LYSI.info&&LYSI.info.ids||[]).indexOf(id)>=0,imp=!!ADM.importados[id];
 if(imp&&!pub)return["ok",n?"Importado ("+n+" de 4 archivos)":"Importado de un reporte"];
 if(n===0)return["","Sin cargar"];if(n===4)return["ok",pub?"Publicado":"4 de 4 archivos"];
 if(f.cargas&&f.filarus&&n===2)return["arr","Solo arranque (2 de 4)"];return["arr",n+" de 4 archivos"];}
function pintarMeses(){var y=$("anio").value,h="",m;for(m=1;m<=12;m++){var id=y+"-"+(m<10?"0":"")+m,e=estadoMes(id);
  h+='<button type="button" class="mesb '+e[0]+'" data-mes="'+id+'" aria-pressed="'+(MES===id)+'"><b>'+MESES[m].charAt(0).toUpperCase()+MESES[m].slice(1)+"</b><span>"+e[1]+"</span></button>";}
 $("meses").innerHTML=h;}
$("meses").addEventListener("click",function(ev){var b=ev.target.closest(".mesb");if(!b)return;MES=b.getAttribute("data-mes");pintarMeses();pintarPanel();});
function nombreMes(id){return MESES[parseInt(id.slice(5),10)]+" "+id.slice(0,4);}
function pintarPanel(){var p=$("panel"),f=ADM.fuentes[MES]||{},aj=(ADM.ajustes[MES]||{}).unidades||{},h="";
 h+="<h3>"+esc(nombreMes(MES).charAt(0).toUpperCase()+nombreMes(MES).slice(1))+"</h3>";
 if(ADM.importados[MES])h+='<div class="estado av">Este mes está cargado desde un reporte ya hecho ('+esc(ADM.importados[MES].origen||"")+'). Si subís sus cuatro archivos y están los del mes anterior, pasa a calcularse acá y reemplaza al importado.</div>';
 h+='<div class="fila"><label for="varios">Elegir los archivos del mes juntos</label><input type="file" id="varios" multiple accept=".xlsx,.xls"></div><p class="nota">Los reconoce por el nombre con que bajan (ReporteConsumos, KmRecorridos, Informe de combustible, Resumen). Si alguno queda en el lugar equivocado, cargalo abajo en su fila.</p>';
 TIPOS.forEach(function(t){var x=f[t[0]];
  h+='<div class="slot"><div class="q">'+t[1]+"<small>"+t[2]+'</small></div><div class="e'+(x?" si":"")+'">'+(x?esc(x.n)+" ("+num(x.b.length*0.75/1024)+" KB)":"Sin cargar")+"</div>"
   +'<input type="file" accept=".xlsx,.xls" data-tipo="'+t[0]+'" aria-label="Archivo de '+t[1]+'">'+(x?'<button type="button" class="btn mini" data-quitar="'+t[0]+'">Quitar</button>':"<span></span>")+"</div>";});
 h+='<h3 style="font-size:20px;margin-top:20px">Decisiones del analista para este mes</h3><p class="nota">Solo si hace falta: mandar una unidad a investigar por un motivo que las reglas no detectan solas. Queda escrito en el reporte como decisión registrada.</p>';
 var ks=Object.keys(aj).filter(function(u){return aj[u].estado==="A INVESTIGAR";});
 ks.forEach(function(u){h+='<div class="fila"><b>'+esc(u)+"</b><span>"+esc(aj[u].motivo||"")+"</span><span class=\"sm\">"+(aj[u].km_confiable===false?"sus km no cuentan":"sus km cuentan en el coeficiente general")+'</span><button type="button" class="btn mini" data-quitar-aj="'+esc(u)+'">Quitar</button></div>';});
 var otros=Object.keys(aj).length-ks.length;if(otros)h+='<p class="nota">Este mes tiene además '+otros+" ajuste(s) de km tomados del reporte ya circulado.</p>";
 h+='<div class="fila"><input type="text" id="aj-u" placeholder="Patente" size="9" aria-label="Patente"><input type="text" id="aj-m" placeholder="Motivo, tal como va a figurar" size="48" aria-label="Motivo"><label><input type="checkbox" id="aj-k" checked> Sus km siguen contando</label><button type="button" class="btn mini" id="aj-add">Agregar</button></div>';
 p.innerHTML=h;p.hidden=false;}
function clasificar(n){n=n.toLowerCase();if(n.indexOf("consumo")>=0&&n.indexOf("informe")<0)return"cargas";if(n.indexOf("km")>=0||n.indexOf("filarus")>=0)return"filarus";if(n.indexOf("informe")>=0||n.indexOf("combustible")>=0||n.indexOf("malla")>=0)return"malla";if(n.indexOf("resumen")>=0||n.indexOf("rendimiento")>=0)return"resumen";return null;}
function leer(file){return new Promise(function(ok,no){var r=new FileReader();r.onload=function(){ok({n:file.name,b:a64(new Uint8Array(r.result))});};r.onerror=function(){no(r.error);};r.readAsArrayBuffer(file);});}
function pintarGas(){var el=$("gas-estado"),hay=!!(LYSI.cajas&&LYSI.cajas.gastos);
 if(GAS.length)estado(el,"Para procesar: "+esc(GAS.map(function(x){return x.n;}).join(" · "))+". Reemplazan a lo publicado cuando publiques.","av");
 else estado(el,hay?"Resultados está publicado"+(LYSI.info&&LYSI.info.gastos?" ("+esc(LYSI.info.gastos)+")":"")+". Para actualizarlo, subí los dos Excel nuevos.":"Todavía no hay nada publicado en Resultados.");}
$("gas-arch").addEventListener("change",function(ev){var fs=Array.prototype.slice.call(ev.target.files||[]);if(!fs.length)return;
 Promise.all(fs.map(leer)).then(function(xs){GAS=xs;invalidar();pintarGas();});});
function invalidar(){RES=null;$("ver-previa-g").disabled=true;$("ver-previa").disabled=true;$("publicar").disabled=true;$("proc-res").innerHTML="";$("proc-estado").innerHTML="";sucio(true);}
$("panel").addEventListener("change",function(ev){var t=ev.target;if(t.type!=="file"||!t.files.length)return;var fs=Array.prototype.slice.call(t.files),tipo=t.getAttribute("data-tipo");
 Promise.all(fs.map(leer)).then(function(xs){ADM.fuentes[MES]=ADM.fuentes[MES]||{};var sin=[];
  xs.forEach(function(x){var k=tipo||clasificar(x.n);if(k)ADM.fuentes[MES][k]=x;else sin.push(x.n);});
  invalidar();pintarMeses();pintarPanel();if(sin.length)$("panel").insertAdjacentHTML("beforeend",'<div class="estado av">No pude reconocer por el nombre: '+esc(sin.join(", "))+". Cargalos en su fila.</div>");});});
$("panel").addEventListener("click",function(ev){var t=ev.target,q=t.getAttribute("data-quitar"),qa=t.getAttribute("data-quitar-aj");
 if(q){delete ADM.fuentes[MES][q];if(!Object.keys(ADM.fuentes[MES]).length)delete ADM.fuentes[MES];invalidar();pintarMeses();pintarPanel();}
 if(qa){delete ADM.ajustes[MES].unidades[qa];invalidar();pintarPanel();}
 if(t.id==="aj-add"){var u=$("aj-u").value.replace(/[^A-Za-z0-9]/g,"").toUpperCase(),m=$("aj-m").value.trim();if(!u||!m){return;}
  ADM.ajustes[MES]=ADM.ajustes[MES]||{};ADM.ajustes[MES].unidades=ADM.ajustes[MES].unidades||{};
  var prev=ADM.ajustes[MES].unidades[u]||{};prev.estado="A INVESTIGAR";prev.motivo=m;prev.km_confiable=$("aj-k").checked;ADM.ajustes[MES].unidades[u]=prev;invalidar();pintarPanel();}});

function estado(el,txt,cls){el.innerHTML='<div class="estado '+(cls||"")+'">'+txt+"</div>";}
function cargarPyodide(){if(PYO)return Promise.resolve(PYO);var base=window.LYSI_PYO||LYSI.pyodide;
 return new Promise(function(ok,no){var s=document.createElement("script");s.src=base+"pyodide.js";s.onload=ok;s.onerror=function(){no(new Error("sin conexión"));};document.head.appendChild(s);})
  .then(function(){return loadPyodide({indexURL:base});})
  .then(function(p){return p.loadPackage(["pandas","micropip"]).then(function(){return p;});})
  .then(function(p){p.globals.set("WHEELS",p.toPy(window.LYSI_WHEELS||["openpyxl"]));return p.runPythonAsync("import micropip\nawait micropip.install(list(WHEELS))").then(function(){return p;});})
  .then(function(p){var src=JSON.parse($("py").textContent),k;p.FS.mkdirTree("/app/motor");for(k in src)p.FS.writeFile("/app/"+k,src[k]);p.runPython("import sys\nsys.path.insert(0,'/app')");PYO=p;return p;});}
function procesar(){var el=$("proc-estado");$("procesar").disabled=true;$("proc-res").innerHTML="";estado(el,"Preparando el motor de cálculo… la primera vez tarda unos segundos.");
 return cargarPyodide().then(function(p){estado(el,"Calculando todos los meses cargados…");
   return new Promise(function(ok){setTimeout(ok,60);}).then(function(){
    p.runPython("import shutil,os\nshutil.rmtree('/datos',ignore_errors=True)\nos.makedirs('/datos')");
    Object.keys(ADM.fuentes).forEach(function(id){p.FS.mkdirTree("/datos/"+id);var f=ADM.fuentes[id];Object.keys(f).forEach(function(k){p.FS.writeFile("/datos/"+id+"/"+k+".xlsx",b64(f[k].b));});
     if(ADM.ajustes[id])p.FS.writeFile("/datos/"+id+"/ajustes.json",JSON.stringify(ADM.ajustes[id]));});
    Object.keys(ADM.importados).forEach(function(id){p.FS.mkdirTree("/datos/"+id);p.FS.writeFile("/datos/"+id+"/importado.json",JSON.stringify(ADM.importados[id]));});
    if(GAS.length){p.FS.mkdirTree("/datos/gastos");GAS.forEach(function(x,i){p.FS.writeFile("/datos/gastos/"+i+"_"+x.n.replace(/[^\w.\- ]/g,"_"),b64(x.b));});}
    return JSON.parse(p.runPython("from motor import armado\narmado.procesar('/datos')"));});})
  .then(function(r){RES=r;$("procesar").disabled=false;pintarRes();})
  .catch(function(err){$("procesar").disabled=false;var m=String(err&&err.message||err);
   estado(el,m.indexOf("sin conexión")>=0||m.indexOf("fetch")>=0||m.indexOf("Failed")>=0?"No se pudo descargar el motor de cálculo. Revisá la conexión a internet y probá de nuevo.":"No se pudo procesar: "+esc(m.slice(-600)),"err");});}
function pintarRes(){var r=RES,h="";
 r.errores.forEach(function(x){h+='<div class="estado err">'+esc(x)+"</div>";});r.pendientes.forEach(function(x){h+='<div class="estado av">'+esc(x)+"</div>";});
 if(r.meses.length){h+='<div class="tw"><table><thead><tr><th>Mes</th><th class="r">km</th><th class="r">Gasoil L</th><th class="r">Coef</th><th class="r">Operativas</th><th class="r">Crít.</th><th class="r">Atenc.</th><th class="r">Norm.</th><th class="r">Bajo</th><th class="r">Invest.</th><th>Total YPF</th><th>Fuente de km</th></tr></thead><tbody>';
  r.meses.forEach(function(m){var d=function(v){return v==null?"—":v;};
   h+="<tr><td><b>"+esc(m.nombre)+'</b></td><td class="r">'+num(m.km)+'</td><td class="r">'+num(m.gasoil,2)+'</td><td class="r">'+num(m.coef,2)+'</td><td class="r">'+m.operativas+(m.importado&&m.metodo!=="ventana"?"":" de "+m.totales)+'</td><td class="r">'+d(m.criticas)+'</td><td class="r">'+d(m.atencion)+'</td><td class="r">'+d(m.normales)+'</td><td class="r">'+d(m.coef_bajo)+'</td><td class="r">'+d(m.n_investigar)+"</td><td>"
    +(m.importado?"—":(m.cierra_ypf?"Cierra":"NO CIERRA")+" ("+num(m.total_ypf,2)+" L)")+"</td><td>"
    +(m.importado?(m.metodo==="ventana"?"Importado: ventana, km Filarus":"Importado: mes calendario, km Filarus"):m.fuente_odo+" odómetro, "+m.fuente_filarus+" Filarus"+(m.malla_anterior?"":" · sin malla del mes anterior"))+"</td></tr>";});
  h+="</tbody></table></div>";
  r.meses.forEach(function(m){if(m.investigar.length){h+='<h3 style="font-size:19px">A investigar en '+esc(m.nombre)+'</h3><ul class="hechos">';m.investigar.forEach(function(x){h+="<li><b>"+esc(x.unidad)+"</b>: "+esc(x.motivo)+(x.manual?" <span class=\"tag\">decisión registrada</span>":"")+"</li>";});h+="</ul>";}});}
 var g=r.gastos;if(g){h+='<h3 style="font-size:19px">Reporte de resultados</h3>';g.errores.forEach(function(x){h+='<div class="estado err">'+esc(x)+"</div>";});
  if(g.html){h+='<p class="nota">'+g.hojas+" hojas leídas · "+esc(g.descripcion)+". Control: el resumen de cada mes, tal como figura en el Excel.</p>";
   if(g.control){h+='<div class="tw"><table><thead><tr>'+g.control.cab.map(function(c){return"<th>"+esc(c)+"</th>";}).join("")+"</tr></thead><tbody>"+g.control.filas.map(function(f){return"<tr>"+f.map(function(c,i){return'<td'+(i?' class="r"':"")+">"+esc(c)+"</td>";}).join("")+"</tr>";}).join("")+"</tbody></table></div>";}}}
 $("proc-res").innerHTML=h;var ok=!!r.html&&!r.errores.length&&!(g&&(g.errores.length||!g.html));$("ver-previa-g").disabled=!(g&&g.html);
 estado($("proc-estado"),ok?"Listo: "+r.meses.length+" mes(es) armados. Revisá el control de abajo y la vista previa antes de publicar.":(r.html?"Se calculó, pero hay archivos con problemas. Corregilos antes de publicar.":"Todavía no hay ningún mes que se pueda calcular."),ok?"":"err");
 $("ver-previa").disabled=!r.html;$("publicar").disabled=!ok;}
$("procesar").addEventListener("click",procesar);
$("ver-previa").addEventListener("click",function(){if(RES&&RES.html)verReporte(RES.html,"Combustible",true);});
$("ver-previa-g").addEventListener("click",function(){if(RES&&RES.gastos&&RES.gastos.html)verReporte(RES.gastos.html,"Reporte de resultados",true);});
function guardarArchivo(txt){var nombre="LYSI_Reportes.html";
 function bajar(){var a=document.createElement("a");a.href=URL.createObjectURL(new Blob([txt],{type:"text/html"}));a.download=nombre;document.body.appendChild(a);a.click();setTimeout(function(){URL.revokeObjectURL(a.href);a.remove();},2000);return"descargado";}
 if(window.showSaveFilePicker){return window.showSaveFilePicker({suggestedName:nombre,types:[{description:"Página web",accept:{"text/html":[".html"]}}]})
   .then(function(h){return h.createWritable().then(function(w){return w.write(txt).then(function(){return w.close();});}).then(function(){return"guardado";});})
   .catch(function(e){if(e&&e.name==="AbortError")throw e;return bajar();});}
 return Promise.resolve(bajar());}
function gh(){var g=ADM&&ADM.github;return g&&g.o&&g.r&&g.t?g:null;}
function ghApi(g,ruta,opt){opt=opt||{};opt.headers={"Authorization":"Bearer "+g.t,"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"};
 return fetch("https://api.github.com/repos/"+encodeURIComponent(g.o)+"/"+encodeURIComponent(g.r)+ruta,opt);}
function pintarDestino(){var g=gh();$("gh-o").value=(ADM.github||{}).o||"";$("gh-r").value=(ADM.github||{}).r||"";$("gh-t").value=(ADM.github||{}).t||"";
 $("pub-nota").textContent=g?"Publicar sube los reportes actualizados al sitio. En uno o dos minutos los ve todo el que entre al link; no hay que mandar nada.":"Todavía no hay un sitio conectado: publicar guarda una versión nueva de este archivo, y hay que reemplazar la anterior a mano.";
 $("gh-nota").textContent=g?"Conectado a "+g.o+"/"+g.r+". Los reportes se publican ahí.":"Para que publicar impacte en un único link, conectá el repositorio de GitHub donde está alojada la app. El token queda guardado cifrado con tu contraseña de administración.";
 $("publicar").textContent=g?"Publicar en el sitio":"Publicar y guardar archivo";}
$("gh-probar").addEventListener("click",function(){var el=$("gh-estado"),g={o:$("gh-o").value.trim(),r:$("gh-r").value.trim(),t:$("gh-t").value.trim(),p:"datos.json"};
 if(!g.o||!g.r||!g.t){ADM.github=null;sucio(true);pintarDestino();estado(el,"Sin conexión configurada: se publica guardando un archivo.","av");return;}
 estado(el,"Probando…");ghApi(g,"").then(function(r){return r.json().then(function(j){
   if(!r.ok){estado(el,"GitHub rechazó la conexión ("+r.status+"): "+esc(j.message||"")+". Revisá cuenta, repositorio y token.","err");return;}
   if(!(j.permissions&&j.permissions.push)){estado(el,"El token entra al repositorio pero no puede escribir. Tiene que tener permiso de escritura sobre el contenido.","err");return;}
   ADM.github=g;sucio(true);pintarDestino();estado(el,"Conexión correcta con "+esc(j.full_name)+" ("+(j.private?"privado":"público")+"). Queda guardada al publicar.");});})
  .catch(function(e){estado(el,"No se pudo conectar con GitHub: "+esc(String(e&&e.message||e)),"err");});});
function subirGitHub(g,nuevo){var cuerpo=a64(utf8(JSON.stringify(nuevo))),ruta="/contents/"+(g.p||"datos.json");
 return ghApi(g,ruta).then(function(r){return r.status===404?null:r.json().then(function(j){if(!r.ok)throw new Error(j.message||r.status);return j.sha;});})
  .then(function(sha){var b={message:"Publicación "+nuevo.info.generado+": "+nuevo.info.meses.join(", "),content:cuerpo};if(sha)b.sha=sha;
   return ghApi(g,ruta,{method:"PUT",body:JSON.stringify(b)});})
  .then(function(r){return r.json().then(function(j){if(!r.ok)throw new Error("GitHub ("+r.status+"): "+(j.message||""));return j;});});}
function archivoCompleto(nuevo){var c={},k;for(k in nuevo)if(k!=="remoto")c[k]=nuevo[k];var a=PLANTILLA.indexOf("/*D0*/"),b=PLANTILLA.indexOf("/*D1*/");
 return "<!doctype html>\n"+PLANTILLA.slice(0,a+6)+JSON.stringify(c)+PLANTILLA.slice(b);}
$("copia").addEventListener("click",function(){var el=$("pub-estado");if(!LYSI.cajas){return;}
 guardarArchivo(archivoCompleto(LYSI)).then(function(como){estado(el,"Copia "+(como==="guardado"?"guardada":"descargada en Descargas")+". Es un archivo completo que abre sin internet, con lo último publicado.");})
  .catch(function(e){if(!(e&&e.name==="AbortError"))estado(el,"No se pudo guardar la copia: "+esc(String(e&&e.message||e)),"err");});});
function cajaGastos(cg){var g=RES.gastos,vieja=LYSI.cajas&&LYSI.cajas.gastos,ant=ADM.claves.gastos;
 if(g&&g.html)return cifrar(g.html,cg,true);
 if(vieja&&ant&&cg!==ant)return abrir(vieja,ant).then(function(h){return cifrar(h,cg,true);});
 return Promise.resolve(vieja||null);}
function publicar(){var el=$("pub-estado"),cc=$("cl-comb").value.trim(),ca=$("cl-adm").value.trim(),cg=$("cl-gas").value.trim();
 var hayG=!!((RES.gastos&&RES.gastos.html)||(LYSI.cajas&&LYSI.cajas.gastos));
 if(!cc||!ca){estado(el,"Las contraseñas de Combustible y de administración tienen que estar completas.","err");return;}
 if(cc===ca){estado(el,"La contraseña de administración tiene que ser distinta de la de Combustible.","err");return;}
 if(hayG&&!cg){estado(el,"Falta la contraseña de Resultados.","err");return;}
 if(hayG&&cg===ca){estado(el,"La contraseña de administración tiene que ser distinta de la de Resultados.","err");return;}
 $("publicar").disabled=true;estado(el,"Cifrando y armando el archivo…");
 setTimeout(function(){
  cajaGastos(cg).then(function(cgx){ADM.claves.combustible=cc;ADM.claves.admin=ca;if(hayG)ADM.claves.gastos=cg;
   return cifrar(RES.html,cc).then(function(c1){return cifrar(JSON.stringify(ADM),ca).then(function(c2){
    var cajas={},k;for(k in (LYSI.cajas||{}))cajas[k]=LYSI.cajas[k];cajas.combustible=c1;if(cgx)cajas.gastos=cgx;
    var nuevo={v:LYSI.v,iter:LYSI.iter,pyodide:LYSI.pyodide,cajas:cajas,admin:c2,info:{meses:RES.meses.map(function(m){return m.nombre;}),ids:RES.meses.filter(function(m){return !m.importado;}).map(function(m){return m.id;}),generado:RES.generado,reglas:RES.reglas}};
    var dg=(RES.gastos&&RES.gastos.html)?RES.gastos.descripcion:(LYSI.info&&LYSI.info.gastos);if(cgx&&dg)nuevo.info.gastos=dg;
    if(LYSI.remoto)nuevo.remoto=LYSI.remoto;var g=gh();
    function hecho(txt){LYSI=nuevo;window.LYSI=nuevo;pintarInfo();pintarGastos();pintarMeses();GAS=[];$("gas-arch").value="";pintarGas();sucio(false);$("publicar").disabled=false;$("copia").disabled=false;estado(el,txt);}
    if(g){estado(el,"Subiendo al sitio…");return subirGitHub(g,nuevo).then(function(){hecho("Publicado en el sitio. En uno o dos minutos lo ve todo el que entre al link.");});}
    return guardarArchivo(archivoCompleto(nuevo)).then(function(como){
     hecho((como==="guardado"?"Publicado y guardado.":"Publicado. El archivo nuevo quedó en Descargas como LYSI_Reportes.html.")+" Reemplazá con ese archivo el que abren todos; el anterior queda desactualizado.");});});});})
  .catch(function(e){$("publicar").disabled=false;estado(el,e&&e.name==="AbortError"?"No se guardó: cancelaste la ventana de guardado.":"No se pudo publicar: "+esc(String(e&&e.message||e)),"err");});},40);}
$("publicar").addEventListener("click",publicar);
})();
"""


def fuentes_py():
    """Código del motor que viaja dentro de la aplicación para correr en el navegador."""
    base = os.path.dirname(__file__)
    out = {}
    for n in ["__init__", "config", "fuentes", "calculo", "render", "armado", "gastos"]:
        out[f"motor/{n}.py"] = open(os.path.join(base, n + ".py"), encoding="utf-8").read()
    return out


def construir(datos):
    """datos: dict con cajas, admin, info (ya cifrado lo que corresponde)."""
    cripto = P.JS.split("window.__lysi=")[0]
    cripto = cripto.replace('function b64(s){var bin=atob(s),o=new Uint8Array(bin.length),i;for(i=0;i<bin.length;i++)o[i]=bin.charCodeAt(i);return o;}', "")
    py = json.dumps(fuentes_py(), ensure_ascii=False).replace("</", "<\\/")
    d = json.dumps(datos, ensure_ascii=False).replace("</", "<\\/")
    return f'''<!doctype html>
<html lang="es-AR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>LYSI Reportes</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700&family=Barlow+Condensed:wght@500;600;700&display=swap" rel="stylesheet">
<style>{P.CSS}{CSS_ADM}{CSS_GAS}</style></head><body>{HTML_CUERPO}
<script id="py" type="application/json">{py}</script>
<script id="datos">window.LYSI=/*D0*/{d}/*D1*/;</script>
<script>var PLANTILLA=document.documentElement.outerHTML;var LYSI=window.LYSI;
{cripto}{JS_UI}</script></body></html>'''


def semilla(base_datos, claves):
    """Primera versión del archivo: calcula con lo que hay en la carpeta y deja las fuentes guardadas para administración."""
    from . import armado, config as C
    r = json.loads(armado.procesar(base_datos))
    adm = {"claves": claves, "fuentes": {}, "ajustes": {}, "importados": {}}
    for a, m, p in armado.meses_disponibles(base_datos):
        mid = f"{a}-{m:02d}"
        imp = os.path.join(p, "importado.json")
        if os.path.exists(imp):
            adm["importados"][mid] = json.load(open(imp, encoding="utf-8"))
        if not os.path.exists(os.path.join(p, "cargas.xlsx")):
            continue
        adm["fuentes"][mid] = {}
        for t in ["cargas", "filarus", "malla", "resumen"]:
            ruta = os.path.join(p, t + ".xlsx")
            if os.path.exists(ruta):
                nom = open(ruta + ".nombre", encoding="utf-8").read().strip() if os.path.exists(ruta + ".nombre") else t + ".xlsx"
                adm["fuentes"][mid][t] = {"n": nom, "b": base64.b64encode(open(ruta, "rb").read()).decode()}
        aj = os.path.join(p, "ajustes.json")
        if os.path.exists(aj):
            adm["ajustes"][mid] = json.load(open(aj, encoding="utf-8"))
    datos = {"v": 2, "iter": P.ITER, "pyodide": PYODIDE,
             "cajas": {"combustible": P.cifrar(r["html"], claves["combustible"])},
             "admin": P.cifrar(json.dumps(adm, ensure_ascii=False), claves["admin"]),
             "info": {"meses": [m["nombre"] for m in r["meses"]], "ids": [m["id"] for m in r["meses"] if not m["importado"]], "generado": r["generado"], "reglas": r["reglas"]}}
    return construir(datos), r


def sitio(base_datos, claves, carpeta):
    """Versión para alojar: index.html sin datos + datos.json. Publicar desde administración reemplaza solo datos.json."""
    html, r = semilla(base_datos, claves)
    a, b = html.index("/*D0*/") + 6, html.index("/*D1*/")
    datos = html[a:b]
    cascara = json.dumps({"v": 2, "iter": P.ITER, "pyodide": PYODIDE, "remoto": "datos.json"})
    os.makedirs(carpeta, exist_ok=True)
    open(os.path.join(carpeta, "index.html"), "w", encoding="utf-8").write(html[:a] + cascara + html[b:])
    open(os.path.join(carpeta, "datos.json"), "w", encoding="utf-8").write(datos)
    open(os.path.join(carpeta, ".nojekyll"), "w").write("")
    return html, r


def cascara():
    """Solo index.html (la app sin datos). Para actualizar el software sin tocar datos.json."""
    return construir({"v": 2, "iter": P.ITER, "pyodide": PYODIDE, "remoto": "datos.json"})
