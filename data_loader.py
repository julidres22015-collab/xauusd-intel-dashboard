import pandas as pd
import numpy as np


def load_and_clean_data(uploaded_file):
    if uploaded_file is None:
        return pd.DataFrame()

    file_name = uploaded_file.name.lower()

    if file_name.endswith(".csv"):
        raw = pd.read_csv(uploaded_file, header=None)
    else:
        raw = pd.read_excel(uploaded_file, header=None)

    header_row = None

    for i in range(len(raw)):
        row_values = raw.iloc[i].fillna("").astype(str).str.lower().tolist()
        row_text = " ".join(map(str, row_values))

        has_time = "time" in row_text or "tiempo" in row_text or "fecha" in row_text
        has_profit = "profit" in row_text or "beneficio" in row_text
        has_type = "type" in row_text or "tipo" in row_text

        if has_time and has_profit and has_type:
            header_row = i
            break

    if header_row is None:
        uploaded_file.seek(0)
        if file_name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    else:
        df = raw.iloc[header_row + 1:].copy()
        df.columns = raw.iloc[header_row].fillna("").astype(str).str.strip()

    df = df.dropna(how="all")
    df = df.loc[:, ~df.columns.astype(str).str.contains("^Unnamed", case=False, regex=True)]

    df.columns = [
        str(c)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace(".", "")
        .replace(":", "")
        for c in df.columns
    ]

    rename_map = {
        "time": "open_time",
        "tiempo": "open_time",
        "fecha": "open_time",
        "deal": "ticket",
        "orden": "ticket",
        "order": "ticket",
        "symbol": "symbol",
        "símbolo": "symbol",
        "simbolo": "symbol",
        "type": "type",
        "tipo": "type",
        "volume": "volume",
        "volumen": "volume",
        "price": "entry_price",
        "precio": "entry_price",
        "s_l": "sl",
        "sl": "sl",
        "t_p": "tp",
        "tp": "tp",
        "profit": "net_profit",
        "beneficio": "net_profit",
        "commission": "commission",
        "comisión": "commission",
        "comision": "commission",
        "swap": "swap",
    }

    df = df.rename(columns={c: rename_map.get(c, c) for c in df.columns})

    if "net_profit" not in df.columns:
        profit_cols = [c for c in df.columns if "profit" in c or "beneficio" in c]
        if profit_cols:
            df["net_profit"] = pd.to_numeric(df[profit_cols[-1]], errors="coerce")
        else:
            df["net_profit"] = 0

    df["net_profit"] = pd.to_numeric(df["net_profit"], errors="coerce").fillna(0)

    if "type" in df.columns:
        df["type"] = df["type"].astype(str).str.lower().str.strip()
        df = df[df["type"].isin(["buy", "sell", "compra", "venta"])]

    if df.empty:
        return pd.DataFrame()

    if "open_time" in df.columns:
        df["open_time"] = pd.to_datetime(df["open_time"], errors="coerce")
    else:
        date_cols = [c for c in df.columns if "time" in c or "fecha" in c or "tiempo" in c]
        if date_cols:
            df["open_time"] = pd.to_datetime(df[date_cols[0]], errors="coerce")
        else:
            df["open_time"] = pd.NaT

    df = df.dropna(subset=["open_time"])

    df["is_winner"] = df["net_profit"] > 0
    df["hour"] = df["open_time"].dt.hour
    df["date"] = df["open_time"].dt.date
    df["weekday_num"] = df["open_time"].dt.weekday
    df["weekday"] = df["open_time"].dt.day_name()

    df["duration_minutes"] = np.nan

    def get_session(hour):
        if 18 <= hour or hour < 2:
            return "Asia"
        elif 2 <= hour < 7:
            return "Londres"
        elif 7 <= hour < 12:
            return "Nueva York"
        return "Fuera de sesión"

    df["session"] = df["hour"].apply(get_session)

    if "volume" in df.columns:
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce")

    return df.reset_index(drop=True)
