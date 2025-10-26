
from __future__ import annotations
from pathlib import Path
import os
import pandas as pd
import numpy as np

ART_DIR = os.path.join("artifacts")
os.makedirs(ART_DIR, exist_ok=True)

BASE_DIR = Path(__file__).resolve().parent.parent
# Buscar automáticamente la carpeta 'data' aunque esté en otro nivel
CANDIDATES = [
    BASE_DIR / "data",
    BASE_DIR.parent / "data",
    Path(__file__).resolve().parent / "data",
    Path(__file__).resolve().parent.parent / "data",
]

DATA_DIR = next((p for p in CANDIDATES if p.exists()), None)
if DATA_DIR is None:
    raise FileNotFoundError("❌ No se encontró carpeta 'data' en ninguna ruta esperada.")



FILE_CONS = "[HackMTY2025]_ConsumptionPrediction_Dataset_v1.xlsx"
FILE_EXP  = "[HackMTY2025]_ExpirationDateManagement_Dataset_v1.xlsx"
FILE_PROD = "[HackMTY2025]_ProductivityEstimation_Dataset_v1.xlsx"

def _to_datetime(s):
    try:
        return pd.to_datetime(s, errors="coerce")
    except Exception:
        return pd.to_datetime(pd.Series(s), errors="coerce").values

def load_all():
    cons_path = os.path.join(DATA_DIR, FILE_CONS)
    exp_path  = os.path.join(DATA_DIR, FILE_EXP)
    prod_path = os.path.join(DATA_DIR, FILE_PROD)

    cons = pd.read_excel(cons_path) if os.path.exists(cons_path) else pd.DataFrame()
    exp  = pd.read_excel(exp_path)  if os.path.exists(exp_path)  else pd.DataFrame()
    prod = pd.read_excel(prod_path) if os.path.exists(prod_path) else pd.DataFrame()

    # Normalize date columns
    for df in [cons, exp, prod]:
        if not isinstance(df, pd.DataFrame) or df.empty:
            continue
        if "date" not in df.columns:
            # try common candidates
            cand = None
            for c in df.columns:
                if str(c).lower() in {"date", "fecha", "flight_date"}:
                    cand = c; break
            if cand is None:
                for c in df.columns:
                    if "date" in str(c).lower():
                        cand = c; break
            if cand is not None:
                df["date"] = _to_datetime(df[cand])
        else:
            df["date"] = _to_datetime(df["date"])

    # Save raw copies (only if not empty)
    if not cons.empty: cons.to_pickle(os.path.join(ART_DIR, "cons_raw.pkl"))
    if not exp.empty:  exp.to_pickle(os.path.join(ART_DIR, "exp_raw.pkl"))
    if not prod.empty: prod.to_pickle(os.path.join(ART_DIR, "master_prod_raw.pkl"))

    # Build a master by left-joining on ['flight','product','date'] when available
    def std_cols(df):
        return {c.lower(): c for c in df.columns}

    master = None
    if not cons.empty:
        master = cons.copy()
    if master is None:
        master = pd.DataFrame()

    # Ensure some expected names exist
    rename_map = {}
    for k in list(master.columns):
        lk = k.lower()
        if lk == "qtyused" or lk == "qty used":
            rename_map[k] = "qty_used"
    if rename_map:
        master = master.rename(columns=rename_map)

    # Merge expiration / waste info if present
    if not exp.empty:
        on_cols = [c for c in ["flight","product","date"] if c in master.columns and c in exp.columns]
        if not on_cols:
            on_cols = [c for c in ["date"] if c in master.columns and c in exp.columns]
        exp_cols = [c for c in exp.columns if c not in on_cols]  # avoid dup
        master = pd.merge(master, exp[on_cols+exp_cols], on=on_cols, how="left")

    # Basic derived columns if missing
    if "waste_units" not in master.columns and "qty_ret" in master.columns:
        try:
            master["waste_units"] = master["qty_ret"].clip(lower=0)
        except Exception:
            pass

    # Normalize 'date'
    if "date" in master.columns:
        master["date"] = _to_datetime(master["date"])
        master = master.sort_values("date")

    # Save
    master.to_pickle(os.path.join(ART_DIR, "master.pkl"))
    print(f"[OK] Guardado artifacts/master.pkl con {len(master)} filas y {len(master.columns)} columnas.")
    print(f"[INFO] Columnas: {list(master.columns)}")

if __name__ == "__main__":
    load_all()
