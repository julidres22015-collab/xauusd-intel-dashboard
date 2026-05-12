"""
XAUUSD Intel System - Dashboard funcional
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent))

from data_loader import load_and_clean_data
from metrics import calculate_all_metrics
from psychology import analyze_psychology
from temporal import analyze_temporal
from alerts import generate_alerts
from report import generate_coach_report

st.set_page_config(
    page_title="XAUUSD Intel System",
    page_icon="🥇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS opcional
try:
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

# Sidebar
with st.sidebar:
    st.markdown("## 🥇 XAUUSD Intel")
    st.markdown("---")

    uploaded_file = st.file_uploader(
        "📁 Sube tu historial MT5",
        type=["xlsx", "xls", "csv"],
        help="Sube el archivo exportado desde MT5"
    )

    st.markdown("---")
    st.markdown("### ⚙️ Configuración")

    timezone = st.selectbox(
        "🕐 Zona horaria del broker",
        ["UTC+0", "UTC+1", "UTC+2", "UTC+3"],
        index=2
    )

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

# Main
st.title("🥇 XAUUSD Intel Dashboard")
st.write("Sistema de análisis operativo para scalping en oro.")

if uploaded_file is None:
    st.info("Sube tu historial de operaciones desde el panel izquierdo para comenzar.")
    st.stop()

with st.spinner("⚙️ Procesando historial..."):
    df = load_and_clean_data(uploaded_file)

if df is None or df.empty:
    st.error("❌ No se pudo procesar el archivo. Verifica el formato.")
    st.stop()

# Cálculos
metrics = calculate_all_metrics(df)
psych = analyze_psychology(df, min_duration_impulse)
temporal = analyze_temporal(df, timezone)
alerts = generate_alerts(df, metrics, psych, temporal)
report = generate_coach_report(df, metrics, psych, temporal, alerts)

tabs = st.tabs([
    "📊 Resumen",
    "🧠 Psicología",
    "⏰ Temporal",
    "📈 PnL",
    "⚠️ Alertas",
    "🤖 Reporte",
    "📋 Datos"
])

with tabs[0]:
    st.subheader("Resumen general")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Operaciones", metrics.get("total_trades", 0))
    col2.metric("Win Rate", f'{metrics.get("win_rate", 0):.2f}%')
    col3.metric("Profit Neto", f'{metrics.get("net_profit", 0):.2f}')
    
    pf = metrics.get("profit_factor", 0)
    if pd.isna(pf):
        pf = 0
    col4.metric("Profit Factor", f"{pf:.2f}")

    st.markdown("### Vista rápida")
    st.dataframe(df.head(20), use_container_width=True)

with tabs[1]:
    st.subheader("Psicología operativa")
    st.write(psych)

with tabs[2]:
    st.subheader("Análisis temporal")
    st.write(temporal)

with tabs[3]:
    st.subheader("PnL y estadísticas")
    st.write(metrics)

    if "net_profit" in df.columns:
        st.line_chart(df["net_profit"].cumsum())

with tabs[4]:
    st.subheader("Alertas")
    for alert in alerts:
        st.warning(alert)

with tabs[5]:
    st.subheader("Reporte tipo coach")
    st.markdown(report)

with tabs[6]:
    st.subheader("Datos procesados")
    st.dataframe(df, use_container_width=True)
