"""
main.py
-------
Interfaz de consola (obligatoria). Solo pide datos, llama a funciones de
motor_reglas.py y logica_difusa.py y muestra sus resultados. No contiene
lógica de inferencia ni del ciclo Mamdani.

Responsable principal: Leandro Ligero (interfaz de consola).

Uso:  python main.py
"""

import motor_reglas as mr
import logica_difusa as ld


# ---------------------------------------------------------------------------
# Utilidades de entrada
# ---------------------------------------------------------------------------
def preguntar_si_no(texto):
    """Pregunta sí/no hasta recibir una respuesta válida."""
    while True:
        r = input(f"  {texto} [s/n]: ").strip().lower()
        if r in ("s", "si", "sí", "y", "yes"):
            return True
        if r in ("n", "no"):
            return False
        print("    Responde 's' o 'n'.")


def pedir_ocupacion():
    """Pide un número entre 0 y 100 y lo valida (acepta coma decimal)."""
    while True:
        texto = input("  Ocupación de la zona (0-100 %): ").strip().replace(",", ".")
        try:
            valor = float(texto)
            if valor == int(valor):
                valor = int(valor)
            ld.fuzzificar_ocupacion(valor)  # lanza ValueError si está fuera de rango
            return valor
        except ValueError:
            print("    Introduce un número entre 0 y 100.")


# ---------------------------------------------------------------------------
# Zona 1: sistema experto
# ---------------------------------------------------------------------------
def zona_sistema_experto():
    print("\n=== SISTEMA EXPERTO: gestión de incidencias ===")
    print("Indica qué se observa en el paquete:\n")
    hechos = {h for h in mr.HECHOS_OBSERVABLES if preguntar_si_no(h.replace("_", " "))}

    if {"destino_identificado", "destino_no_identificado"} <= hechos:
        print("\n  Aviso: has marcado destino identificado y no identificado a la vez.")

    finales, traza = mr.encadenar_hacia_adelante(hechos)
    print("\n" + mr.formatear_traza(hechos, finales, traza))

    while True:
        nombre = input(
            "¿Por qué una regla (R1-R7) no se activó? Nombre (Enter para volver): "
        ).strip().upper()
        if not nombre:
            return
        print("  " + mr.explicar_por_que_no(nombre, hechos, finales, traza) + "\n")


# ---------------------------------------------------------------------------
# Zona 2: sistema difuso
# ---------------------------------------------------------------------------
def zona_sistema_difuso():
    print("\n=== SISTEMA DIFUSO: desvío según la ocupación de la zona ===")
    o = pedir_ocupacion()
    print("\n" + ld.explicar_desvio(o))


def comparar_umbral():
    print("\n=== COMPARACIÓN ALREDEDOR DEL UMBRAL (80 %) ===")
    print(f"{'Ocupación':>10} | {'Regla rígida':<17} | {'Desvío difuso':>13}")
    for o in (79, 80, 81):
        _, _, _, d = ld.inferir_desvio(o)
        rigida = "desviar_paquetes" if ld.regla_rigida(o) else "no desviar"
        print(f"{o:>9}% | {rigida:<17} | {d:>13.2f}")


# ---------------------------------------------------------------------------
# Menú
# ---------------------------------------------------------------------------
def main():
    acciones = {
        "1": zona_sistema_experto,
        "2": zona_sistema_difuso,
        "3": comparar_umbral,
    }
    while True:
        print("\n--- Gestión de incidencias del centro logístico ---")
        print("1. Sistema experto (hechos, reglas y traza)")
        print("2. Sistema difuso (ocupación de una zona)")
        print("3. Comparar regla rígida y difusa (79 %, 80 %, 81 %)")
        print("0. Salir")
        try:
            opcion = input("Elige una opción: ").strip()
        except EOFError:
            break
        if opcion == "0":
            break
        accion = acciones.get(opcion)
        if accion is None:
            print("Opción no válida.")
            continue
        try:
            accion()
        except EOFError:
            break
    print("Hasta luego.")


if __name__ == "__main__":
    main()