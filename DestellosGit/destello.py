#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DESTELLO · lector de linternas con OpenCV
=========================================

Lee las fotos (o un vídeo, o la cámara en directo) de las 4 linternas,
reconoce el color y la forma de cada luz, transcribe el programa a código C
y lo ejecuta para mostrar la salida.

Uso rápido:
    python destello.py fotos/ejemplo1_hola              # carpeta de fotos
    python destello.py grabacion.mp4                     # un vídeo
    python destello.py --camara mis_fotos                # hacer las fotos con la webcam (ESPACIO)
    python destello.py --directo                         # webcam en automático: C en directo

Opciones útiles:
    --revisar      guarda copias de las fotos con lo que ha detectado dibujado encima
    --salida X.c   nombre del archivo C que se genera (por defecto: programa.c)

Colores y formas (la ruleta):
    rojo  = círculo   = 0
    verde = cuadrado  = 1
    azul  = triángulo = 2
"""

import argparse
import os
import re
import sys

try:
    import cv2
    import numpy as np
except ImportError:
    print("Falta OpenCV. Instálalo con:  pip install opencv-python numpy")
    sys.exit(1)

# La consola de Windows a veces no muestra ● ■ ▲ si no se fuerza UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# =====================================================================
# 1. EL LENGUAJE
# =====================================================================

SIMBOLO = "●■▲"
COLOR = ["rojo", "verde", "azul"]
FORMA = ["círculo", "cuadrado", "triángulo"]
TIPO = ["dato", "operación", "control"]
ABC = "ABCDEFGHIJKLMNÑOPQRSTUVWXYZ"          # 27 letras: A = 0 … Z = 26
# ASCII extendido 128–255 (la tabla de clase, página de códigos 850)
EXT = bytes(range(128, 256)).decode("cp850")

# Linterna 1 verde = operación; las otras tres dicen cuál
OPERACIONES = {
    (0, 0, 0): "IMPRIMIR", (1, 1, 1): "LETRA",   (2, 2, 2): "ESPACIO",
    (0, 0, 1): "SUMAR",    (0, 0, 2): "RESTAR",  (0, 1, 0): "MULTIPLICAR",
    (1, 0, 0): "DUPLICAR", (1, 0, 1): "CAMBIAR", (2, 0, 0): "BORRAR",
    (1, 2, 1): "ASCII",    (0, 2, 0): "RESTO",   (0, 1, 2): "ROTAR",
    (1, 1, 2): "PALABRA",  (1, 1, 0): "UNIR",    (1, 0, 2): "ENCIMA",
}
# Linterna 1 azul = control
CONTROL = {
    (0, 0, 0): "SI", (1, 1, 1): "SI NO", (2, 2, 2): "FIN SI",
    (0, 1, 2): "MIENTRAS", (2, 1, 0): "FIN MIENTRAS", (2, 0, 2): "PARAR",
}


def valor(d):
    """Linternas 2, 3 y 4 en base 3: ×9, ×3, ×1."""
    return d[1] * 9 + d[2] * 3 + d[3]


def nombre(d):
    """Nombre de la instrucción de un destello (o None si no significa nada)."""
    if d[0] == 0:
        return "DATO"
    tabla = OPERACIONES if d[0] == 1 else CONTROL
    return tabla.get(tuple(d[1:]))


def simbolos(d):
    return SIMBOLO[d[0]] + " " + "".join(SIMBOLO[c] for c in d[1:])


def etiqueta(d):
    n = nombre(d)
    if n == "DATO":
        v = valor(d)
        return f"dato {v} (letra {ABC[v]})"
    return n or "??? no significa nada"


class ErrorDestello(Exception):
    pass


def emparejar(prog):
    """Busca qué SI / SI NO / FIN SI y MIENTRAS / FIN MIENTRAS van juntos."""
    pareja, si, mientras = {}, [], []
    for i, d in enumerate(prog):
        n = nombre(d)
        if n is None:
            raise ErrorDestello(f"Destello {i+1} ({simbolos(d)}): no significa nada.")
        if n == "SI":
            si.append([i, None])
        elif n == "SI NO":
            if not si:
                raise ErrorDestello(f"Destello {i+1}: SI NO sin un SI antes.")
            si[-1][1] = i
        elif n == "FIN SI":
            if not si:
                raise ErrorDestello(f"Destello {i+1}: FIN SI sin un SI antes.")
            ini, sino = si.pop()
            pareja[ini] = (sino, i)
            if sino is not None:
                pareja[sino] = (None, i)
        elif n == "MIENTRAS":
            mientras.append(i)
        elif n == "FIN MIENTRAS":
            if not mientras:
                raise ErrorDestello(f"Destello {i+1}: FIN MIENTRAS sin un MIENTRAS antes.")
            ini = mientras.pop()
            pareja[ini] = i
            pareja[i] = ini
    if si:
        raise ErrorDestello(f"Destello {si[0][0]+1}: este SI nunca se cierra (falta FIN SI).")
    if mientras:
        raise ErrorDestello(f"Destello {mientras[0]+1}: este MIENTRAS nunca se cierra (falta FIN MIENTRAS).")
    return pareja


class Salida:
    """Escribe la salida con las mismas reglas de espacios que la web."""
    def __init__(self):
        self.texto, self.ultimo = "", None   # ultimo: None, 'num', 'letra', 'esp'

    def numero(self, n):
        if self.ultimo in ("num", "letra"):
            self.texto += " "
        self.texto += str(n); self.ultimo = "num"

    def letras(self, s):
        if self.ultimo == "num":
            self.texto += " "
        self.texto += s; self.ultimo = "letra"

    def caracter(self, s):
        self.texto += s; self.ultimo = "esp" if s == " " else "letra"

    def espacio(self):
        self.texto += " "; self.ultimo = "esp"


def ejecutar(prog, max_pasos=10000):
    """Intérprete de Destello. Devuelve el texto que escribe el programa."""
    pareja = emparejar(prog)
    pila, out = [], Salida()

    def sacar(cuantos, quien):
        if len(pila) < cuantos:
            raise ErrorDestello(f"Destello {pc+1}: {quien} necesita {cuantos} número(s) en la pila.")
        r = pila[-cuantos:]
        del pila[-cuantos:]
        return r

    pc, pasos = 0, 0
    while pc < len(prog):
        pasos += 1
        if pasos > max_pasos:
            raise ErrorDestello("Demasiados pasos: parece un bucle que no termina.")
        d, n, sig = prog[pc], nombre(prog[pc]), pc + 1
        if n == "DATO":
            pila.append(valor(d))
        elif n == "IMPRIMIR":
            if not pila: raise ErrorDestello(f"Destello {pc+1}: IMPRIMIR con la pila vacía.")
            out.numero(pila[-1])
        elif n == "LETRA":
            (v,) = sacar(1, n)
            if not 0 <= v <= 26: raise ErrorDestello(f"Destello {pc+1}: {v} no es una letra (0 a 26).")
            out.letras(ABC[v])
        elif n == "ESPACIO":
            out.espacio()
        elif n == "PALABRA":
            if not pila: raise ErrorDestello(f"Destello {pc+1}: PALABRA con la pila vacía.")
            if any(not 0 <= v <= 26 for v in pila): raise ErrorDestello(f"Destello {pc+1}: hay números que no son letras.")
            out.letras("".join(ABC[v] for v in pila)); pila.clear()
        elif n in ("SUMAR", "RESTAR", "MULTIPLICAR", "RESTO", "UNIR", "ASCII"):
            a, b = sacar(2, n)
            if n == "SUMAR": pila.append(a + b)
            elif n == "RESTAR": pila.append(a - b)
            elif n == "MULTIPLICAR": pila.append(a * b)
            elif n == "UNIR": pila.append(a * 10 + b)
            elif n == "RESTO":
                if b == 0: raise ErrorDestello(f"Destello {pc+1}: RESTO entre 0.")
                pila.append(a % b)
            else:
                v = a * 27 + b
                if not 0 <= v <= 255: raise ErrorDestello(f"Destello {pc+1}: {v} no es un código ASCII (0 a 255).")
                out.caracter(chr(v) if v < 128 else EXT[v - 128])
        elif n == "DUPLICAR":
            if not pila: raise ErrorDestello(f"Destello {pc+1}: DUPLICAR con la pila vacía.")
            pila.append(pila[-1])
        elif n == "CAMBIAR":
            a, b = sacar(2, n); pila += [b, a]
        elif n == "BORRAR":
            sacar(1, n)
        elif n == "ROTAR":
            a, b, c = sacar(3, n); pila += [b, c, a]
        elif n == "ENCIMA":
            if len(pila) < 2: raise ErrorDestello(f"Destello {pc+1}: ENCIMA necesita 2 números.")
            pila.append(pila[-2])
        elif n == "SI":
            (v,) = sacar(1, n)
            if v == 0:
                sino, fin = pareja[pc]
                sig = (sino if sino is not None else fin) + 1
        elif n == "SI NO":
            sig = pareja[pc][1] + 1
        elif n == "MIENTRAS":
            if not pila or pila[-1] == 0:
                sig = pareja[pc] + 1
        elif n == "FIN MIENTRAS":
            sig = pareja[pc]
        elif n == "PARAR":
            break
        pc = sig
    return out.texto


# =====================================================================
# 2. TRANSCRIPCIÓN A C
# =====================================================================

CABECERA_C = r'''/* Programa transcrito automáticamente desde los destellos de las linternas.
   Cada línea es un destello: ● rojo/círculo · ■ verde/cuadrado · ▲ azul/triángulo
   Compilar:  gcc programa.c -o programa      Ejecutar:  ./programa          */
#include <stdio.h>
#include <stdlib.h>

/* ---- La pila de Destello ---- */
static int pila[1000];
static int cima_pila = 0;
static int ultimo = 0;   /* 0 = nada o espacio, 1 = número, 2 = letra */

void apilar(int v) { pila[cima_pila++] = v; }
int desapilar(void) {
    if (cima_pila == 0) { fprintf(stderr, "\nError: la pila está vacía\n"); exit(1); }
    return pila[--cima_pila];
}
int cima(void) { return cima_pila > 0 ? pila[cima_pila - 1] : 0; }

static const char *ABC[27] = {"A","B","C","D","E","F","G","H","I","J","K","L","M","N",
                              "Ñ","O","P","Q","R","S","T","U","V","W","X","Y","Z"};

void imprimir(void) { if (ultimo) printf(" "); printf("%d", cima()); ultimo = 1; }
void letra(void)    { int v = desapilar(); if (ultimo == 1) printf(" "); printf("%s", ABC[v]); ultimo = 2; }
void espacio(void)  { printf(" "); ultimo = 0; }
void palabra(void) {
    if (ultimo == 1) printf(" ");
    for (int i = 0; i < cima_pila; i++) printf("%s", ABC[pila[i]]);
    cima_pila = 0; ultimo = 2;
}
'''

ASCII_C = '''
static const char *EXT[128] = {%s};
void ascii(int v) {
    if (v < 128) putchar(v); else printf("%%s", EXT[v - 128]);
    ultimo = (v == ' ') ? 0 : 2;
}
'''


def codigo_c_de(n, v=None):
    """Línea de C para cada instrucción. Devuelve (línea, cambio de sangría antes, después)."""
    binaria = "{{ int b = desapilar(), a = desapilar(); {} }}"
    tabla = {
        "DATO": (f"apilar({v});", 0, 0),
        "IMPRIMIR": ("imprimir();", 0, 0),
        "LETRA": ("letra();", 0, 0),
        "ESPACIO": ("espacio();", 0, 0),
        "PALABRA": ("palabra();", 0, 0),
        "SUMAR": (binaria.format("apilar(a + b);"), 0, 0),
        "RESTAR": (binaria.format("apilar(a - b);"), 0, 0),
        "MULTIPLICAR": (binaria.format("apilar(a * b);"), 0, 0),
        "RESTO": (binaria.format("apilar(a % b);"), 0, 0),
        "UNIR": (binaria.format("apilar(a * 10 + b);"), 0, 0),
        "ASCII": (binaria.format("ascii(a * 27 + b);"), 0, 0),
        "DUPLICAR": ("apilar(cima());", 0, 0),
        "CAMBIAR": (binaria.format("apilar(b); apilar(a);"), 0, 0),
        "BORRAR": ("desapilar();", 0, 0),
        "ROTAR": ("{ int c = desapilar(), b = desapilar(), a = desapilar(); apilar(b); apilar(c); apilar(a); }", 0, 0),
        "ENCIMA": ("apilar(pila[cima_pila - 2]);", 0, 0),
        "SI": ("if (desapilar() != 0) {", 0, +1),
        "SI NO": ("} else {", -1, +1),
        "FIN SI": ("}", -1, 0),
        "MIENTRAS": ("while (cima() != 0) {", 0, +1),
        "FIN MIENTRAS": ("}", -1, 0),
        "PARAR": ("goto fin;", 0, 0),
    }
    return tabla[n]


def transcribir_a_c(prog):
    emparejar(prog)  # comprueba que esté bien formado
    usa_ascii = any(nombre(d) == "ASCII" for d in prog)
    lineas = [CABECERA_C]
    if usa_ascii:
        lineas.append(ASCII_C % ", ".join('"%s"' % ("\\\\" if c == "\\" else c) for c in EXT))
    lineas.append("int main(void) {")
    sangria = 1
    ancho = 44
    for i, d in enumerate(prog):
        n = nombre(d)
        linea, antes, despues = codigo_c_de(n, valor(d) if n == "DATO" else None)
        sangria += antes
        txt = "    " * sangria + linea
        comentario = f"// {i+1:>2}  {simbolos(d)}  {etiqueta(d)}"
        lineas.append(txt.ljust(ancho) + ("" if len(txt) < ancho else "  ") + comentario)
        sangria += despues
    if any(nombre(d) == "PARAR" for d in prog):
        lineas.append("fin:")
    lineas.append('    printf("\\n");')
    lineas.append("    return 0;")
    lineas.append("}")
    return "\n".join(lineas) + "\n"


# =====================================================================
# 3. VISIÓN: leer las 4 linternas de una foto
# =====================================================================

def clasificar_forma(contorno):
    """Compara la luz con un círculo, un cuadrado y un triángulo: gana el que mejor encaja."""
    area = cv2.contourArea(contorno)
    if area <= 0:
        return None, 0
    (_, _), r = cv2.minEnclosingCircle(contorno)
    circulo = area / (np.pi * r * r)
    (_, (w, h), _) = cv2.minAreaRect(contorno)
    cuadrado = area / (w * h) if w * h > 0 else 0
    cuadrado *= min(w, h) / max(w, h) if max(w, h) > 0 else 0   # un rectángulo muy alargado no es un cuadrado
    pts = contorno.reshape(-1, 1, 2).astype(np.float32)
    area_tri, _ = cv2.minEnclosingTriangle(pts)
    triangulo = area / area_tri if area_tri > 0 else 0
    notas = [circulo, cuadrado, triangulo]
    mejor = int(np.argmax(notas))
    return mejor, notas[mejor]


def clasificar_color(hsv, mascara):
    """Cuenta los píxeles de cada color dentro de la luz (solo los que tienen color de verdad)."""
    H, S, V = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    sel = (mascara > 0) & (S > 70) & (V > 50)
    h = H[sel]
    if h.size < 15:
        return None, 0
    rojo = np.count_nonzero((h <= 15) | (h >= 160))
    verde = np.count_nonzero((h >= 35) & (h <= 88))
    azul = np.count_nonzero((h >= 90) & (h <= 135))
    cuentas = [rojo, verde, azul]
    mejor = int(np.argmax(cuentas))
    return mejor, cuentas[mejor] / max(1, sum(cuentas))


def buscar_luces(img):
    """Devuelve la máscara de zonas brillantes y sus contornos (de mayor a menor)."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    V = cv2.GaussianBlur(hsv[..., 2], (5, 5), 0)
    umbral, _ = cv2.threshold(V, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    umbral = max(umbral, 70)
    mascara = (V > umbral).astype(np.uint8) * 255
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, k)
    contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    minimo = 0.0008 * img.shape[0] * img.shape[1]
    contornos = [c for c in contornos if cv2.contourArea(c) >= minimo]
    contornos.sort(key=cv2.contourArea, reverse=True)
    return hsv, contornos


def leer_destello(img, estricto=False):
    """Lee una foto. Devuelve (destello, detalles, avisos). destello = None si es una pausa (oscuridad)."""
    escala = 1000 / max(img.shape[:2])
    if escala < 1:
        img = cv2.resize(img, None, fx=escala, fy=escala, interpolation=cv2.INTER_AREA)
    hsv, contornos = buscar_luces(img)
    if not contornos:
        return None, [], img, []
    avisos = []
    if len(contornos) < 4:
        raise ErrorDestello(f"Solo se ven {len(contornos)} luces (hacen falta 4).")
    if len(contornos) > 4:
        avisos.append(f"Se ven {len(contornos)} manchas de luz; uso las 4 más grandes.")
    contornos = contornos[:4]
    # De izquierda a derecha
    contornos.sort(key=lambda c: cv2.boundingRect(c)[0] + cv2.boundingRect(c)[2] / 2)

    destello, detalles = [], []
    for i, c in enumerate(contornos):
        x, y, w, h = cv2.boundingRect(c)
        m = 8
        x0, y0 = max(0, x - m), max(0, y - m)
        x1, y1 = min(img.shape[1], x + w + m), min(img.shape[0], y + h + m)
        trozo_hsv = hsv[y0:y1, x0:x1]
        # Dentro de cada luz, separamos el núcleo (la figura) del halo con un umbral propio
        V = trozo_hsv[..., 2]
        _, nucleo = cv2.threshold(V, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        cs, _ = cv2.findContours(nucleo, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        forma_c = max(cs, key=cv2.contourArea) if cs else c - [x0, y0]
        forma, nota_forma = clasificar_forma(forma_c)
        zona = np.zeros(V.shape, np.uint8)
        cv2.drawContours(zona, [c - [x0, y0]], -1, 255, -1)
        color, nota_color = clasificar_color(trozo_hsv, zona)

        if estricto and (color is None or forma is None or color != forma):
            raise ErrorDestello("Hay luces que no parecen de las linternas (sin color o con color y forma distintos).")
        if color is None and forma is None:
            raise ErrorDestello(f"Linterna {i+1}: no reconozco ni el color ni la forma.")
        if color is None:
            elegido = forma
            avisos.append(f"Linterna {i+1}: la luz sale muy blanca; me fío de la forma ({FORMA[forma]}).")
        elif forma is None or color == forma:
            elegido = color
        else:
            elegido = forma
            avisos.append(f"Linterna {i+1}: el color parece {COLOR[color]} pero la forma es {FORMA[forma]}. "
                          f"Me fío de la forma. Si no es correcto, repetid esta foto.")
        destello.append(elegido)
        detalles.append({"contorno": c, "forma": forma, "color": color, "elegido": elegido})
    return destello, detalles, img, avisos


def dibujar_revision(img, detalles, destello, titulo):
    out = img.copy()
    pinta = [(60, 60, 255), (80, 220, 80), (255, 140, 60)]
    for i, d in enumerate(detalles):
        x, y, w, h = cv2.boundingRect(d["contorno"])
        cv2.drawContours(out, [d["contorno"]], -1, (255, 255, 255), 2)
        txt = f"{i+1}: {['rojo','verde','azul'][d['elegido']]} {['circulo','cuadrado','triangulo'][d['elegido']]}"
        cv2.putText(out, txt, (x, max(18, y - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, pinta[d["elegido"]], 2)
    if destello:
        n = nombre(destello) or "???"
        if n == "DATO":
            n = f"DATO {valor(destello)}"
        cv2.putText(out, f"{titulo}  ->  {n}", (12, out.shape[0] - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    return out


# =====================================================================
# 4. FUENTES: carpeta de fotos, vídeo o cámara
# =====================================================================

EXT_FOTO = (".jpg", ".jpeg", ".png", ".bmp", ".webp")
EXT_VIDEO = (".mp4", ".mov", ".avi", ".mkv", ".m4v", ".3gp")


def orden_natural(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def fotos_de_carpeta(carpeta):
    nombres = sorted((f for f in os.listdir(carpeta) if f.lower().endswith(EXT_FOTO)), key=orden_natural)
    if not nombres:
        raise ErrorDestello(f"No hay fotos (.jpg, .png…) en la carpeta {carpeta}")
    for n in nombres:
        img = cv2.imread(os.path.join(carpeta, n))
        if img is None:
            print(f"  ! No puedo abrir {n}, la salto.")
            continue
        yield n, img


def fotos_de_video(ruta, min_fotogramas=3):
    """Separa el vídeo en destellos: tramos con luz separados por oscuridad. Usa el fotograma del medio."""
    cap = cv2.VideoCapture(ruta)
    if not cap.isOpened():
        raise ErrorDestello(f"No puedo abrir el vídeo {ruta}")
    tramo, num, n_destello = [], 0, 0

    def hay_luz(frame):
        peque = cv2.resize(frame, (320, int(320 * frame.shape[0] / frame.shape[1])))
        _, cs = buscar_luces(peque)
        return len(cs) >= 4

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        num += 1
        if hay_luz(frame):
            tramo.append((num, frame))
        elif tramo:
            if len(tramo) >= min_fotogramas:
                n_destello += 1
                f_num, f = tramo[len(tramo) // 2]
                yield f"vídeo, destello {n_destello} (fotograma {f_num})", f
            tramo = []
    if len(tramo) >= min_fotogramas:
        n_destello += 1
        f_num, f = tramo[len(tramo) // 2]
        yield f"vídeo, destello {n_destello} (fotograma {f_num})", f
    cap.release()


def hacer_fotos_con_camara(carpeta, indice_camara=0):
    """Vista previa de la webcam. ESPACIO = guardar foto · Q = terminar."""
    os.makedirs(carpeta, exist_ok=True)
    cap = cv2.VideoCapture(indice_camara)
    if not cap.isOpened():
        raise ErrorDestello("No encuentro ninguna cámara. Prueba con --indice-camara 1")
    n = len([f for f in os.listdir(carpeta) if f.lower().endswith(EXT_FOTO)])
    print("Cámara abierta. ESPACIO = hacer foto · Q = terminar")
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        vista = frame.copy()
        try:
            d, det, peque, _ = leer_destello(frame)
            if d:
                vista = dibujar_revision(peque, det, d, "en directo")
        except ErrorDestello as e:
            cv2.putText(vista, str(e)[:60], (12, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(vista, f"Fotos: {n}   ESPACIO = foto   Q = terminar", (12, vista.shape[0] - 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.imshow("Destello - camara", vista)
        tecla = cv2.waitKey(1) & 0xFF
        if tecla == ord(" "):
            n += 1
            ruta = os.path.join(carpeta, f"{n:02d}.jpg")
            cv2.imwrite(ruta, frame)
            print(f"  Guardada {ruta}")
        elif tecla in (ord("q"), 27):
            break
    cap.release()
    cv2.destroyAllWindows()



def _ascii(t):
    """cv2.putText no sabe dibujar tildes ni ● ■ ▲: los quitamos para la ventana."""
    import unicodedata
    t = t.replace("●", "R").replace("■", "V").replace("▲", "A").replace("Ñ", "NY")
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()


def _panel_codigo(prog, alto, ancho=560):
    """Panel lateral con el C que se va escribiendo y la salida en directo."""
    panel = np.full((alto, ancho, 3), (30, 22, 20), np.uint8)
    cv2.putText(panel, "CODIGO C EN DIRECTO", (16, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (140, 210, 255), 2)
    lineas, sangria = [], 1
    for i, d in enumerate(prog):
        n = nombre(d)
        if n is None:
            continue
        linea, antes, despues = codigo_c_de(n, valor(d) if n == "DATO" else None)
        sangria = max(0, sangria + antes)
        lineas.append(("  " * sangria + linea, f"// {i+1} {etiqueta(d)}"))
        sangria += despues
    visibles = lineas[-((alto - 170) // 26):]
    y = 72
    for codigo, com in visibles:
        cv2.putText(panel, _ascii(codigo)[:34], (16, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (235, 235, 235), 1)
        cv2.putText(panel, _ascii(com)[:24], (330, y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (150, 150, 150), 1)
        y += 26
    try:
        salida = ejecutar(prog) if prog else ""
    except ErrorDestello:
        salida = "(falta cerrar el bloque)"
    cv2.line(panel, (16, alto - 90), (ancho - 16, alto - 90), (90, 90, 90), 1)
    cv2.putText(panel, "SALIDA", (16, alto - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (140, 210, 255), 1)
    cv2.putText(panel, _ascii(salida)[:30], (16, alto - 24), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (110, 210, 255), 2)
    return panel


def en_directo(fuente=0, carpeta="grabacion_directo", estables=4, mostrar=True):
    """
    Modo automático: la cámara mira la pared y cada destello se apunta solo.
    - Un destello cuenta cuando las 4 luces se leen IGUAL durante `estables` fotogramas seguidos.
    - Después hay que tapar las linternas (oscuridad) para que acepte el siguiente.
    - Q o ESC para terminar. Con un vídeo, termina al acabar el vídeo.
    Guarda la foto de cada destello en `carpeta`.
    """
    cap = cv2.VideoCapture(fuente)
    if not cap.isOpened():
        raise ErrorDestello("No encuentro la cámara (prueba --indice-camara 1) o no puedo abrir el vídeo.")
    os.makedirs(carpeta, exist_ok=True)
    prog, armado, ultimo, cuenta, oscuros = [], True, None, 0, 0
    print("\nMODO DIRECTO: mostrad cada destello y tapad las linternas entre uno y otro. Q = terminar.\n")
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        try:
            d, det, peque, _ = leer_destello(frame, estricto=True)
            problema = None
            if d is not None and nombre(d) is None:
                problema = f"{simbolos(d)} no significa nada"
                d = "?"
        except ErrorDestello as e:
            d, det, peque, problema = "?", [], cv2.resize(frame, None, fx=1000 / max(frame.shape[:2]), fy=1000 / max(frame.shape[:2])) if max(frame.shape[:2]) > 1000 else frame, str(e)

        if d is None:                        # oscuridad: listo para el siguiente
            oscuros += 1
            if oscuros >= 2:
                armado, ultimo, cuenta = True, None, 0
        elif d != "?":
            oscuros = 0
            if armado:
                cuenta = cuenta + 1 if d == ultimo else 1
                ultimo = d
                if cuenta >= estables:
                    prog.append(d)
                    armado = False
                    cv2.imwrite(os.path.join(carpeta, f"{len(prog):02d}.jpg"), frame)
                    print(f"  {len(prog):>2}. {simbolos(d)}   {etiqueta(d)}")
        else:
            oscuros = 0

        if mostrar:
            vista = dibujar_revision(peque, det, d, "en directo") if det else peque.copy()
            estado = ("LISTO: mostrad el destello %d" % (len(prog) + 1)) if armado else "APUNTADO. Tapad las linternas"
            color = (120, 230, 120) if armado else (90, 200, 255)
            if problema:
                estado, color = _ascii(problema), (80, 80, 255)
            cv2.rectangle(vista, (0, 0), (vista.shape[1], 50), (0, 0, 0), -1)
            cv2.putText(vista, estado[:70], (12, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            panel = _panel_codigo(prog, vista.shape[0])
            cv2.imshow("Destello - en directo (Q = terminar)", np.hstack([vista, panel]))
            if (cv2.waitKey(1) & 0xFF) in (ord("q"), 27):
                break
    cap.release()
    if mostrar:
        cv2.destroyAllWindows()
    return prog

# =====================================================================
# 5. PROGRAMA PRINCIPAL
# =====================================================================

def main():
    ap = argparse.ArgumentParser(description="Lee las fotos de Destello, las transcribe a C y ejecuta el programa.")
    ap.add_argument("entrada", nargs="?", help="carpeta con las fotos, o un vídeo")
    ap.add_argument("--camara", metavar="CARPETA", help="hacer las fotos con la webcam y guardarlas en CARPETA")
    ap.add_argument("--indice-camara", type=int, default=0, help="número de cámara (0, 1…)")
    ap.add_argument("--salida", default="programa.c", help="archivo C que se genera (por defecto programa.c)")
    ap.add_argument("--revisar", action="store_true", help="guarda las fotos con lo detectado dibujado encima")
    ap.add_argument("--directo", nargs="?", const="grabacion_directo", metavar="CARPETA",
                    help="modo automático con la webcam: detecta cada destello solo y escribe el C en directo")
    ap.add_argument("--sin-ventana", action="store_true", help=argparse.SUPPRESS)
    args = ap.parse_args()

    if args.directo:
        fuente = args.entrada if args.entrada and args.entrada.lower().endswith(EXT_VIDEO) else args.indice_camara
        try:
            prog = en_directo(fuente, args.directo, estables=3 if isinstance(fuente, str) else 4, mostrar=not args.sin_ventana)
        except ErrorDestello as e:
            print(f"  ✗ {e}")
            return 1
        return terminar(prog, args.salida)

    if args.camara:
        hacer_fotos_con_camara(args.camara, args.indice_camara)
        args.entrada = args.camara
    if not args.entrada:
        ap.print_help()
        return 1

    if os.path.isdir(args.entrada):
        fuente = fotos_de_carpeta(args.entrada)
        carpeta_rev = os.path.join(args.entrada, "revision")
    elif args.entrada.lower().endswith(EXT_VIDEO):
        fuente = fotos_de_video(args.entrada)
        carpeta_rev = os.path.splitext(args.entrada)[0] + "_revision"
    else:
        print(f"No sé leer «{args.entrada}». Pasa una carpeta de fotos o un vídeo.")
        return 1
    if args.revisar:
        os.makedirs(carpeta_rev, exist_ok=True)

    print("\n1) LEYENDO LOS DESTELLOS")
    print("-" * 72)
    prog, fallos = [], 0
    for titulo, img in fuente:
        try:
            d, det, peque, avisos = leer_destello(img)
        except ErrorDestello as e:
            fallos += 1
            print(f"  {titulo:<28} ✗ {e}")
            continue
        if d is None:
            print(f"  {titulo:<28}   (oscuridad: pausa, la salto)")
            continue
        prog.append(d)
        print(f"  {titulo:<28} {simbolos(d)}   {len(prog):>2}. {etiqueta(d)}")
        for a in avisos:
            print(f"  {'':<28}   ! {a}")
        if args.revisar:
            base = re.sub(r"[^\w.-]+", "_", os.path.splitext(titulo)[0])
            cv2.imwrite(os.path.join(carpeta_rev, base + "_revision.jpg"), dibujar_revision(peque, det, d, titulo))

    if fallos:
        print(f"\n  {fallos} foto(s) no se han podido leer. Repetidlas y volved a ejecutar.")
        return 1
    if not prog:
        print("  No se ha leído ningún destello.")
        return 1

    r = terminar(prog, args.salida)
    if args.revisar:
        print(f"\n  Fotos de revisión en: {carpeta_rev}")
    return r


def terminar(prog, salida):
    if not prog:
        print("  No se ha leído ningún destello.")
        return 1
    print("\n2) TRANSCRIPCIÓN A C")
    print("-" * 72)
    try:
        c = transcribir_a_c(prog)
    except ErrorDestello as e:
        print(f"  ✗ {e}")
        return 1
    with open(salida, "w", encoding="utf-8") as f:
        f.write(c)
    cuerpo = c[c.index("int main(void) {"):]
    print(cuerpo)
    print(f"  Guardado en {salida}")

    print("\n3) SALIDA DEL PROGRAMA")
    print("-" * 72)
    try:
        print("  " + ejecutar(prog))
    except ErrorDestello as e:
        print(f"  ✗ {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
