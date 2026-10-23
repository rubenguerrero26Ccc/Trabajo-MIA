# S02. Sistema experto explicable para la gestión de incidencias en un centro logístico

## Integrantes

| Integrante | Responsable principal de |
|---|---|
| Hugo Silva | `motor_reglas.py`: base de reglas, motor de encadenamiento hacia adelante y regla propia R7 |
| Ruben Guerrero | `logica_difusa.py` y `graficos.py`: funciones de pertenencia, ciclo Mamdani y apartado 5 |
| Leandro Ligero | `main.py` (consola) y `app.py` (Streamlit), README y ZIP |
| Leonardo Acchioni | `pruebas.py`, casos A-D, inferencia manual P-104 e informe |

## Estructura del proyecto

```
grupo_X_practica_s02/
├── motor_reglas.py     # hechos, reglas (R1-R7), motor de inferencia, traza y "por qué no"
├── logica_difusa.py    # funciones de pertenencia y ciclo Mamdani (sin dependencias del motor)
├── graficos.py         # figuras (matplotlib) y curva de respuesta (A2)
├── main.py             # interfaz de consola (obligatoria)
├── app.py              # interfaz Streamlit (opcional, A10)
├── pruebas.py          # pruebas automatizadas (A9)
├── README.md
└── informe_grupo_X_s02.docx
```

Dos cadenas independientes; la interfaz solo llama a funciones y muestra resultados:

```
base de conocimiento -> motor de inferencia -> interfaz
funciones de pertenencia -> inferencia difusa -> interfaz
```

## Instalación de dependencias

Requiere Python 3.9 o superior.

```
pip install numpy matplotlib
pip install streamlit      # solo si se quiere usar app.py
```

## Cómo ejecutar

```
python main.py             # interfaz de consola: menú con las dos zonas
python pruebas.py          # batería de pruebas (también vale: pytest pruebas.py)
python graficos.py         # guarda las figuras en la carpeta figuras/
streamlit run app.py       # interfaz Streamlit (opcional)
```

## Ampliaciones

- **A10** Interfaz Streamlit (`app.py`).
- **A9** Pruebas automatizadas (`pruebas.py`).
- **A2** Curva de respuesta: desvío difuso frente al escalón de la regla rígida (`graficos.py`).
- **A6** Explicación «por qué no» de una regla (`explicar_por_que_no` en `motor_reglas.py`).