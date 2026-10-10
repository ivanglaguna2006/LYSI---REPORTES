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
.adm-door{background:#fff;border:1px solid var(--ln);border-radius:12px;padding:18px 22px 10px;margin-top:26px;display:flex;gap:10px 14px;align-items:center;flex-wrap:wrap;color:var(--tx2);font-size:15px}
.adm-door span{flex:1 1 220px}
.adm-door input{font:inherit;padding:10px 13px;border:1px solid #8A8F84;background:#fff;color:var(--tx);border-radius:8px;width:230px}
.adm-door button{font:600 15px var(--ti);padding:10px 18px;border:1px solid var(--lima);border-radius:8px;background:var(--lima);color:var(--ink);cursor:pointer}
.adm-door input::placeholder{color:#6B7066}
.adm-door .msj{flex-basis:100%;margin:0}
#previa{background:#FFF7E0;color:var(--ink);border-bottom:2px solid #E65100;padding:8px 20px;display:flex;gap:14px;align-items:center;flex-wrap:wrap;font-size:14.5px}
#previa button,.btn{font:600 15px var(--ti);padding:8px 16px;border-radius:8px;border:1px solid var(--ink);background:#fff;color:var(--ink);cursor:pointer}
.btn:hover{background:var(--bg2)}
.btn.pri{background:var(--lima);color:var(--ink);border-color:var(--lima);font-size:16.5px;padding:10px 22px}
.btn.pri:hover{background:#A9D64F}
.btn[disabled]{opacity:.45;cursor:not-allowed}
.btn.mini{font-size:13.5px;padding:3px 10px}
.adm section{padding-top:34px}
.adm .pasos{counter-reset:p}
.adm section>h2{counter-increment:p}
.adm section>h2:before{content:counter(p) ". "}
.adm label{font-weight:600;font-size:14.5px}
.adm input[type=text],.adm input[type=password],.adm select{font:inherit;padding:8px 10px;border:1px solid #B9BEB3;border-radius:6px;background:#fff;color:var(--tx)}
.anio{display:flex;gap:10px;align-items:center;margin:8px 0 12px}
.meses{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px;max-width:1100px}
.mesb{text-align:left;font:inherit;border:1px solid var(--ln);background:#fff;border-radius:6px;padding:9px 11px;cursor:pointer;border-left:5px solid #C9CDC3}
.mesb b{display:block;font:600 18px var(--ti)}
.mesb span{font-size:13px;color:var(--tx2)}
.mesb.ok{border-left-color:var(--lima)}
.mesb.arr{border-left-color:#E65100}
.mesb[aria-pressed=true]{background:var(--lima0);border-color:var(--lima2)}
.panel{border:1px solid var(--ln);border-radius:6px;padding:14px 16px 16px;margin-top:14px;max-width:1100px}
.panel h3{margin-top:0;font-size:24px}
.slot{display:grid;grid-template-columns:minmax(210px,1.2fr) minmax(180px,1.4fr) auto auto;gap:6px 14px;align-items:center;padding:8px 0;border-top:1px solid var(--ln)}
.slot .q{font-weight:600}
.slot .q small{display:block;font-weight:400;color:var(--tx2);font-size:13px}
.slot .e{font-size:14px;color:var(--tx2);overflow-wrap:anywhere}
.slot .e.si{color:var(--lima2);font-weight:600}
.fila{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:8px 0}
.estado{padding:10px 13px;border-left:4px solid var(--lima);background:var(--lima0);border-radius:0 6px 6px 0;max-width:1100px;margin:10px 0;font-size:14.5px}
.estado.err{border-left-color:#C62828;background:#FDECEA}
.estado.av{border-left-color:#E65100;background:#FFF7E0}
.sucio{display:inline-block;background:#E65100;color:#fff;font:600 13px var(--cu);letter-spacing:0;padding:3px 9px;border-radius:3px;margin-left:10px;vertical-align:middle}
@media (max-width:700px){.slot{grid-template-columns:1fr}}
"""

CSS_GAS = r"""
.tablero{margin:0 0 40px}
.est-l{background:#fff;border:1px solid var(--ln);border-radius:12px;box-shadow:0 1px 2px rgba(26,26,26,.04);overflow:hidden}
.est-l table{width:100%;border-collapse:collapse;font-size:16.5px}
.est-l th,.est-l td{position:static;background:none;color:var(--tx);text-align:left;padding:15px 24px;border-top:1px solid var(--ln);vertical-align:top;white-space:normal;font-family:var(--cu);font-weight:400}
.est-l thead th{border-top:0;font:600 16px var(--ti);color:var(--tx2);padding-bottom:11px;background:var(--bg2)}
.est-l tbody tr:nth-child(even) td{background:none}
.est-l tbody th{font:600 19px var(--ti);letter-spacing:-.01em;width:34%}
.est-l small{display:block;font:400 13.5px var(--cu);color:var(--tx2);margin-top:3px;letter-spacing:0}
.estc{display:inline-flex;align-items:center;gap:8px;border-radius:20px;padding:6px 15px;font:600 15px var(--ti);white-space:nowrap}
.estc:before{content:"";width:9px;height:9px;border-radius:50%;background:currentColor}
.estc.ok{background:var(--lima0);color:#2C3A14}
.estc.ok:before{background:var(--lima2)}
.estc.pend{background:#FFF1D6;color:#7A4A00}
.estc.curso{background:#E8EEF5;color:#274562}
.estc.prep{background:var(--bg2);color:var(--tx2)}
@media (max-width:640px){.tablero{margin-bottom:28px}.est-l table{font-size:15px}.est-l th,.est-l td{padding:12px 10px}.est-l th:first-child{padding-left:14px}.est-l tbody th{font-size:15.5px;width:36%}.est-l thead th{font-size:14px}.estc{font-size:13px;padding:4px 10px;gap:6px}.est-l small{font-size:12.5px}}
@media print{.tablero{display:none}}
/* Reporte de resultados: viene de Excel (títulos en mayúsculas, color por rubro). Se lleva al mismo sistema que Combustible. */
.gst .tw{margin:8px 0 14px}
.gst th{white-space:normal;text-align:center;vertical-align:bottom;min-width:62px;position:static;font-size:12px;letter-spacing:.04em;line-height:1.2}
.gst th[style*="2E5233"],.gst h3.barra[style*="2E5233"]{background:var(--ink)!important}
/* el ocre del Excel con texto blanco no llegaba al contraste mínimo: se oscurece */
.gst th[style*="C4841D"],.gst h3.barra[style*="C4841D"],.gst td[style*="C4841D;color:#fff"]{background:#8F5E0F!important}
.gst td.c{text-align:center}
.gst th.gap{background:#fff}
.gst .aph h1{font-size:clamp(23px,2.3vw,31px);line-height:1.15;letter-spacing:.01em}
.gst section>h2{font-size:19px;letter-spacing:.03em;line-height:1.25}
.gst section>h2[style*="2E5233"]{border-left-color:var(--lima)!important}
.gst .tw.sl{border:0;margin:14px 0 0}
.gst .tw.sl td{border:0;font:600 19px var(--ti);padding:2px 0}
.gst .gr{color:var(--tx2)}
.gst td .obs{min-width:220px;max-width:460px;color:inherit}
.gst tbody tr:nth-child(even) td{background:transparent}
.gst td{font-size:13.5px;padding-left:8px;padding-right:8px}
.gst th{padding-left:7px;padding-right:7px}
.gk{margin:14px 0 10px;grid-template-columns:repeat(auto-fit,minmax(225px,1fr))}
.gk .kl{font-size:12px;font-weight:600;color:var(--tx2);margin:0 0 5px;letter-spacing:.07em;line-height:1.3}
.gk .kv{font-size:28px}
.gk .kv[style*="2E5233"]{color:var(--ink)!important}
.gk .kn{margin-top:4px}
h3.barra{color:#fff;padding:8px 13px;margin:26px 0 8px;font-size:15px;letter-spacing:.05em;border-radius:6px}
h3.barra.b2{font-size:13.5px;margin:14px 0 4px}
details.gd>summary{font-weight:600}
details.gd .pt{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:8px}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:16px 0 4px}
.chips button{font:500 14px var(--cu);border:1px solid #8A8F84;background:#fff;color:var(--tx);border-radius:16px;padding:3px 11px;cursor:pointer;text-align:left}
.chips button:hover{background:var(--bg2)}
.chips button[aria-current=true]{background:var(--ink);color:#fff;border-color:var(--ink)}
.lnk{font:inherit;font-weight:600;color:var(--lima2);background:none;border:0;padding:0;cursor:pointer;text-decoration:underline}
.gfig{margin:14px 0 20px;max-width:1180px}
.gfig img{max-width:100%;height:auto;display:block;border:1px solid var(--ln);border-radius:10px;cursor:zoom-in}
#zoom{position:fixed;inset:0;z-index:60;background:rgba(26,26,26,.86);display:grid;place-items:center;padding:56px 18px 18px;cursor:zoom-out;outline:none}
#zoom img{max-width:100%;max-height:100%;background:#fff;border-radius:8px}
#zoom .bt{position:absolute;top:10px;right:14px}
.gfig img:focus-visible{outline:3px solid var(--lima2);outline-offset:2px}
@media print{#zoom{display:none!important}}
/* el gráfico de barras del Excel toma los colores de la marca */
.gst .chart rect[fill="#2E7D32"]{fill:var(--lima)}
.gst .gfig .le i[style*="2E7D32"]{background:var(--lima)!important}
.gst .gfig .ley{margin-top:10px}
.gp{max-width:100ch;margin:6px 0}
.gst p.aviso{margin:8px 0}
/* en pantallas anchas las 19 hojas pasan a un índice fijo a la izquierda */
@media (min-width:1500px){
 .gst[data-grupo]{display:grid;grid-template-columns:196px minmax(0,1fr);column-gap:32px;align-items:start}
 .gst[data-grupo]>*{grid-column:2;min-width:0}
 .gst[data-grupo]>.aph{grid-column:1/-1;padding-bottom:14px;border-bottom:1px solid var(--ln)}
 .gst[data-grupo]>.chips{grid-column:1;grid-row:2/span 300;position:sticky;top:calc(var(--cabh,96px) + 14px);max-height:calc(100vh - var(--cabh,96px) - 28px);overflow-y:auto;flex-direction:column;flex-wrap:nowrap;gap:0;margin:22px 0 0;padding:0 0 12px}
 .gst[data-grupo]>.chips button{border:0;border-left:3px solid var(--ln);border-radius:0;padding:6px 12px;font-size:14.5px;color:var(--tx2);background:none}
 .gst[data-grupo]>.chips button:hover{color:var(--ink);background:var(--bg2)}
 .gst[data-grupo]>.chips button[aria-current=true]{border-left-color:var(--lima);color:var(--ink);font-weight:600;background:var(--lima0)}
 .gst[data-grupo]>section:first-of-type{padding-top:26px}
}
/* en tablet y celular las hojas van en una tira fija bajo la cabecera, con la hoja activa siempre a la vista */
@media (max-width:900px){
 .gst .chips{position:sticky;top:var(--cabh,96px);z-index:20;background:var(--bg);flex-wrap:nowrap;overflow-x:auto;margin:14px -20px 0;padding:8px 20px;border-bottom:1px solid var(--ln);scrollbar-width:none}
 .gst .chips::-webkit-scrollbar{display:none}
 .gst .chips button{flex:none;white-space:nowrap}
}
@media (max-width:640px){.gk{grid-template-columns:1fr 1fr}.gk .kv{font-size:19px;white-space:normal;overflow-wrap:anywhere}.gk .kl{font-size:11px}
 .gst .chips{margin:14px -16px 0;padding:8px 16px}
 .gst .aph h1{font-size:23px}.gst section>h2{font-size:17px}}
"""

HTML_CUERPO = r"""
<svg width="0" height="0" style="position:absolute" aria-hidden="true"><symbol id="lg" viewBox="0 0 960 920"><path fill="currentColor" fill-rule="evenodd" d="M385 689C384 688 385 686 392 673C395 669 398 663 400 660C411 640 437 601 439 600C440 600 449 600 484 600C538 600 545 599 558 597C611 588 642 548 629 500C625 484 615 468 602 456C597 453 598 452 611 446C638 435 667 429 693 429C702 429 701 428 706 438C724 476 730 519 721 560C707 622 654 670 585 683C582 684 580 684 579 684C569 686 547 689 529 689C513 690 386 690 385 689ZM118 587C118 587 118 531 118 462C118 394 118 271 118 188C118 38 118 38 119 37C120 36 215 36 216 38C217 38 217 477 216 480C216 480 213 484 209 488C178 517 152 546 126 580C120 588 119 588 119 588C118 588 118 588 118 587ZM520 410C512 405 512 405 528 400C544 394 555 391 573 388C586 385 592 384 604 383C615 382 616 382 617 382C617 382 617 383 616 383C615 383 606 385 603 386C580 390 561 396 546 402C544 403 541 404 538 405C535 406 531 408 529 409C524 411 524 411 520 410ZM406 356C384 343 372 335 356 320C333 298 313 267 306 238C284 151 336 68 427 45C442 41 453 39 472 37C484 36 691 36 692 38C693 39 693 126 692 127C691 128 691 128 587 128C472 128 474 128 462 130C412 138 386 175 400 216C406 235 422 252 447 266C449 267 453 269 454 270C457 271 473 280 489 288C494 290 508 298 520 304C568 328 564 325 549 326C544 326 538 327 536 327C533 328 528 328 525 329C493 332 451 343 416 356C411 358 410 358 406 356Z"/><path fill="#94C337" fill-rule="evenodd" d="M291 897C289 896 283 886 278 880C277 878 274 874 273 872C271 870 269 867 269 866C268 865 266 863 266 862C264 860 263 858 262 856C260 854 257 850 255 846C252 843 250 839 250 838C249 837 248 836 247 835C247 834 244 831 242 827C238 821 235 817 231 811C230 810 227 806 225 802C222 799 220 795 219 793C216 790 216 789 217 786C218 784 219 780 220 778C220 777 221 775 222 773C222 772 223 770 224 769C224 768 225 766 225 765C226 764 226 763 226 763C226 763 227 761 228 759C228 757 230 754 230 753C231 751 232 748 234 746C240 732 244 724 246 719C250 711 254 704 256 701C257 699 259 695 260 692C262 688 264 686 264 685C264 684 266 682 267 680C268 678 270 675 271 673C272 671 274 668 275 666C276 664 277 663 277 662C278 662 278 660 279 658C280 657 282 653 284 650C286 647 289 643 289 642C293 637 309 613 314 605C318 600 333 580 337 575C338 573 340 571 341 570C342 568 344 566 345 564C347 563 348 561 349 560C350 559 352 557 354 554C356 552 358 549 359 548C361 546 366 541 370 536C372 535 375 531 378 528C392 513 406 499 416 491C418 489 421 486 422 485C423 484 426 482 428 480C429 479 433 476 436 474C450 463 462 454 475 446C477 444 480 442 482 441C483 440 486 439 487 438C488 438 491 436 493 435C497 433 500 431 508 427C511 425 527 417 530 416C531 415 534 414 537 413C540 412 543 410 544 410C545 409 548 408 550 408C552 407 554 406 556 406C557 405 559 404 561 404C562 403 565 402 566 402C568 401 570 401 572 400C573 400 576 399 576 399C580 398 588 395 594 394C596 394 598 393 600 393C601 393 604 392 606 392C609 391 611 391 612 390C613 390 615 390 616 390C618 390 626 389 628 389C635 387 678 387 686 389C687 389 692 390 695 390C696 390 698 390 700 391C702 391 705 392 707 392C710 393 715 394 719 394C721 395 727 396 728 397C728 397 729 397 730 398C732 398 734 399 737 400C739 400 742 401 744 402C746 402 748 403 750 404C752 405 755 406 757 407C764 410 780 417 785 420C786 421 789 422 791 423C796 426 811 436 817 440C819 442 822 444 824 445C826 447 830 450 838 458C849 467 868 486 875 494C876 496 878 498 879 499C882 503 888 510 890 511C890 512 892 514 893 516C894 517 896 520 897 522C899 523 900 526 901 527C903 529 908 536 912 542C913 544 915 547 916 548C918 551 919 553 919 554C919 555 914 550 910 545C909 543 906 540 901 534C888 517 869 498 852 483C850 482 848 480 847 480C847 479 845 478 843 476C841 475 838 472 835 470C833 469 829 466 828 465C824 462 818 459 808 453C800 448 787 441 784 440C783 440 782 440 781 439C780 439 779 438 778 438C777 438 775 437 774 436C772 436 770 435 768 434C767 434 764 433 762 432C754 430 745 427 740 426C739 426 736 426 735 425C733 425 730 424 724 424C723 424 721 423 719 423C711 421 681 422 672 423C670 423 667 424 665 424C662 424 659 425 658 425C656 426 654 426 652 426C651 427 649 427 648 427C648 428 646 428 644 428C643 428 640 429 637 430C635 431 632 432 631 432C629 432 628 433 627 433C626 434 623 435 621 436C618 436 615 438 614 438C612 439 610 440 608 441C597 445 576 456 563 465C548 475 544 478 532 488C531 489 528 491 527 492C515 502 493 524 482 536C480 539 476 542 475 544C474 545 471 548 469 551C467 553 464 556 463 558C461 560 458 564 456 566C455 568 452 571 451 572C447 578 441 586 438 589C437 591 436 593 435 594C434 595 431 600 421 614C416 622 414 625 410 630C410 631 407 635 406 638C404 640 402 643 402 643C401 645 395 655 393 658C391 661 390 664 388 668C385 673 383 677 381 680C380 682 377 686 376 690C374 693 372 696 371 697C368 703 344 750 344 752C344 752 342 756 340 760C338 765 336 769 336 770C336 770 335 772 334 775C333 777 332 780 331 782C331 783 330 784 329 786C329 787 328 788 328 789C328 790 327 792 326 794C325 796 324 798 324 799C324 799 324 800 323 801C323 802 322 804 322 804C322 805 321 807 320 809C320 811 318 814 317 817C316 820 315 824 314 825C314 827 313 830 312 831C312 832 311 834 311 834C311 835 310 836 310 836C310 837 310 838 310 839C308 844 305 854 304 857C304 858 303 860 303 861C303 861 302 863 302 865C301 868 298 879 297 883C297 884 297 886 296 887C296 888 296 890 296 891C295 893 295 894 294 895C294 898 292 899 291 897ZM177 736C177 735 175 733 174 730C172 728 170 726 170 725C168 721 163 714 162 712C161 711 157 705 152 698C147 691 142 682 139 679C137 676 134 671 132 668C128 663 126 660 123 654C120 650 107 631 104 627C102 623 101 625 116 604C118 601 122 596 123 594C125 591 128 588 129 586C131 584 133 582 134 580C137 576 139 573 142 570C143 568 146 565 147 563C149 561 152 558 153 556C155 554 158 551 160 548C162 545 164 543 164 543C164 543 166 542 168 540C180 525 204 501 219 487C230 477 232 476 234 473C236 472 238 470 240 469C242 467 245 465 247 463C249 461 253 458 256 456C258 454 261 451 262 450C263 450 267 447 271 444C275 441 280 437 283 435C285 434 288 431 290 430C294 427 315 413 321 410C323 409 326 406 329 405C332 404 335 402 336 401C337 400 340 398 343 397C347 394 376 380 382 377C384 376 387 375 389 374C392 373 394 372 395 372C396 371 397 370 399 370C404 368 407 366 412 365C414 364 418 362 421 361C423 360 427 359 429 358C431 358 435 356 437 356C439 355 442 354 443 354C444 354 446 353 447 353C449 352 455 350 456 350C457 350 459 349 462 348C464 348 467 347 469 346C476 345 480 344 483 343C485 342 487 342 488 342C488 342 490 342 492 341C497 340 504 338 508 338C510 338 513 337 514 337C516 337 518 336 520 336C522 336 525 335 527 335C529 335 533 334 536 334C540 334 544 333 545 333C554 332 554 332 584 332C609 332 613 332 615 332C619 333 620 333 627 334C630 334 635 335 636 335C638 335 641 336 643 336C645 336 647 336 648 337C649 337 651 338 653 338C655 338 657 338 659 339C660 339 663 340 664 340C666 340 668 341 670 341C671 341 674 342 676 343C679 343 682 344 683 344C684 345 687 345 688 346C691 346 696 348 699 349C700 350 704 351 707 352C713 354 722 357 732 361C735 362 738 364 738 364C742 365 773 382 776 384C777 385 778 386 778 386C782 388 801 401 806 405C807 406 809 408 810 408C812 409 814 411 815 412C816 413 818 415 820 416C821 417 824 420 826 422C828 424 831 427 833 428C835 430 848 443 852 448C854 449 856 452 857 453C860 456 864 461 866 464C867 464 869 467 871 469C874 474 881 483 884 487C885 489 886 491 887 492C888 492 889 495 890 496C891 498 893 502 895 504C899 510 903 517 905 522C906 524 908 526 908 527C910 529 914 537 914 537C914 539 912 538 910 535C908 531 903 522 902 521C902 520 901 519 900 518C899 517 897 513 894 510C892 507 890 503 889 502C888 502 887 499 885 497C884 496 882 493 880 491C879 490 876 486 874 484C873 482 869 478 867 476C861 469 847 455 842 450C838 446 834 443 831 441C830 440 828 438 826 437C824 435 818 430 811 425C805 421 793 413 787 410C772 402 771 401 769 400C768 400 766 399 764 398C762 397 760 396 759 396C758 395 755 394 753 394C746 391 735 387 732 386C730 386 729 385 728 385C728 385 727 385 725 384C724 384 722 384 721 383C720 383 718 382 717 382C716 382 714 381 713 381C712 381 710 380 708 380C707 380 705 380 704 379C703 379 700 378 699 378C696 378 694 378 689 377C688 377 684 376 682 376C679 376 675 375 673 375C659 374 618 374 610 375C609 376 606 376 604 376C600 376 596 377 592 378C590 378 588 378 588 378C586 378 580 379 568 382C564 382 561 383 546 387C543 388 537 390 526 394C520 396 512 398 510 399C508 400 507 400 507 400C507 400 505 401 503 402C501 403 499 404 498 404C497 404 495 405 494 406C492 407 490 408 489 408C488 408 483 411 478 413C473 415 468 417 468 417C468 417 444 430 441 432C440 432 439 433 437 434C435 435 416 446 412 449C411 450 410 451 409 451C406 453 405 454 400 458C397 460 392 463 390 464C387 466 384 468 382 470C381 471 378 473 376 474C374 476 371 478 369 480C368 481 365 483 364 484C362 485 359 488 357 490C355 492 352 494 352 494C350 495 349 497 340 504C327 516 302 541 294 550C293 552 291 554 289 556C288 558 285 561 284 562C283 564 281 566 280 566C276 571 275 573 273 575C272 577 270 579 269 581C262 590 251 604 241 620C237 625 234 631 232 632C231 634 230 636 229 637C226 643 221 651 216 660C207 676 206 680 200 693C196 701 195 703 193 707C193 708 192 710 191 711C191 712 190 715 189 717C186 726 181 736 181 737C180 738 178 737 177 736Z"/></symbol></svg>
<div id="acceso"><header class="barra"><div class="marca"><svg class="lgm" viewBox="0 0 960 920" role="img" aria-label="LYSI"><use href="#lg"/></svg></div><span class="razon">Logística y Servicios Integrales</span><span class="priv"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="5" y="10.5" width="14" height="10" rx="2"/><path d="M8 10.5V7.5a4 4 0 0 1 8 0v3"/><path d="M12 14.5v2.5"/></svg><span>Acceso privado</span></span></header>
<div class="acc">
<p class="ceja">Gestión de flota</p>
<h1>Reportes de flota</h1>
<p class="sub">Consultá los reportes y la evolución de tu operación.</p>
<section class="tablero" id="estado" hidden><div class="rdh"><h2>Estado de los reportes</h2><span id="est-hoy"></span></div><div class="est-l" id="est-l"></div></section>
<div class="rdh"><h2>Reportes disponibles</h2><span id="cuantos"></span></div>
<div class="puertas">
<div class="puerta"><div class="pc"><span class="ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 20.5V5.5a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v15M3.5 20.5h13M7.5 7h5v4.5h-5zM15 9.5h1.5a2 2 0 0 1 2 2v4.2a1.4 1.4 0 0 0 2.8 0V8.8L18.6 6"/></svg></span><div><h3>Combustible</h3><p id="desc-combustible">Consumos mensuales y evaluación anual de la flota.</p>
<span class="per" id="per-combustible" hidden><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="5.5" width="16" height="14.5" rx="2"/><path d="M4 10h16M8.5 3.5v4M15.5 3.5v4"/></svg><span></span></span></div></div>
<div class="fm" data-caja="combustible" data-nombre="Combustible"><label for="pw-combustible">Contraseña del reporte</label>
<div class="campo"><input id="pw-combustible" type="password" placeholder="Ingresá tu contraseña" autocomplete="new-password"><button type="button" class="ojo" aria-label="Mostrar la contraseña" aria-pressed="false"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z"/><circle cx="12" cy="12" r="2.8"/></svg></button></div>
<button type="button" class="entrar">Acceder al reporte <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4.5 12h15M13.5 6l6 6-6 6"/></svg></button></div>
<p class="msj" id="msj-combustible" role="status"></p></div>
<div class="puerta"><div class="pc"><span class="ico"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><rect x="3.5" y="13" width="4.4" height="8" rx="1"/><rect x="9.8" y="8.5" width="4.4" height="12.5" rx="1"/><rect x="16.1" y="3.5" width="4.4" height="17.5" rx="1"/></svg></span><div><h3>Reporte de resultados</h3><p id="desc-gastos">Compras, proveedores y gastos de mantenimiento.</p>
<span class="per" id="per-gastos" hidden><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="5.5" width="16" height="14.5" rx="2"/><path d="M4 10h16M8.5 3.5v4M15.5 3.5v4"/></svg><span></span></span></div></div>
<div class="fm" data-caja="gastos" data-nombre="Reporte de resultados" id="fm-gastos" hidden><label for="pw-gastos">Contraseña del reporte</label>
<div class="campo"><input id="pw-gastos" type="password" placeholder="Ingresá tu contraseña" autocomplete="new-password"><button type="button" class="ojo" aria-label="Mostrar la contraseña" aria-pressed="false"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z"/><circle cx="12" cy="12" r="2.8"/></svg></button></div>
<button type="button" class="entrar">Acceder al reporte <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4.5 12h15M13.5 6l6 6-6 6"/></svg></button></div><span class="pronto" id="pronto-gastos">En preparación</span>
<p class="msj" id="msj-gastos" role="status"></p></div>
</div>
<div class="adm-door" id="adm-door" hidden><span>Administración: cargar los archivos de un mes y publicar.</span>
<input id="pw-admin" type="password" placeholder="Contraseña de administración" aria-label="Contraseña de administración" autocomplete="new-password"><button type="button" id="btn-admin">Administrar</button>
<p class="msj" id="msj-admin" role="status"></p></div>
<p class="pie"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="5" y="10.5" width="14" height="10" rx="2"/><path d="M8 10.5V7.5a4 4 0 0 1 8 0v3"/><path d="M12 14.5v2.5"/></svg><span id="pie">Cada reporte tiene una contraseña independiente.</span></p></div>
<footer class="fin"><span>LYSI · Plataforma de reportes</span><span id="actualizado"></span></footer></div>

<div id="app" hidden><a class="saltar" href="#contenido">Saltar al contenido</a><div class="cab"><div class="in"><span class="logo"><svg class="lgm" viewBox="0 0 960 920" role="img" aria-label="LYSI"><use href="#lg"/></svg></span><span class="donde" id="donde"></span><div class="imp"><button id="imp-btn" class="bt" type="button" aria-label="Imprimir o guardar en PDF" aria-controls="imp-menu" aria-expanded="false"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 8.5V3.5h10v5M7 17H5a1.5 1.5 0 0 1-1.5-1.5v-5A2 2 0 0 1 5.5 8.5h13a2 2 0 0 1 2 2v5A1.5 1.5 0 0 1 19 17h-2"/><rect x="7" y="13.5" width="10" height="7" rx="1"/></svg><span>Imprimir / PDF</span></button><div id="imp-menu" hidden><button type="button" data-imp="resumen">Solo el resumen<small>La primera sección de esta pestaña</small></button><button type="button" data-imp="todo">Todo lo de esta pestaña<small>Todas las secciones, con los detalles abiertos</small></button></div></div><button id="salir" type="button">Cerrar</button></div>
<div class="tabs" id="tabs" role="navigation" aria-label="Apartados"></div>
<div id="previa" hidden><b>Vista previa.</b> Así va a quedar; todavía no está publicado. <button type="button" id="volver-adm">Volver a administración</button></div></div>
<div class="imp-cab"><svg class="lgm" viewBox="0 0 960 920" role="img" aria-label="LYSI"><use href="#lg"/></svg><div><b>Logística y Servicios Integrales</b><span id="imp-tit"></span></div><span class="f" id="imp-fecha"></span></div>
<main id="contenido" tabindex="-1"></main></div>

<div id="adm" class="adm" hidden><div class="cab"><div class="in"><span class="logo"><svg class="lgm" viewBox="0 0 960 920" role="img" aria-label="LYSI"><use href="#lg"/></svg></span><span class="donde">Administración</span><button id="salir-adm" type="button">Cerrar</button></div></div>
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
<div class="fila"><label for="gh-o">Cuenta de GitHub</label><input type="text" id="gh-o" size="18" autocomplete="off"><label for="gh-r">Repositorio</label><input type="text" id="gh-r" size="18" autocomplete="off"><label for="gh-t">Token</label><input type="password" id="gh-t" size="30" autocomplete="new-password"></div>
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
function mayus(s){s=String(s||"");return s.charAt(0).toUpperCase()+s.slice(1);}
function periodo(id,txt){var c=$("per-"+id);c.hidden=!txt;c.lastChild.textContent=txt||"";}
var CARGADO=!LYSI.remoto,FALLO=false,PYO_URL=LYSI.pyodide,TITULO=document.title,ORIGEN=null;
var QUIETO=!!(window.matchMedia&&window.matchMedia("(prefers-reduced-motion:reduce)").matches);
function pintarInfo(){var inf=LYSI.info||{},ms=inf.meses||[],t="";
 if(ms.length){var x=ms[0].split(" "),y=ms[ms.length-1].split(" ");t=ms.length>1?mayus(x[0])+(x[1]&&x[1]!==y[1]?" "+x[1]:"")+" – "+mayus(y[0])+(y[1]?" "+y[1]:""):mayus(ms[0]);}
 periodo("combustible",t);if(CARGADO)$("pie").textContent="Cada reporte tiene una contraseña independiente.";
 var g=/^(\d\d)\/(\d\d)\/(\d{4})/.exec(inf.generado||"");$("actualizado").textContent=g?"Actualizado el "+Number(g[1])+" de "+MESES[Number(g[2])]+" de "+g[3]:"";
 $("reglas").textContent=inf.reglas||"";}
// Mientras los datos se están bajando la tarjeta dice «Cargando…»; «En preparación» es solo para un reporte que todavía no existe.
function pintarGastos(){var hay=!!(LYSI.cajas&&LYSI.cajas.gastos),inf=LYSI.info||{},pr=$("pronto-gastos");$("fm-gastos").hidden=!hay;pr.hidden=hay;
 pr.textContent=CARGADO?"En preparación":(FALLO?"Sin cargar":"Cargando…");
 var t=hay&&inf.gastos?String(inf.gastos).split(" · ")[0].replace(/ a ([a-záéíóú])/,function(m,l){return " – "+l.toUpperCase();}):"";periodo("gastos",t);
 $("cuantos").textContent=CARGADO?(hay?"2 reportes":"1 reporte"):"";pintarEstado();}
// Estado de cada reporte mes por mes: el mes anterior (que ya tiene que estar cargado) y el mes en curso.
// Combustible es mensual; Resultados es quincenal (el corte parcial del mes en curso se espera desde el 16).
function pintarEstado(){var el=$("estado");if(!CARGADO||FALLO||!LYSI.info){el.hidden=true;return;}
 var inf=LYSI.info,hoy=new Date(),y=hoy.getFullYear(),m=hoy.getMonth()+1,d=hoy.getDate(),act=y*12+m,ant=act-1;
 function nom(i){var yy=Math.floor((i-1)/12),mm=i-yy*12;return mayus(MESES[mm])+" "+yy;}
 function celda(c){return'<td><span class="estc '+c[0]+'">'+esc(c[1])+"</span>"+(c[2]?"<small>"+esc(c[2])+"</small>":"")+"</td>";}
 var comb={},ms=inf.meses||[],i;for(i=0;i<ms.length;i++){var u=String(ms[i]).toLowerCase().split(" "),k=MESES.indexOf(u[0]);if(k>0)comb[Number(u[1])*12+k]=1;}
 function eComb(x){if(comb[x])return["ok","Cargado",""];return x===act?["curso","En curso","Se carga cuando cierre el mes"]:["pend","Pendiente","Falta cargarlo"];}
 var hayG=!!(LYSI.cajas&&LYSI.cajas.gastos&&inf.gastos),gi=0,par=false;
 if(hayG){var t=String(inf.gastos).split(" · ")[0],w=t.toLowerCase().split(" a ").pop().replace(/[^a-záéíóúñ ]/g," ").trim().split(" ")[0],gm=MESES.indexOf(w),gf=/^(\d\d)\/(\d\d)\/(\d{4})/.exec(inf.gastos_fecha||"");
  par=/parcial/i.test(t);var gy=gf?Number(gf[3]):y;if(gm>(gf?Number(gf[2]):m))gy--;gi=gm>0?gy*12+gm:0;}
 function eRes(x){if(!hayG)return["prep","En preparación",""];
  if(x<act){if(gi>x||(gi===x&&!par))return["ok","Cargado",""];return gi===x?["pend","Pendiente","Falta el cierre del mes"]:["pend","Pendiente","Falta cargarlo"];}
  if(gi>=x)return["ok","Corte cargado","Cierra el 1 de "+MESES[m<12?m+1:1]];
  return d>=16?["pend","Pendiente","Falta el corte del 16"]:["curso","En curso","Primer corte: 16 de "+MESES[m]];}
 var h='<table><thead><tr><th scope="col">Reporte</th><th scope="col">'+esc(nom(ant))+'</th><th scope="col">'+esc(nom(act))+"<small>mes en curso</small></th></tr></thead><tbody>"
  +'<tr><th scope="row">Combustible<small>Mensual</small></th>'+celda(eComb(ant))+celda(eComb(act))+"</tr>"
  +'<tr><th scope="row">Reporte de resultados<small>Quincenal</small></th>'+celda(eRes(ant))+celda(eRes(act))+"</tr></tbody></table>";
 $("est-l").innerHTML=h;$("est-hoy").textContent="Hoy: "+d+" de "+MESES[m]+" de "+y;el.hidden=false;}
// Ver u ocultar la contraseña mientras se escribe.
function ojo(inp,ver){inp.type=ver?"text":"password";var o=inp.parentNode.querySelector(".ojo");
 if(o){o.setAttribute("aria-pressed",ver?"true":"false");o.setAttribute("aria-label",ver?"Ocultar la contraseña":"Mostrar la contraseña");}}
document.addEventListener("click",function(ev){var o=ev.target.closest&&ev.target.closest(".ojo");if(!o)return;var inp=o.parentNode.querySelector("input");ojo(inp,inp.type==="password");inp.focus();});
pintarGastos();pintarInfo();
// El acceso de administración no se muestra en el inicio: aparece entrando con #admin al final de la dirección…
var PUERTA_HASH=false;
function verPuertaAdm(){var v=/^#admin$/i.test(location.hash);
 if(v){PUERTA_HASH=true;$("adm-door").hidden=false;setTimeout(function(){try{$("pw-admin").focus();}catch(e){}},50);}
 else if(PUERTA_HASH){PUERTA_HASH=false;$("adm-door").hidden=true;}}
verPuertaAdm();window.addEventListener("hashchange",verPuertaAdm);
// …o, con el mismo link para todos, tocando cinco veces seguidas el logo de la pantalla de inicio.
(function(){var p=document.querySelector("#acceso .marca"),n=0,t=null;if(!p)return;
 p.addEventListener("click",function(){n++;clearTimeout(t);t=setTimeout(function(){n=0;},2500);
  if(n>=5){n=0;var d=$("adm-door");d.hidden=!d.hidden;if(!d.hidden){d.scrollIntoView({block:"center"});setTimeout(function(){try{$("pw-admin").focus();}catch(e){}},50);}}});})();
var LISTO=Promise.resolve();
function cargarDatos(){FALLO=false;var pie=$("pie"),r0=$("reintentar");if(r0)r0.remove();pie.parentNode.classList.remove("err");pie.textContent="Cargando los reportes…";pintarGastos();
 LISTO=fetch(LYSI.remoto+"?t="+Date.now(),{cache:"no-store"}).then(function(r){if(!r.ok)throw new Error("http "+r.status);return r.json();})
  .then(function(d){d.remoto=LYSI.remoto;LYSI=d;window.LYSI=d;CARGADO=true;pintarInfo();pintarGastos();})
  .catch(function(e){FALLO=true;pintarGastos();pie.parentNode.classList.add("err");pie.textContent="No se pudieron cargar los reportes ("+(e&&e.message||e)+"). Revisá la conexión.";
   var b=document.createElement("button");b.type="button";b.id="reintentar";b.className="bt";b.textContent="Reintentar";b.addEventListener("click",cargarDatos);pie.parentNode.appendChild(b);
   throw new Error("sin datos");});
 LISTO.catch(function(){});}
if(LYSI.remoto)cargarDatos();
function medir(){var cs=document.querySelectorAll(".cab"),i;for(i=0;i<cs.length;i++)if(cs[i].offsetHeight)document.documentElement.style.setProperty("--cabh",cs[i].offsetHeight+"px");}
if(document.fonts&&document.fonts.ready)document.fonts.ready.then(medir);
// Tablas más anchas que la pantalla: se desvanecen a la derecha mientras quede algo por ver.
var SOM=0;
function sombras(){if(SOM)return;SOM=1;setTimeout(function(){SOM=0;var ap=cont.querySelector(".apartado:not([hidden])");if(!ap)return;
 var ts=ap.querySelectorAll(".tw"),i;for(i=0;i<ts.length;i++){var t=ts[i];if(!t.clientWidth)continue;t.classList.toggle("mas",t.scrollWidth-t.clientWidth-t.scrollLeft>6);}},60);}
document.addEventListener("scroll",function(ev){if(ev.target&&ev.target.classList&&ev.target.classList.contains("tw"))sombras();},true);
document.addEventListener("toggle",sombras,true);
function enfocar(el){if(!el)return;try{if(!el.hasAttribute("tabindex"))el.setAttribute("tabindex","-1");el.focus({preventScroll:true});}catch(e){}}
function mostrar(id,foco){var aps=cont.querySelectorAll(".apartado"),i,ok=false;for(i=0;i<aps.length;i++){var v=aps[i].id===id;aps[i].hidden=!v;ok=ok||v;}
 if(!ok&&aps.length){aps[aps.length-1].hidden=false;id=aps[aps.length-1].id;}
 var ap=document.getElementById(id),gr=ap&&ap.getAttribute("data-grupo");
 var bs=document.querySelectorAll(".tabs button");for(i=0;i<bs.length;i++){var on=bs[i].getAttribute("data-ir")===id||(gr&&bs[i].getAttribute("data-grupo")===gr);bs[i].setAttribute("aria-current",on?"true":"false");if(on&&bs[i].scrollIntoView)try{bs[i].scrollIntoView({block:"nearest",inline:"nearest"});}catch(e){}}
 // la hoja activa queda a la vista dentro de su lista (tira en celular, índice lateral en pantallas anchas)
 var ch=ap&&ap.querySelector(".chips"),ca=ch&&ch.querySelector('button[aria-current="true"]');
 if(ca){var rc=ch.getBoundingClientRect(),ra=ca.getBoundingClientRect();ch.scrollLeft+=ra.left-rc.left-(ch.clientWidth-ra.width)/2;ch.scrollTop+=ra.top-rc.top-(ch.clientHeight-ra.height)/2;}
 try{window.scrollTo({top:0,left:0,behavior:"instant"});}catch(e){window.scrollTo(0,0);}medir();espiar();sombras();
 var h=ap&&ap.querySelector("h1");document.title=(h?h.textContent.trim()+" · ":"")+$("donde").textContent+" · "+TITULO;if(foco)enfocar(h);}
// Presentación solamente: no cambia ningún número ni texto de los reportes.
function realzar(){var i,st=cont.querySelectorAll("style");
 // colores que vienen del Excel: el verde por defecto pasa al negro de la marca y el ocre se oscurece para que el texto blanco se lea
 for(i=0;i<st.length;i++)st[i].textContent=st[i].textContent.replace(/#2E5233/gi,"#1A1A1A").replace(/#C4841D;color:#fff/gi,"#8F5E0F;color:#fff");
 var E={"críticas":"c","en atención":"a","normales":"n","coeficiente bajo":"b","a investigar":"i"},ks=cont.querySelectorAll(".kpi>.kl");
 for(i=0;i<ks.length;i++){var t=(ks[i].textContent||"").trim().toLowerCase(),k=ks[i].parentNode;if(t==="coeficiente general")k.classList.add("kpi-h");else if(E[t])k.setAttribute("data-e",E[t]);}
 // ayudas para lectores de pantalla y teclado
 var ths=cont.querySelectorAll("thead th");for(i=0;i<ths.length;i++)ths[i].setAttribute("scope","col");
 var ts=cont.querySelectorAll(".tw");for(i=0;i<ts.length;i++){var p=ts[i].previousElementSibling;while(p&&!/^H[23]$/.test(p.tagName))p=p.previousElementSibling;
  if(!p){var d=ts[i].closest("details");p=d&&d.querySelector("summary");}
  ts[i].setAttribute("role","region");ts[i].setAttribute("aria-label","Tabla"+(p?": "+p.textContent.trim().slice(0,90):""));}
 // tablas cuya primera columna es un texto largo (no una patente): en celular esa columna se ajusta en varias líneas
 var tb=cont.querySelectorAll(".apartado:not(.gst) table");for(i=0;i<tb.length;i++){var rs=tb[i].tBodies[0]?tb[i].tBodies[0].rows:[],mx=0,j;
  for(j=0;j<rs.length&&j<40;j++)if(rs[j].cells[0])mx=Math.max(mx,(rs[j].cells[0].textContent||"").length);if(mx>26)tb[i].classList.add("c1l");}
 var gs=cont.querySelectorAll(".gfig img");for(i=0;i<gs.length;i++){var s=gs[i].closest("section"),h=s&&s.querySelector("h2"),n=h?h.textContent.trim():"";
  gs[i].alt="Gráfico"+(n?": "+n:" del reporte");gs[i].setAttribute("role","button");gs[i].setAttribute("tabindex","0");gs[i].setAttribute("aria-label","Ampliar el gráfico"+(n?": "+n:""));}}
// Marca en la barra de secciones cuál se está leyendo.
var ESP=0;
function espiar(){if(ESP)return;ESP=1;(window.requestAnimationFrame||setTimeout)(function(){ESP=0;
 var ap=cont.querySelector(".apartado:not([hidden])"),nav=ap&&ap.querySelector(".subnav");if(!nav)return;
 var ls=nav.querySelectorAll("a"),corte=nav.getBoundingClientRect().bottom+60,act=null,i;
 for(i=0;i<ls.length;i++){var s=document.getElementById((ls[i].getAttribute("href")||"").slice(1));if(s&&s.getBoundingClientRect().top<=corte)act=ls[i];}
 if(!act)act=ls[0];
 for(i=0;i<ls.length;i++){var on=ls[i]===act;if((ls[i].getAttribute("aria-current")==="true")!==on){if(on){ls[i].setAttribute("aria-current","true");
   var d=ls[i].offsetLeft-nav.offsetLeft-(nav.clientWidth-ls[i].offsetWidth)/2;try{nav.scrollTo({left:d,behavior:QUIETO?"auto":"smooth"});}catch(e){nav.scrollLeft=d;}}else ls[i].removeAttribute("aria-current");}}},16);}
window.addEventListener("scroll",espiar,{passive:true});
function verReporte(htmlTxt,nombre,previa){cont.innerHTML=htmlTxt;realzar();var t=cont.querySelector("template[data-tabs]");$("tabs").innerHTML=t?t.innerHTML:"";$("donde").textContent=nombre;
 $("previa").hidden=!previa;acceso.hidden=true;adm.hidden=true;app.hidden=false;
 mostrar((cont.querySelector("[data-inicio]")||{getAttribute:function(){return"";}}).getAttribute("data-inicio"),true);}
document.addEventListener("click",function(ev){var c=ev.target.closest&&ev.target.closest.bind(ev.target);if(!c)return;
 var b=c("[data-ir]");if(b){mostrar(b.getAttribute("data-ir"),true);return;}
 // las secciones se recorren sin ensuciar la dirección ni el botón «Atrás»
 var a=c(".subnav a");if(a){var s=document.getElementById((a.getAttribute("href")||"").slice(1));if(s){ev.preventDefault();s.scrollIntoView({block:"start",behavior:QUIETO?"auto":"smooth"});enfocar(s.querySelector("h2"));}return;}
 if(c(".saltar")){ev.preventDefault();enfocar(cont);}});
function puerta(inp,btn,msj,accion){
 function mal(t,inv){msj.style.color="";msj.textContent=t;if(inv)inp.setAttribute("aria-invalid","true");}
 function entrar(){if(btn.disabled)return;var pw=(inp.value||"").trim();if(!pw){mal("Escribí la contraseña.",true);inp.focus();return;}
  inp.removeAttribute("aria-invalid");btn.disabled=true;msj.style.color="var(--tx2)";msj.textContent="Abriendo…";
  setTimeout(function(){var pr;try{pr=LISTO.then(function(){return accion(pw);});}catch(err){pr=Promise.reject(err);}
   pr.then(function(){inp.value="";ojo(inp,false);msj.textContent="";btn.disabled=false;})
    .catch(function(err){btn.disabled=false;var m=err&&err.message;
     if(m==="clave"){mal("Contraseña incorrecta. Probá de nuevo.",true);inp.select();}
     else if(m==="sin datos"){mal("Todavía no se pudieron cargar los reportes. Tocá «Reintentar» al pie de la página.");}
     else if(m==="viejo"){mal("Tu navegador es antiguo para este reporte. Actualizalo o abrilo con Chrome, Edge o Safari al día.");}
     else{mal("No se pudo abrir el reporte ("+(m||err)+"). Recargá la página y probá de nuevo.");}});},40);}
 if(msj.id)inp.setAttribute("aria-describedby",msj.id);
 inp.addEventListener("input",function(){inp.removeAttribute("aria-invalid");});
 btn.addEventListener("click",entrar);inp.addEventListener("keydown",function(ev){if(ev.key==="Enter"||ev.keyCode===13){ev.preventDefault();entrar();}});}
Array.prototype.forEach.call(document.querySelectorAll("[data-caja]"),function(fm){var id=fm.getAttribute("data-caja");
 puerta(fm.querySelector("input"),fm.querySelector(".entrar"),$("msj-"+id),function(pw){
  if(!LYSI.cajas||!LYSI.cajas[id])return Promise.reject(new Error("todavía no hay reportes publicados"));
  return abrir(LYSI.cajas[id],pw).then(function(h){ORIGEN=fm;verReporte(h,fm.getAttribute("data-nombre"),false);});});});
function cerrarTodo(){terminarImp();menuImp(false);cerrarZoom();cont.innerHTML="";$("tabs").innerHTML="";app.hidden=true;adm.hidden=true;acceso.hidden=false;ADM=null;RES=null;
 // al cerrar no queda ninguna contraseña ni el token escritos en la página
 ["cl-comb","cl-gas","cl-adm","gh-t"].forEach(function(k){var x=$(k);if(x)x.value="";});
 document.title=TITULO;window.scrollTo(0,0);var o=ORIGEN&&ORIGEN.querySelector(".entrar");ORIGEN=null;if(o)try{o.focus({preventScroll:true});}catch(e){}}
$("salir").addEventListener("click",function(){if(!$("previa").hidden){volverAdm();return;}cerrarTodo();});
window.addEventListener("resize",function(){medir();sombras();});

// ───────────── Imprimir o guardar en PDF ─────────────
// Solo cambia qué se muestra en el papel; al terminar, la pantalla queda como estaba.
var IMP=null;
function partesImp(ap){var ss=ap.querySelectorAll("section"),libre=false,i;
 // en Resultados, si la hoja ya abre con indicadores sueltos, el resumen son esos indicadores y sus notas
 if(ap.classList.contains("gst"))for(i=0;i<ap.children.length;i++)if(ap.children[i].classList.contains("kpis"))libre=true;
 return {ss:ss,libre:libre};}
function prepararImp(modo){terminarImp();cerrarZoom();var ap=cont.querySelector(".apartado:not([hidden])");if(!ap)return false;
 var p=partesImp(ap),oc=[],ds=[],i;
 if(modo==="resumen")for(i=0;i<p.ss.length;i++)if(p.libre||i>0){p.ss[i].classList.add("imp-o");oc.push(p.ss[i]);}
 if(modo==="todo")Array.prototype.forEach.call(ap.querySelectorAll("details:not([open])"),function(d){d.open=true;ds.push(d);});
 document.body.setAttribute("data-imp",modo);var h=ap.querySelector("h1"),hoy=new Date();
 var tit=$("donde").textContent+(h?" · "+h.textContent.trim():"")+(modo==="resumen"?" · resumen":"");$("imp-tit").textContent=tit;
 $("imp-fecha").textContent="Impreso el "+hoy.getDate()+" de "+MESES[hoy.getMonth()+1]+" de "+hoy.getFullYear();
 // pie en todas las hojas: qué reporte es y número de página (los navegadores que no lo soportan lo ignoran)
 var st=document.createElement("style");st.id="imp-pag";var f="font:8pt Barlow,Arial,sans-serif;color:#5A6055";
 st.textContent='@page{@bottom-left{content:"LYSI · '+tit.replace(/["\\\n\r]/g," ")+'";'+f+'}@bottom-right{content:"Página " counter(page) " de " counter(pages);'+f+'}}';
 document.head.appendChild(st);IMP={oc:oc,ds:ds,st:st};return true;}
function terminarImp(){if(!IMP)return;IMP.oc.forEach(function(s){s.classList.remove("imp-o");});IMP.ds.forEach(function(d){d.open=false;});if(IMP.st.parentNode)IMP.st.parentNode.removeChild(IMP.st);
 document.body.removeAttribute("data-imp");IMP=null;sombras();}
window.addEventListener("afterprint",terminarImp);
function menuImp(v){if(v){var ap=cont.querySelector(".apartado:not([hidden])"),r=document.querySelector('#imp-menu [data-imp="resumen"]');if(r)r.hidden=!ap||!partesImp(ap).ss.length;}
 $("imp-menu").hidden=!v;$("imp-btn").setAttribute("aria-expanded",v?"true":"false");}
$("imp-btn").addEventListener("click",function(ev){ev.stopPropagation();menuImp($("imp-menu").hidden);});
document.querySelector(".imp").addEventListener("focusout",function(ev){if(ev.relatedTarget&&!this.contains(ev.relatedTarget))menuImp(false);});
document.addEventListener("click",function(ev){var b=ev.target.closest&&ev.target.closest("[data-imp]");
 if(b&&b.id!=="imp-btn"&&b.tagName==="BUTTON"){menuImp(false);if(prepararImp(b.getAttribute("data-imp")))setTimeout(function(){window.print();},60);return;}
 if(!$("imp-menu").hidden&&!(ev.target.closest&&ev.target.closest(".imp")))menuImp(false);});
// Gráficos que vienen como imagen: un clic (o Enter) los abre a pantalla completa.
var ZO=null;
function cerrarZoom(){var z=$("zoom");if(!z)return;z.parentNode.removeChild(z);document.body.style.overflow="";var o=ZO;ZO=null;if(o)try{o.focus({preventScroll:true});}catch(e){}}
function abrirZoom(im){ZO=im;var z=document.createElement("div");z.id="zoom";z.setAttribute("role","dialog");z.setAttribute("aria-modal","true");z.setAttribute("aria-label",im.alt||"Gráfico ampliado");z.tabIndex=-1;
 var b=document.createElement("button");b.type="button";b.className="bt";b.textContent="Cerrar";var c=document.createElement("img");c.src=im.src;c.alt=im.alt;
 z.appendChild(b);z.appendChild(c);document.body.appendChild(z);document.body.style.overflow="hidden";b.focus();}
document.addEventListener("click",function(ev){if($("zoom")){cerrarZoom();return;}var im=ev.target.closest&&ev.target.closest(".gfig img");if(im)abrirZoom(im);});
document.addEventListener("keydown",function(ev){var z=$("zoom");
 if(ev.key==="Escape"){if(z){cerrarZoom();return;}if(!$("imp-menu").hidden){menuImp(false);$("imp-btn").focus();}return;}
 if(z){if(ev.key==="Tab"){ev.preventDefault();z.querySelector("button").focus();}return;}
 if((ev.key==="Enter"||ev.key===" ")&&ev.target&&ev.target.matches&&ev.target.matches(".gfig img")){ev.preventDefault();abrirZoom(ev.target);}});

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
function cargarPyodide(){if(PYO)return Promise.resolve(PYO);var base=window.LYSI_PYO||PYO_URL||LYSI.pyodide; // la dirección sale de la app, no de datos.json
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
    var dg=(RES.gastos&&RES.gastos.html)?RES.gastos.descripcion:(LYSI.info&&LYSI.info.gastos);if(cgx&&dg){nuevo.info.gastos=dg;var df=(RES.gastos&&RES.gastos.html)?RES.generado:(LYSI.info&&LYSI.info.gastos_fecha);if(df)nuevo.info.gastos_fecha=df;}
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
<link rel="manifest" href="manifest.webmanifest"><link rel="icon" type="image/png" sizes="192x192" href="icono-192.png"><link rel="apple-touch-icon" href="icono-180.png"><meta name="theme-color" content="#1A1A1A">
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='-60 -80 1080 1080'%3E%3Crect x='-60' y='-80' width='1080' height='1080' rx='190' fill='%23fff'/%3E%3Cpath fill='%231A1A1A' fill-rule='evenodd' d='M385 689C384 688 385 686 392 673C395 669 398 663 400 660C411 640 437 601 439 600C440 600 449 600 484 600C538 600 545 599 558 597C611 588 642 548 629 500C625 484 615 468 602 456C597 453 598 452 611 446C638 435 667 429 693 429C702 429 701 428 706 438C724 476 730 519 721 560C707 622 654 670 585 683C582 684 580 684 579 684C569 686 547 689 529 689C513 690 386 690 385 689ZM118 587C118 587 118 531 118 462C118 394 118 271 118 188C118 38 118 38 119 37C120 36 215 36 216 38C217 38 217 477 216 480C216 480 213 484 209 488C178 517 152 546 126 580C120 588 119 588 119 588C118 588 118 588 118 587ZM520 410C512 405 512 405 528 400C544 394 555 391 573 388C586 385 592 384 604 383C615 382 616 382 617 382C617 382 617 383 616 383C615 383 606 385 603 386C580 390 561 396 546 402C544 403 541 404 538 405C535 406 531 408 529 409C524 411 524 411 520 410ZM406 356C384 343 372 335 356 320C333 298 313 267 306 238C284 151 336 68 427 45C442 41 453 39 472 37C484 36 691 36 692 38C693 39 693 126 692 127C691 128 691 128 587 128C472 128 474 128 462 130C412 138 386 175 400 216C406 235 422 252 447 266C449 267 453 269 454 270C457 271 473 280 489 288C494 290 508 298 520 304C568 328 564 325 549 326C544 326 538 327 536 327C533 328 528 328 525 329C493 332 451 343 416 356C411 358 410 358 406 356Z'/%3E%3Cpath fill='%2394C337' fill-rule='evenodd' d='M291 897C289 896 283 886 278 880C277 878 274 874 273 872C271 870 269 867 269 866C268 865 266 863 266 862C264 860 263 858 262 856C260 854 257 850 255 846C252 843 250 839 250 838C249 837 248 836 247 835C247 834 244 831 242 827C238 821 235 817 231 811C230 810 227 806 225 802C222 799 220 795 219 793C216 790 216 789 217 786C218 784 219 780 220 778C220 777 221 775 222 773C222 772 223 770 224 769C224 768 225 766 225 765C226 764 226 763 226 763C226 763 227 761 228 759C228 757 230 754 230 753C231 751 232 748 234 746C240 732 244 724 246 719C250 711 254 704 256 701C257 699 259 695 260 692C262 688 264 686 264 685C264 684 266 682 267 680C268 678 270 675 271 673C272 671 274 668 275 666C276 664 277 663 277 662C278 662 278 660 279 658C280 657 282 653 284 650C286 647 289 643 289 642C293 637 309 613 314 605C318 600 333 580 337 575C338 573 340 571 341 570C342 568 344 566 345 564C347 563 348 561 349 560C350 559 352 557 354 554C356 552 358 549 359 548C361 546 366 541 370 536C372 535 375 531 378 528C392 513 406 499 416 491C418 489 421 486 422 485C423 484 426 482 428 480C429 479 433 476 436 474C450 463 462 454 475 446C477 444 480 442 482 441C483 440 486 439 487 438C488 438 491 436 493 435C497 433 500 431 508 427C511 425 527 417 530 416C531 415 534 414 537 413C540 412 543 410 544 410C545 409 548 408 550 408C552 407 554 406 556 406C557 405 559 404 561 404C562 403 565 402 566 402C568 401 570 401 572 400C573 400 576 399 576 399C580 398 588 395 594 394C596 394 598 393 600 393C601 393 604 392 606 392C609 391 611 391 612 390C613 390 615 390 616 390C618 390 626 389 628 389C635 387 678 387 686 389C687 389 692 390 695 390C696 390 698 390 700 391C702 391 705 392 707 392C710 393 715 394 719 394C721 395 727 396 728 397C728 397 729 397 730 398C732 398 734 399 737 400C739 400 742 401 744 402C746 402 748 403 750 404C752 405 755 406 757 407C764 410 780 417 785 420C786 421 789 422 791 423C796 426 811 436 817 440C819 442 822 444 824 445C826 447 830 450 838 458C849 467 868 486 875 494C876 496 878 498 879 499C882 503 888 510 890 511C890 512 892 514 893 516C894 517 896 520 897 522C899 523 900 526 901 527C903 529 908 536 912 542C913 544 915 547 916 548C918 551 919 553 919 554C919 555 914 550 910 545C909 543 906 540 901 534C888 517 869 498 852 483C850 482 848 480 847 480C847 479 845 478 843 476C841 475 838 472 835 470C833 469 829 466 828 465C824 462 818 459 808 453C800 448 787 441 784 440C783 440 782 440 781 439C780 439 779 438 778 438C777 438 775 437 774 436C772 436 770 435 768 434C767 434 764 433 762 432C754 430 745 427 740 426C739 426 736 426 735 425C733 425 730 424 724 424C723 424 721 423 719 423C711 421 681 422 672 423C670 423 667 424 665 424C662 424 659 425 658 425C656 426 654 426 652 426C651 427 649 427 648 427C648 428 646 428 644 428C643 428 640 429 637 430C635 431 632 432 631 432C629 432 628 433 627 433C626 434 623 435 621 436C618 436 615 438 614 438C612 439 610 440 608 441C597 445 576 456 563 465C548 475 544 478 532 488C531 489 528 491 527 492C515 502 493 524 482 536C480 539 476 542 475 544C474 545 471 548 469 551C467 553 464 556 463 558C461 560 458 564 456 566C455 568 452 571 451 572C447 578 441 586 438 589C437 591 436 593 435 594C434 595 431 600 421 614C416 622 414 625 410 630C410 631 407 635 406 638C404 640 402 643 402 643C401 645 395 655 393 658C391 661 390 664 388 668C385 673 383 677 381 680C380 682 377 686 376 690C374 693 372 696 371 697C368 703 344 750 344 752C344 752 342 756 340 760C338 765 336 769 336 770C336 770 335 772 334 775C333 777 332 780 331 782C331 783 330 784 329 786C329 787 328 788 328 789C328 790 327 792 326 794C325 796 324 798 324 799C324 799 324 800 323 801C323 802 322 804 322 804C322 805 321 807 320 809C320 811 318 814 317 817C316 820 315 824 314 825C314 827 313 830 312 831C312 832 311 834 311 834C311 835 310 836 310 836C310 837 310 838 310 839C308 844 305 854 304 857C304 858 303 860 303 861C303 861 302 863 302 865C301 868 298 879 297 883C297 884 297 886 296 887C296 888 296 890 296 891C295 893 295 894 294 895C294 898 292 899 291 897ZM177 736C177 735 175 733 174 730C172 728 170 726 170 725C168 721 163 714 162 712C161 711 157 705 152 698C147 691 142 682 139 679C137 676 134 671 132 668C128 663 126 660 123 654C120 650 107 631 104 627C102 623 101 625 116 604C118 601 122 596 123 594C125 591 128 588 129 586C131 584 133 582 134 580C137 576 139 573 142 570C143 568 146 565 147 563C149 561 152 558 153 556C155 554 158 551 160 548C162 545 164 543 164 543C164 543 166 542 168 540C180 525 204 501 219 487C230 477 232 476 234 473C236 472 238 470 240 469C242 467 245 465 247 463C249 461 253 458 256 456C258 454 261 451 262 450C263 450 267 447 271 444C275 441 280 437 283 435C285 434 288 431 290 430C294 427 315 413 321 410C323 409 326 406 329 405C332 404 335 402 336 401C337 400 340 398 343 397C347 394 376 380 382 377C384 376 387 375 389 374C392 373 394 372 395 372C396 371 397 370 399 370C404 368 407 366 412 365C414 364 418 362 421 361C423 360 427 359 429 358C431 358 435 356 437 356C439 355 442 354 443 354C444 354 446 353 447 353C449 352 455 350 456 350C457 350 459 349 462 348C464 348 467 347 469 346C476 345 480 344 483 343C485 342 487 342 488 342C488 342 490 342 492 341C497 340 504 338 508 338C510 338 513 337 514 337C516 337 518 336 520 336C522 336 525 335 527 335C529 335 533 334 536 334C540 334 544 333 545 333C554 332 554 332 584 332C609 332 613 332 615 332C619 333 620 333 627 334C630 334 635 335 636 335C638 335 641 336 643 336C645 336 647 336 648 337C649 337 651 338 653 338C655 338 657 338 659 339C660 339 663 340 664 340C666 340 668 341 670 341C671 341 674 342 676 343C679 343 682 344 683 344C684 345 687 345 688 346C691 346 696 348 699 349C700 350 704 351 707 352C713 354 722 357 732 361C735 362 738 364 738 364C742 365 773 382 776 384C777 385 778 386 778 386C782 388 801 401 806 405C807 406 809 408 810 408C812 409 814 411 815 412C816 413 818 415 820 416C821 417 824 420 826 422C828 424 831 427 833 428C835 430 848 443 852 448C854 449 856 452 857 453C860 456 864 461 866 464C867 464 869 467 871 469C874 474 881 483 884 487C885 489 886 491 887 492C888 492 889 495 890 496C891 498 893 502 895 504C899 510 903 517 905 522C906 524 908 526 908 527C910 529 914 537 914 537C914 539 912 538 910 535C908 531 903 522 902 521C902 520 901 519 900 518C899 517 897 513 894 510C892 507 890 503 889 502C888 502 887 499 885 497C884 496 882 493 880 491C879 490 876 486 874 484C873 482 869 478 867 476C861 469 847 455 842 450C838 446 834 443 831 441C830 440 828 438 826 437C824 435 818 430 811 425C805 421 793 413 787 410C772 402 771 401 769 400C768 400 766 399 764 398C762 397 760 396 759 396C758 395 755 394 753 394C746 391 735 387 732 386C730 386 729 385 728 385C728 385 727 385 725 384C724 384 722 384 721 383C720 383 718 382 717 382C716 382 714 381 713 381C712 381 710 380 708 380C707 380 705 380 704 379C703 379 700 378 699 378C696 378 694 378 689 377C688 377 684 376 682 376C679 376 675 375 673 375C659 374 618 374 610 375C609 376 606 376 604 376C600 376 596 377 592 378C590 378 588 378 588 378C586 378 580 379 568 382C564 382 561 383 546 387C543 388 537 390 526 394C520 396 512 398 510 399C508 400 507 400 507 400C507 400 505 401 503 402C501 403 499 404 498 404C497 404 495 405 494 406C492 407 490 408 489 408C488 408 483 411 478 413C473 415 468 417 468 417C468 417 444 430 441 432C440 432 439 433 437 434C435 435 416 446 412 449C411 450 410 451 409 451C406 453 405 454 400 458C397 460 392 463 390 464C387 466 384 468 382 470C381 471 378 473 376 474C374 476 371 478 369 480C368 481 365 483 364 484C362 485 359 488 357 490C355 492 352 494 352 494C350 495 349 497 340 504C327 516 302 541 294 550C293 552 291 554 289 556C288 558 285 561 284 562C283 564 281 566 280 566C276 571 275 573 273 575C272 577 270 579 269 581C262 590 251 604 241 620C237 625 234 631 232 632C231 634 230 636 229 637C226 643 221 651 216 660C207 676 206 680 200 693C196 701 195 703 193 707C193 708 192 710 191 711C191 712 190 715 189 717C186 726 181 736 181 737C180 738 178 737 177 736Z'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700&family=Jost:wght@400;500;600&display=swap" rel="stylesheet">
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
