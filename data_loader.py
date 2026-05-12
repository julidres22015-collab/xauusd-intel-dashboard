import pandas as pd
import numpy as np

def load_and_clean_data(uploaded_file):
    if uploaded_file is None:
        return pd.DataFrame()

    # Leer archivo completo sin encabezados
    if uploaded_file.name.endswith(".csv"):
        raw = pd.read_csv(uploaded_file, header=None)
    else:
        raw = pd.read_excel(uploaded_file, header=None)

    # Buscar fila donde empieza la tabla de operaciones
    header_row = None
    for i in range(len(raw)):
    row_values = raw.iloc[i].fillna("").astype(str).str.lower().tolist()
    row_text = " ".join(map(str, row_values))

        if ("time" in row_text or "tiempo" in row_text or "fecha" in row_text) and (
            "profit" in row_text or "beneficio" in row_text
        ):
            header_row = i
            break

    if header_row is None:
        # Si no encuentra encabezado, intentar lectura normal
        uploaded_file.seek(0)
        df = pd.read_excel(uploaded_file) if not uploaded_file.name.endswith(".csv") else pd.read_csv(uploaded_file)
    else:
        # Usar esa fila como encabezado
        df = raw.iloc[header_row + 1:].copy()
        df.columns = raw.iloc[header_row].astype(str).str.strip()

    # Limpiar columnas vacías
    df = df.dropna(how="all")
    df = df.loc[:, ~df.columns.astype(str).str.contains("^Unnamed", case=False, regex=True)]

    # Normalizar nombres
    df.columns = [
        str(c).strip().lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace(".", "")
        .replace(":", "")
        for c in df.columns
    ]

    # Mapear columnas comunes de MT5
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

    # Si hay varias columnas price, dejar la primera como entry_price
    if "entry_price" not in df.columns:
        price_cols = [c for c in df.columns if "price" in c or "precio" in c]
        if price_cols:
            df["entry_price"] = pd.to_numeric(df[price_cols[0]], errors="coerce")

    # Profit
    if "net_profit" not in df.columns:
        profit_cols = [c for c in df.columns if "profit" in c or "beneficio" in c]
        if profit_cols:
            df["net_profit"] = pd.to_numeric(df[profit_cols[-1]], errors="coerce")
        else:
            df["net_profit"] = 0

    df["net_profit"] = pd.to_numeric(df["net_profit"], errors="coerce").fillna(0)

    # Eliminar filas que no sean operaciones reales
    if "type" in df.columns:
        df["type"] = df["type"].astype(str).str.lower()
        df = df[df["type"].isin(["buy", "sell", "compra", "venta"])]

    # Si no hay type, filtrar por profit distinto de 0
    if df.empty:
        return pd.DataFrame()

    # Fechas
    if "open_time" in df.columns:
        df["open_time"] = pd.to_datetime(df["open_time"], errors="coerce")
    else:
        date_cols = [c for c in df.columns if "time" in c or "fecha" in c]
        if date_cols:
            df["open_time"] = pd.to_datetime(df[date_cols[0]], errors="coerce")
        else:
            df["open_time"] = pd.NaT

    df = df.dropna(subset=["open_time"])

    # Métricas derivadas
    df["is_winner"] = df["net_profit"] > 0
    df["hour"] = df["open_time"].dt.hour
    df["date"] = df["open_time"].dt.date
    df["weekday_num"] = df["open_time"].dt.weekday
    df["weekday"] = df["open_time"].dt.day_name()

    # Duración: si no hay cierre, se deja vacío
    df["duration_minutes"] = np.nan

    # Sesiones aproximadas Colombia
    def get_session(hour):
        if 18 <= hour or hour < 2:
            return "Asia"
        elif 2 <= hour < 7:
            return "Londres"
        elif 7 <= hour < 12:
            return "Nueva York"
        else:
            return "Fuera de sesión"

    df["session"] = df["hour"].apply(get_session)

    # Volumen
    if "volume" in df.columns:
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce")

    return df.reset_index(drop=True)
