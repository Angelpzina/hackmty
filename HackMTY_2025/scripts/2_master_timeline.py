from __future__ import annotations
import os
import json
import pandas as pd

ART_DIR = "artifacts"
os.makedirs(ART_DIR, exist_ok=True)

MPATH = os.path.join(ART_DIR, "master.pkl")
TPATH = os.path.join(ART_DIR, "timeline.pkl")
MPATH_JSON = os.path.join(ART_DIR, "metadata.json")

# Columnas que esperas (activas solo si existen)
NUM_SUM_COLS   = ["qty_used", "waste_units", "qty_loaded", "qty_ret"]
NUM_MEAN_COLS  = ["days_to_expire_at_flight"]
TIME_CANDIDATES = ["timestamp", "datetime", "fecha", "created_at"]

def _ensure_date_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Garantiza una columna 'date' de tipo datetime normalizada (medianoche).
    Si ya viene 'date', la parsea; si no, intenta derivarla de columnas temporales comunes.
    """
    if "date" in df.columns:
        if not pd.api.types.is_datetime64_any_dtype(df["date"]):
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"]).copy()
        df["date"] = df["date"].dt.normalize()
        return df

    # Buscar una columna temporal alternativa
    time_col = next((c for c in TIME_CANDIDATES if c in df.columns), None)
    if time_col is None:
        raise RuntimeError(
            f"No encuentro columna temporal para construir 'date'. "
            f"Tengo columnas: {df.columns.tolist()}"
        )
    if not pd.api.types.is_datetime64_any_dtype(df[time_col]):
        df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=[time_col]).copy()
    df["date"] = df[time_col].dt.normalize()
    return df

def build_timeline():
    if not os.path.exists(MPATH):
        raise FileNotFoundError("No existe artifacts/master.pkl. Corre primero scripts/1_setup_load.py")

    df = pd.read_pickle(MPATH)

    # 0) Validaciones básicas
    if df is None or df.empty:
        print("[master_timeline] Master vacío. Genero timeline vacío.")
        tline = pd.DataFrame(columns=["date"]).set_index("date")
        tline.to_pickle(TPATH)
        with open(MPATH_JSON, "w") as f:
            json.dump({"fields": [], "n_days": 0}, f, indent=2)
        print("[OK] timeline.pkl vacío (0 días).")
        return

    # 1) Asegurar columna 'date'
    df = _ensure_date_column(df)

    # 2) Armar agregaciones solo con columnas presentes
    agg = {}
    present_sum = [c for c in NUM_SUM_COLS if c in df.columns]
    present_mean = [c for c in NUM_MEAN_COLS if c in df.columns]

    for c in present_sum:
        agg[c] = "sum"
    for c in present_mean:
        agg[c] = "mean"

    # Fallback mínimo para evitar "No objects to concatenate"
    # Si no hay ninguna de las columnas esperadas, cuenta filas por día.
    if not agg:
        # Usamos la primera columna existente solo para contar registros por día
        first_col = df.columns[0]
        agg = {"n_records": (first_col, "count")}

        # Usar Named Aggregation si estamos mezclando dict de tuplas
        grouped = df.groupby("date", as_index=True)
        tline = grouped.agg(**agg).sort_index()
    else:
        # Modo clásico dict simple (todas las cols mapean a función)
        grouped = df.groupby("date", as_index=True)
        try:
            tline = grouped.agg(agg).sort_index()
        except Exception as e:
            # Si hay colisiones de estilos de agg, pasamos a Named Aggregation explícita
            named_aggs = {k: (k, v) for k, v in agg.items()}
            tline = grouped.agg(**named_aggs).sort_index()

    # 3) Si por alguna razón queda vacío, guardamos estructura mínima
    if tline is None or tline.empty:
        print("[master_timeline] Resultado vacío tras agg. Guardo estructura mínima.")
        tline = pd.DataFrame(index=pd.Index([], name="date"))

    # 4) Guardar resultados como antes
    tline.to_pickle(TPATH)
    meta = {
        "fields": list(tline.columns),
        "n_days": int(tline.shape[0]),
    }
    with open(MPATH_JSON, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"[OK] timeline.pkl con {tline.shape[0]} días. Campos: {list(tline.columns)}")

if __name__ == "__main__":
    build_timeline()
