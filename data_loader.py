import pandas as pd
import numpy as np

def load_and_clean_data(uploaded_file):
    if uploaded_file is None:
        return pd.DataFrame()

    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

    # Intento básico de normalización de columnas comunes de MT5
    rename_map = {
        "time": "open_time",
        "open_time": "open_time",
        "close_time": "close_time",
        "symbol": "symbol",
        "type": "type",
        "volume": "volume",
        "price": "entry_price",
        "price_open": "entry_price",
        "price_close": "close_price",
        "profit": "net_profit",
        "commission": "commission",
        "swap": "swap",
        "s/l": "sl",
        "t/p": "tp",
    }

    df = df.rename(columns={c: rename_map.get(c, c) for c in df.columns})

    # Profit
    if "net_profit" not in df.columns:
        possible_profit = [c for c in df.columns if "profit" in c or "beneficio" in c]
        if possible_profit:
            df["net_profit"] = pd.to_numeric(df[possible_profit[0]], errors="coerce")
        else:
            df["net_profit"] = 0

    df["net_profit"] = pd.to_numeric(df["net_profit"], errors="coerce").fillna(0)
    df["is_winner"] = df["net_profit"] > 0

    # Fechas
    date_cols = [c for c in df.columns if "time" in c or "fecha" in c or "hora" in c]
    for c in date_cols:
        df[c] = pd.to_datetime(df[c], errors="coerce")

    if "open_time" in df.columns:
        df["hour"] = df["open_time"].dt.hour
        df["date"] = df["open_time"].dt.date
        df["weekday_num"] = df["open_time"].dt.weekday
        df["weekday"] = df["open_time"].dt.day_name()
    else:
        df["hour"] = 0
        df["date"] = pd.Timestamp.today().date()
        df["weekday_num"] = 0
        df["weekday"] = "N/A"

    # Duración
    if "open_time" in df.columns and "close_time" in df.columns:
        df["duration_minutes"] = (df["close_time"] - df["open_time"]).dt.total_seconds() / 60
    else:
        df["duration_minutes"] = np.nan

    # Sesiones aproximadas hora Colombia
    def get_session(hour):
        if 18 <= hour or hour < 2:
            return "Asia"
        elif 2 <= hour < 7:
            return "Londres"
        elif 7 <= hour < 12:
            return "Nueva York"
        elif 7 <= hour < 10:
            return "Solapamiento"
        else:
            return "Fuera de sesión"

    df["session"] = df["hour"].apply(get_session)

    return df
