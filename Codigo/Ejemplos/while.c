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
    apilar(3);                              //  1  ● ●■●  dato 3 (letra D)
    while (cima() != 0) {                   //  2  ▲ ●■▲  MIENTRAS
        imprimir();                         //  3  ■ ●●●  IMPRIMIR
        apilar(1);                          //  4  ● ●●■  dato 1 (letra B)
        { int b = desapilar(), a = desapilar(); apilar(a - b); }//  5  ■ ●●▲  RESTAR
    }                                       //  6  ▲ ▲■●  FIN MIENTRAS
    printf("\n");
    return 0;
}
