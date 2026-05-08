"""
Psychology Engine - Detección de patrones psicológicos en los datos
El corazón del sistema: detecta errores conductuales reales
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List


def analyze_psychology(df: pd.DataFrame, impulse_threshold_sec: int = 30) -> Dict[str, Any]:
    """
    Análisis psicológico completo basado en patrones de datos.
    Detecta: revenge trading, FOMO, sobreoperación, cierre prematuro, etc.
    """
    
    p = {}
    
    # ── 1. REVENGE TRADING ───────────────────────────────────────────────────
    p['revenge'] = detect_revenge_trading(df)
    
    # ── 2. SOBREOPERACIÓN ────────────────────────────────────────────────────
    p['overtrading'] = detect_overtrading(df)
    
    # ── 3. OPERACIONES IMPULSIVAS ────────────────────────────────────────────
    p['impulsive'] = detect_impulsive_trades(df, impulse_threshold_sec)
    
    # ── 4. CORTE PREMATURO DE GANANCIAS ─────────────────────────────────────
    p['premature_close'] = detect_premature_profit_close(df)
    
    # ── 5. ESPERANZA EN PÉRDIDAS ─────────────────────────────────────────────
    p['hope_in_losses'] = detect_hope_in_losses(df)
    
    # ── 6. ESCALADO EMOCIONAL DE LOTAJE ─────────────────────────────────────
    p['lot_escalation'] = detect_lot_escalation(df)
    
    # ── 7. FATIGA OPERATIVA ──────────────────────────────────────────────────
    p['fatigue'] = detect_trading_fatigue(df)
    
    # ── 8. EXCESO DE CONFIANZA ───────────────────────────────────────────────
    p['overconfidence'] = detect_overconfidence(df)
    
    # ── 9. FOMO ──────────────────────────────────────────────────────────────
    p['fomo'] = detect_fomo(df)
    
    # ── 10. Score psicológico global ─────────────────────────────────────────
    p['psych_score'] = calculate_psych_score(p)
    
    return p


def detect_revenge_trading(df: pd.DataFrame) -> Dict:
    """
    Detecta revenge trading:
    - Entradas rápidas después de pérdidas
    - Aumento de lotaje después de pérdidas
    - Muchas operaciones consecutivas tras pérdida
    """
    
    result = {
        'detected': False,
        'severity': 0,
        'signals': [],
        'data': {}
    }
    
    if len(df) < 5:
        return result
    
    # Tiempo entre cierre de pérdida y siguiente apertura
    losers_idx = df[df['is_loser']].index
    revenge_entries = []
    
    for idx in losers_idx:
        next_idx = idx + 1
        if next_idx < len(df):
            time_gap = df.loc[next_idx, 'time_since_last_close']
            if pd.notna(time_gap) and time_gap < 60:  # menos de 1 minuto
                revenge_entries.append({
                    'after_loss': df.loc[idx, 'net_profit'],
                    'time_gap_sec': time_gap,
                    'next_result': df.loc[next_idx, 'net_profit']
                })
    
    result['data']['quick_entries_after_loss'] = len(revenge_entries)
    result['data']['revenge_entries'] = revenge_entries
    
    # Calcular win rate de estas entradas "venganza"
    if revenge_entries:
        revenge_wr = sum(1 for e in revenge_entries if e['next_result'] > 0) / len(revenge_entries)
        result['data']['revenge_win_rate'] = revenge_wr * 100
        
        if len(revenge_entries) >= 5:
            result['detected'] = True
            result['severity'] = min(10, len(revenge_entries) // 3)
            result['signals'].append(
                f"Se detectaron {len(revenge_entries)} entradas en menos de 60 seg después de pérdidas"
            )
            result['signals'].append(
                f"Win rate en entradas post-pérdida: {revenge_wr*100:.1f}% (probablemente inferior al promedio)"
            )
    
    # Secuencias de pérdidas seguidas de pérdidas
    consecutive_losses_then_entry = _count_loss_streaks_with_reentry(df)
    result['data']['avg_trades_after_streak'] = consecutive_losses_then_entry
    
    if consecutive_losses_then_entry > 2:
        result['detected'] = True
        result['severity'] = max(result['severity'], 5)
        result['signals'].append(
            f"Promedio de {consecutive_losses_then_entry:.1f} operaciones extra después de rachas de pérdidas"
        )
    
    return result


def detect_overtrading(df: pd.DataFrame) -> Dict:
    """
    Detecta sobreoperación:
    - Días con demasiadas operaciones
    - Relación entre cantidad de ops y resultado
    """
    
    result = {'detected': False, 'severity': 0, 'signals': [], 'data': {}}
    
    daily = df.groupby('date').agg(
        trades=('net_profit', 'count'),
        pnl=('net_profit', 'sum'),
        win_rate=('is_winner', 'mean')
    ).reset_index()
    
    avg_trades = daily['trades'].mean()
    result['data']['avg_daily_trades'] = avg_trades
    result['data']['max_daily_trades'] = daily['trades'].max()
    
    # Días de alto volumen vs bajo volumen
    high_vol_days = daily[daily['trades'] > daily['trades'].quantile(0.75)]
    low_vol_days = daily[daily['trades'] <= daily['trades'].quantile(0.25)]
    
    if len(high_vol_days) > 0 and len(low_vol_days) > 0:
        high_vol_pnl = high_vol_days['pnl'].mean()
        low_vol_pnl = low_vol_days['pnl'].mean()
        high_vol_wr = high_vol_days['win_rate'].mean()
        low_vol_wr = low_vol_days['win_rate'].mean()
        
        result['data']['high_vol_avg_pnl'] = high_vol_pnl
        result['data']['low_vol_avg_pnl'] = low_vol_pnl
        result['data']['high_vol_wr'] = high_vol_wr * 100
        result['data']['low_vol_wr'] = low_vol_wr * 100
        result['data']['daily_summary'] = daily
        
        if low_vol_pnl > high_vol_pnl * 1.2:
            result['detected'] = True
            result['severity'] = 7
            result['signals'].append(
                f"Días de pocas operaciones ({low_vol_days['trades'].mean():.0f} ops) "
                f"ganas {low_vol_pnl:.2f} vs días de muchas operaciones ({high_vol_days['trades'].mean():.0f} ops) "
                f"ganas {high_vol_pnl:.2f}"
            )
    
    # Rendimiento según número de operación del día
    pnl_by_num = df.groupby('trade_num_of_day')['net_profit'].agg(['mean', 'count'])
    result['data']['pnl_by_trade_number'] = pnl_by_num.reset_index()
    
    # ¿Hay caída significativa después de cierta operación?
    first_ops_avg = df[df['trade_num_of_day'] <= 5]['net_profit'].mean()
    late_ops_avg = df[df['trade_num_of_day'] > 10]['net_profit'].mean()
    
    if len(df[df['trade_num_of_day'] > 10]) > 20 and late_ops_avg < first_ops_avg * 0.5:
        result['detected'] = True
        result['severity'] = max(result['severity'], 6)
        result['signals'].append(
            f"Tu rentabilidad cae significativamente después de la operación 10 del día"
        )
    
    return result


def detect_impulsive_trades(df: pd.DataFrame, threshold_sec: int = 30) -> Dict:
    """Detecta operaciones cerradas muy rápido (impulsividad)"""
    
    result = {'detected': False, 'severity': 0, 'signals': [], 'data': {}}
    
    impulsive = df[df['duration_seconds'] < threshold_sec]
    result['data']['count'] = len(impulsive)
    result['data']['pct_of_total'] = len(impulsive) / len(df) * 100
    result['data']['avg_pnl'] = impulsive['net_profit'].mean() if len(impulsive) > 0 else 0
    result['data']['trades'] = impulsive
    
    if len(impulsive) > 0:
        normal_avg = df[df['duration_seconds'] >= threshold_sec]['net_profit'].mean()
        impulsive_avg = impulsive['net_profit'].mean()
        result['data']['vs_normal_avg'] = normal_avg
        
        if result['data']['pct_of_total'] > 15:
            result['detected'] = True
            result['severity'] = int(result['data']['pct_of_total'] / 5)
            result['signals'].append(
                f"{result['data']['pct_of_total']:.1f}% de tus operaciones duran menos de {threshold_sec} segundos"
            )
            if impulsive_avg < normal_avg:
                result['signals'].append(
                    f"Las operaciones impulsivas tienen peor rendimiento: "
                    f"{impulsive_avg:.2f} vs {normal_avg:.2f} promedio"
                )
    
    return result


def detect_premature_profit_close(df: pd.DataFrame) -> Dict:
    """
    Detecta cierre prematuro de ganancias:
    - Ganancias pequeñas vs pérdidas grandes
    - TP muy conservador vs SL
    """
    
    result = {'detected': False, 'severity': 0, 'signals': [], 'data': {}}
    
    winners = df[df['is_winner']]
    losers = df[df['is_loser']]
    
    if len(winners) == 0 or len(losers) == 0:
        return result
    
    avg_win = winners['net_profit'].mean()
    avg_loss = abs(losers['net_profit'].mean())
    rr = avg_win / avg_loss if avg_loss > 0 else 0
    
    result['data']['avg_win'] = avg_win
    result['data']['avg_loss'] = avg_loss
    result['data']['rr_ratio'] = rr
    result['data']['win_duration_avg'] = winners['duration_minutes'].mean()
    result['data']['loss_duration_avg'] = losers['duration_minutes'].mean()
    
    # Ganancias vs pérdidas en duración
    if losers['duration_minutes'].mean() > winners['duration_minutes'].mean() * 1.5:
        result['detected'] = True
        result['severity'] = 6
        result['signals'].append(
            f"Tus pérdidas duran {losers['duration_minutes'].mean():.1f} min promedio "
            f"vs ganancias {winners['duration_minutes'].mean():.1f} min → dejas correr pérdidas"
        )
    
    if rr < 0.8:
        result['detected'] = True
        result['severity'] = max(result['severity'], 7)
        result['signals'].append(
            f"Tu ratio R/R real es {rr:.2f} — ganas {avg_win:.2f} pero pierdes {avg_loss:.2f} promedio"
        )
    
    # % de trades que alcanzan el TP vs los que se cierran antes
    result['data']['rr_distribution'] = winners['net_profit'].describe().to_dict()
    
    return result


def detect_hope_in_losses(df: pd.DataFrame) -> Dict:
    """Detecta si el trader mantiene pérdidas con esperanza"""
    
    result = {'detected': False, 'severity': 0, 'signals': [], 'data': {}}
    
    losers = df[df['is_loser']]
    
    if len(losers) < 5:
        return result
    
    # Pérdidas que duran mucho tiempo
    long_losers = losers[losers['duration_minutes'] > losers['duration_minutes'].quantile(0.75)]
    result['data']['long_losses_count'] = len(long_losers)
    result['data']['long_losses_avg_pnl'] = long_losers['net_profit'].mean()
    result['data']['long_losses_pct'] = len(long_losers) / len(losers) * 100
    
    # Las pérdidas largas son peores que pérdidas cortas?
    short_losers = losers[losers['duration_minutes'] <= losers['duration_minutes'].quantile(0.25)]
    
    if len(long_losers) > 0 and len(short_losers) > 0:
        long_avg = long_losers['net_profit'].mean()
        short_avg = short_losers['net_profit'].mean()
        result['data']['long_vs_short_loss'] = {'long': long_avg, 'short': short_avg}
        
        if abs(long_avg) > abs(short_avg) * 2:
            result['detected'] = True
            result['severity'] = 7
            result['signals'].append(
                f"Tus pérdidas largas ({long_losers['duration_minutes'].mean():.0f} min) "
                f"son {abs(long_avg/short_avg):.1f}x peores que las cortas → esperanza emocional"
            )
    
    return result


def detect_lot_escalation(df: pd.DataFrame) -> Dict:
    """Detecta escalado emocional del lotaje"""
    
    result = {'detected': False, 'severity': 0, 'signals': [], 'data': {}}
    
    if 'volume' not in df.columns:
        return result
    
    # Comparar lotaje después de pérdidas vs ganancias
    df_copy = df.copy()
    df_copy['prev_result'] = df_copy['net_profit'].shift(1)
    df_copy['prev_was_loss'] = df_copy['prev_result'] < 0
    
    after_win = df_copy[~df_copy['prev_was_loss']]['volume'].mean()
    after_loss = df_copy[df_copy['prev_was_loss']]['volume'].mean()
    
    result['data']['avg_lot_after_win'] = after_win
    result['data']['avg_lot_after_loss'] = after_loss
    
    if pd.notna(after_loss) and pd.notna(after_win) and after_win > 0:
        escalation_ratio = after_loss / after_win
        result['data']['escalation_ratio'] = escalation_ratio
        
        if escalation_ratio > 1.3:
            result['detected'] = True
            result['severity'] = int((escalation_ratio - 1) * 10)
            result['signals'].append(
                f"Usas {escalation_ratio:.2f}x más lotaje después de pérdidas → "
                f"{after_loss:.2f} lots vs {after_win:.2f} lots"
            )
    
    # Correlación entre pérdida consecutiva y lotaje
    result['data']['volume_std'] = df['volume'].std()
    result['data']['volume_cv'] = df['volume'].std() / df['volume'].mean() * 100  # coef variación
    
    if result['data']['volume_cv'] > 50:
        result['detected'] = True
        result['severity'] = max(result['severity'], 5)
        result['signals'].append(
            f"Tu lotaje es muy inconsistente (CV={result['data']['volume_cv']:.0f}%) → señal de operativa emocional"
        )
    
    return result


def detect_trading_fatigue(df: pd.DataFrame) -> Dict:
    """Detecta fatiga operativa (rendimiento cae con más operaciones)"""
    
    result = {'detected': False, 'severity': 0, 'signals': [], 'data': {}}
    
    # Rendimiento por sesión del día (mañana vs tarde)
    df_copy = df.copy()
    
    morning = df_copy[df_copy['hour'] < 12]['net_profit'].mean()
    afternoon = df_copy[(df_copy['hour'] >= 12) & (df_copy['hour'] < 17)]['net_profit'].mean()
    evening = df_copy[df_copy['hour'] >= 17]['net_profit'].mean()
    
    result['data']['morning_avg'] = morning
    result['data']['afternoon_avg'] = afternoon
    result['data']['evening_avg'] = evening
    
    # Rendimiento por posición en el día
    pnl_by_pos = df.groupby('trade_num_of_day')['net_profit'].mean()
    
    # Regresión simple para detectar tendencia
    if len(pnl_by_pos) > 5:
        x = pnl_by_pos.index.values
        y = pnl_by_pos.values
        
        # Correlación entre posición y rendimiento
        corr = np.corrcoef(x, y)[0, 1] if len(x) > 2 else 0
        result['data']['fatigue_correlation'] = corr
        result['data']['pnl_by_position'] = pnl_by_pos.to_dict()
        
        if corr < -0.4:
            result['detected'] = True
            result['severity'] = int(abs(corr) * 10)
            result['signals'].append(
                f"Fuerte correlación negativa ({corr:.2f}) entre número de operación del día y rentabilidad → fatiga operativa"
            )
    
    return result


def detect_overconfidence(df: pd.DataFrame) -> Dict:
    """Detecta exceso de confianza (lotaje muy alto después de rachas ganadoras)"""
    
    result = {'detected': False, 'severity': 0, 'signals': [], 'data': {}}
    
    if 'volume' not in df.columns:
        return result
    
    # Calcular racha actual antes de cada operación
    df_copy = df.copy()
    df_copy['win_streak_before'] = 0
    
    streak = 0
    for i in range(len(df_copy)):
        df_copy.iloc[i, df_copy.columns.get_loc('win_streak_before')] = streak
        if df_copy.iloc[i]['is_winner']:
            streak += 1
        else:
            streak = 0
    
    # Comparar volumen después de racha larga vs corta
    high_streak = df_copy[df_copy['win_streak_before'] >= 3]['volume'].mean()
    low_streak = df_copy[df_copy['win_streak_before'] <= 1]['volume'].mean()
    
    result['data']['volume_after_streak'] = high_streak
    result['data']['volume_normal'] = low_streak
    
    if pd.notna(high_streak) and pd.notna(low_streak) and low_streak > 0:
        ratio = high_streak / low_streak
        result['data']['overconfidence_ratio'] = ratio
        
        # También analizar win rate en esas operaciones
        wr_high = df_copy[df_copy['win_streak_before'] >= 3]['is_winner'].mean()
        result['data']['wr_after_streak'] = wr_high * 100 if pd.notna(wr_high) else 0
        
        if ratio > 1.4:
            result['detected'] = True
            result['severity'] = int((ratio - 1) * 10)
            result['signals'].append(
                f"Usas {ratio:.1f}x más volumen después de 3+ ganancias seguidas → exceso de confianza"
            )
    
    return result


def detect_fomo(df: pd.DataFrame) -> Dict:
    """Detecta FOMO: entradas después de sesiones sin operar"""
    
    result = {'detected': False, 'severity': 0, 'signals': [], 'data': {}}
    
    # FOMO = entradas muy rápidas al inicio de sesión
    session_starts = df.groupby(['date', 'session'])['open_time'].min()
    
    # Operaciones que abren en los primeros 5 minutos de sesión
    first_trades = []
    for date in df['date'].unique():
        day_df = df[df['date'] == date].sort_values('open_time')
        if len(day_df) > 0:
            first_op = day_df.iloc[0]['open_time']
            very_early = day_df[day_df['open_time'] <= first_op + pd.Timedelta(minutes=5)]
            if len(very_early) > 2:
                first_trades.append({
                    'date': date,
                    'early_trades': len(very_early),
                    'early_pnl': very_early['net_profit'].sum()
                })
    
    result['data']['days_with_early_burst'] = len(first_trades)
    result['data']['early_burst_details'] = first_trades
    
    if len(first_trades) > len(df['date'].unique()) * 0.3:
        avg_pnl = np.mean([d['early_pnl'] for d in first_trades])
        result['data']['avg_early_pnl'] = avg_pnl
        
        if avg_pnl < 0:
            result['detected'] = True
            result['severity'] = 5
            result['signals'].append(
                f"En {len(first_trades)} días abres múltiples trades en los primeros 5 min de sesión (FOMO)"
            )
    
    return result


def _count_loss_streaks_with_reentry(df: pd.DataFrame) -> float:
    """Cuenta cuántas ops extra se hacen después de rachas de pérdidas"""
    
    extra_ops = []
    i = 0
    
    while i < len(df) - 3:
        # Detectar racha de 2+ pérdidas
        if df.iloc[i]['is_loser'] and df.iloc[i+1]['is_loser'] if i+1 < len(df) else False:
            # Contar ops hasta que el día termina o hay pausa larga
            streak_end = i + 2
            while streak_end < len(df):
                gap = df.iloc[streak_end]['time_since_last_close']
                if pd.notna(gap) and gap > 3600:  # pausa mayor a 1 hora
                    break
                streak_end += 1
            
            extra_ops.append(streak_end - i - 2)
            i = streak_end
        else:
            i += 1
    
    return np.mean(extra_ops) if extra_ops else 0


def calculate_psych_score(psych_data: Dict) -> Dict:
    """Calcula un score psicológico global (0-100, mayor = mejor)"""
    
    penalties = {
        'revenge': psych_data.get('revenge', {}).get('severity', 0) * 3,
        'overtrading': psych_data.get('overtrading', {}).get('severity', 0) * 2,
        'impulsive': psych_data.get('impulsive', {}).get('severity', 0) * 2,
        'premature_close': psych_data.get('premature_close', {}).get('severity', 0) * 3,
        'hope_in_losses': psych_data.get('hope_in_losses', {}).get('severity', 0) * 3,
        'lot_escalation': psych_data.get('lot_escalation', {}).get('severity', 0) * 2,
        'fatigue': psych_data.get('fatigue', {}).get('severity', 0) * 2,
        'overconfidence': psych_data.get('overconfidence', {}).get('severity', 0) * 2,
        'fomo': psych_data.get('fomo', {}).get('severity', 0) * 1,
    }
    
    total_penalty = sum(penalties.values())
    score = max(0, 100 - total_penalty)
    
    if score >= 80:
        grade = 'A'
        label = 'Excelente disciplina'
        color = '#00C853'
    elif score >= 60:
        grade = 'B'
        label = 'Disciplina aceptable'
        color = '#FFD600'
    elif score >= 40:
        grade = 'C'
        label = 'Disciplina moderada'
        color = '#FF6D00'
    else:
        grade = 'D'
        label = 'Disciplina crítica'
        color = '#D50000'
    
    return {
        'score': score,
        'grade': grade,
        'label': label,
        'color': color,
        'penalties': penalties,
        'top_issues': sorted(penalties.items(), key=lambda x: x[1], reverse=True)[:3]
    }
