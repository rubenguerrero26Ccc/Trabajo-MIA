"""
motor_reglas.py
---------------
Base de conocimiento y motor de inferencia por encadenamiento hacia adelante
para la gestión de incidencias en un centro logístico.

Responsable principal: Hugo Silva (motor de reglas y nueva regla R7).

Cadena de este módulo (no depende de la lógica difusa ni de la interfaz):

    base de conocimiento -> motor de inferencia -> (la interfaz muestra)

Las reglas son DATOS (lista de diccionarios). El motor no conoce ningún hecho
concreto: si mañana se cambian las reglas por las de otro dominio, el motor
no necesita ninguna modificación.
"""

from typing import Any, Dict, List, Set, Tuple

# ---------------------------------------------------------------------------
# Hechos
# ---------------------------------------------------------------------------
# Hechos observables: los introduce el personal de turno.
HECHOS_OBSERVABLES: List[str] = [
    "codigo_no_legible",
    "destino_no_identificado",
    "destino_identificado",
    "embalaje_danado",
    "contenido_fragil",
    "peso_fuera_rango",
    "documentacion_incompleta",
    "sin_incidencias",
]

# Hechos derivados: los genera el motor al aplicar reglas.
HECHOS_DERIVADOS: List[str] = [
    "solicitar_lectura_manual",
    "enviar_revision",
    "comprobar_peso",
    "retener_temporalmente",
    "autorizar_clasificacion",
]

# ---------------------------------------------------------------------------
# Base de reglas
# ---------------------------------------------------------------------------
Regla = Dict[str, Any]

# Reglas R1-R6 del guion (apartado 7.2).
REGLAS_INICIALES: List[Regla] = [
    {
        "nombre": "R1",
        "condiciones": {"codigo_no_legible"},
        "conclusion": "solicitar_lectura_manual",
    },
    {
        "nombre": "R2",
        "condiciones": {"solicitar_lectura_manual", "destino_no_identificado"},
        "conclusion": "enviar_revision",
    },
    {
        "nombre": "R3",
        "condiciones": {"embalaje_danado", "contenido_fragil"},
        "conclusion": "enviar_revision",
    },
    {
        "nombre": "R4",
        "condiciones": {"peso_fuera_rango"},
        "conclusion": "comprobar_peso",
    },
    {
        "nombre": "R5",
        "condiciones": {"comprobar_peso", "documentacion_incompleta"},
        "conclusion": "retener_temporalmente",
    },
    {
        "nombre": "R6",
        "condiciones": {"destino_identificado", "sin_incidencias"},
        "conclusion": "autorizar_clasificacion",
    },
]

# Regla propia del grupo (apartado 13).
# Situación: un paquete con el embalaje dañado y contenido NO frágil (caso D)
# no producía ninguna conclusión. Se decide enviarlo igualmente a revisión,
# porque un embalaje dañado puede esconder daños en el contenido.
REGLA_PROPIA: Regla = {
    "nombre": "R7",
    "condiciones": {"embalaje_danado"},
    "conclusion": "enviar_revision",
}

# Base de conocimiento vigente (R1-R7). Es la que usa la interfaz.
REGLAS_BASE: List[Regla] = REGLAS_INICIALES + [REGLA_PROPIA]


# ---------------------------------------------------------------------------
# Motor de inferencia
# ---------------------------------------------------------------------------
def encadenar_hacia_adelante(
    hechos_iniciales: Set[str],
    reglas: List[Regla] = REGLAS_BASE,
) -> Tuple[Set[str], List[Dict[str, Any]]]:
    """Encadenamiento hacia adelante.

    Recibe hechos iniciales + base de reglas y devuelve (hechos_finales, traza).

    En cada vuelta:
      1. se miran las reglas cuyas condiciones están TODAS en los hechos que
         había al empezar la vuelta;
      2. se disparan en orden, añadiendo su conclusión como hecho nuevo
         (si ya estaba, la regla no se dispara: no aporta nada);
      3. se registra en la traza qué regla generó cada conclusión.
    Se repite hasta que una vuelta completa no produce hechos nuevos.

    Cada entrada de la traza es:
        {"vuelta": int, "regla": str, "condiciones": [str], "conclusion": str}

    No modifica los argumentos de entrada.
    """
    hechos = set(hechos_iniciales)
    traza: List[Dict[str, Any]] = []
    vuelta = 0
    hay_novedad = True

    while hay_novedad:
        hay_novedad = False
        vuelta += 1
        disponibles = set(hechos)  # hechos al empezar la vuelta
        for regla in reglas:
            if regla["conclusion"] in hechos:
                continue
            if regla["condiciones"].issubset(disponibles):
                hechos.add(regla["conclusion"])
                traza.append(
                    {
                        "vuelta": vuelta,
                        "regla": regla["nombre"],
                        "condiciones": sorted(regla["condiciones"]),
                        "conclusion": regla["conclusion"],
                    }
                )
                hay_novedad = True

    return hechos, traza


def conclusiones(hechos_iniciales: Set[str], hechos_finales: Set[str]) -> Set[str]:
    """Hechos nuevos obtenidos por inferencia (finales menos iniciales)."""
    return set(hechos_finales) - set(hechos_iniciales)


# ---------------------------------------------------------------------------
# Presentación de la traza (la interfaz solo imprime este texto)
# ---------------------------------------------------------------------------
def formatear_traza(
    hechos_iniciales: Set[str],
    hechos_finales: Set[str],
    traza: List[Dict[str, Any]],
) -> str:
    """Texto comprensible: hechos iniciales, cada regla disparada y conclusiones."""
    lineas = ["Hechos iniciales:"]
    if hechos_iniciales:
        lineas += [f"  - {h}" for h in sorted(hechos_iniciales)]
    else:
        lineas.append("  (ninguno)")

    lineas.append("")
    if not traza:
        lineas.append(
            "Ninguna regla se ha activado: la base de reglas no cubre esta "
            "situación y no se obtiene ninguna conclusión."
        )
    for paso in traza:
        lineas.append(f"[vuelta {paso['vuelta']}] {paso['regla']}")
        lineas.append("    " + "\n    + ".join(paso["condiciones"]))
        lineas.append(f"    -> {paso['conclusion']}")
        lineas.append("")

    nuevas = sorted(conclusiones(hechos_iniciales, hechos_finales))
    lineas.append("Conclusiones:")
    if nuevas:
        lineas += [f"  - {c}" for c in nuevas]
    else:
        lineas.append("  (ninguna)")
    return "\n".join(lineas).rstrip() + "\n"


# ---------------------------------------------------------------------------
# Ampliación A6: explicación "por qué no"
# ---------------------------------------------------------------------------
def explicar_por_que_no(
    nombre_regla: str,
    hechos_iniciales: Set[str],
    hechos_finales: Set[str],
    traza: List[Dict[str, Any]],
    reglas: List[Regla] = REGLAS_BASE,
) -> str:
    """Explica por qué una regla se disparó o, si no, qué condición le faltó."""
    regla = next((r for r in reglas if r["nombre"] == nombre_regla), None)
    if regla is None:
        return f"La regla {nombre_regla} no existe en la base de conocimiento."

    paso = next((p for p in traza if p["regla"] == nombre_regla), None)
    if paso is not None:
        return (
            f"{nombre_regla} SÍ se activó en la vuelta {paso['vuelta']} y "
            f"generó {regla['conclusion']}."
        )

    faltan = sorted(regla["condiciones"] - set(hechos_finales))
    if faltan:
        return (
            f"{nombre_regla} no se activó: le faltó(n) "
            + ", ".join(faltan)
            + " (ni observado(s) ni derivado(s))."
        )

    # Condiciones completas pero sin dispararse: su conclusión ya existía.
    quien = next(
        (p["regla"] for p in traza if p["conclusion"] == regla["conclusion"]), None
    )
    if quien:
        return (
            f"{nombre_regla} tenía todas sus condiciones, pero no se registró "
            f"porque {regla['conclusion']} ya había sido obtenida por {quien}."
        )
    return (
        f"{nombre_regla} tenía todas sus condiciones, pero {regla['conclusion']} "
        "ya figuraba entre los hechos iniciales."
    )


if __name__ == "__main__":
    # Comprobación rápida del hito H2: inferencia del paquete P-104.
    ini = {"codigo_no_legible", "destino_no_identificado"}
    fin, tr = encadenar_hacia_adelante(ini)
    print(formatear_traza(ini, fin, tr))