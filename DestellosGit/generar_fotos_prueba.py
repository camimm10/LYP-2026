#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera fotos (y un vídeo) de PRUEBA de los 3 ejemplos de la presentación,
imitando las 4 linternas sobre una pared oscura. Sirven para probar
destello.py antes de tener el mecanismo real.

    python generar_fotos_prueba.py
"""
import os
import cv2
import numpy as np

rng = np.random.default_rng(7)

# Los 3 ejemplos de la presentación (0 rojo/círculo, 1 verde/cuadrado, 2 azul/triángulo)
EJEMPLOS = {
    "ejemplo1_hola": [
        [0, 0, 2, 1], [0, 1, 2, 0], [0, 1, 0, 2], [0, 0, 0, 0], [1, 1, 1, 2],
    ],
    "ejemplo2_if_else": [
        [0, 0, 2, 1], [0, 0, 0, 2], [1, 0, 2, 0], [2, 0, 0, 0], [0, 0, 2, 2],
        [1, 1, 1, 1], [2, 1, 1, 1], [0, 1, 2, 1], [1, 1, 1, 1], [2, 2, 2, 2],
    ],
    "ejemplo3_while": [
        [0, 0, 1, 0], [2, 0, 1, 2], [1, 0, 0, 0], [0, 0, 0, 1], [1, 0, 0, 2], [2, 2, 1, 0],
    ],
}

# Colores de luz tras el celofán (BGR)
LUZ = [(70, 70, 255), (110, 235, 100), (255, 140, 70)]
W, H = 1600, 900


def figura(mask, k, cx, cy, r, ang):
    if k == 0:
        cv2.circle(mask, (int(cx), int(cy)), int(r), 255, -1, cv2.LINE_AA)
        return
    if k == 1:
        pts = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1]], float) * r * 0.85
    else:
        pts = np.array([[0, -1.15], [1.0, 0.6], [-1.0, 0.6]], float) * r
    a = np.deg2rad(ang)
    R = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    pts = pts @ R.T + [cx, cy]
    cv2.fillPoly(mask, [pts.astype(np.int32)], 255, cv2.LINE_AA)


def foto(destello):
    # Pared oscura con algo de luz ambiente y ruido de cámara
    yy, xx = np.mgrid[0:H, 0:W]
    fondo = 18 + 10 * np.exp(-((xx - W / 2) ** 2 + (yy - H) ** 2) / (2 * 600 ** 2))
    img = np.dstack([fondo * 1.15, fondo, fondo * 0.95]).astype(np.float32)
    # Posiciones: los altavoces (1 y 4) más bajos que los ojos (2 y 3), como en el pulpo
    xs = [260, 640, 960, 1340]
    ys = [520, 400, 400, 520]
    for i, k in enumerate(destello):
        cx = xs[i] + rng.normal(0, 12)
        cy = ys[i] + rng.normal(0, 10)
        r = 85 * rng.uniform(0.9, 1.1)
        mask = np.zeros((H, W), np.uint8)
        figura(mask, k, cx, cy, r, rng.normal(0, 7))
        m = cv2.GaussianBlur(mask.astype(np.float32) / 255, (0, 0), 1.6)
        halo = cv2.GaussianBlur(mask.astype(np.float32) / 255, (0, 0), 28) * 0.45
        col = np.array(LUZ[k], np.float32) * rng.uniform(0.85, 1.05)
        nucleo = col * 0.8 + 255 * 0.2          # el centro sale algo blanquecino
        img += m[..., None] * nucleo + halo[..., None] * col
    img += rng.normal(0, 4, img.shape)
    img = np.clip(img, 0, 255).astype(np.uint8)
    # Pequeña perspectiva, como si la foto no estuviera perfectamente de frente
    d = 25
    src = np.float32([[0, 0], [W, 0], [W, H], [0, H]])
    dst = np.float32([[rng.uniform(0, d), rng.uniform(0, d)], [W - rng.uniform(0, d), rng.uniform(0, d)],
                      [W - rng.uniform(0, d), H - rng.uniform(0, d)], [rng.uniform(0, d), H - rng.uniform(0, d)]])
    img = cv2.warpPerspective(img, cv2.getPerspectiveTransform(src, dst), (W, H), borderValue=(18, 18, 18))
    return img


def main():
    base = "fotos_prueba"
    for nombre, prog in EJEMPLOS.items():
        carpeta = os.path.join(base, nombre)
        os.makedirs(carpeta, exist_ok=True)
        for i, d in enumerate(prog, 1):
            cv2.imwrite(os.path.join(carpeta, f"{i:02d}.jpg"), foto(d), [cv2.IMWRITE_JPEG_QUALITY, 88])
        print(f"  {carpeta}: {len(prog)} fotos")

    # Un vídeo del ejemplo 3: cada destello ~1 s, con oscuridad entre medias
    ruta = os.path.join(base, "ejemplo3_while.mp4")
    vw = cv2.VideoWriter(ruta, cv2.VideoWriter_fourcc(*"mp4v"), 10, (W // 2, H // 2))
    oscuro = cv2.resize(foto([0, 0, 0, 0]) * 0, (W // 2, H // 2)) + 18
    for d in EJEMPLOS["ejemplo3_while"]:
        for _ in range(5):
            vw.write(oscuro)
        f = cv2.resize(foto(d), (W // 2, H // 2))
        for _ in range(10):
            vw.write(f)
    for _ in range(5):
        vw.write(oscuro)
    vw.release()
    print(f"  {ruta}: vídeo de prueba")


if __name__ == "__main__":
    main()
