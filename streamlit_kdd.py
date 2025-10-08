"""Dashboard Streamlit para mostrar analíticas KDD en tiempo real."""

from __future__ import annotations

import json
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from analisis_kdd import CACHE_FILE, extract_from_postgres, run_once

st.set_page_config(page_title="Analítica CBD Veterinaria", layout="wide")
REFRESH_INTERVAL = int(st.secrets.get("analytics_refresh", 30000))


@st.cache_data(show_spinner=False, ttl=max(REFRESH_INTERVAL // 1000, 5))
def load_cache() -> dict:
    if not CACHE_FILE.exists():
        result = run_once()
        if not result:
            return {}
    try:
        return json.loads(CACHE_FILE.read_text())
    except json.JSONDecodeError:
        return {}


def render_summary(data: dict) -> None:
    st.title("Analítica en tiempo real de tratamientos CBD veterinarios")
    generated_at = data.get("generated_at")
    if generated_at:
        timestamp = datetime.fromisoformat(generated_at)
        st.caption(f"Actualizado: {timestamp:%d/%m/%Y %H:%M:%S} UTC")

    totals = data.get("totals", {})
    especies = data.get("especies", {})
    tasa_exito = data.get("tasa_tratamiento_exitoso", {})

    col1, col2, col3 = st.columns(3)
    col1.metric("Consultas", totals.get("consultas", 0))
    col2.metric("Pacientes", totals.get("pacientes", 0))
    promedio_exito = (
        sum(tasa_exito.values()) / len(tasa_exito) if tasa_exito else 0
    )
    col3.metric("Tasa de éxito promedio", f"{promedio_exito:.1f}%")

    if especies:
        df_especies = pd.DataFrame(
            {"especie": list(especies.keys()), "conteo": list(especies.values())}
        )
        fig_especies = px.pie(
            df_especies,
            values="conteo",
            names="especie",
            title="Distribución por especie",
        )
        st.plotly_chart(fig_especies, use_container_width=True)

    if tasa_exito:
        df_tasa = pd.DataFrame(
            {
                "especie": list(tasa_exito.keys()),
                "tasa_exito": list(tasa_exito.values()),
            }
        )
        fig_tasa = px.bar(
            df_tasa,
            x="especie",
            y="tasa_exito",
            title="Tasa de éxito por especie",
            labels={"tasa_exito": "% éxito"},
        )
        st.plotly_chart(fig_tasa, use_container_width=True)


def render_clustering(data: dict) -> None:
    clustering = data.get("clustering", [])
    if not clustering:
        st.info("Aún no hay suficientes datos para clustering.")
        return

    df_clustering = pd.DataFrame(clustering)
    st.subheader("Clusters de pacientes")
    st.dataframe(df_clustering)

    fig = px.bar(
        df_clustering,
        x="cluster",
        y="conteo",
        hover_data=["edad_prom", "peso_prom", "dosis_prom"],
        title="Distribución de pacientes por cluster",
    )
    st.plotly_chart(fig, use_container_width=True)


def render_model(data: dict) -> None:
    modelo = data.get("modelo_predictivo", {})
    st.subheader("Modelo predictivo")
    st.metric("Accuracy", f"{modelo.get('accuracy', 0)*100:.1f}%")

    importancia = modelo.get("importancia_caracteristicas", [])
    if importancia:
        df_importancia = pd.DataFrame(importancia)
        fig_importancia = px.bar(
            df_importancia,
            x="importancia",
            y="caracteristica",
            orientation="h",
            title="Importancia de características",
        )
        st.plotly_chart(fig_importancia, use_container_width=True)

    matriz = modelo.get("matriz_confusion")
    if matriz:
        df_matriz = pd.DataFrame(matriz, columns=["Pred. No", "Pred. Sí"], index=["Real No", "Real Sí"])
        st.write("Matriz de confusión")
        st.dataframe(df_matriz)


def render_etl_log(data: dict) -> None:
    log_entries = data.get("etl_log", [])
    with st.expander("Bitácora de limpieza (ETL)"):
        if not log_entries:
            st.info("No se registraron reglas de limpieza en la última ejecución.")
            return

        for entry in log_entries:
            st.markdown(f"**Regla:** {entry.get('regla')}")
            st.write(entry.get("descripcion", ""))
            st.caption(f"Registros afectados: {entry.get('registros_afectados', 0)}")
            detalles = entry.get("detalles")
            if detalles:
                st.json(detalles)
            st.markdown("---")


def render_dataset() -> None:
    st.subheader("Datos crudos")
    df = extract_from_postgres()
    if df.empty:
        st.warning("No se encontraron registros en la base de datos.")
    else:
        st.dataframe(df.tail(100))


def main() -> None:
    st_autorefresh(interval=REFRESH_INTERVAL, key="analytics-refresh")
    data = load_cache()
    if not data:
        st.warning("No hay datos disponibles aún. Esperando próxima actualización...")
        if st.button("Forzar actualización"):
            run_once()
            st.experimental_rerun()
        return

    render_summary(data)
    render_clustering(data)
    render_model(data)
    render_etl_log(data)
    with st.expander("Ver dataset crudo"):
        render_dataset()


if __name__ == "__main__":
    main()
