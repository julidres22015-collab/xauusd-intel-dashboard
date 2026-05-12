import pandas as pd

def analyze_temporal(df: pd.DataFrame, timezone=None):
    if df is None or df.empty:
        return {}

    result = {}

    if "hour" in df.columns:
        result["by_hour"] = df.groupby("hour").agg(
            trades=("net_profit", "count"),
            net_profit=("net_profit", "sum"),
            win_rate=("is_winner", "mean"),
            avg_profit=("net_profit", "mean")
        ).reset_index()

    if "session" in df.columns:
        result["by_session"] = df.groupby("session").agg(
            trades=("net_profit", "count"),
            net_profit=("net_profit", "sum"),
            win_rate=("is_winner", "mean"),
            avg_profit=("net_profit", "mean")
        ).reset_index()

    if "weekday" in df.columns:
        result["by_weekday"] = df.groupby("weekday").agg(
            trades=("net_profit", "count"),
            net_profit=("net_profit", "sum"),
            win_rate=("is_winner", "mean"),
            avg_profit=("net_profit", "mean")
        ).reset_index()

    if "date" in df.columns:
        result["by_date"] = df.groupby("date").agg(
            trades=("net_profit", "count"),
            net_profit=("net_profit", "sum"),
            win_rate=("is_winner", "mean")
        ).reset_index()

    return result
