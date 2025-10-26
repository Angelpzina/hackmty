from __future__ import annotations
import os, json, warnings
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from joblib import dump

warnings.filterwarnings("ignore", category=FutureWarning)

ART_DIR = "artifacts"
os.makedirs(ART_DIR, exist_ok=True)

MPATH = os.path.join(ART_DIR, "master.pkl")
MODEL_PATH = os.path.join(ART_DIR, "pipeline_rf.joblib")
META_PATH = os.path.join(ART_DIR, "training_metadata.json")  # NUEVO

TARGET_CANDIDATES = [
    "qty_used", "qty_consumed", "used_units", "consumption", "demand",
    "sales", "qty_sold", "qty_out", "cantidad_usada"
]

TIME_CANDIDATES = ["date", "timestamp", "datetime", "fecha", "created_at"]

def _ensure_datetime(df: pd.DataFrame) -> tuple[pd.DataFrame, str | None]:
    """Normaliza/crea columna 'date' si existe alguna temporal; regresa nombre usado."""
    time_col = next((c for c in TIME_CANDIDATES if c in df.columns), None)
    if time_col is None:
        return df, None
    if not pd.api.types.is_datetime64_any_dtype(df[time_col]):
        df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=[time_col]).copy()
    if time_col != "date":
        df["date"] = df[time_col]
    df["date"] = df["date"].dt.tz_localize(None) if getattr(df["date"].dtype, "tz", None) else df["date"]
    return df, "date"

def _pick_target(df: pd.DataFrame) -> str | None:
    for t in TARGET_CANDIDATES:
        if t in df.columns and pd.api.types.is_numeric_dtype(df[t]):
            return t
    # fallback: mayor varianza numérica razonable (excluye obvias auxiliares)
    num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    blacklist = {"year", "month", "day", "dow", "weekofyear", "iso_week", "weekday", "hour", "minute"}
    num_cols = [c for c in num_cols if c.lower() not in blacklist]
    if not num_cols:
        return None
    variances = df[num_cols].var(numeric_only=True).sort_values(ascending=False)
    return variances.index[0] if not variances.empty else None

def _add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    if "date" not in df.columns:
        return df
    d = df["date"]
    df = df.copy()
    df["dow"] = d.dt.dayofweek
    df["month"] = d.dt.month
    # compatibilidad pandas viejas/nuevas
    try:
        df["weekofyear"] = d.dt.isocalendar().week.astype(int)
    except Exception:
        df["weekofyear"] = d.dt.weekofyear
    return df

def _add_lag_features(df: pd.DataFrame, target: str) -> pd.DataFrame:
    if "date" not in df.columns or target not in df.columns:
        return df
    df = df.sort_values("date").copy()
    df[f"{target}_lag_1"] = df[target].shift(1)
    df[f"{target}_lag_7"] = df[target].shift(7)
    df[f"{target}_roll7_mean"] = df[target].rolling(window=7, min_periods=1).mean().shift(1)
    return df

def train_simple():
    if not os.path.exists(MPATH):
        raise FileNotFoundError("No existe artifacts/master.pkl. Corre primero scripts/1_setup_load.py")

    df: pd.DataFrame = pd.read_pickle(MPATH)

    if df is None or df.empty:
        print("[WARN] master.pkl está vacío; no entreno.")
        return

    # Asegurar fecha y enriquecer
    df, date_col = _ensure_datetime(df)
    target = _pick_target(df)

    if target is None:
        print("[WARN] No encontré una columna objetivo numérica plausible; me salto el entrenamiento.")
        return

    if target != "qty_used":
        print(f"[INFO] Objetivo seleccionado automáticamente: '{target}' (no se encontró 'qty_used').")

    # Enriquecer con features temporales y lags si hay fecha
    df = _add_time_features(df)
    df = _add_lag_features(df, target)

    # Definir features numéricos (excluir target y columnas claramente no predictoras)
    drop_cols = {target}
    drop_cols.update({"date"})  # el datetime no entra directo (ya derivamos dow/month/week)
    # también evita IDs 100% únicos (si existen)
    id_like = [c for c in df.columns if c.lower() in {"id", "ticket_id", "event_id"}]
    drop_cols.update(id_like)

    candidate_features = [c for c in df.columns
                          if c not in drop_cols and pd.api.types.is_numeric_dtype(df[c])]

    if not candidate_features:
        print("[WARN] No hay columnas numéricas para usar como features; no entreno.")
        return

    # Separar X, y (quita filas con y NaN)
    df = df.dropna(subset=[target]).copy()
    X = df[candidate_features]
    y = df[target].astype(float)

    # Evitar columnas con varianza cero
    nunique = X.nunique()
    keep = nunique[nunique > 1].index.tolist()
    if not keep:
        print("[WARN] Todas las features tienen varianza cero; no entreno.")
        return
    X = X[keep]

    # Preprocesamiento + modelo
    pre = ColumnTransformer([
        ("num", Pipeline(steps=[
            ("imp", SimpleImputer(strategy="median")),
            ("sc", StandardScaler())
        ]), X.columns.tolist())
    ])

    model = Pipeline([
        ("pre", pre),
        ("rf", RandomForestRegressor(
            n_estimators=200,
            max_depth=None,
            random_state=7,
            n_jobs=-1
        ))
    ])

    model.fit(X, y)

    # Guardar modelo y metadatos
    dump(model, MODEL_PATH)
    meta = {
        "target": target,
        "features": X.columns.tolist(),
        "n_rows_train": int(X.shape[0]),
        "date_col_present": bool(date_col),
        "notes": "Modelo RandomForestRegressor con enriquecimiento temporal/lag si hubo fecha."
    }
    with open(META_PATH, "w") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    # Compatibilidad con otros scripts que esperaban este archivo
    with open(os.path.join(ART_DIR, "sarimax_summary.json"), "w") as f:
        json.dump({"note": "placeholder for compatibility"}, f)

    print(f"[OK] Guardado {MODEL_PATH}")
    print(f"[OK] Target: {target} | Features: {len(X.columns)} | Filas entrenadas: {X.shape[0]}")
    if "date" in df.columns:
        extra = [c for c in X.columns if c.endswith(("_lag_1", "_lag_7", "roll7_mean"))]
        if extra:
            print(f"[OK] Features temporales incluidas: {extra}")

if __name__ == "__main__":
    train_simple()


