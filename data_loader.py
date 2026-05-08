"""
Temporal Analysis - Análisis completo por horario, sesión y día
"""

import pandas as pd
import numpy as np
from typing import Dict, Any


def analyze_temporal(df: pd.DataFrame, timezone: str = "UTC+2") -> Dict[str, Any]:
    """Análisis completo del rendimiento temporal"""
    
    t = {}
    
    # ── Por hora del día ──────────────────────────────────────────────────────
    hourly = df.groupby('hour').agg(
        trades=('net_profit', 'count'),
        total_pnl=('net_profit', 'sum'),
        avg_pnl=('net_profit', 'mean'),
        win_rate=('is_winner', 'mean'),
        total_wins=('is_winner', 'sum'),
        avg_duration=('duration_minutes', 'mean')
    ).reset_index()
    hourly['win_rate_pct'] = hourly['win_rate'] * 100
    t['hourly'] = hourly
    
    # ── Por sesión ────────────────────────────────────────────────────────────
    session = df.groupby('session').agg(
        trades=('net_profit', 'count'),
        total_pnl=('net_profit', 'sum'),
        avg_pnl=('net_profit', 'mean'),
        win_rate=('is_winner', 'mean'),
        avg_duration=('duration_minutes', 'mean')
    ).reset_index()
    session['win_rate_pct'] = session['win_rate'] * 100
    t['by_session'] = session
    
    best_session = session.loc[session['total_pnl'].idxmax(), 'session'] if len(session) > 0 else 'N/A'
    worst_session = session.loc[session['total_pnl'].idxmin(), 'session'] if len(session) > 0 else 'N/A'
    t['best_session'] = best_session
    t['worst_session'] = worst_session
    
    # ── Por día de la semana ──────────────────────────────────────────────────
    weekly = df.groupby(['weekday_num', 'weekday']).agg(
        trades=('net_profit', 'count'),
        total_pnl=('net_profit', 'sum'),
        avg_pnl=('net_profit', 'mean'),
        win_rate=('is_winner', 'mean'),
    ).reset_index().sort_values('weekday_num')
    weekly['win_rate_pct'] = weekly['win_rate'] * 100
    t['by_weekday'] = weekly
    
    # ── Heatmap hora x día de semana ─────────────────────────────────────────
    heatmap_data = df.pivot_table(
        values='net_profit',
        index='hour',
        columns='weekday_num',
        aggfunc='sum',
        fill_value=0
    )
    t['heatmap_pnl'] = heatmap_data
    
    heatmap_wr = df.pivot_table(
        values='is_winner',
        index='hour',
        columns='weekday_num',
        aggfunc='mean',
        fill_value=0
    )
    t['heatmap_wr'] = heatmap_wr
    
    heatmap_count = df.pivot_table(
        values='net_profit',
        index='hour',
        columns='weekday_num',
        aggfunc='count',
        fill_value=0
    )
    t['heatmap_count'] = heatmap_count
    
    # ── Calendario de ganancias ───────────────────────────────────────────────
    calendar = df.groupby('date').agg(
        pnl=('net_profit', 'sum'),
        trades=('net_profit', 'count'),
        win_rate=('is_winner', 'mean')
    ).reset_index()
    t['calendar'] = calendar
    
    # ── Mejor/peor horario ────────────────────────────────────────────────────
    if len(hourly) > 0:
        t['best_hour'] = int(hourly.loc[hourly['total_pnl'].idxmax(), 'hour'])
        t['worst_hour'] = int(hourly.loc[hourly['total_pnl'].idxmin(), 'hour'])
        t['most_active_hour'] = int(hourly.loc[hourly['trades'].idxmax(), 'hour'])
        
    return t
