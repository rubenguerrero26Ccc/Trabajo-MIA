"""
logica_difusa.py
----------------
Sistema difuso tipo Mamdani para decidir el nivel de desvío de paquetes
a partir de la ocupación de una zona de clasificación (0-100 %).

Cadena de este módulo (no depende del motor de reglas ni de la interfaz):

    funciones de pertenencia -> inferencia difusa -> (la interfaz muestra)

Elecciones del esquema Mamdani (apartado 18 del guion):
    implicación      -> mínimo   (se recorta el consecuente)
    agregación       -> máximo
    desfuzzificación -> centroide (aproximado sobre una rejilla con NumPy)
"""

import numpy as np

# ---------------------------------------------------------------------------
# Rejilla del universo de discurso de la salida (desvío), 0..100
# ---------------------------------------------------------------------------
X = np.linspace(0, 100, 1001)

# ---------------------------------------------------------------------------
# Funciones de pertenencia
# ---------------------------------------------------------------------------


def _subida(x, a, b):
    """Tramo ascendente de 0 a 1 entre a y b. Si a == b es un 'hombro':
    salto directo (1 si x >= a), sin dividir entre cero."""
    x = np.asarray(x, dtype=float)
    if b == a:
        return (x >= a).astype(float)
    return np.clip((x - a) / (b - a), 0.0, 1.0)


def _bajada(x, c, d):
    """Tramo descendente de 1 a 0 entre c y d. Si c == d es un 'hombro':
    1 si x <= c, 0 después, sin dividir entre cero."""
    x = np.asarray(x, dtype=float)
    if d == c:
        return (x <= c).astype(float)
    return np.clip((d - x) / (d - c), 0.0, 1.0)


def trapezoidal(x, a, b, c, d):
    """Función trapezoidal [a, b, c, d]. Admite hombros (a == b o c == d).
    Devuelve un grado (float) o un array de grados según la entrada."""
    return np.minimum(_subida(x, a, b), _bajada(x, c, d))


def triangular(x, a, b, c):
    """Función triangular [a, b, c]: es un trapezoide con b == c en la cima."""
    return trapezoidal(x, a, b, b, c)


# ---------------------------------------------------------------------------
# Definición de las variables difusas (datos, no lógica)
# ---------------------------------------------------------------------------
# Entrada: ocupación de la zona (%)
OCUPACION = {
    "baja": ("trapezoidal", (0, 0, 40, 55)),
    "media": ("triangular", (45, 65, 85)),
    "alta": ("trapezoidal", (70, 85, 100, 100)),
}

# Salida: nivel de desvío de paquetes
DESVIO = {
    "bajo": ("trapezoidal", (0, 0, 20, 40)),
    "medio": ("triangular", (25, 50, 75)),
    "alto": ("trapezoidal", (60, 80, 100, 100)),
}

# Reglas difusas (separadas del motor, como las reglas del sistema clásico)
REGLAS_DIFUSAS = [
    {"nombre": "D1", "si_ocupacion": "baja", "entonces_desvio": "bajo"},
    {"nombre": "D2", "si_ocupacion": "media", "entonces_desvio": "medio"},
    {"nombre": "D3", "si_ocupacion": "alta", "entonces_desvio": "alto"},
]


def _evaluar(definicion, x):
    """Evalúa una función de pertenencia descrita como (forma, parámetros)."""
    forma, params = definicion
    if forma == "triangular":
        return triangular(x, *params)
    return trapezoidal(x, *params)


# ---------------------------------------------------------------------------
# Regla rígida original (para comparar)
# ---------------------------------------------------------------------------
UMBRAL_RIGIDO = 80


def regla_rigida(ocupacion):
    """SI ocupacion_zona > 80 ENTONCES desviar_paquetes. Devuelve True/False."""
    return ocupacion > UMBRAL_RIGIDO


# ---------------------------------------------------------------------------
# Etapas del ciclo Mamdani
# ---------------------------------------------------------------------------


def _validar_ocupacion(o):
    if not 0 <= o <= 100:
        raise ValueError(f"La ocupación debe estar entre 0 y 100 (recibido: {o})")


def fuzzificar_ocupacion(o):
    """Etapa 1. Devuelve {"baja": g, "media": g, "alta": g} para la ocupación o."""
    _validar_ocupacion(o)
    return {t: float(_evaluar(d, o)) for t, d in OCUPACION.items()}


def activar_reglas(grados):
    """Etapa 2. Grado de activación de cada regla = pertenencia de su antecedente.
    Devuelve {"D1": a1, "D2": a2, "D3": a3}."""
    return {r["nombre"]: grados[r["si_ocupacion"]] for r in REGLAS_DIFUSAS}


def recortar_consecuentes(activaciones):
    """Etapa 3 (implicación por mínimo). Devuelve {"D1": array, ...} con cada
    consecuente recortado a la altura de la activación de su regla."""
    salidas = {}
    for r in REGLAS_DIFUSAS:
        mu_consecuente = _evaluar(DESVIO[r["entonces_desvio"]], X)
        salidas[r["nombre"]] = np.minimum(activaciones[r["nombre"]], mu_consecuente)
    return salidas


def agregar(recortadas):
    """Etapa 4 (agregación por máximo). Devuelve el array mu_agg(y)."""
    return np.max(np.vstack(list(recortadas.values())), axis=0)


def centroide(mu_agg):
    """Etapa 5 (desfuzzificación). Centroide numérico sum(y*mu)/sum(mu).
    Devuelve None si el área es 0 (ninguna regla se activa)."""
    area = np.sum(mu_agg)
    if area == 0:
        return None
    return float(np.sum(X * mu_agg) / area)


def inferir_desvio(o):
    """Ciclo Mamdani completo para una ocupación o (0-100).

    Devuelve (grados, activaciones, salida_agregada, d_final):
        grados           dict  {"baja", "media", "alta"}
        activaciones     dict  {"D1", "D2", "D3"}
        salida_agregada  array mu_agg(y) sobre la rejilla X
        d_final          float nivel de desvío desfuzzificado (0-100)
    """
    grados = fuzzificar_ocupacion(o)
    activaciones = activar_reglas(grados)
    recortadas = recortar_consecuentes(activaciones)
    salida_agregada = agregar(recortadas)
    d_final = centroide(salida_agregada)
    return grados, activaciones, salida_agregada, d_final


def curvas_pertenencia():
    """Curvas de pertenencia para dibujar (las usan graficos.py y app.py).
    Devuelve (X, {término: array} de la ocupación, {término: array} del desvío)."""
    ocupacion = {t: _evaluar(d, X) for t, d in OCUPACION.items()}
    desvio = {t: _evaluar(d, X) for t, d in DESVIO.items()}
    return X, ocupacion, desvio


# ---------------------------------------------------------------------------
# Texto explicativo (la interfaz solo lo imprime)
# ---------------------------------------------------------------------------


def explicar_desvio(o):
    """Devuelve un texto con grados, reglas activadas, desvío final y la
    respuesta de la regla rígida, para que la interfaz solo tenga que mostrarlo."""
    grados, activaciones, _, d_final = inferir_desvio(o)
    lineas = [f"Ocupación seleccionada: {o} %", "", "Grados de pertenencia:"]
    lineas += [f"  - ocupación {t}: {g:.3f}" for t, g in grados.items()]
    lineas += ["", "Reglas difusas:"]
    for r in REGLAS_DIFUSAS:
        a = activaciones[r["nombre"]]
        estado = "ACTIVADA" if a > 0 else "no activada"
        lineas.append(
            f"  - {r['nombre']}: SI ocupación es {r['si_ocupacion']} "
            f"ENTONCES desvío es {r['entonces_desvio']} -> grado {a:.3f} ({estado})"
        )
    lineas += ["", f"Nivel de desvío final (centroide): {d_final:.2f}"]
    rigida = "desviar_paquetes" if regla_rigida(o) else "no desviar"
    lineas.append(f"Regla rígida (ocupación > {UMBRAL_RIGIDO}): {rigida}")
    return "\n".join(lineas)


if __name__ == "__main__":
    # Comprobaciones rápidas del hito H4
    print("Extremos (hombros):")
    for o in (0, 100):
        print(f"  o={o}: {fuzzificar_ocupacion(o)}")
    print()
    print(explicar_desvio(80))
