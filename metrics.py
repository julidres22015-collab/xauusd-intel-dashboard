import pandas as pd
import numpy as np

def calculate_all_metrics(df: pd.DataFrame):
    if df is None or df.empty:
        return {}

    total_trades = len(df)
    wins = df[df["net_profit"] > 0]
    losses = df[df["net_profit"] < 0]

    gross_profit = wins["net_profit"].sum() if len(wins) else 0
    gross_loss = abs(losses["net_profit"].sum()) if len(losses) else 0

    win_rate = len(wins) / total_trades * 100 if total_trades else 0
    profit_factor = gross_profit / gross_loss if gross_loss != 0 else np.nan

    avg_win = wins["net_profit"].mean() if len(wins) else 0
    avg_loss = losses["net_profit"].mean() if len(losses) else 0

    expectancy = df["net_profit"].mean()
    net_profit = df["net_profit"].sum()

    equity_curve = df["net_profit"].cumsum()
    running_max = equity_curve.cummax()
    drawdown = equity_curve - running_max
    max_drawdown = drawdown.min() if len(drawdown) else 0

    return {
        "total_trades": total_trades,
        "winning_trades": len(wins),
        "losing_trades": len(losses),
        "win_rate": win_rate,
        "net_profit": net_profit,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "profit_factor": profit_factor,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "expectancy": expectancy,
        "best_trade": df["net_profit"].max(),
        "worst_trade": df["net_profit"].min(),
        "max_drawdown": max_drawdown,
        "avg_duration": df["duration_minutes"].mean() if "duration_minutes" in df.columns else np.nan,
        "equity_curve": equity_curve,
        "drawdown_curve": drawdown,
    }
