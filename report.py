def generate_coach_report(df, metrics=None, psychology=None, temporal=None, alerts=None):
    metrics = metrics or {}
    psychology = psychology or {}
    alerts = alerts or []

    total_trades = metrics.get("total_trades", 0)
    win_rate = metrics.get("win_rate", 0)
    net_profit = metrics.get("net_profit", 0)
    profit_factor = metrics.get("profit_factor", 0)
    avg_win = metrics.get("avg_win", 0)
    avg_loss = metrics.get("avg_loss", 0)

    report = f"""
### Informe automático de trading

Analizaste **{total_trades} operaciones**.

- Resultado neto: **{net_profit:.2f}**
- Win rate: **{win_rate:.2f}%**
- Profit factor: **{profit_factor:.2f}**
- Ganancia promedio: **{avg_win:.2f}**
- Pérdida promedio: **{avg_loss:.2f}**

### Lectura rápida

"""

    if avg_win > 0 and abs(avg_loss) > avg_win:
        report += "- Estás perdiendo más por operación perdedora de lo que ganas por operación ganadora. Revisa si estás cortando ganancias y dejando correr pérdidas.\n"

    if profit_factor and profit_factor < 1:
        report += "- Tu profit factor está por debajo de 1. El sistema, tal como está operado, no está siendo rentable.\n"

    if win_rate < 45:
        report += "- Tu porcentaje de acierto está bajo. Revisa calidad de entradas, horarios y contexto.\n"

    if alerts:
        report += "\n### Alertas detectadas\n"
        for alert in alerts:
            report += f"- {alert}\n"

    report += "\n### Próximo paso sugerido\n"
    report += "Revisa tus peores horarios, compara duración de ganadoras vs perdedoras y evita aumentar lotaje después de pérdidas."

    return report
