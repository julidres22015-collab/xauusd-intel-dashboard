"""
XAUUSD Intel System - Sistema de Inteligencia Operativa para Scalping
Desarrollado para análisis conductual y operativo avanzado
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Agregar el directorio al path
sys.path.append(str(Path(__file__).parent))

from data_loader import load_and_clean_data
from metrics import calculate_all_metrics
from psychology import analyze_psychology
from temporal import analyze_temporal
from alerts import generate_alerts
from report import generate_coach_report

# ── Configuración de página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="XAUUSD Intel System",
    page_icon="🥇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS Global ───────────────────────────────────────────────────────────────
with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    # st.image("assets/logo.png", use_column_width=True)
    st.markdown("## 🥇 XAUUSD Intel")
    st.markdown("---")
    
    uploaded_file = st.file_uploader(
        "📁 Sube tu historial MT5",
        type=["xlsx", "xls", "csv"],
        help="Exporta desde MT5: Historial de cuenta → Click derecho → Guardar como Informe Detallado"
    )
    
    st.markdown("---")
    st.markdown("### ⚙️ Configuración")
    
    timezone = st.selectbox("🕐 Zona horaria del broker", 
                            ["UTC+0", "UTC+1", "UTC+2", "UTC+3"], index=2)
    
    min_duration_impulse = st.slider(
        "⚡ Umbral operación impulsiva (seg)", 
        10, 120, 30
    )
    
    overtrading_threshold = st.slider(
        "📊 Umbral sobreoperación (ops/día)", 
        5, 30, 15
    )
    
    st.markdown("---")
    st.caption("v2.0 · XAUUSD Intel System")
    
uploaded_file = st.file_uploader(
    "Sube tu historial de operaciones",
    type=["xlsx", "csv"]
)
# ── Main Content ─────────────────────────────────────────────────────────────
if uploaded_file is None:
    st.title("XAUUSD Intel Dashboard")
    st.write("Sube tu historial de operaciones para comenzar el análisis.")
else:
    with st.spinner("⚙️ Procesando historial..."):
        df = load_and_clean_data(uploaded_file)
    
    if df is None or df.empty:
        st.error("❌ No se pudo procesar el archivo. Verifica el formato.")
        st.stop()
    
    # Calcular todo
    metrics = calculate_all_metrics(df)
    psych = analyze_psychology(df, min_duration_impulse)
    temporal = analyze_temporal(df, timezone)
    alerts = generate_alerts(df, metrics, psych, overtrading_threshold)
    report = generate_coach_report(metrics, psych, temporal)
    
    # Guardar en session state
    st.session_state['df'] = df
    st.session_state['metrics'] = metrics
    st.session_state['psych'] = psych
    st.session_state['temporal'] = temporal
    
    # Navegación por pestañas
    tabs = st.tabs([
        "📊 Overview",
        "🧠 Psicología",
        "⏰ Temporal",
        "📈 P&L Avanzado",
        "⚠️ Alertas",
        "🤖 Informe IA",
        "🏷️ Etiquetas"
    ])
    
    with tabs[0]: _render_overview(df, metrics)
    with tabs[1]: _render_psychology(df, psych)
    with tabs[2]: _render_temporal(df, temporal)
    with tabs[3]: _render_pnl(df, metrics)
    with tabs[4]: _render_alerts(alerts)
    with tabs[5]: _render_report(report)
    with tabs[6]: _render_labels(df)


def _render_welcome():
    """Pantalla de inicio cuando no hay datos"""
    st.markdown("""
    <div class="welcome-container">
        <h1>🥇 XAUUSD Intel System</h1>
        <p class="subtitle">Sistema de Inteligencia Operativa para Scalping</p>
        <div class="feature-grid">
            <div class="feature-card">🧠 Análisis Psicológico</div>
            <div class="feature-card">📊 Métricas Avanzadas</div>
            <div class="feature-card">⏰ Análisis Temporal</div>
            <div class="feature-card">⚠️ Alertas Automáticas</div>
            <div class="feature-card">🤖 Informe IA Coach</div>
            <div class="feature-card">🏷️ Sistema de Etiquetas</div>
        </div>
        <p>← Sube tu archivo MT5 en el panel izquierdo para comenzar</p>
    </div>
    """, unsafe_allow_html=True)
