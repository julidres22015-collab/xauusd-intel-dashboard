import pandas as pd
import numpy as np

def analyze_psychology(df: pd.DataFrame):
    if df is None or df.empty:
        return {
            "alerts": [],
            "risk_flags": [],
            "summary": "No hay datos suficientes para analizar psicología operativa."
        }

    alerts = []
    risk_flags = []

    total_trades = len(df)
    avg_win = df.loc[df["net_profit"] > 0, "net_profit"].mean()
    avg_loss = abs(df.loc[df["net_profit"] < 0, "net_profit"].mean())

    avg_win = 0 if pd.isna(avg_win) else avg_win
    avg_loss = 0 if pd.isna(avg_loss) else avg_loss

    # Cortar ganancias / alargar pérdidas
    if avg_loss > avg_win and avg_win > 0:
        alerts.append("Tus pérdidas promedio son mayores que tus ganancias promedio. Posible patrón de cortar ganancias y alargar pérdidas.")

    # Duración ganadoras vs perdedoras
    if "duration_minutes" in df.columns:
        win_duration = df.loc[df["net_profit"] > 0, "duration_minutes"].mean()
        loss_duration = df.loc[df["net_profit"] < 0, "duration_minutes"].mean()

        if not pd.isna(win_duration) and not pd.isna(loss_duration):
            if loss_duration > win_duration * 1.5:
                alerts.append("Tus operaciones perdedoras duran mucho más que tus ganadoras. Puede indicar esperanza emocional en pérdidas.")

    # Sobreoperación
    if "date" in df.columns:
        trades_per_day = df.groupby("date").size()
        avg_trades_day = trades_per_day.mean()

        if avg_trades_day > 10:
            alerts.append("Promedio alto de operaciones por día. Posible sobreoperación.")

        if trades_per_day.max() > avg_trades_day * 2 and avg_trades_day > 0:
            risk_flags.append("Hay días con actividad operativa anormalmente alta.")

    # Revenge trading básico
    if "net_profit" in df.columns:
        losses = df["net_profit"] < 0
        max_loss_streak = 0
        current = 0

        for loss in losses:
            if loss:
                current += 1
                max_loss_streak = max(max_loss_streak, current)
            else:
                current = 0

        if max_loss_streak >= 3:
            alerts.append(f"Tuviste una racha de {max_loss_streak} pérdidas consecutivas. Revisa si hubo revenge trading.")

    # Lotaje emocional
    if "volume" in df.columns:
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
        avg_volume = df["volume"].mean()

        if avg_volume and df["volume"].max() > avg_volume * 2:
            risk_flags.append("Detecté operaciones con lotaje muy superior al promedio. Posible aumento emocional del riesgo.")

    summary = "Análisis psicológico generado con base en duración, frecuencia, rachas, profit y lotaje."

    return {
        "alerts": alerts,
        "risk_flags": risk_flags,
        "summary": summary,
        "avg_win": avg_win,
        "avg_loss": avg_loss
    }
