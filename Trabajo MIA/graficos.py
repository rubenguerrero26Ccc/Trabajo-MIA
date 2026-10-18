"""
graficos.py
-----------
Gráficos del sistema difuso (apartado 5 de la plantilla y ampliación A2).
Solo dibuja: los cálculos los hace logica_difusa.py.

Responsable principal: Ruben Guerrero (lógica difusa y gráficos).

Uso:  python graficos.py   (guarda las figuras en la carpeta figuras/)
"""

import os

import matplotlib

matplotlib.use("Agg")  # no necesita pantalla; Streamlit y ficheros funcionan igual
import matplotlib.pyplot as plt
import numpy as np

import logica_difusa as ld


def fig_funciones_ocupacion():
    X, ocupacion, _ = ld.curvas_pertenencia()
    fig, ax = plt.subplots(figsize=(6, 3.2))
    for termino, mu in ocupacion.items():
        ax.plot(X, mu, label=f"ocupación {termino}")
    ax.set(xlabel="Ocupación (%)", ylabel="Grado de pertenencia", ylim=(-0.02, 1.05))
    ax.set_title("Funciones de pertenencia de la ocupación")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig


def fig_funciones_desvio():
    X, _, desvio = ld.curvas_pertenencia()
    fig, ax = plt.subplots(figsize=(6, 3.2))
    for termino, mu in desvio.items():
        ax.plot(X, mu, label=f"desvío {termino}")
    ax.set(xlabel="Nivel de desvío", ylabel="Grado de pertenencia", ylim=(-0.02, 1.05))
    ax.set_title("Funciones de pertenencia del desvío")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig


def fig_mamdani(o):
    """Consecuentes recortados, salida agregada y centroide para la ocupación o."""
    grados, activaciones, agregada, d_final = ld.inferir_desvio(o)
    recortadas = ld.recortar_consecuentes(activaciones)
    fig, ax = plt.subplots(figsize=(6, 3.4))
    for nombre, mu in recortadas.items():
        ax.plot(ld.X, mu, linestyle="--", label=f"{nombre} recortada")
    ax.fill_between(ld.X, agregada, alpha=0.25, color="tab:gray", label="salida agregada")
    ax.axvline(d_final, color="black", linewidth=1.5, label=f"centroide = {d_final:.2f}")
    ax.set(xlabel="Nivel de desvío", ylabel="Pertenencia", ylim=(-0.02, 1.05))
    ax.set_title(f"Ciclo Mamdani con ocupación {o} %")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig


def fig_curva_respuesta():
    """Ampliación A2: regla rígida (escalón) frente al desvío difuso de 0 a 100 %."""
    ocupaciones = np.arange(0, 101)
    difuso = [ld.inferir_desvio(int(o))[3] for o in ocupaciones]
    escalon = [100 if ld.regla_rigida(o) else 0 for o in ocupaciones]
    fig, ax = plt.subplots(figsize=(6, 3.4))
    ax.step(ocupaciones, escalon, where="post", label="regla rígida (> 80 → desviar)")
    ax.plot(ocupaciones, difuso, label="desvío difuso (centroide)")
    ax.axvline(ld.UMBRAL_RIGIDO, color="gray", linestyle=":")
    ax.set(xlabel="Ocupación (%)", ylabel="Desvío (0-100)")
    ax.set_title("Respuesta escalonada frente a respuesta gradual")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig


def guardar_todas(carpeta="figuras"):
    os.makedirs(carpeta, exist_ok=True)
    figuras = {
        "fig1_ocupacion.png": fig_funciones_ocupacion(),
        "fig2_desvio.png": fig_funciones_desvio(),
        "fig3_mamdani_80.png": fig_mamdani(80),
        "fig4_curva_respuesta.png": fig_curva_respuesta(),
    }
    for nombre, fig in figuras.items():
        fig.savefig(os.path.join(carpeta, nombre), dpi=150)
        plt.close(fig)
    return list(figuras)


if __name__ == "__main__":
    print("Figuras guardadas:", ", ".join(guardar_todas()))