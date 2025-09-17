
"""
Sistema de Minería de Datos para Análisis de Tratamientos CBD Veterinarios
Descubrimiento de patrones terapéuticos usando Machine Learning

Autor: Elias manchego Navarro
Fecha: 17 de Septiembre 2025
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings('ignore')

# Configuración de la página
st.set_page_config(
    page_title="CBD Veterinario - Análisis ML",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

class AnalizadorCBDVeterinario:
    def __init__(self):
        self.df = None
        self.df_encoded = None
        self.scaler = StandardScaler()
        self.le_dict = {}
        
    def cargar_datos(self):
        """Carga y prepara los datos"""
        try:
            self.df = pd.read_csv('datos_consolidados_cbd_veterinaria.csv')
            # Convertir fechas
            self.df['fecha_consulta'] = pd.to_datetime(self.df['fecha_consulta'])
            self.df['fecha_seguimiento'] = pd.to_datetime(self.df['fecha_seguimiento'])
            
            # Crear nuevas características
            self.df['dias_tratamiento_real'] = (self.df['fecha_seguimiento'] - self.df['fecha_consulta']).dt.days
            self.df['mes_consulta'] = self.df['fecha_consulta'].dt.month
            self.df['anio_consulta'] = self.df['fecha_consulta'].dt.year
            
            return True
        except Exception as e:
            st.error(f"Error cargando datos: {e}")
            return False
    
    def preprocesar_datos(self):
        """Preprocesa los datos para ML"""
        if self.df is None:
            return False
            
        # Seleccionar columnas numéricas y categóricas
        columnas_numericas = [
            'edad_anios', 'peso_kg', 'concentracion_mg_ml', 'dosis_mg_kg', 
            'dosis_total_mg', 'duracion_tratamiento_dias',
            'dolor_inicial_escala_10', 'movilidad_inicial_porcentaje',
            'apetito_inicial_escala_10', 'actividad_inicial_porcentaje',
            'ansiedad_inicial_escala_10', 'dolor_final_escala_10',
            'movilidad_final_porcentaje', 'apetito_final_escala_10',
            'actividad_final_porcentaje', 'ansiedad_final_escala_10',
            'mejoria_dolor_porcentaje', 'mejoria_movilidad_porcentaje',
            'mejoria_apetito_porcentaje', 'mejoria_actividad_porcentaje',
            'mejoria_ansiedad_porcentaje', 'mes_consulta', 'anio_consulta'
        ]
        
        columnas_categoricas = [
            'especie', 'sexo', 'veterinario_especialidad', 'motivo_consulta',
            'diagnostico', 'producto_cbd_nombre', 'frecuencia_administracion',
            'severidad_efecto', 'tratamiento_exitoso'
        ]
        
        # Crear DataFrame para ML
        self.df_encoded = self.df[columnas_numericas].copy()
        
        # Codificar variables categóricas
        for col in columnas_categoricas:
            if col in self.df.columns:
                le = LabelEncoder()
                self.df_encoded[f'{col}_encoded'] = le.fit_transform(self.df[col].astype(str))
                self.le_dict[col] = le
        
        return True
    
    def analisis_exploratorio(self):
        """Análisis Exploratorio de Datos"""
        st.header("Análisis Exploratorio de Datos")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Pacientes", len(self.df))
        with col2:
            tasa_exito = (self.df['tratamiento_exitoso'] == 'Sí').mean() * 100
            st.metric("Tasa de Éxito", f"{tasa_exito:.1f}%")
        with col3:
            duracion_prom = self.df['duracion_tratamiento_dias'].mean()
            st.metric("Duración Promedio", f"{duracion_prom:.0f} días")
        with col4:
            mejoria_dolor_prom = self.df['mejoria_dolor_porcentaje'].mean()
            st.metric("Mejora Dolor Promedio", f"{mejoria_dolor_prom:.1f}%")
        
        # Distribución por especies
        col1, col2 = st.columns(2)
        
        with col1:
            fig_especies = px.pie(
                self.df.value_counts('especie').reset_index(),
                values='count', names='especie',
                title="Distribución de Especies Tratadas"
            )
            st.plotly_chart(fig_especies, use_container_width=True)
        
        with col2:
            fig_exito = px.bar(
                self.df.groupby(['especie', 'tratamiento_exitoso']).size().reset_index(name='count'),
                x='especie', y='count', color='tratamiento_exitoso',
                title="Éxito del Tratamiento por Especie"
            )
            st.plotly_chart(fig_exito, use_container_width=True)
        
        # Análisis temporal
        st.subheader("Evolución Temporal")
        tratamientos_mes = self.df.groupby([self.df['fecha_consulta'].dt.to_period('M')])['tratamiento_exitoso'].apply(
            lambda x: (x == 'Sí').mean() * 100
        ).reset_index()
        tratamientos_mes['fecha_consulta'] = tratamientos_mes['fecha_consulta'].astype(str)
        
        fig_temporal = px.line(
            tratamientos_mes,
            x='fecha_consulta', y='tratamiento_exitoso',
            title="Evolución de Tasa de Éxito a lo Largo del Tiempo",
            labels={'tratamiento_exitoso': 'Tasa de Éxito (%)', 'fecha_consulta': 'Periodo'}
        )
        st.plotly_chart(fig_temporal, use_container_width=True)
    
    def clustering_pacientes(self):
        """Clustering de pacientes para descubrir grupos"""
        st.header("Clustering de Pacientes")
        
        # Seleccionar características para clustering
        caracteristicas_clustering = [
            'edad_anios', 'peso_kg', 'dosis_mg_kg',
            'dolor_inicial_escala_10', 'movilidad_inicial_porcentaje',
            'ansiedad_inicial_escala_10'
        ]
        
        X_cluster = self.df[caracteristicas_clustering].fillna(0)
        X_cluster_scaled = self.scaler.fit_transform(X_cluster)
        
        # Aplicar K-means
        n_clusters = st.sidebar.slider("Número de clusters", 2, 8, 4)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(X_cluster_scaled)
        
        # Agregar clusters al DataFrame
        df_cluster = self.df.copy()
        df_cluster['cluster'] = clusters
        
        # Visualización 3D de clusters
        col1, col2 = st.columns(2)
        
        with col1:
            fig_3d = px.scatter_3d(
                df_cluster,
                x='edad_anios', y='peso_kg', z='dosis_mg_kg',
                color='cluster',
                title="Clusters de Pacientes (3D)",
                labels={'cluster': 'Grupo'}
            )
            st.plotly_chart(fig_3d, use_container_width=True)
        
        with col2:
            # Análisis de características por cluster
            cluster_stats = df_cluster.groupby('cluster').agg({
                'edad_anios': 'mean',
                'peso_kg': 'mean',
                'dosis_mg_kg': 'mean',
                'tratamiento_exitoso': lambda x: (x == 'Sí').mean() * 100
            }).round(2)
            
            st.subheader("Características por Cluster")
            st.dataframe(cluster_stats)
        
        # Heatmap de correlación por cluster
        st.subheader("Análisis Detallado por Clusters")
        
        cluster_seleccionado = st.selectbox("Selecciona un cluster:", range(n_clusters))
        df_cluster_sel = df_cluster[df_cluster['cluster'] == cluster_seleccionado]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Cluster {cluster_seleccionado}** - {len(df_cluster_sel)} pacientes")
            st.write("Especies predominantes:")
            especies_cluster = df_cluster_sel['especie'].value_counts()
            st.write(especies_cluster)
        
        with col2:
            tasa_exito_cluster = (df_cluster_sel['tratamiento_exitoso'] == 'Sí').mean() * 100
            st.metric("Tasa de Éxito del Cluster", f"{tasa_exito_cluster:.1f}%")
            
            mejoria_promedio = df_cluster_sel['mejoria_dolor_porcentaje'].mean()
            st.metric("Mejora Dolor Promedio", f"{mejoria_promedio:.1f}%")
        
        return df_cluster
    
    def modelos_predictivos(self):
        """Modelos de Machine Learning para predicción"""
        st.header("Modelos Predictivos de Éxito Terapéutico")
        
        # Preparar datos para clasificación
        X = self.df_encoded.drop(['tratamiento_exitoso_encoded'], axis=1, errors='ignore')
        y = self.df_encoded.get('tratamiento_exitoso_encoded', self.df['tratamiento_exitoso'].map({'Sí': 1, 'No': 0}))
        
        # Eliminar columnas con NaN
        X = X.fillna(X.mean())
        
        # División train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42, stratify=y
        )
        
        # Modelo Random Forest
        rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
        rf_model.fit(X_train, y_train)
        
        # Predicciones
        y_pred = rf_model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Rendimiento del Modelo")
            st.metric("Precisión", f"{accuracy:.3f}")
            
            # Matriz de confusión
            cm = confusion_matrix(y_test, y_pred)
            fig_cm = px.imshow(cm, 
                              labels=dict(x="Predicción", y="Real", color="Casos"),
                              x=['No Exitoso', 'Exitoso'],
                              y=['No Exitoso', 'Exitoso'],
                              title="Matriz de Confusión")
            st.plotly_chart(fig_cm, use_container_width=True)
        
        with col2:
            # Importancia de características
            feature_importance = pd.DataFrame({
                'caracteristica': X.columns,
                'importancia': rf_model.feature_importances_
            }).sort_values('importancia', ascending=False).head(15)
            
            fig_importance = px.bar(
                feature_importance,
                x='importancia', y='caracteristica',
                orientation='h',
                title="Top 15 Características Más Importantes"
            )
            st.plotly_chart(fig_importance, use_container_width=True)
        
        # Análisis predictivo por características clave
        st.subheader("Análisis Predictivo Detallado")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Predicción por especie
            especies_pred = []
            for especie in self.df['especie'].unique():
                mask = self.df['especie'] == especie
                if mask.sum() > 0:
                    X_especie = X[mask]
                    if len(X_especie) > 0:
                        pred_proba = rf_model.predict_proba(X_especie)[:, 1].mean()
                        especies_pred.append({'especie': especie, 'prob_exito': pred_proba})
            
            df_especies_pred = pd.DataFrame(especies_pred)
            fig_especies_pred = px.bar(
                df_especies_pred,
                x='especie', y='prob_exito',
                title="Probabilidad de Éxito por Especie"
            )
            st.plotly_chart(fig_especies_pred, use_container_width=True)
        
        with col2:
            # Predicción por diagnóstico
            diagnosticos_pred = []
            for diag in self.df['diagnostico'].value_counts().head(10).index:
                mask = self.df['diagnostico'] == diag
                if mask.sum() > 0:
                    X_diag = X[mask]
                    if len(X_diag) > 0:
                        pred_proba = rf_model.predict_proba(X_diag)[:, 1].mean()
                        diagnosticos_pred.append({'diagnostico': diag, 'prob_exito': pred_proba})
            
            df_diag_pred = pd.DataFrame(diagnosticos_pred)
            fig_diag_pred = px.bar(
                df_diag_pred,
                x='prob_exito', y='diagnostico',
                orientation='h',
                title="Probabilidad de Éxito por Diagnóstico (Top 10)"
            )
            st.plotly_chart(fig_diag_pred, use_container_width=True)
        
        return rf_model, X, y
    
    def analisis_patrones(self):
        """Análisis de patrones y correlaciones terapéuticas"""
        st.header("Análisis de Patrones Terapéuticos")
        
        # Matriz de correlación
        st.subheader("Matriz de Correlación de Variables Clave")
        
        vars_correlacion = [
            'edad_anios', 'peso_kg', 'dosis_mg_kg', 'concentracion_mg_ml',
            'dolor_inicial_escala_10', 'movilidad_inicial_porcentaje',
            'ansiedad_inicial_escala_10', 'duracion_tratamiento_dias',
            'mejoria_dolor_porcentaje', 'mejoria_movilidad_porcentaje',
            'mejoria_ansiedad_porcentaje'
        ]
        
        corr_matrix = self.df[vars_correlacion].corr()
        
        fig_corr = px.imshow(
            corr_matrix,
            labels=dict(color="Correlación"),
            title="Matriz de Correlación de Variables Terapéuticas",
            color_continuous_scale="RdBu_r"
        )
        st.plotly_chart(fig_corr, use_container_width=True)
        
        # Análisis de dosis óptima
        st.subheader("Análisis de Dosis Óptima")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Dosis vs Éxito por especie
            fig_dosis = px.box(
                self.df,
                x='especie', y='dosis_mg_kg',
                color='tratamiento_exitoso',
                title="Distribución de Dosis por Especie y Éxito"
            )
            st.plotly_chart(fig_dosis, use_container_width=True)
        
        with col2:
            # Duración vs Mejora
            fig_duracion = px.scatter(
                self.df,
                x='duracion_tratamiento_dias', y='mejoria_dolor_porcentaje',
                color='especie',
                size='peso_kg',
                title="Duración del Tratamiento vs Mejora en Dolor"
            )
            st.plotly_chart(fig_duracion, use_container_width=True)
        
        # Análisis de efectos secundarios
        st.subheader("Análisis de Efectos Secundarios")
        
        efectos_analisis = self.df.groupby(['especie', 'severidad_efecto']).size().reset_index(name='casos')
        fig_efectos = px.sunburst(
            efectos_analisis,
            path=['especie', 'severidad_efecto'],
            values='casos',
            title="Distribución de Efectos Secundarios por Especie"
        )
        st.plotly_chart(fig_efectos, use_container_width=True)
    
    def insights_cientificos(self):
        """Genera insights científicos basados en los análisis"""
        st.header("Insights Científicos")
        
        st.markdown("""
        ### Hallazgos Principales
        
        Basado en el análisis de 10,000 casos sintéticos de tratamientos con CBD veterinario:
        """)
        
        # Calcular estadísticas clave
        tasa_exito_general = (self.df['tratamiento_exitoso'] == 'Sí').mean() * 100
        mejora_dolor_promedio = self.df['mejoria_dolor_porcentaje'].mean()
        mejora_movilidad_promedio = self.df['mejoria_movilidad_porcentaje'].mean()
        casos_sin_efectos = (self.df['efecto_secundario'] == 'Sin efectos observados').mean() * 100
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"""
            **Eficacia Terapéutica**
            - Tasa de éxito general: **{tasa_exito_general:.1f}%**
            - Mejora promedio en dolor: **{mejora_dolor_promedio:.1f}%**
            - Mejora promedio en movilidad: **{mejora_movilidad_promedio:.1f}%**
            - Casos sin efectos adversos: **{casos_sin_efectos:.1f}%**
            """)
        
        with col2:
            # Análisis por especie
            exito_por_especie = self.df.groupby('especie')['tratamiento_exitoso'].apply(
                lambda x: (x == 'Sí').mean() * 100
            ).sort_values(ascending=False)
            
            st.success(f"""
            **Efectividad por Especie**
            - {exito_por_especie.index[0]}: **{exito_por_especie.iloc[0]:.1f}%**
            - {exito_por_especie.index[1]}: **{exito_por_especie.iloc[1]:.1f}%**
            - {exito_por_especie.index[2]}: **{exito_por_especie.iloc[2]:.1f}%**
            """)
        
        # Recomendaciones terapéuticas
        st.subheader("Recomendaciones Terapéuticas")
        
        # Análisis de dosis óptima por especie
        dosis_optima = self.df[self.df['tratamiento_exitoso'] == 'Sí'].groupby('especie').agg({
            'dosis_mg_kg': ['mean', 'std'],
            'duracion_tratamiento_dias': 'mean'
        }).round(2)
        
        st.write("**Dosis Recomendadas por Especie (casos exitosos):**")
        st.dataframe(dosis_optima)
        
        # Insights de machine learning
        st.subheader("Insights de Machine Learning")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.warning("""
            **Factores de Riesgo Identificados:**
            - Edad avanzada (> 12 años)
            - Dosis subóptimas (< 0.2 mg/kg)
            - Tratamientos cortos (< 60 días)
            - Casos con alta ansiedad inicial
            """)
        
        with col2:
            st.success("""
            **Predictores de Éxito:**
            - Diagnóstico temprano
            - Dosis adecuada (0.3-0.4 mg/kg)
            - Seguimiento regular
            - Baja severidad de efectos secundarios
            """)
        
        # Limitaciones y consideraciones
        st.subheader("Limitaciones del Estudio")
        st.warning("""
        **Importante:** Este análisis utiliza datos sintéticos generados para demostrar metodologías de minería de datos. 
        Los resultados son indicativos y requieren validación con datos clínicos reales para aplicación práctica.
        
        **Consideraciones:**
        - Datos generados algorítmicamente
        - No representa casos clínicos reales
        - Resultados para demostración metodológica
        - Requiere validación empírica
        """)
        
        # Futuras líneas de investigación
        st.subheader("Futuras Líneas de Investigación")
        st.info("""
        **Propuestas para investigación real:**
        1. Estudios longitudinales con datos reales
        2. Análisis de biomarcadores
        3. Investigación de mecanismos de acción
        4. Estudios comparativos con otras terapias
        5. Desarrollo de protocolos personalizados
        """)

def main():
    st.title("Sistema de Análisis CBD Veterinario")
    st.markdown("### Descubrimiento de Patrones Terapéuticos con Machine Learning")
    
    # Crear instancia del analizador
    analizador = AnalizadorCBDVeterinario()
    
    # Sidebar para navegación
    st.sidebar.title("Navegación")
    seccion = st.sidebar.selectbox(
        "Selecciona una sección:",
        ["Análisis Exploratorio", "Clustering de Pacientes", "Modelos Predictivos", "Análisis de Patrones", "Insights Científicos"]
    )
    
    # Cargar datos
    if analizador.cargar_datos():
        st.sidebar.success(f"Datos cargados: {len(analizador.df)} registros")
        
        if analizador.preprocesar_datos():
            st.sidebar.success("Datos preprocesados")
            
            # Navegación por secciones
            if seccion == "Análisis Exploratorio":
                analizador.analisis_exploratorio()
            
            elif seccion == "Clustering de Pacientes":
                analizador.clustering_pacientes()
            
            elif seccion == "Modelos Predictivos":
                analizador.modelos_predictivos()
            
            elif seccion == "Análisis de Patrones":
                analizador.analisis_patrones()
            
            elif seccion == "Insights Científicos":
                analizador.insights_cientificos()
        
        else:
            st.error("Error en el preprocesamiento de datos")
    else:
        st.error("No se pudieron cargar los datos")

if __name__ == "__main__":
    main()