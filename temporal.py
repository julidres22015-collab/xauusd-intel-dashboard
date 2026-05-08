"""
Metrics Engine - Cálculo completo de métricas de trading
Incluye métricas avanzadas de scalping y ratios profesionales
"""

import pandas as pd
import numpy as np
from typing import Dict, Any


def calculate_all_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """Calcula todas las métricas del sistema"""
    
    m = {}
    
    # ── Básicas ──────────────────────────────────────────────────────────────
    m['total_trades'] = len(df)
    m['winners'] = df['is_winner'].sum()
    m['losers'] = df['is_loser'].sum()
    m['breakeven'] = m['total_trades'] - m['winners'] - m['losers']
    m['win_rate'] = m['winners'] / m['total_trades'] * 100 if m['total_trades'] > 0 else 0
    
    # ── P&L ──────────────────────────────────────────────────────────────────
    m['total_profit'] = df[df['is_winner']]['net_profit'].sum()
    m['total_loss'] = abs(df[df['is_loser']]['net_profit'].sum())
    m['net_pnl'] = df['net_profit'].sum()
    m['gross_pnl'] = df['profit'].sum()
    m['total_commission'] = df.get('commission', pd.Series([0])).fillna(0).sum()
    
    m['avg_win'] = df[df['is_winner']]['net_profit'].mean() if m['winners'] > 0 else 0
    m['avg_loss'] = df[df['is_loser']]['net_profit'].mean() if m['losers'] > 0 else 0
    m['best_trade'] = df['net_profit'].max()
    m['worst_trade'] = df['net_profit'].min()
    
    # ── Ratios Profesionales ─────────────────────────────────────────────────
    m['profit_factor'] = m['total_profit'] / m['total_loss'] if m['total_loss'] > 0 else np.inf
    m['rr_ratio'] = abs(m['avg_win'] / m['avg_loss']) if m['avg_loss'] != 0 else 0
    m['expectancy'] = (m['win_rate']/100 * m['avg_win']) + ((1 - m['win_rate']/100) * m['avg_loss'])
    
    # ── Drawdown ─────────────────────────────────────────────────────────────
    equity_curve = df['cumulative_profit']
    rolling_max = equity_curve.cummax()
    drawdown = equity_curve - rolling_max
    
    m['max_drawdown'] = drawdown.min()
    m['max_drawdown_pct'] = (drawdown / rolling_max.replace(0, np.nan)).min() * 100
    m['avg_drawdown'] = drawdown[drawdown < 0].mean() if (drawdown < 0).any() else 0
    
    # Calcular duración del drawdown máximo
    dd_periods = (drawdown < 0).astype(int)
    m['drawdown_duration'] = dd_periods.sum()  # en número de operaciones
    
    # ── Rachas ───────────────────────────────────────────────────────────────
    results = df['is_winner'].astype(int)
    
    # Racha ganadora máxima
    max_win_streak = 0
    max_loss_streak = 0
    current_win = 0
    current_loss = 0
    
    for r in results:
        if r == 1:
            current_win += 1
            current_loss = 0
            max_win_streak = max(max_win_streak, current_win)
        else:
            current_loss += 1
            current_win = 0
            max_loss_streak = max(max_loss_streak, current_loss)
    
    m['max_win_streak'] = max_win_streak
    m['max_loss_streak'] = max_loss_streak
    
    # ── Temporal ─────────────────────────────────────────────────────────────
    daily = df.groupby('date').agg(
        pnl=('net_profit', 'sum'),
        trades=('net_profit', 'count')
    )
    
    m['total_days'] = len(daily)
    m['positive_days'] = (daily['pnl'] > 0).sum()
    m['negative_days'] = (daily['pnl'] < 0).sum()
    m['breakeven_days'] = m['total_days'] - m['positive_days'] - m['negative_days']
    m['day_win_rate'] = m['positive_days'] / m['total_days'] * 100 if m['total_days'] > 0 else 0
    
    m['best_day_pnl'] = daily['pnl'].max()
    m['worst_day_pnl'] = daily['pnl'].min()
    m['avg_trades_per_day'] = daily['trades'].mean()
    m['max_trades_per_day'] = daily['trades'].max()
    
    # ── Duración ─────────────────────────────────────────────────────────────
    m['avg_duration_all'] = df['duration_seconds'].mean() / 60  # en minutos
    m['avg_duration_winners'] = df[df['is_winner']]['duration_seconds'].mean() / 60
    m['avg_duration_losers'] = df[df['is_loser']]['duration_seconds'].mean() / 60
    
    # ── Volumen/Lotaje ────────────────────────────────────────────────────────
    if 'volume' in df.columns:
        m['avg_volume'] = df['volume'].mean()
        m['max_volume'] = df['volume'].max()
        m['min_volume'] = df['volume'].min()
        m['volume_std'] = df['volume'].std()
    
    # ── Concentración de ganancias ───────────────────────────────────────────
    top5_pnl = df.nlargest(5, 'net_profit')['net_profit'].sum()
    m['top5_contribution'] = top5_pnl / m['net_pnl'] * 100 if m['net_pnl'] > 0 else 0
    
    # ── Rendimiento por número de operación del día ──────────────────────────
    by_trade_num = df.groupby('trade_num_of_day')['net_profit'].mean()
    m['pnl_by_trade_num'] = by_trade_num.to_dict()
    
    # ── Equity curve data ────────────────────────────────────────────────────
    m['equity_data'] = df[['open_time', 'cumulative_profit']].copy()
    m['drawdown_data'] = pd.DataFrame({
        'time': df['open_time'],
        'drawdown': drawdown.values
    })
    
    # ── Tabla resumen diario ──────────────────────────────────────────────────
    m['daily_summary'] = daily.reset_index()
    
    return m


def calculate_advanced_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Estadísticas avanzadas opcionales"""
    
    stats = {}
    
    # Sharpe ratio aproximado (diario)
    daily_pnl = df.groupby('date')['net_profit'].sum()
    if daily_pnl.std() > 0:
        stats['sharpe_ratio'] = daily_pnl.mean() / daily_pnl.std() * np.sqrt(252)
    else:
        stats['sharpe_ratio'] = 0
    
    # Correlación entre duración y profit
    stats['duration_profit_corr'] = df['duration_seconds'].corr(df['net_profit'])
    
    # Correlación entre volumen y profit
    if 'volume' in df.columns:
        stats['volume_profit_corr'] = df['volume'].corr(df['net_profit'])
    
    # Número de operaciones que representan el 80% del profit (Pareto)
    positive_trades = df[df['is_winner']].sort_values('net_profit', ascending=False)
    cumsum = positive_trades['net_profit'].cumsum()
    total_profit = positive_trades['net_profit'].sum()
    pareto_idx = (cumsum >= total_profit * 0.8).idxmax() if len(positive_trades) > 0 else 0
    
    if len(positive_trades) > 0:
        n_pareto = positive_trades.index.get_loc(pareto_idx) + 1
        stats['pareto_pct'] = n_pareto / len(positive_trades) * 100
    else:
        stats['pareto_pct'] = 0
    
    return stats
