# LYP-2026
- Enzo Sánchez Pérez
- Camila Montoya Morales
- Paloma Domínguez Montero
- Diego Andrés Boscán Guillamón

# Destello ● ■ ▲

**Destello** es un lenguaje de programación esotérico que hemos creado para la asignatura de **Lenguajes y Paradigmas**. No se escribe con teclado: se programa con **cuatro linternas** que proyectan luces de colores y formas sobre una pared. Después hacemos fotos de cada destello, y un programa en Python con **OpenCV** las lee, las **transcribe a código C** y ejecuta el resultado.

```
linternas  ──►  fotos  ──►  OpenCV reconoce ● ■ ▲  ──►  código C  ──►  salida: HOLA
```

---

## La idea

Nuestro logo cuenta la historia de **Octavio**, un Octaviano de 5 años el cual se encuentra en una posicion desesperada, y se ve forzado a encontrar una manera de poder comunicarse con los humanos.

[Lore de Octavio](Documentacion/Lore_Octavianos.md)

Para el mecanismo nos inspiramos en:
- **Los focos y el código morse**: la luz como señal.
- **El View-Master y las cámaras antiguas**: un disco que gira y cambia lo que ves. De ahí sale la **ruleta** de cada linterna.
- **El obturador**: entre destello y destello se tapan todas las luces, y esa oscuridad separa las instrucciones, como un salto de línea.
- **El UNO ColorADD**, la versión para personas con daltonismo: por eso **cada color tiene su propia forma**.

---

## Cómo funciona el lenguaje

### Las cuatro linternas
Las linternas están **en fila** y se leen de izquierda a derecha. Delante de cada una hay una ruleta con tres agujeros tapados con papel celofán:

| Color | Forma | Valor |
|---|---|---|
| Rojo | ● círculo | 0 |
| Verde | ■ cuadrado | 1 |
| Azul | ▲ triángulo | 2 |

### Cómo se lee un destello
- **La linterna 1 dice el tipo de instrucción:**

  | Linterna 1 | Las otras tres significan… |
  |---|---|
  | ● rojo · **dato** | un número (●▲■ = 0×9 + 2×3 + 1 = **7**) |
  | ■ verde · **operación** | qué operación hacer (●▲● = RESTO) |
  | ▲ azul · **control** | qué control (●●● = SI) |

- **Las linternas 2, 3 y 4** forman un número en base 3 (×9, ×3, ×1), del 0 al 26. Son 27 valores, justo las 27 letras del alfabeto español (A = 0, B = 1 … H = 7 … Z = 26).

### Un lenguaje de pila
Destello guarda los números en una **pila**: primero se ponen los números y después la operación (**notación polaca inversa**, como las calculadoras HP antiguas o lenguajes como Forth y PostScript).

```
● ●▲■   dato 7      pila: 7
● ●●▲   dato 2      pila: 7 2
■ ●▲●   RESTO       pila: 1      (7 ÷ 2 = 3 y sobra 1)
```

### Instrucciones

**Operaciones** (linterna 1 = ■ verde)

| Destello | Nombre | Qué hace |
|---|---|---|
| ■ ●●● | IMPRIMIR | Escribe el número de arriba de la pila |
| ■ ■■■ | LETRA | Escribe el número de arriba como letra (7 → H) |
| ■ ■■▲ | PALABRA | Escribe toda la pila como letras |
| ■ ▲▲▲ | ESPACIO | Escribe un espacio |
| ■ ●●■ | SUMAR | a + b |
| ■ ●●▲ | RESTAR | a − b |
| ■ ●■● | MULTIPLICAR | a × b |
| ■ ●▲● | RESTO | Resto de a ÷ b |
| ■ ■■● | UNIR | a × 10 + b (2, 9 → 29) |
| ■ ■●● | DUPLICAR | Copia el número de arriba |
| ■ ■●■ | CAMBIAR | Intercambia los dos de arriba |
| ■ ▲●● | BORRAR | Quita el de arriba |
| ■ ●■▲ | ROTAR | a b c → b c a |
| ■ ■●▲ | ENCIMA | Copia arriba el segundo (a b → a b a) |
| ■ ■▲■ | ASCII | Escribe el carácter ASCII alto × 27 + bajo |

**Control** (linterna 1 = ▲ azul)

| Destello | Nombre | En C |
|---|---|---|
| ▲ ●●● | SI | `if (… != 0) {` |
| ▲ ■■■ | SI NO | `} else {` |
| ▲ ▲▲▲ | FIN SI | `}` |
| ▲ ●■▲ | MIENTRAS | `while (… != 0) {` |
| ▲ ▲■● | FIN MIENTRAS | `}` |
| ▲ ▲●▲ | PARAR | fin del programa |

MIENTRAS se abre con rojo-verde-azul y se cierra al revés, con azul-verde-rojo, como un paréntesis de luz.

---

## Ejemplos

### 1 · Hola (5 destellos)
```c
printf("HOLA");
```
```
● ●▲■  H (7)   ● ■▲●  O (15)   ● ■●▲  L (11)   ● ●●●  A (0)   ■ ■■▲  PALABRA
```
Salida: `HOLA`

### 2 · if / else: ¿par o impar? (10 destellos)
```c
int n = 7;
if (n % 2 != 0) { printf("I"); } else { printf("P"); }
```
```
● ●▲■  7        ● ●●▲  2        ■ ●▲●  RESTO
▲ ●●●  SI       ● ●▲▲  I        ■ ■■■  LETRA
▲ ■■■  SI NO    ● ■▲■  P        ■ ■■■  LETRA
▲ ▲▲▲  FIN SI
```
Salida: `I`. Si el primer destello es un 8, sale `P`.

### 3 · Bucle while: cuenta atrás (6 destellos)
```c
int n = 3;
while (n != 0) { printf("%d ", n); n = n - 1; }
```
```
● ●■●  3    ▲ ●■▲  MIENTRAS    ■ ●●●  IMPRIMIR
● ●●■  1    ■ ●●▲  RESTAR      ▲ ▲■●  FIN MIENTRAS
```
Salida: `3 2 1`. Solo hay que fotografiar 6 destellos, aunque el bucle dé 3 vueltas.

---

## El mecanismo

> *(Añadid aquí fotos del pulpo y de las linternas.)*

**Materiales:**
- 4 Linternas
- Ruletas: cartón y cartulina, tijeras
- Filtros: papel celofán rojo, verde y azul, celo, pegamento
- Figuras: rotulador
- Estructura: caja de cartón y cartulina
- Captura: cámara, móvil

---

## Instalación

Necesitamos **Python 3** y **OpenCV**:

```
pip install -r requirements.txt
```

## Uso

**Con una carpeta de fotos** (una foto por destello, con nombres `01.jpg`, `02.jpg`…):
```
python destello.py fotos_prueba/ejemplo1_hola --salida hola.c
```

**Con un vídeo** (el programa separa los destellos por la oscuridad que hay entre ellos):
```
python destello.py grabacion.mp4
```

**Con la webcam** (ESPACIO = hacer foto, Q = terminar):
```
python destello.py --camara mis_fotos/hola
```

El programa hace tres cosas:
1. **Lee cada foto**: busca las 4 luces, las ordena de izquierda a derecha y reconoce el color y la forma de cada una. Si el color y la forma no coinciden, avisa.
2. **Transcribe a C**: genera un archivo `.c` con una línea por destello.
3. **Ejecuta el programa** y muestra la salida.

Con `--revisar` guarda también las fotos con lo detectado dibujado encima, en la carpeta `revision/`.

El archivo C generado se puede compilar con `gcc hola.c -o hola`, o pegarlo en un compilador online.

### Para que las fotos salgan bien
- Clase a oscuras y el móvil fijo.
- Sin flash.
- Las 4 luces enteras y separadas, sin que salgan completamente blancas.

**En directo con la webcam** (detecta cada destello solo; Q = terminar):
```
python destello.py --directo --salida hola.c
```
---

## Archivos

| Archivo | Qué es |
|---|---|
| `destello.py` | Lector con OpenCV, transcriptor a C e intérprete de Destello |
| `generar_fotos_prueba.py` | Crea fotos y un vídeo simulados de los tres ejemplos |
| `fotos_prueba/` | Fotos simuladas para probar sin el mecanismo |
| `requirements.txt` | Dependencias de Python |

---

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

En este vídeo se ve por dentro cómo funciona la máquina: cada linterna tiene delante una ruleta con tres filtros de celofán (rojo, verde y azul). Los palos ubicados en la parte superior se mueven de izquierda a derecha y de abajo hacia arriba y de arriba hacia abajo, para ir rotando la posición de la ruleta y así cambiar el filtro que es el que queremos que se vea por el agujero y que, a su vez, quedará delante de la linterna. ▶️ https://github.com/user-attachments/assets/1e25311b-9f11-4773-8c53-73770de4e341

Proyecto de **Lenguajes y Paradigmas**, curso 2026-2027. Parte del código se desarrolló con ayuda de Claude (IA).
