"""
Coach Report Generator - Genera informes automáticos tipo coach de trading
"""

import pandas as pd
from typing import Dict, Any


def generate_coach_report(metrics: Dict, psych: Dict, temporal: Dict) -> str:
    """
    Genera un informe escrito automático en lenguaje natural.
    Actúa como un coach de trading analizado los datos reales.
    """
    
    report_sections = []
    
    # ── EVALUACIÓN GENERAL ────────────────────────────────────────────────────
    wr = metrics.get('win_rate', 0)
    pf = metrics.get('profit_factor', 0)
    net = metrics.get('net_pnl', 0)
    psych_score = psych.get('psych_score', {}).get('score', 50)
    
    general = f"""## 📋 Evaluación General

Tu rendimiento en el período analizado muestra un **win rate del {wr:.1f}%** con un profit factor de **{pf:.2f}**. """
    
    if net > 0:
        general += f"El resultado neto es positivo ({net:.2f}), lo que indica que la estrategia base funciona. "
    else:
        general += f"El resultado neto es negativo ({net:.2f}), lo que requiere atención inmediata. "
    
    if pf > 1.5:
        general += "Tu profit factor es sólido, lo que sugiere que cuando operas bien, lo haces muy bien."
    elif pf > 1.0:
        general += "Tu profit factor es marginalmente positivo. Hay margen de mejora significativo."
    else:
        general += "Tu profit factor por debajo de 1.0 es preocupante. Las pérdidas superan las ganancias."
    
    report_sections.append(general)
    
    # ── ANÁLISIS R/R ─────────────────────────────────────────────────────────
    rr = metrics.get('rr_ratio', 0)
    avg_win = metrics.get('avg_win', 0)
    avg_loss = metrics.get('avg_loss', 0)
    
    rr_section = f"""## ⚖️ Análisis de Riesgo/Beneficio

Tu ganancia promedio es **{avg_win:.2f}** y tu pérdida promedio es **{abs(avg_loss):.2f}**, lo que da un ratio R/R real de **{rr:.2f}**. """
    
    if rr < 0.8:
        rr_section += f"""
Esto es uno de los problemas más serios detectados. Con un win rate de {wr:.1f}% y un R/R de {rr:.2f}, necesitarías un win rate de al menos **{(1/(1+rr))*100:.0f}%** solo para estar en breakeven.

**Diagnóstico**: Estás cortando ganancias demasiado rápido y/o dejando correr las pérdidas. Esto es un patrón psicológico clásico del trader que tiene miedo de perder ganancias acumuladas pero no acepta pérdidas."""
    elif rr >= 1.0:
        rr_section += "Tu ratio R/R es positivo, lo que es una base sólida. Mantén esta disciplina."
    else:
        rr_section += "Tu ratio R/R necesita mejoras. Trabaja en no cerrar posiciones ganadoras prematuramente."
    
    report_sections.append(rr_section)
    
    # ── ANÁLISIS PSICOLÓGICO ──────────────────────────────────────────────────
    psych_section = "## 🧠 Diagnóstico Psicológico\n\n"
    
    issues_found = []
    
    if psych.get('revenge', {}).get('detected', False):
        revenge_data = psych['revenge']['data']
        issues_found.append(
            f"**Revenge Trading**: Se detectaron {revenge_data.get('quick_entries_after_loss', 0)} "
            f"entradas en menos de 60 segundos después de pérdidas. "
            f"Este es uno de los hábitos más destructivos del trader."
        )
    
    if psych.get('overtrading', {}).get('detected', False):
        ot_data = psych['overtrading']['data']
        issues_found.append(
            f"**Sobreoperación**: En días de alta actividad ({ot_data.get('high_vol_avg_pnl', 0):.2f} promedio) "
            f"tu rendimiento es peor que en días de baja actividad ({ot_data.get('low_vol_avg_pnl', 0):.2f}). "
            f"Más operaciones no significa más ganancias."
        )
    
    if psych.get('hope_in_losses', {}).get('detected', False):
        issues_found.append(
            "**Esperanza en Pérdidas**: Tus pérdidas largas son significativamente peores que las cortas. "
            "Estás manteniendo posiciones perdedoras con la esperanza de que se recuperen."
        )
    
    if psych.get('lot_escalation', {}).get('detected', False):
        issues_found.append(
            "**Escalado Emocional**: Usas más lotaje después de pérdidas, lo que amplifica el riesgo "
            "exactamente cuando estás más vulnerable psicológicamente."
        )
    
    if psych.get('fatigue', {}).get('detected', False):
        issues_found.append(
            "**Fatiga Operativa**: Tu rendimiento cae significativamente a medida que avanza el día. "
            "Estás operando cuando ya no deberías."
        )
    
    if issues_found:
        psych_section += "Se identificaron los siguientes patrones psicológicos en tus datos:\n\n"
        for issue in issues_found:
            psych_section += f"- {issue}\n"
    else:
        psych_section += "No se detectaron patrones psicológicos críticos. Tu disciplina operativa es sólida."
    
    psych_section += f"\n\n**Score Psicológico: {psych_score:.0f}/100** — {psych.get('psych_score', {}).get('label', '')}"
    
    report_sections.append(psych_section)
    
    # ── ANÁLISIS TEMPORAL ─────────────────────────────────────────────────────
    if temporal:
        temporal_section = "## ⏰ Análisis Temporal\n\n"
        
        best_session = temporal.get('best_session', 'N/A')
        worst_session = temporal.get('worst_session', 'N/A')
        best_hour = temporal.get('best_hour', 'N/A')
        worst_hour = temporal.get('worst_hour', 'N/A')
        
        temporal_section += f"""Tu mejor sesión es **{best_session}** y tu peor sesión es **{worst_session}**.

En términos de hora, rindes mejor alrededor de las **{best_hour}:00h** y peor alrededor de las **{worst_hour}:00h**.

**Recomendación**: Concentra tu operativa en las sesiones y horarios donde históricamente tienes mejor rendimiento. Considera no operar en tu horario de peor rendimiento."""
        
        report_sections.append(temporal_section)
    
    # ── FORTALEZAS ────────────────────────────────────────────────────────────
    strengths = []
    
    if wr > 55:
        strengths.append(f"Win rate sólido del {wr:.1f}%")
    if pf > 1.5:
        strengths.append(f"Profit factor fuerte de {pf:.2f}")
    if rr >= 1.0:
        strengths.append(f"Ratio R/R positivo de {rr:.2f}")
    if metrics.get('max_loss_streak', 10) <= 4:
        strengths.append(f"Rachas perdedoras controladas (máx. {metrics['max_loss_streak']})")
    if not psych.get('revenge', {}).get('detected', False):
        strengths.append("Sin evidencia de revenge trading")
    
    if strengths:
        strength_section = "## 💪 Fortalezas Identificadas\n\n"
        for s in strengths:
            strength_section += f"✅ {s}\n"
        report_sections.append(strength_section)
    
    # ── PLAN DE ACCIÓN ────────────────────────────────────────────────────────
    action_section = """## 🎯 Plan de Acción Prioritario

Basado en el análisis completo, las acciones más importantes en orden de prioridad son:

"""
    
    priority = 1
    
    if psych.get('revenge', {}).get('detected', False):
        action_section += f"{priority}. **Regla de pausa post-pérdida**: Espera mínimo 15 minutos después de cada pérdida antes de volver a operar.\n"
        priority += 1
    
    if rr < 0.8:
        action_section += f"{priority}. **Ajuste de R/R**: Mueve el TP al menos 1.2x la distancia del SL en cada operación.\n"
        priority += 1
    
    if psych.get('overtrading', {}).get('detected', False):
        action_section += f"{priority}. **Límite diario**: Establece un máximo de {max(8, int(metrics.get('avg_trades_per_day', 10)))} operaciones por día.\n"
        priority += 1
    
    if psych.get('lot_escalation', {}).get('detected', False):
        action_section += f"{priority}. **Lotaje fijo**: Usa siempre el mismo lotaje, independientemente del resultado anterior.\n"
        priority += 1
    
    if psych.get('hope_in_losses', {}).get('detected', False):
        action_section += f"{priority}. **Respeto absoluto al SL**: Nunca muevas el SL en contra de la posición.\n"
        priority += 1
    
    if priority == 1:
        action_section += "Tu trading está relativamente bien gestionado. Continúa trabajando en la consistencia y documenta cada operación."
    
    report_sections.append(action_section)
    
    # Unir todo el reporte
    return "\n\n---\n\n".join(report_sections)
