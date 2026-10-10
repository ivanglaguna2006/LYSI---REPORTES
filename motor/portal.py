# -*- coding: utf-8 -*-
"""Arma el archivo único del software: pantalla de acceso + apartados cifrados con contraseña.

Cifrado: PBKDF2-HMAC-SHA256 -> clave AES-256-CTR + clave HMAC-SHA256 (cifrar y después autenticar).
Sin la contraseña el archivo no contiene ningún dato legible."""
import os
import base64
import hmac
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

ITER = 120000


def cifrar(texto, clave):
    salt, iv = os.urandom(16), os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", clave.encode("utf-8"), salt, ITER, 64)
    enc = Cipher(algorithms.AES(dk[:32]), modes.CTR(iv)).encryptor()
    ct = enc.update(texto.encode("utf-8")) + enc.finalize()
    tag = hmac.new(dk[32:], iv + ct, hashlib.sha256).digest()
    b = lambda x: base64.b64encode(x).decode()
    return {"s": b(salt), "i": b(iv), "t": b(tag), "c": b(ct), "n": ITER}



def descifrar(caja, clave):
    """Inverso de cifrar(). Lanza ValueError si la contraseña no corresponde."""
    b = base64.b64decode
    salt, iv, tag, ct = b(caja["s"]), b(caja["i"]), b(caja["t"]), b(caja["c"])
    dk = hashlib.pbkdf2_hmac("sha256", clave.encode("utf-8"), salt, int(caja.get("n", ITER)), 64)
    if not hmac.compare_digest(hmac.new(dk[32:], iv + ct, hashlib.sha256).digest(), tag):
        raise ValueError("contraseña incorrecta")
    dec = Cipher(algorithms.AES(dk[:32]), modes.CTR(iv)).decryptor()
    return (dec.update(ct) + dec.finalize()).decode("utf-8")


CSS = r"""
:root{--v1:#1B5E20;--v2:#2E7D32;--v3:#4CAF50;--v0:#E8F5E9;--ng:#000;--tx:#16191a;--tx2:#4d5553;--ln:#dfe4df;--bg:#fff;--bg2:#f5f7f5}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--tx);font:15px/1.5 Barlow,"Segoe UI",system-ui,sans-serif;-webkit-text-size-adjust:100%}
h1,h2,h3,.marca,.kv,th,.tabs button,.subnav a,.est,.tag{font-family:"Barlow Condensed","Arial Narrow",Barlow,sans-serif}
[hidden]{display:none!important}
/* acceso */
#acceso{min-height:100vh;background:var(--ng);color:#fff;display:grid;grid-template-rows:auto 1fr auto}
.cinta{height:6px;background:var(--v2)}
.acc{width:min(880px,100%);margin:0 auto;padding:9vh 20px 40px}
.marca{font-size:clamp(84px,17vw,168px);font-weight:700;line-height:.82;letter-spacing:-.02em;margin:0}
.marca b{color:var(--v3);font-weight:700}
.sub{font-size:19px;color:#c9d2cb;margin:14px 0 46px;max-width:34em}
.puerta{border-top:1px solid #2c2f2d;padding:22px 0;display:grid;grid-template-columns:1fr auto;gap:8px 24px;align-items:end}
.puerta h2{font-size:30px;font-weight:600;margin:0;line-height:1.1}
.puerta p{margin:4px 0 0;color:#a9b3ac;font-size:14.5px}
.puerta .fm{display:flex;gap:8px;flex-wrap:wrap}
.puerta input{font:inherit;padding:11px 12px;border:1px solid #4a514c;background:#111;color:#fff;border-radius:3px;width:230px}
.puerta input:focus-visible,.puerta button:focus-visible,.tabs button:focus-visible,.subnav a:focus-visible,#salir:focus-visible,summary:focus-visible{outline:3px solid var(--v3);outline-offset:2px}
.puerta button{font:600 18px "Barlow Condensed","Arial Narrow",sans-serif;padding:10px 22px;border:0;border-radius:3px;background:var(--v2);color:#fff;cursor:pointer}
.puerta button:hover{background:var(--v1)}
.puerta button[disabled]{opacity:.6;cursor:wait}
.msj{grid-column:1/-1;min-height:1.4em;margin:0;font-size:14.5px;color:#ffb4a9}
.pronto{color:#8d968f;font:500 16px "Barlow Condensed","Arial Narrow",sans-serif;border:1px solid #3a403c;padding:8px 14px;border-radius:3px}
.pie{color:#7d867f;font-size:13px;padding:18px 20px;width:min(880px,100%);margin:0 auto}
/* aplicación */
.cab{position:sticky;top:0;z-index:30;background:var(--ng);color:#fff;border-bottom:5px solid var(--v2)}
.cab .in{display:flex;align-items:center;gap:18px;padding:8px 20px;max-width:1500px;margin:0 auto}
.cab .logo{font:700 30px/1 "Barlow Condensed","Arial Narrow",sans-serif;letter-spacing:-.01em}
.cab .logo b{color:var(--v3)}
.cab .donde{color:#c9d2cb;font-size:15px}
#salir{margin-left:auto;font:500 15px Barlow,sans-serif;background:none;color:#fff;border:1px solid #555;border-radius:3px;padding:6px 12px;cursor:pointer}
.tabs{display:flex;gap:4px;overflow-x:auto;padding:0 20px;max-width:1500px;margin:0 auto}
.tabs button{font-size:18px;font-weight:500;background:none;border:0;color:#c9d2cb;padding:8px 14px 9px;cursor:pointer;white-space:nowrap;border-bottom:4px solid transparent}
.tabs button[aria-current="true"]{color:#fff;border-bottom-color:var(--v3);font-weight:600}
.tabs .sep{width:1px;background:#3a403c;margin:8px 6px}
main{max-width:1500px;margin:0 auto;padding:0 20px 80px}
.aph{padding:30px 0 8px}
.aph h1{font-size:clamp(44px,7vw,76px);font-weight:700;line-height:.95;margin:0;letter-spacing:-.01em}
.aph p{margin:8px 0 0;color:var(--tx2)}
.subnav{position:sticky;top:var(--cabh,96px);z-index:20;background:var(--bg);display:flex;gap:2px;overflow-x:auto;border-bottom:1px solid var(--ln);margin:14px -20px 0;padding:0 20px}
.subnav a{font-size:16.5px;font-weight:500;color:var(--tx2);text-decoration:none;padding:9px 12px;white-space:nowrap}
.subnav a:hover{color:var(--v1);background:var(--v0)}
section{padding-top:34px;scroll-margin-top:calc(var(--cabh,96px) + 44px)}
section>h2{font-size:34px;font-weight:600;line-height:1.05;margin:0 0 10px;padding-left:12px;border-left:6px solid var(--v2)}
h3{font-size:21px;font-weight:600;margin:26px 0 8px}
.lead{font-size:19px;line-height:1.45;max-width:62em;margin:6px 0 16px}
.nota{color:var(--tx2);max-width:78em;margin:6px 0 12px;font-size:14.5px}
.aviso{background:#FFF8E1;border-left:4px solid #E65100;padding:9px 12px;max-width:78em;font-size:14.5px}
.franja{display:flex;height:22px;gap:2px;border-radius:3px;overflow:hidden;max-width:980px}
.ley{display:flex;flex-wrap:wrap;gap:4px 18px;margin:8px 0 4px;font-size:14px;color:var(--tx2)}
.le i{display:inline-block;width:11px;height:11px;border-radius:2px;margin-right:6px;vertical-align:-1px}
.le b{color:var(--tx)}
.kpis{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:0;border-top:1px solid var(--ln);border-left:1px solid var(--ln)}
.kpi{padding:12px 14px 13px;border-right:1px solid var(--ln);border-bottom:1px solid var(--ln)}
.kv{font-size:32px;font-weight:600;line-height:1.05;font-variant-numeric:tabular-nums}
.kl{font-size:14.5px;font-weight:600;margin-top:2px}
.kn{font-size:13px;color:var(--tx2)}
.tw{overflow-x:auto;border:1px solid var(--ln);border-radius:3px;max-width:100%}
table{border-collapse:collapse;width:100%;font-size:13.5px;font-variant-numeric:tabular-nums}
th{background:var(--v1);color:#fff;font-size:15px;font-weight:600;padding:7px 9px;white-space:nowrap;position:sticky;top:0;text-align:left}
td{padding:5px 9px;border-top:1px solid var(--ln);vertical-align:top;white-space:nowrap}
td.r,th.r{text-align:right}
tbody tr:nth-child(even) td{background:var(--bg2)}
tr.tot td{font-weight:700;background:var(--v0)!important;border-top:2px solid var(--v2)}
td .obs{white-space:normal;display:inline-block;min-width:240px;max-width:520px;color:var(--tx2);font-size:13px;line-height:1.35}
.est{display:inline-block;color:#fff;font-size:14px;font-weight:600;padding:1px 8px 2px;border-radius:2px;white-space:nowrap}
.tag{display:inline-block;background:#111;color:#fff;font-size:12.5px;padding:0 6px 1px;border-radius:2px}
.bd{width:110px;height:11px;display:block;margin-top:4px}
.nc{color:#8a5a00}
.sm{color:var(--tx2);font-weight:400;font-size:14px}
.vac{color:#aaa}
.mz{padding-left:13px}
details.hist{border:1px solid var(--ln);border-radius:3px;margin:6px 0}
details.hist>summary{cursor:pointer;padding:9px 12px;font-size:15.5px;list-style-position:inside}
details.hist[open]>summary{background:var(--v0);border-bottom:1px solid var(--ln)}
details.hist .tw{border:0;border-radius:0}
ul.hechos{margin:6px 0;padding-left:20px;max-width:86em}
ul.hechos li{margin:5px 0}
.pods{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:0;border-top:1px solid var(--ln);border-left:1px solid var(--ln);margin:14px 0 10px}
.pod{padding:14px 16px 16px;border-right:1px solid var(--ln);border-bottom:1px solid var(--ln)}
.pt{font-size:14px;font-weight:600;color:var(--tx2)}
.pn{font:700 30px/1.05 "Barlow Condensed","Arial Narrow",sans-serif;margin:4px 0 2px}
.pl{font-weight:600;font-variant-numeric:tabular-nums}
.pd{font-size:13.5px;color:var(--tx2);margin-top:6px;line-height:1.4}
.dos{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:22px;margin:14px 0 20px}
figure{margin:0}
figcaption{font:600 17px "Barlow Condensed","Arial Narrow",sans-serif;margin-bottom:4px}
.chart{width:100%;height:auto;display:block}
.chart .ax{font:12px Barlow,sans-serif;fill:#5b6360}
.chart .dl{font:600 13px Barlow,sans-serif;fill:#16191a}
.chart .in{font:600 12px Barlow,sans-serif;fill:#fff}
@media (max-width:640px){.puerta{grid-template-columns:1fr}.puerta input{width:100%}.puerta .fm{width:100%}section>h2{font-size:28px}.kv{font-size:27px}.cab .donde{display:none}}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
@media print{.cab,.subnav,#acceso{display:none!important}.apartado{display:block!important}th{position:static}}
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
 return new Promise(function(ok){var listo=false;function puro(){if(listo)return;listo=true;ok(pbkdf2(utf8(pw),salt,it,64));}
  try{if(window.crypto&&crypto.subtle&&crypto.subtle.importKey){var t=setTimeout(puro,2500);
   crypto.subtle.importKey("raw",utf8(pw),"PBKDF2",false,["deriveBits"]).then(function(k){return crypto.subtle.deriveBits({name:"PBKDF2",salt:salt,iterations:it,hash:"SHA-256"},k,512);})
   .then(function(b){if(listo)return;listo=true;clearTimeout(t);ok(new Uint8Array(b));},function(){clearTimeout(t);puro();});return;}}catch(e){}
  puro();});}
function abrir(caja,pw){var salt=b64(caja.s),iv=b64(caja.i),tag=b64(caja.t),ct=b64(caja.c);
 return derivar(pw,salt,caja.n).then(function(dk){var m=new Uint8Array(16+ct.length);m.set(iv);m.set(ct,16);var t=hmac(hmacEst(dk.subarray(32)),m),d=0,i;for(i=0;i<32;i++)d|=t[i]^tag[i];
  if(d)throw new Error("clave");return new TextDecoder().decode(ctr(dk.subarray(0,32),iv,ct));});}
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
<link href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700&family=Barlow+Condensed:wght@500;600;700&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>
<div id="acceso"><div class="cinta"></div><div class="acc">
<p class="marca">LYSI<b>.</b></p>
<p class="sub">Reportes de flota de Logística y Servicios Integrales S.A. Cada reporte se abre con su propia contraseña.</p>
{"".join(puertas)}</div>
<p class="pie">{pie} Generado el {generado}. Este archivo no guarda ni envía la contraseña: sin ella, el contenido no se puede leer.</p></div>
<div id="app" hidden><div class="cab"><div class="in"><span class="logo">LYSI<b>.</b></span><span class="donde" id="donde"></span><button id="salir" type="button">Cerrar</button></div>
<div class="tabs" id="tabs" role="navigation" aria-label="Apartados"></div></div><main id="contenido"></main></div>
<script>window.LYSI_CAJAS={json.dumps(datos)};</script><script>{JS}</script></body></html>'''
