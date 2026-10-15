# LYP-2026
- Enzo Sánchez Pérez
- Camila Montoya Morales
- Paloma Domínguez Montero
- Diego Andrés Boscán Guillamón
## Proyecto
- [Destello: lenguaje esotérico con luces y formas](DestellosGit/)
## Vídeo de la prueba
- Prueba en directo con la máquina: la cámara lee los destellos y va escribiendo el código C.
▶️ [Ver el vídeo de la prueba](https://drive.google.com/file/d/12iUT1PS-s8eFzh9WUY3eGnGoOSZEL67N/view?usp=sharing)
**En directo con la webcam** (detecta cada destello solo):
```
python destello.py --directo --salida hola.c
```
1. En pantalla aparecen 4 recuadros, uno por linterna. Ajusta la cámara para que cada agujero quede dentro de su recuadro.
2. Muestra cada destello quieto ~1 s: el programa lo apunta y va escribiendo el código C y la pila.
3. Tapa las linternas antes del siguiente destello.
Teclas: B = borrar el último destello · R = empezar de nuevo · Q = terminar.
Si se cambia de cámara o de sitio, se pueden volver a marcar los recuadros con `--zona`.
