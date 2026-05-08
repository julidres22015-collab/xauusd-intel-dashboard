import pandas as pd
import numpy as np

def generate_alerts(df: pd.DataFrame, metrics=None, psychology=None, temporal=None):
    alerts = []

    if df is None or df.empty:
        return ["Sube un archivo de operaciones para generar alertas."]

    # Win rate bajo
    win_rate = metrics.get("win_rate", 0) if isinstance(metrics, dict) else 0
    if win_rate < 45:
        alerts.append("Tu win rate está por debajo del 45%. Revisa la calidad de tus entradas.")

    # Profit factor débil
    pf = metrics.get("profit_factor", np.nan) if isinstance(metrics, dict) else np.nan
    if not pd.isna(pf) and pf < 1:
        alerts.append("Tu profit factor está por debajo de 1. Tu sistema está perdiendo más de lo que gana.")

    # Cortar ganancias y alargar pérdidas
    avg_win = metrics.get("avg_win", 0) if isinstance(metrics, dict) else 0
    avg_loss = abs(metrics.get("avg_loss", 0)) if isinstance(metrics, dict) else 0

    if avg_win > 0 and avg_loss > avg_win:
        alerts.append("Tus pérdidas promedio son mayores que tus ganancias. Posible patrón de cortar ganancias y alargar pérdidas.")

    # Sobreoperación
    if "date" in df.columns:
        trades_per_day = df.groupby("date").size()
        if trades_per_day.mean() > 10:
            alerts.append("Estás haciendo muchas operaciones por día. Posible sobreoperación.")

    # Lotaje emocional
    if "volume" in df.columns:
        vol = pd.to_numeric(df["volume"], errors="coerce")
        if vol.max() > vol.mean() * 2:
            alerts.append("Hay operaciones con lotaje muy superior al promedio. Revisa posible riesgo emocional.")

    # Alertas psicológicas
    if isinstance(psychology, dict):
        alerts.extend(psychology.get("alerts", []))
        alerts.extend(psychology.get("risk_flags", []))

    if not alerts:
        alerts.append("No se detectaron alertas graves con la información cargada.")

    return alerts
