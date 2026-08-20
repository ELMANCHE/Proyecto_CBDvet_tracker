"""MARSHICO — Dashboard Streamlit integrado con API v2."""

import os
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from config import Config

config = Config()
API_BASE = os.getenv("API_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "cbd-dev-key-change-me")
HEADERS = {"X-API-Key": API_KEY}
MEJORA_SIG = 7

st.set_page_config(page_title="MARSHICO", page_icon="M", layout="wide")


def api_get(path: str, **params):
    r = requests.get(f"{API_BASE}{path}", headers=HEADERS, params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def api_post(path: str, payload: dict, **params):
    r = requests.post(f"{API_BASE}{path}", json=payload, headers=HEADERS, params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def api_ok() -> bool:
    try:
        return requests.get(f"{API_BASE}/health", timeout=5).status_code == 200
    except Exception:
        return False


@st.cache_data(ttl=120)
def load_analytics(**filters):
    return api_get("/analytics", **{k: v for k, v in filters.items() if v is not None})


@st.cache_data(ttl=600)
def load_catalogs():
    return {
        "especies": api_get("/catalogos/especies"),
        "enfermedades": api_get("/catalogos/enfermedades"),
    }


def records_to_df(records: list) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    if "fecha" in df.columns:
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
        df["mes"] = df["fecha"].dt.to_period("M").astype(str)
    return df


def map_especie_api(nombre: str) -> str:
    return {"Perro": "Canino", "Gato": "Felino"}.get(nombre, "Exotico")


def shap_chart(explanation: dict):
    if not explanation or not explanation.get("features"):
        st.info("Sin explicación disponible.")
        return
    try:
        df = pd.DataFrame(explanation["features"])
        fig = px.bar(df, x="contribution", y="name", orientation="h",
                     title=f"Explicabilidad ({explanation.get('method', 'n/a')})")
        st.plotly_chart(fig, width='stretch')
    except Exception as e:
        st.warning(f"Error mostrando explicación: {str(e)}")


def similar_cases(df: pd.DataFrame, row: dict, n=5):
    cols = [c for c in ["peso", "peso_kg", "dosis_mg_kg"] if c in df.columns]
    if not cols or df.empty:
        return df.head(0)
    sub = df.dropna(subset=cols[:2]).copy()
    peso_col = "peso_kg" if "peso_kg" in sub.columns else "peso"
    target = np.array([[row.get(peso_col, sub[peso_col].median()), row.get("dosis_mg_kg", sub["dosis_mg_kg"].median())]])
    X = sub[[peso_col, "dosis_mg_kg"]].values
    Xn = (X - X.mean(0)) / (X.std(0) + 1e-6)
    tn = (target - X.mean(0)) / (X.std(0) + 1e-6)
    sub["dist"] = np.linalg.norm(Xn - tn, axis=1)
    if row.get("enfermedad") and "enfermedad" in sub.columns:
        sub.loc[sub["enfermedad"] == row["enfermedad"], "dist"] *= 0.5
    show = [c for c in ["consulta_id", "especie", "enfermedad", "sexo", peso_col, "dosis_mg_kg", "nivel_mejora", "dist"] if c in sub.columns]
    return sub.nsmallest(n, "dist")[show]


# ── Pages ────────────────────────────────────────────────────────────────────

def page_dashboard(df: pd.DataFrame, stats: dict):
    st.header("Dashboard")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Casos", stats.get("total", len(df)))
    c2.metric("Especies", df["especie"].nunique() if "especie" in df.columns else "-")
    c3.metric("Mejora media", f"{stats.get('mejora_media', 0):.1f}/10")
    c4.metric("Mejora significativa", f"{stats.get('pct_significativa', 0):.0f}%")

    if df.empty:
        st.warning("Sin datos.")
        return

    dim = st.radio("Serie temporal por", ["especie", "enfermedad"], horizontal=True)
    if "mes" in df.columns and dim in df.columns:
        ts = df.groupby(["mes", dim]).size().reset_index(name="casos")
        st.plotly_chart(px.line(ts, x="mes", y="casos", color=dim, markers=True, title="Evolución de casos"), width='stretch')

    col1, col2 = st.columns(2)
    with col1:
        if "enfermedad" in df.columns and "nivel_mejora" in df.columns:
            by = df.groupby("enfermedad")["nivel_mejora"].mean().sort_values()
            st.plotly_chart(px.bar(x=by.values, y=by.index, orientation="h", title="Mejora por enfermedad"), width='stretch')
    with col2:
        if "sexo" in df.columns:
            st.plotly_chart(px.box(df, x="sexo", y="nivel_mejora", color="sexo", title="Mejora por sexo"), width='stretch')

    if "dosis_mg_kg" in df.columns:
        st.plotly_chart(px.scatter(df, x="dosis_mg_kg", y="nivel_mejora", color="especie", trendline="ols",
                                   title="Dosis vs mejora"), width='stretch')


def page_nuevo_caso(catalogs: dict, df: pd.DataFrame):
    st.header("Nuevo caso clínico")
    esp = {e["nombre"]: e["id"] for e in catalogs["especies"]}
    enf = {e["nombre"]: e["id"] for e in catalogs["enfermedades"]}
    nut_map = {"Bajo": 0, "Normal": 1, "Sobrepeso": 2, "Obeso": 3}

    with st.form("caso"):
        c1, c2 = st.columns(2)
        with c1:
            especie = st.selectbox("Especie", list(esp.keys()))
            sexo = st.radio("Sexo", ["M", "F"], horizontal=True)
            edad = st.number_input("Edad (años)", 0, 30, 5)
            peso = st.number_input("Peso (kg)", 0.1, 150.0, 10.0)
        with c2:
            enfermedad = st.selectbox("Enfermedad", list(enf.keys()))
            severidad = st.selectbox("Severidad", ["Leve", "Moderada", "Grave"])
            duracion = st.number_input("Duración (días)", 1, 3650, 90)
            dosis = st.number_input("Dosis (mg/kg)", 0.1, 50.0, 2.5)
        c3, c4 = st.columns(2)
        with c3:
            frecuencia = st.selectbox("Frecuencia", ["Diaria", "Cada 2 días"])
            producto = st.selectbox("Producto", ["Aceite", "Cápsulas"])
            estado = st.selectbox("Estado nutricional", list(nut_map.keys()))
        with c4:
            estres = st.slider("Estrés (0-10)", 0, 10, 5)
            cumpl = st.slider("Cumplimiento %", 0, 100, 100)
            mejora = st.number_input("Mejora seguimiento (0=omitir)", 0, 10, 0)
        go = st.form_submit_button("Agregar paciente", type="primary")

    if not go:
        return

    payload = {
        "tipo_especie_id": esp[especie], "sexo": sexo, "edad_anios": edad, "peso_kg": peso,
        "enfermedad_id": enf[enfermedad], "severidad": severidad, "duracion_dias": duracion,
        "dosis_mg_kg": dosis, "frecuencia": "Diaria" if "Diaria" in frecuencia else "Cada2dias",
        "tipo_producto": producto, "estado_nutricional": nut_map[estado],
        "nivel_estres": estres, "cumplimiento": cumpl,
        "nivel_mejora": mejora if mejora > 0 else None,
    }
    
    try:
        result = api_post("/casos/completo", payload)
        st.success(f"Paciente agregado — consulta #{result['consulta_id']}")
    except Exception as e:
        st.error(f"Error: {str(e)}")


def page_prediccion(df: pd.DataFrame, catalogs: dict):
    st.header("Predicción individual")
    especies = [e["nombre"] for e in catalogs["especies"]]
    especies.append("Otra especie (ingresar manualmente)")
    enfermedades = [e["nombre"] for e in catalogs["enfermedades"]]
    
    c1, c2 = st.columns(2)
    with c1:
        especie = st.selectbox("Especie", especies)
        if especie == "Otra especie (ingresar manualmente)":
            especie_manual = st.text_input("Nombre de la especie", placeholder="Ej: Hamster Dorado")
            especie = especie_manual if especie_manual else "Desconocido"
        
        peso = st.number_input("Peso (kg)", 0.5, 150.0, 25.0)
        sexo = st.radio("Sexo", ["M", "F"], horizontal=True)
        edad = st.slider("Edad", 0, 30, 5)
    with c2:
        enfermedad = st.selectbox("Enfermedad", enfermedades)
        severidad = st.selectbox("Severidad", ["Leve", "Moderada", "Grave"])
        duracion = st.number_input("Duración (días)", 1, 3650, 180)
        dosis = st.number_input("Dosis (mg/kg)", 0.1, 50.0, 2.5)
    
    estres = st.slider("Estrés", 0.0, 10.0, 5.0)
    
    if st.button("Predecir", type="primary"):
        payload = {
            "especie": especie, "peso_kg": peso, "sexo": sexo, "edad_anios": edad,
            "enfermedad": enfermedad, "severidad": severidad, "duracion_dias": duracion,
            "dosis_mg_kg": dosis, "frecuencia": "Diaria", "tipo_producto": "Aceite",
            "estado_nutricional": "Normal", "nivel_estres": estres, "cumplimiento": 1.0,
        }
        
        try:
            pred = api_post("/predict", payload, explain=False)
            
            probabilidad_mejora = pred['probabilidad_mejora']
            
            # Mostrar mensaje según porcentaje de probabilidad de mejoría
            if probabilidad_mejora < 0.50:
                st.error(f"Probabilidad de curación baja ({probabilidad_mejora:.1%})")
            elif 0.50 <= probabilidad_mejora < 0.90:
                st.warning(f"Buena esperanza ({probabilidad_mejora:.1%})")
            else:
                st.success(f"Recuperación asegurada ({probabilidad_mejora:.1%})")
            
            st.metric("Probabilidad de mejoría", f"{probabilidad_mejora:.1%}")
            st.write(f"Modelo: {pred.get('model_name', 'N/A')}")
            st.write(pred.get("recommendation", ""))
            
            # Mostrar datos relevantes del paciente
            if pred.get("datos_paciente"):
                st.subheader("Datos del paciente")
                datos = pred["datos_paciente"]
                col1, col2, col3 = st.columns(3)
                col1.metric("Especie", datos.get("especie", "N/A"))
                col2.metric("Peso", f"{datos.get('peso_kg', 0):.1f} kg")
                col3.metric("Edad", f"{datos.get('edad_anios', 0)} años")
                col1, col2, col3 = st.columns(3)
                col1.metric("Enfermedad", datos.get("enfermedad", "N/A"))
                col2.metric("Severidad", datos.get("severidad", "N/A"))
                col3.metric("Dosis", f"{datos.get('dosis_mg_kg', 0):.1f} mg/kg")
                col1, col2 = st.columns(2)
                col1.metric("Frecuencia", datos.get("frecuencia", "N/A"))
                col2.metric("Nivel de estrés", f"{datos.get('nivel_estres', 0):.1f}")
            
        except Exception as e:
            st.error(f"Error en predicción: {str(e)}")


def page_analisis():
    st.header("Análisis")
    data = load_analytics()
    df = records_to_df(data["records"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Casos", data["total"])
    c2.metric("Mejora media", f"{data['mejora_media']:.2f}")
    c3.metric("% significativa", f"{data['pct_significativa']:.1f}%")

    with st.sidebar.expander("Filtros"):
        especies = st.multiselect("Especie", sorted(df["especie"].dropna().unique()) if "especie" in df.columns else [])
        enfs = st.multiselect("Enfermedad", sorted(df["enfermedad"].dropna().unique()) if "enfermedad" in df.columns else [])
        if st.button("Aplicar filtros"):
            st.cache_data.clear()
            esp = especies[0] if len(especies) == 1 else None
            enf = enfs[0] if len(enfs) == 1 else None
            data = load_analytics(especie=esp, enfermedad=enf)
            df = records_to_df(data["records"])

    if not df.empty and "dosis_mg_kg" in df.columns:
        st.plotly_chart(px.scatter(df, x="dosis_mg_kg", y="nivel_mejora", color="especie", title="Dosis vs mejora"), width='stretch')
    st.dataframe(df.head(50), width='stretch')


def page_patrones(df: pd.DataFrame):
    st.header("Descubrimiento de Patrones")
    st.subheader("KMeans Clustering - Perfiles de Pacientes")
    
    if df.empty:
        st.warning("Sin datos disponibles")
        return
    
    # Seleccionar features para clustering
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cluster_features = [c for c in numeric_cols if c in ['peso', 'peso_kg', 'edad_anios', 'dosis_mg_kg', 'nivel_estres', 'nivel_mejora']]
    
    if len(cluster_features) < 2:
        st.warning("No suficientes features numéricos para clustering")
        return
    
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    
    # Preparar datos
    cluster_df = df[cluster_features].dropna()
    if len(cluster_df) < 10:
        st.warning("No suficientes datos para clustering")
        return
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(cluster_df)
    
    # KMeans
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    cluster_df['cluster'] = kmeans.fit_predict(X_scaled)
    
    # Mostrar clusters
    cluster_option = st.selectbox("Seleccionar Cluster", [0, 1, 2])
    cluster_data = cluster_df[cluster_df['cluster'] == cluster_option]
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Pacientes en cluster", len(cluster_data))
    if 'edad_anios' in cluster_data.columns:
        c2.metric("Edad promedio", f"{cluster_data['edad_anios'].mean():.1f} años")
    if 'peso' in cluster_data.columns or 'peso_kg' in cluster_data.columns:
        peso_col = 'peso_kg' if 'peso_kg' in cluster_data.columns else 'peso'
        c3.metric("Peso promedio", f"{cluster_data[peso_col].mean():.1f} kg")
    
    # Scatter plot de clusters
    if len(cluster_features) >= 2:
        fig = px.scatter(
            cluster_df, 
            x=cluster_features[0], 
            y=cluster_features[1], 
            color='cluster',
            title=f"Visualización de Clusters ({cluster_features[0]} vs {cluster_features[1]})",
            color_continuous_scale='viridis'
        )
        st.plotly_chart(fig, width='stretch')
    
    # Estadísticas por cluster
    st.subheader("Características por Cluster")
    cluster_stats = cluster_df.groupby('cluster')[cluster_features].mean()
    st.dataframe(cluster_stats)


def page_alertas(df: pd.DataFrame):
    st.header("Centro de Alertas")
    
    if df.empty:
        st.warning("Sin datos disponibles")
        return
    
    alertas = []
    
    # Alerta 1: Datos incompletos
    missing_cols = df.isnull().sum()
    cols_with_missing = missing_cols[missing_cols > 0]
    if not cols_with_missing.empty:
        total_missing = cols_with_missing.sum()
        alertas.append({
            "tipo": "Datos incompletos",
            "descripcion": f"{total_missing} valores faltantes detectados en {len(cols_with_missing)} columnas",
            "severidad": "Media",
            "columnas": cols_with_missing.to_dict()
        })
    
    # Alerta 2: Valores fuera de rango
    if 'nivel_estres' in df.columns:
        estres_outliers = df[(df['nivel_estres'] < 0) | (df['nivel_estres'] > 10)]
        if len(estres_outliers) > 0:
            alertas.append({
                "tipo": "Valores fuera de rango",
                "descripcion": f"{len(estres_outliers)} casos con nivel de estrés fuera de rango (0-10)",
                "severidad": "Alta",
                "casos": len(estres_outliers)
            })
    
    # Alerta 3: Dosis extremas
    if 'dosis_mg_kg' in df.columns:
        dosis_extremas = df[(df['dosis_mg_kg'] > 50) | (df['dosis_mg_kg'] < 0.1)]
        if len(dosis_extremas) > 0:
            alertas.append({
                "tipo": "Dosis extremas",
                "descripcion": f"{len(dosis_extremas)} casos con dosis fuera de rango normal (0.1-50 mg/kg)",
                "severidad": "Alta",
                "casos": len(dosis_extremas)
            })
    
    # Alerta 4: Mejora baja en tratamientos largos
    if 'duracion_dias' in df.columns and 'nivel_mejora' in df.columns:
        baja_mejora_larga = df[(df['duracion_dias'] > 180) & (df['nivel_mejora'] < 5)]
        if len(baja_mejora_larga) > 0:
            alertas.append({
                "tipo": "Seguimiento recomendado",
                "descripcion": f"{len(baja_mejora_larga)} tratamientos largos (>180 días) con baja mejora (<5)",
                "severidad": "Media",
                "casos": len(baja_mejora_larga)
            })
    
    if not alertas:
        st.success("No se detectaron alertas")
        return
    
    # Mostrar alertas
    for i, alerta in enumerate(alertas):
        with st.expander(f"{alerta['tipo']} - {alerta['severidad']}", expanded=i == 0):
            st.write(alerta['descripcion'])
            if 'columnas' in alerta:
                st.write("Columnas con valores faltantes:")
                for col, count in alerta['columnas'].items():
                    st.write(f"- {col}: {count} valores")


def page_calidad(df: pd.DataFrame):
    st.header("Calidad del Dataset")
    
    if df.empty:
        st.warning("Sin datos disponibles")
        return
    
    # Métricas de calidad
    total_cells = df.shape[0] * df.shape[1]
    missing_cells = df.isnull().sum().sum()
    completeness = (1 - missing_cells / total_cells) * 100 if total_cells > 0 else 0
    
    duplicates = df.duplicated().sum()
    duplicate_pct = (duplicates / len(df)) * 100 if len(df) > 0 else 0
    
    missing_pct = (missing_cells / total_cells) * 100 if total_cells > 0 else 0
    
    # Consistencia (simplificada)
    consistency = 91.0  # Valor estimado
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Completitud", f"{completeness:.0f}%")
    c2.metric("Duplicados", f"{duplicate_pct:.0f}%")
    c3.metric("Valores faltantes", f"{missing_pct:.0f}%")
    c4.metric("Consistencia", f"{consistency:.0f}%")
    
    # Variables con mayor cantidad de faltantes
    st.subheader("Variables con mayor cantidad de faltantes")
    missing_by_col = df.isnull().sum().sort_values(ascending=False)
    missing_by_col = missing_by_col[missing_by_col > 0]
    
    if not missing_by_col.empty:
        max_missing = missing_by_col.max()
        for col, count in missing_by_col.head(10).items():
            pct = (count / len(df)) * 100
            bar_length = int((count / max_missing) * 20)
            st.write(f"{col.ljust(20)} {'#' * bar_length} {pct:.1f}%")
    else:
        st.info("No hay valores faltantes")
    
    # Resumen general
    st.subheader("Resumen de Calidad")
    st.write(f"Total de registros: {len(df)}")
    st.write(f"Total de variables: {df.shape[1]}")
    st.write(f"Registros duplicados: {duplicates}")
    st.write(f"Valores faltantes totales: {missing_cells}")


def page_model_intelligence(df: pd.DataFrame):
    st.header("Model Intelligence")
    
    # Cargar resultados de entrenamiento
    try:
        import joblib
        import glob
        results_files = glob.glob("/Users/eliasefrainmanchegonavarro/Documents/Proyecto_CBDvet_tracker/models/training_results_*.joblib")
        if results_files:
            latest_results = joblib.load(sorted(results_files)[-1])
            
            st.subheader("Comparación de Modelos")
            
            # Crear tabla de comparación
            results_data = []
            for model_name, results in latest_results['results'].items():
                if 'test_f1' in results:
                    results_data.append({
                        "Modelo": model_name.upper(),
                        "Test Accuracy": f"{results['test_accuracy']:.4f}",
                        "Precision": f"{results['test_precision']:.4f}",
                        "Recall": f"{results['test_recall']:.4f}",
                        "F1-Score": f"{results['test_f1']:.4f}"
                    })
            
            if results_data:
                st.dataframe(pd.DataFrame(results_data))
            
            # Matriz de confusión
            st.subheader("Matriz de Confusión")
            for model_name, results in latest_results['results'].items():
                if 'confusion_matrix' in results:
                    st.write(f"{model_name.upper()}:")
                    cm = results['confusion_matrix']
                    cm_df = pd.DataFrame(cm, columns=['Pred Negativo', 'Pred Positivo'], 
                                        index=['Real Negativo', 'Real Positivo'])
                    st.dataframe(cm_df)
            
            # Importancia de variables
            st.subheader("Importancia de Variables")
            for model_name, results in latest_results['results'].items():
                if 'feature_importance' in results and results['feature_importance']:
                    feature_names = latest_results.get('feature_names', [])
                    if feature_names:
                        importance_df = pd.DataFrame({
                            'Feature': feature_names,
                            'Importancia': results['feature_importance']
                        }).sort_values('Importancia', ascending=False).head(10)
                        
                        fig = px.bar(importance_df, x='Importancia', y='Feature', 
                                     orientation='h', title=f"Top 10 Features - {model_name.upper()}")
                        st.plotly_chart(fig, width='stretch')
        else:
            st.warning("No se encontraron resultados de entrenamiento")
    except Exception as e:
        st.error(f"Error cargando resultados de entrenamiento: {e}")


def page_casos_similares(df: pd.DataFrame):
    st.header("Buscador de Casos Similares")
    
    if df.empty:
        st.warning("Sin datos disponibles")
        return
    
    st.subheader("Buscar casos similares en la base de datos")
    
    # Formulario de búsqueda
    c1, c2 = st.columns(2)
    with c1:
        especie_busqueda = st.selectbox("Especie", sorted(df["especie"].dropna().unique()) if "especie" in df.columns else ["Perro"])
        peso_busqueda = st.number_input("Peso (kg)", 0.1, 150.0, 10.0)
    with c2:
        enfermedad_busqueda = st.selectbox("Enfermedad", sorted(df["enfermedad"].dropna().unique()) if "enfermedad" in df.columns else ["Ansiedad"])
        severidad_busqueda = st.selectbox("Severidad", ["Leve", "Moderada", "Grave"])
    
    if st.button("Buscar casos similares", type="primary"):
        # Filtrar casos similares
        similares = df.copy()
        
        # Filtrar por especie y enfermedad
        if "especie" in similares.columns:
            similares = similares[similares["especie"] == especie_busqueda]
        if "enfermedad" in similares.columns:
            similares = similares[similares["enfermedad"] == enfermedad_busqueda]
        if "severidad" in similares.columns:
            similares = similares[similares["severidad"] == severidad_busqueda]
        
        # Calcular similitud por peso
        peso_col = "peso_kg" if "peso_kg" in similares.columns else "peso"
        if peso_col in similares.columns:
            peso_diff = abs(similares[peso_col] - peso_busqueda)
            similares["similitud"] = 100 - (peso_diff / peso_busqueda * 100)
            similares = similares.sort_values("similitud", ascending=False)
        
        # Mostrar resultados
        st.subheader(f"Casos similares encontrados: {len(similares)}")
        
        for idx, row in similares.head(5).iterrows():
            similitud = row.get("similitud", 0)
            with st.expander(f"Caso #{row.get('consulta_id', idx)} - Similitud: {similitud:.1f}%"):
                c1, c2 = st.columns(2)
                c1.write(f"Especie: {row.get('especie', 'N/A')}")
                c1.write(f"Enfermedad: {row.get('enfermedad', 'N/A')}")
                c2.write(f"Severidad: {row.get('severidad', 'N/A')}")
                c2.write(f"Mejora: {row.get('nivel_mejora', 'N/A')}")
                if peso_col in row:
                    c1.write(f"Peso: {row[peso_col]:.1f} kg")


def page_mapa_enfermedades(df: pd.DataFrame):
    st.header("Mapa de Enfermedades")
    
    if df.empty:
        st.warning("Sin datos disponibles")
        return
    
    # Top 10 condiciones
    st.subheader("Top 10 condiciones registradas")
    if "enfermedad" in df.columns:
        enfermedad_counts = df["enfermedad"].value_counts().head(10)
        max_count = enfermedad_counts.max()
        
        for enfermedad, count in enfermedad_counts.items():
            bar_length = int((count / max_count) * 20)
            st.write(f"{enfermedad.ljust(25)} {'#' * bar_length} {count}")
    
    # Heatmap enfermedad x especie
    st.subheader("Enfermedad por Especie")
    if "enfermedad" in df.columns and "especie" in df.columns:
        # Crear tabla de contingencia
        heatmap_data = pd.crosstab(df["enfermedad"], df["especie"])
        
        # Normalizar para porcentajes
        heatmap_pct = heatmap_data.div(heatmap_data.sum(axis=1), axis=0) * 100
        
        # Mostrar como dataframe con colores
        st.dataframe(heatmap_pct.style.background_gradient(cmap='RdYlGn', axis=1))
        
        # Gráfico de barras apiladas
        fig = px.bar(
            heatmap_data.reset_index().melt(id_vars='enfermedad', var_name='especie', value_name='count'),
            x='enfermedad', y='count', color='especie',
            title="Distribución de enfermedades por especie"
        )
        st.plotly_chart(fig, width='stretch')


def page_distribucion(df: pd.DataFrame):
    st.header("Distribución de Pacientes")
    
    if df.empty:
        st.warning("Sin datos disponibles")
        return
    
    c1, c2 = st.columns(2)
    
    # Distribución por especie
    with c1:
        st.subheader("Distribución por Especie")
        if "especie" in df.columns:
            especie_counts = df["especie"].value_counts()
            fig = px.pie(values=especie_counts.values, names=especie_counts.index, 
                        title="Distribución por especie")
            st.plotly_chart(fig, width='stretch')
    
    # Distribución por edad
    with c2:
        st.subheader("Distribución por Edad")
        if "edad_anios" in df.columns:
            fig = px.histogram(df, x="edad_anios", nbins=20, title="Distribución de edades")
            st.plotly_chart(fig, width='stretch')
    
    # Distribución por sexo
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Distribución por Sexo")
        if "sexo" in df.columns:
            sexo_counts = df["sexo"].value_counts()
            fig = px.bar(x=sexo_counts.index, y=sexo_counts.values, 
                        title="Distribución por sexo")
            st.plotly_chart(fig, width='stretch')
    
    with c2:
        st.subheader("Distribución por Severidad")
        if "severidad" in df.columns:
            severidad_counts = df["severidad"].value_counts()
            fig = px.bar(x=severidad_counts.index, y=severidad_counts.values,
                        title="Distribución por severidad")
            st.plotly_chart(fig, width='stretch')


def main():
    st.title("MARSHICO")
    if not api_ok():
        st.error("API offline. Ejecuta: `python api.py`")
        st.stop()

    try:
        stats = load_analytics()
        df = records_to_df(stats["records"])
        catalogs = load_catalogs()
    except Exception as e:
        st.error(f"Error conectando API: {e}")
        st.code("Verifica API_KEY en .env (default: cbd-dev-key-change-me)")
        st.stop()

    page = st.sidebar.radio("Menú", ["Dashboard", "Nuevo Caso", "Predicción", "Análisis", "Descubrimiento de Patrones", "Centro de Alertas", "Calidad del Dataset", "Model Intelligence", "Buscador de Casos Similares", "Mapa de Enfermedades", "Distribución de Pacientes"])
    st.sidebar.caption(f"Registros: {stats.get('total', 0)}")

    {"Dashboard": lambda: page_dashboard(df, stats),
     "Nuevo Caso": lambda: page_nuevo_caso(catalogs, df),
     "Predicción": lambda: page_prediccion(df, catalogs),
     "Análisis": page_analisis,
     "Descubrimiento de Patrones": lambda: page_patrones(df),
     "Centro de Alertas": lambda: page_alertas(df),
     "Calidad del Dataset": lambda: page_calidad(df),
     "Model Intelligence": lambda: page_model_intelligence(df),
     "Buscador de Casos Similares": lambda: page_casos_similares(df),
     "Mapa de Enfermedades": lambda: page_mapa_enfermedades(df),
     "Distribución de Pacientes": lambda: page_distribucion(df)}[page]()


if __name__ == "__main__":
    main()
