"""
app.py
------
Interfaz Streamlit (opcional, ampliación A10).
Igual que main.py, solo llama a funciones de los otros módulos y muestra
sus resultados.

Responsable principal: Leandro Ligero (interfaces).

Uso:  streamlit run app.py
"""

import streamlit as st

import graficos
import logica_difusa as ld
import motor_reglas as mr

st.set_page_config(page_title="Incidencias del centro logístico", layout="wide")
st.title("Gestión de incidencias en un centro logístico")

tab_experto, tab_difuso = st.tabs(["Sistema experto", "Sistema difuso"])

# ---------------------------------------------------------------------------
# Zona 1: sistema experto
# ---------------------------------------------------------------------------
with tab_experto:
    st.subheader("Hechos observados")
    columnas = st.columns(2)
    hechos = set()
    for i, hecho in enumerate(mr.HECHOS_OBSERVABLES):
        if columnas[i % 2].checkbox(hecho.replace("_", " "), key=f"hecho_{hecho}"):
            hechos.add(hecho)

    if {"destino_identificado", "destino_no_identificado"} <= hechos:
        st.warning("Has marcado destino identificado y no identificado a la vez.")

    if st.button("Ejecutar inferencia", type="primary"):
        finales, traza = mr.encadenar_hacia_adelante(hechos)
        st.session_state["resultado"] = (set(hechos), finales, traza)

    if "resultado" in st.session_state:
        iniciales, finales, traza = st.session_state["resultado"]
        st.markdown("**Hechos iniciales:** " + (", ".join(sorted(iniciales)) or "ninguno"))
        nuevas = sorted(mr.conclusiones(iniciales, finales))
        if nuevas:
            st.success("Conclusiones: " + ", ".join(nuevas))
        else:
            st.info("Ninguna regla se activó: la base de reglas no cubre esta situación.")
        st.markdown("**Traza de inferencia**")
        st.code(mr.formatear_traza(iniciales, finales, traza), language="text")

        nombre = st.selectbox(
            "¿Por qué no se activó una regla?", [r["nombre"] for r in mr.REGLAS_BASE]
        )
        st.write(mr.explicar_por_que_no(nombre, iniciales, finales, traza))

# ---------------------------------------------------------------------------
# Zona 2: sistema difuso
# ---------------------------------------------------------------------------
with tab_difuso:
    ocupacion = st.slider("Ocupación de la zona (%)", 0, 100, 80)
    grados, activaciones, _, d_final = ld.inferir_desvio(ocupacion)

    c1, c2, c3 = st.columns(3)
    c1.metric("Ocupación seleccionada", f"{ocupacion} %")
    c2.metric("Desvío final (centroide)", f"{d_final:.2f}")
    c3.metric(
        "Regla rígida (> 80)",
        "desviar_paquetes" if ld.regla_rigida(ocupacion) else "no desviar",
    )

    st.markdown("**Grados de pertenencia**")
    st.table({t: [f"{g:.3f}"] for t, g in grados.items()})

    st.markdown("**Reglas difusas**")
    st.code(ld.explicar_desvio(ocupacion), language="text")

    g1, g2 = st.columns(2)
    g1.pyplot(graficos.fig_funciones_ocupacion())
    g2.pyplot(graficos.fig_mamdani(ocupacion))
    st.pyplot(graficos.fig_curva_respuesta())