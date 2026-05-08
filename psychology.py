"""
Data Loader - Carga y limpieza automática de exportaciones MT5
Detecta columnas, limpia datos, normaliza fechas
"""

import pandas as pd
import numpy as np
import re
from io import BytesIO
import streamlit as st


# Mapeo de nombres de columnas MT5 (español e inglés)
COLUMN_ALIASES = {
    'open_time': ['hora apertura', 'open time', 'fecha apertura', 'time', 'open', 'apertura'],
    'ticket': ['ticket', 'posición', 'position', 'deal', 'orden'],
    'symbol': ['símbolo', 'symbol', 'instrumento'],
    'type': ['tipo', 'type', 'direction', 'dirección'],
    'volume': ['volumen', 'volume', 'lots', 'lotes', 'size'],
    'open_price': ['precio apertura', 'open price', 'open', 'precio de apertura', 'entry'],
    'sl': ['stop loss', 's/l', 'sl'],
    'tp': ['take profit', 't/p', 'tp'],
    'close_time': ['hora cierre', 'close time', 'fecha cierre', 'close'],
    'close_price': ['precio cierre', 'close price', 'close', 'precio de cierre', 'exit'],
    'commission': ['comisión', 'commission', 'comision'],
    'swap': ['swap', 'rollover'],
    'profit': ['beneficio', 'profit', 'ganancia', 'p&l', 'resultado', 'benefit']
}


def load_and_clean_data(uploaded_file) -> pd.DataFrame:
    """
    Carga un archivo Excel/CSV exportado de MT5 y lo normaliza.
    Returns DataFrame limpio con columnas estandarizadas.
    """
    try:
        # Detectar tipo de archivo
        filename = uploaded_file.name.lower()
        
        if filename.endswith('.csv'):
            df = _load_csv(uploaded_file)
        else:
            df = _load_excel(uploaded_file)
        
        if df is None or df.empty:
            return None
        
        # Pipeline de limpieza
        df = _normalize_columns(df)
        df = _clean_data(df)
        df = _calculate_derived_fields(df)
        df = _classify_sessions(df)
        
        return df
    
    except Exception as e:
        st.error(f"Error cargando archivo: {str(e)}")
        return None


def _load_csv(file) -> pd.DataFrame:
    """Carga CSV con detección automática de separador"""
    content = file.read().decode('utf-8', errors='ignore')
    file.seek(0)
    
    # Detectar separador
    sep = ',' if content.count(',') > content.count(';') else ';'
    
    # Intentar con diferentes encodings y skip de filas de cabecera MT5
    for skiprows in [0, 1, 2, 3]:
        try:
            df = pd.read_csv(file, sep=sep, skiprows=skiprows, encoding='utf-8')
            file.seek(0)
            if len(df.columns) >= 8:
                return df
        except:
            file.seek(0)
    
    return pd.read_csv(file, sep=sep)


def _load_excel(file) -> pd.DataFrame:
    """Carga Excel con detección de hoja correcta"""
    xl = pd.ExcelFile(file)
    
    # Buscar hoja con datos de trading
    best_sheet = None
    best_cols = 0
    
    for sheet in xl.sheet_names:
        try:
            # Probar diferentes filas de inicio
            for skiprows in [0, 1, 2, 3, 4]:
                df = pd.read_excel(file, sheet_name=sheet, skiprows=skiprows)
                file.seek(0)
                
                # Verificar que tiene columnas de trading
                cols_lower = [str(c).lower() for c in df.columns]
                score = sum(1 for alias_list in COLUMN_ALIASES.values() 
                           for alias in alias_list 
                           if any(alias in col for col in cols_lower))
                
                if score > best_cols and len(df) > 5:
                    best_cols = score
                    best_sheet = (sheet, skiprows)
        except:
            file.seek(0)
    
    if best_sheet:
        file.seek(0)
        return pd.read_excel(file, sheet_name=best_sheet[0], skiprows=best_sheet[1])
    
    file.seek(0)
    return pd.read_excel(file)


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Detecta y renombra columnas al estándar del sistema"""
    rename_map = {}
    cols_lower = {col: str(col).lower().strip() for col in df.columns}
    
    for standard_name, aliases in COLUMN_ALIASES.items():
        for col, col_lower in cols_lower.items():
            if col in rename_map.values():
                continue
            for alias in aliases:
                if alias in col_lower and standard_name not in rename_map.values():
                    rename_map[col] = standard_name
                    break
    
    df = df.rename(columns=rename_map)
    return df


def _clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Limpieza profunda del DataFrame"""
    
    # Eliminar filas completamente vacías
    df = df.dropna(how='all')
    
    # Eliminar filas de resumen/totales (MT5 las agrega al final)
    if 'profit' in df.columns:
        df = df[pd.to_numeric(df['profit'], errors='coerce').notna()]
    
    # Convertir fechas
    for date_col in ['open_time', 'close_time']:
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce', dayfirst=True)
    
    # Convertir numéricos
    numeric_cols = ['volume', 'open_price', 'close_price', 'sl', 'tp', 
                    'commission', 'swap', 'profit']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Normalizar tipo (buy/sell)
    if 'type' in df.columns:
        df['type'] = df['type'].astype(str).str.lower().str.strip()
        df['type'] = df['type'].map(lambda x: 'buy' if 'buy' in x or 'compra' in x 
                                    else ('sell' if 'sell' in x or 'venta' in x else x))
    
    # Filtrar solo XAUUSD si hay múltiples símbolos
    if 'symbol' in df.columns:
        xau_mask = df['symbol'].astype(str).str.upper().str.contains('XAU|GOLD|ORO', na=False)
        if xau_mask.sum() > 0:
            df = df[xau_mask]
    
    # Eliminar filas sin profit o fechas
    df = df.dropna(subset=['profit', 'open_time', 'close_time'])
    
    # Ordenar cronológicamente
    df = df.sort_values('open_time').reset_index(drop=True)
    
    return df


def _calculate_derived_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Calcular campos derivados importantes"""
    
    # Duración en segundos
    df['duration_seconds'] = (df['close_time'] - df['open_time']).dt.total_seconds()
    df['duration_minutes'] = df['duration_seconds'] / 60
    
    # Profit neto (incluyendo comisión y swap)
    df['net_profit'] = df['profit'] + df.get('commission', 0).fillna(0) + df.get('swap', 0).fillna(0)
    
    # Resultado binario
    df['is_winner'] = df['net_profit'] > 0
    df['is_loser'] = df['net_profit'] < 0
    
    # Fecha y hora por separado
    df['date'] = df['open_time'].dt.date
    df['hour'] = df['open_time'].dt.hour
    df['weekday'] = df['open_time'].dt.day_name()
    df['weekday_num'] = df['open_time'].dt.dayofweek
    
    # Riesgo en puntos (si hay SL)
    if 'sl' in df.columns and 'open_price' in df.columns:
        df['sl_pips'] = abs(df['open_price'] - df['sl'].fillna(df['open_price'])) * 10
    
    # Balance acumulado (ordenado por tiempo)
    df['cumulative_profit'] = df['net_profit'].cumsum()
    
    # Número de operación del día
    df['trade_num_of_day'] = df.groupby('date').cumcount() + 1
    
    # Gap entre operaciones (tiempo desde cierre de anterior a apertura de siguiente)
    df['time_since_last_close'] = (df['open_time'] - df['close_time'].shift(1)).dt.total_seconds()
    
    return df


def _classify_sessions(df: pd.DataFrame) -> pd.DataFrame:
    """Clasificar operaciones por sesión de mercado (hora UTC)"""
    
    def get_session(hour):
        if 0 <= hour < 8:
            return 'Asiática'
        elif 8 <= hour < 12:
            return 'Londres'
        elif 12 <= hour < 17:
            return 'Nueva York'
        elif 17 <= hour < 21:
            return 'Solapamiento NY-Londres'
        else:
            return 'Asiática'
    
    df['session'] = df['hour'].apply(get_session)
    
    return df
