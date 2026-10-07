/* Programa transcrito automáticamente desde los destellos de las linternas.
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

int main(void) {
    apilar(7);                              //  1  ● ●▲■  dato 7 (letra H)
    apilar(15);                             //  2  ● ■▲●  dato 15 (letra O)
    apilar(11);                             //  3  ● ■●▲  dato 11 (letra L)
    apilar(0);                              //  4  ● ●●●  dato 0 (letra A)
    palabra();                              //  5  ■ ■■▲  PALABRA
    printf("\n");
    return 0;
}
