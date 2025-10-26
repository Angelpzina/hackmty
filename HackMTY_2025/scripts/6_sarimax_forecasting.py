from __future__ import annotations
import os, json
from pathlib import Path
import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX

# Rutas robustas
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
ART_DIR = BASE_DIR / "artifacts"; ART_DIR.mkdir(parents=True, exist_ok=True)

MPATH = ART_DIR / "master.pkl"
FPATH = ART_DIR / "sarimax_forecast.pkl"
JPATH = ART_DIR / "sarimax_summary.json"
META_PATH = ART_DIR / "training_metadata.json"

TARGET_CANDIDATES = ["qty_used","Quantity","qty_consumed","used_units","consumption",
                     "demand","sales","qty_sold","qty_out","cantidad_usada"]
DATE_CANDIDATES = ["date","timestamp","datetime","fecha","created_at"]

H = 30
ORDER = (2,1,2)
SEASONAL_ORDER = (1,1,1,7)
MIN_OBS = 3
MIN_VAR = 1e-9
FORCE_GLOBAL = True  # <<< importantísimo: ignora grupos para asegurar forecast

def _pick_target(df: pd.DataFrame) -> str | None:
    if META_PATH.exists():
        try:
            meta = json.loads(META_PATH.read_text())
            t = meta.get("target")
            if t in df.columns:
                return t
        except Exception:
            pass
    for c in TARGET_CANDIDATES:
        if c in df.columns:
            return c
    return None

def _pick_date(df: pd.DataFrame) -> str | None:
    for c in DATE_CANDIDATES:
        if c in df.columns:
            return c
    return None

def _infer_freq(idx: pd.DatetimeIndex) -> str:
    f = pd.infer_freq(idx)
    if f: return f
    span = (idx.max() - idx.min()).days + 1
    if span <= 0: return "D"
    density = idx.normalize().nunique() / span
    return "W" if density < 0.3 else "D"

def _prep_series(df: pd.DataFrame, date_col: str, target: str):
    s = df[[date_col, target]].copy()
    s[date_col] = pd.to_datetime(s[date_col], errors="coerce")
    s = s.dropna(subset=[date_col, target]).sort_values(date_col)
    if s.empty: return None, None, "empty"
    idx = pd.DatetimeIndex(s[date_col])
    freq = _infer_freq(idx)
    rule = "W" if freq == "W" else "D"
    y = s.set_index(date_col).resample(rule)[target].sum()
    y = pd.to_numeric(y, errors="coerce").astype(float).fillna(0.0)
    if y.dropna().shape[0] == 0: return None, None, "all_nan"
    return y, rule, None

def _fit_sarimax(y: pd.Series):
    try:
        model = SARIMAX(y, order=ORDER, seasonal_order=SEASONAL_ORDER,
                        enforce_stationarity=False, enforce_invertibility=False)
        return model.fit(disp=False)
    except Exception:
        return None

def _forecast_index(last_idx: pd.Timestamp, h: int, freq: str):
    from pandas.tseries.frequencies import to_offset
    start = last_idx + to_offset(freq)
    return pd.date_range(start, periods=h, freq=freq)

def _forecast_naive(y: pd.Series, h: int, freq: str):
    # promedio de los últimos k (mejor que puro último valor si hay ruido)
    k = min(5, len(y))
    val = float(y.iloc[-k:].mean()) if k>0 else float(y.iloc[-1])
    idx = _forecast_index(y.index[-1], h, freq)
    return pd.DataFrame({"date": idx, "yhat": val, "y_lo": np.nan, "y_hi": np.nan})

def build_sarimax():
    if not MPATH.exists():
        raise FileNotFoundError(f"No existe {MPATH}. Corre primero scripts/1_setup_load.py")

    df = pd.read_pickle(MPATH)
    if df is None or df.empty:
        print("[WARN] master vacío")
        return

    target = _pick_target(df)
    if target is None:
        print("[WARN] Sin columna objetivo (p.ej. 'Quantity')")
        return

    date_col = _pick_date(df)
    if date_col is None:
        print("[WARN] Sin columna de fecha")
        return

    # Siempre global para asegurar forecast
    y, freq, err = _prep_series(df, date_col, target)
    summaries = []
    if y is None:
        JPATH.write_text(json.dumps({"target": target, "reason": err or "prep_failed"}, indent=2))
        print("[WARN] Serie global vacía")
        return

    status = ""
    if len(y.dropna()) >= MIN_OBS and float(y.var()) >= MIN_VAR:
        res = _fit_sarimax(y)
        if res is not None:
            try:
                fc = res.get_forecast(steps=H)
                mean = fc.predicted_mean.values
                ci = fc.conf_int(alpha=0.2).values.T  # low, high
                idx = _forecast_index(y.index[-1], H, freq)
                out = pd.DataFrame({"date": idx, "yhat": mean, "y_lo": ci[0], "y_hi": ci[1]})
                status = "sarimax_ok"
            except Exception:
                out = _forecast_naive(y, H, freq); status = "naive_after_fail"
        else:
            out = _forecast_naive(y, H, freq); status = "naive_fallback"
    else:
        out = _forecast_naive(y, H, freq); status = "naive_too_short_or_constant"

    out["target"] = target
    out = out.dropna(subset=["date"]).sort_values("date")
    out.to_pickle(FPATH)

    JPATH.write_text(json.dumps({
        "target": target,
        "horizon": H,
        "order": ORDER,
        "seasonal_order": SEASONAL_ORDER,
        "freq_used": freq,
        "n_obs": int(len(y)),
        "var": float(y.var()),
        "status": status
    }, indent=2, ensure_ascii=False))

    print(f"[OK] Guardado {FPATH} ({len(out)} filas) | status={status} | freq={freq} | n_obs={len(y)}")

if __name__ == "__main__":
    build_sarimax()

# ===================== NUEVO BLOQUE: Pronóstico + Buffer (Pegar al final) =====================
import json, os
import pandas as pd
import streamlit as st

st.divider()
st.header("📈 Pronóstico (SARIMAX)")

# Cargar meta para saber el target real
meta = {}
if os.path.exists("artifacts/training_metadata.json"):
    meta = json.load(open("artifacts/training_metadata.json"))
target = meta.get("target", "Quantity")

if not os.path.exists("artifacts/sarimax_forecast.pkl"):
    st.warning("No encuentro `artifacts/sarimax_forecast.pkl`. Corre `scripts/6_sarimax_forecasting.py`.")
else:
    fc = pd.read_pickle("artifacts/sarimax_forecast.pkl")
    fc["date"] = pd.to_datetime(fc["date"], errors="coerce")
    fc = fc.dropna(subset=["date"]).sort_values("date")

    # Selector de producto si viene por grupos
    grp_cols = [c for c in ["product","product_name"] if c in fc.columns]
    if grp_cols:
        fc["_label"] = fc[grp_cols].astype(str).agg(" | ".join, axis=1)
        options = sorted(fc["_label"].unique().tolist())
        pick = st.selectbox("Producto", options) if options else None
        fc_view = fc[fc["_label"] == pick] if pick else fc
    else:
        fc_view = fc

    if fc_view.empty:
        st.info("No hay datos para graficar con el filtro actual.")
    else:
        # Línea central
        st.line_chart(fc_view.set_index("date")[["yhat"]], height=300)
        # Banda (opcional, si tienes altair)
        try:
            import altair as alt
            base = alt.Chart(fc_view).encode(x="date:T")
            band = base.mark_area(opacity=0.2).encode(y="y_lo:Q", y2="y_hi:Q")
            line = base.mark_line().encode(y="yhat:Q")
            st.altair_chart(band + line, use_container_width=True)
        except Exception:
            pass

st.header("🧯 Buffer recomendado (p95)")
if not os.path.exists("artifacts/buffer_table.pkl"):
    st.warning("No encuentro `artifacts/buffer_table.pkl`. Corre `scripts/4_buffer_recommendation.py`.")
else:
    buf = pd.read_pickle("artifacts/buffer_table.pkl")
    st.dataframe(buf, use_container_width=True)

