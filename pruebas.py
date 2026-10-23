"""
pruebas.py
----------
Ampliación A9: batería de pruebas automatizadas con assert.
Comprueba los casos A-D, la inferencia manual de P-104, la regla propia R7 y
valores de referencia de la lógica difusa.

Responsable principal: Leonardo Acchioni (pruebas e informe).

Uso:  python pruebas.py      (también compatible con pytest)
"""

import motor_reglas as mr
import logica_difusa as ld


def inferir(hechos, reglas=mr.REGLAS_BASE):
    finales, traza = mr.encadenar_hacia_adelante(set(hechos), reglas)
    return finales, [(p["regla"], p["conclusion"]) for p in traza]


# ----------------------------- sistema clásico -----------------------------
def test_p104_inferencia_manual():
    finales, traza = inferir({"codigo_no_legible", "destino_no_identificado"})
    assert traza == [("R1", "solicitar_lectura_manual"), ("R2", "enviar_revision")]
    _, tr = mr.encadenar_hacia_adelante(
        {"codigo_no_legible", "destino_no_identificado"}
    )
    assert [p["vuelta"] for p in tr] == [1, 2]  # R2 necesita la salida de R1


def test_caso_a_flujo_normal():
    finales, traza = inferir({"destino_identificado", "sin_incidencias"})
    assert traza == [("R6", "autorizar_clasificacion")]


def test_caso_b_inferencia_encadenada():
    finales, traza = inferir({"codigo_no_legible", "destino_no_identificado"})
    assert "enviar_revision" in finales and "solicitar_lectura_manual" in finales


def test_caso_c_dos_caminos_misma_conclusion():
    hechos = {
        "codigo_no_legible",
        "destino_no_identificado",
        "embalaje_danado",
        "contenido_fragil",
    }
    finales, traza = inferir(hechos)
    # R1 y R3 actúan en la vuelta 1; R3 deja enviar_revision antes de que R2 pueda
    # y la traza conserva solo el primer camino.
    assert traza == [("R1", "solicitar_lectura_manual"), ("R3", "enviar_revision")]
    assert "enviar_revision" in finales


def test_caso_d_sin_r7_no_hay_conclusion():
    finales, traza = inferir({"embalaje_danado"}, mr.REGLAS_INICIALES)
    assert traza == [] and finales == {"embalaje_danado"}


def test_caso_d_con_r7_envia_a_revision():
    finales, traza = inferir({"embalaje_danado"})
    assert traza == [("R7", "enviar_revision")]


def test_cadena_peso_documentacion():
    finales, traza = inferir({"peso_fuera_rango", "documentacion_incompleta"})
    assert traza == [("R4", "comprobar_peso"), ("R5", "retener_temporalmente")]


def test_motor_no_modifica_entradas():
    ini = {"codigo_no_legible"}
    copia = set(ini)
    mr.encadenar_hacia_adelante(ini)
    assert ini == copia


def test_motor_separado_de_las_reglas():
    """El mismo motor funciona con reglas de otro dominio sin tocarlo."""
    otras = [
        {"nombre": "X1", "condiciones": {"nube"}, "conclusion": "lluvia"},
        {"nombre": "X2", "condiciones": {"lluvia"}, "conclusion": "paraguas"},
    ]
    finales, traza = inferir({"nube"}, otras)
    assert traza == [("X1", "lluvia"), ("X2", "paraguas")]


def test_por_que_no():
    ini = {"codigo_no_legible"}
    fin, tr = mr.encadenar_hacia_adelante(ini)
    assert "destino_no_identificado" in mr.explicar_por_que_no("R2", ini, fin, tr)


# ------------------------------ sistema difuso -----------------------------
def casi(a, b, tol=0.01):
    return abs(a - b) <= tol


def test_extremos_hombros():
    assert ld.fuzzificar_ocupacion(0) == {"baja": 1.0, "media": 0.0, "alta": 0.0}
    assert ld.fuzzificar_ocupacion(100) == {"baja": 0.0, "media": 0.0, "alta": 1.0}


def test_valores_referencia_alrededor_del_umbral():
    esperado = {79: (0.300, 0.600, 70.47), 80: (0.250, 0.667, 72.60), 81: (0.200, 0.733, 74.78)}
    for o, (media, alta, final) in esperado.items():
        grados, _, _, d = ld.inferir_desvio(o)
        assert casi(grados["media"], media, 0.001)
        assert casi(grados["alta"], alta, 0.001)
        assert casi(d, final)


def test_centroides_extremos():
    assert casi(ld.inferir_desvio(0)[3], 15.53)
    assert casi(ld.inferir_desvio(100)[3], 84.47)


def test_regla_rigida_salta_en_81():
    assert [ld.regla_rigida(o) for o in (79, 80, 81)] == [False, False, True]


def test_difuso_es_gradual_y_creciente():
    valores = [ld.inferir_desvio(o)[3] for o in range(0, 101)]
    assert all(b >= a - 1e-9 for a, b in zip(valores, valores[1:]))
    # Cada 1 % de ocupación mueve el desvío como mucho ~3,4 puntos (máximo en 45→46 %),
    # frente al salto de 100 puntos del escalón de la regla rígida.
    assert max(abs(b - a) for a, b in zip(valores, valores[1:])) < 4


def test_ocupacion_fuera_de_rango():
    for o in (-1, 101):
        try:
            ld.inferir_desvio(o)
        except ValueError:
            continue
        raise AssertionError(f"debía rechazar {o}")


if __name__ == "__main__":
    pruebas = [f for n, f in sorted(globals().items()) if n.startswith("test_")]
    for prueba in pruebas:
        prueba()
        print(f"OK  {prueba.__name__}")
    print(f"\n{len(pruebas)} pruebas superadas.")