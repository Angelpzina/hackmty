from __future__ import annotations
import os, json, math
import pandas as pd
import numpy as np

ART_DIR = "artifacts"
os.makedirs(ART_DIR, exist_ok=True)

MPATH = os.path.join(ART_DIR, "master.pkl")
BPATH = os.path.join(ART_DIR, "buffer_table.pkl")
META_PATH = os.path.join(ART_DIR, "training_metadata.json")

TARGET_CANDIDATES = [
    "qty_used", "Quantity", "qty_consumed", "used_units", "consumption",
    "demand", "sales", "qty_sold", "qty_out", "cantidad_usada"
]

PRODUCT_COL_CANDIDATES = [
    ["product", "product_name"],
    ["product"],
    ["product_name"],
    ["sku"],
    ["item"],
]

def _pick_target(df: pd.DataFrame) -> str | None:
    # 1) si hay metadata de entrenamiento, úsala
    if os.path.exists(META_PATH):
        try:
            meta = json.load(open(META_PATH))
            tgt = meta.get("target")
            if tgt and tgt in df.columns and pd.api.types.is_numeric_dtype(pd.to_numeric(df[tgt], errors="coerce")):
                return tgt
        except Exception:
            pass
    # 2) candidatos conocidos
    for c in TARGET_CANDIDATES:
        if c in df.columns:
            s = pd.to_numeric(df[c], errors="coerce")
            if s.notna().any():
                return c
    # 3) fallback: columna numérica con mayor varianza
    num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(pd.to_numeric(df[c], errors="coerce"))]
    if not num_cols:
        return None
    variances = pd.DataFrame({
        "col": num_cols,
        "var": [pd.to_numeric(df[c], errors="coerce").var() for c in num_cols]
    }).dropna().sort_values("var", ascending=False)
    return variances["col"].iloc[0] if not variances.empty else None

def _pick_group_cols(df: pd.DataFrame) -> list[str] | None:
    for cand in PRODUCT_COL_CANDIDATES:
        if all(c in df.columns for c in cand):
            return cand
    return None

def _q95(series: pd.Series) -> float:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return np.nan
    # usar método robusto de cuantiles
    return float(s.quantile(0.95, interpolation="linear"))

def build_buffer_table():
    if not os.path.exists(MPATH):
        raise FileNotFoundError("No existe artifacts/master.pkl. Corre primero scripts/1_setup_load.py")

    df = pd.read_pickle(MPATH)

    if df is None or df.empty:
        # guardar tabla vacía pero con columnas estándar
        tab = pd.DataFrame(columns=["avg", "p95", "total", "reco_buffer"])
        tab.to_pickle(BPATH)
        print("[WARN] master vacío. Guardé buffer_table.pkl vacío.")
        return

    target = _pick_target(df)
    if target is None:
        raise RuntimeError("No encontré una columna objetivo numérica (e.g., 'qty_used' o 'Quantity').")

    # asegurar numérico
    df[target] = pd.to_numeric(df[target], errors="coerce")

    # opcional: si tienes fecha y quieres filtrar a ventana reciente, activa esto
    # if "date" in df.columns:
    #     df = df.sort_values("date")
    #     cutoff = df["date"].max() - pd.Timedelta(days=180)
    #     df = df[df["date"] >= cutoff].copy()

    grp_cols = _pick_group_cols(df)

    if grp_cols:
        g = df.groupby(grp_cols)[target]
        tab = g.agg(
            avg=("mean"),
            p95=_q95,
            total=("sum")
        ).reset_index()
    else:
        s = df[target]
        tab = pd.DataFrame({
            "avg": [s.mean()],
            "p95": [_q95(s)],
            "total": [s.sum()]
        })

    # buffer recomendado = techo del p95 (entero no negativo)
    tab["reco_buffer"] = tab["p95"].apply(lambda x: int(max(0, math.ceil(x))) if pd.notna(x) else 0)

    tab.to_pickle(BPATH)
    cols_info = grp_cols if grp_cols else []
    print(f"[OK] Guardado {BPATH} usando target='{target}' agrupando por {cols_info if cols_info else '[sin grupos]'}")
    if grp_cols:
        print(f"[OK] Filas: {len(tab)}  | Ejemplo:\n{tab.head(3)}")
    else:
        print(f"[OK] Resumen global: {tab.to_dict(orient='records')[0]}")

if __name__ == "__main__":
    build_buffer_table()
