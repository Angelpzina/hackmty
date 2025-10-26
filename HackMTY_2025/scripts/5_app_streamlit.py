
import os
import pandas as pd
import streamlit as st

st.set_page_config(page_title="HackMTY 2025 — Forecast", layout="wide")

ART_DIR = "artifacts"
CSV_DIR = os.path.join(ART_DIR, "csv")
PLOTS_DIR = os.path.join(ART_DIR, "plots")

@st.cache_data(show_spinner=False)
def load_master():
    path = os.path.join(ART_DIR, "master.pkl")
    if os.path.exists(path):
        return pd.read_pickle(path)
    return None

def block_series(name: str, target: str):
    st.subheader(f"{name} ({target}) — Histórico y pronóstico")

    m = load_master()
    if m is None or "date" not in m.columns:
        st.warning("No se encontró el master. Corre: `python scripts/1_setup_load.py`")
        return

    # Histórico (simple)
    hist = m[["date", target]] if target in m.columns else None
    if hist is not None:
        hist = hist.dropna().copy()
    else:
        st.warning(f"No existe la columna '{target}' en master.")
        return

    # Pronóstico
    fcsv = os.path.join(CSV_DIR, f"forecast_{target}.csv")
    fpng = os.path.join(PLOTS_DIR, f"{target}.png")
    if not os.path.exists(fcsv) or not os.path.exists(fpng):
        st.info("Aún no hay pronóstico generado. Corre: `python scripts/6_sarimax_forecasting.py`")
        return

    fdf = pd.read_csv(fcsv)
    with st.expander("Ver tabla de pronóstico (CSV)", expanded=False):
        st.dataframe(fdf, width='stretch')

    # Mostrar figura pre-renderizada
    st.image(fpng, use_column_width='stretch')

tabs = st.tabs(["Consumo", "Desperdicio", "Caducidad"])

with tabs[0]:
    block_series("Consumo", "qty_used")
with tabs[1]:
    block_series("Desperdicio", "waste_units")
with tabs[2]:
    block_series("Caducidad", "days_to_expire_at_flight")

st.caption("Si cambiaste nombres de columnas, ajusta `scripts/5_app_streamlit.py`.")


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
            st.altair_chart(band + line, width='stretch')
        except Exception:
            pass

st.header("🧯 Buffer recomendado (p95)")
if not os.path.exists("artifacts/buffer_table.pkl"):
    st.warning("No encuentro `artifacts/buffer_table.pkl`. Corre `scripts/4_buffer_recommendation.py`.")
else:
    buf = pd.read_pickle("artifacts/buffer_table.pkl")
    st.dataframe(buf, width='stretch')

# ===================== BLOQUE: overlay histórico + forecast con ejes + refresh =====================
import os, json, subprocess
import pandas as pd
import streamlit as st

st.divider()
st.header("📈 Pronóstico (SARIMAX) — Histórico vs. Futuro")

# — meta: target real —
meta = {}
if os.path.exists("artifacts/training_metadata.json"):
    meta = json.load(open("artifacts/training_metadata.json"))
target = meta.get("target", "Quantity")

# — botón de actualización end-to-end —
colr1, colr2 = st.columns([1,3])
with colr1:
    if st.button("🔄 Actualizar datos y pronóstico"):
        with st.spinner("Actualizando artefactos (1→6)…"):
            # Lanza cada script en orden; asume que estás en la raíz del repo
            cmds = [
                ["python", "scripts/1_setup_load.py"],
                ["python", "scripts/2_master_timeline.py"],
                ["python", "scripts/3_model_training.py"],
                ["python", "scripts/4_buffer_recommendation.py"],
                ["python", "scripts/6_sarimax_forecasting.py"],
            ]
            ok = True
            for c in cmds:
                r = subprocess.run(c, capture_output=True, text=True)
                if r.returncode != 0:
                    ok = False
                    st.error(f"Falló: {' '.join(c)}\n{r.stderr[:1000]}")
                    break
            if ok:
                st.success("Listo. Artefactos actualizados ✅")
                st.rerun()

with colr2:
    st.markdown(
        "Esta vista muestra el **histórico** (línea fina) y el **pronóstico** (línea gruesa) "
        "del objetivo detectado: **`%s`**. La banda sombreada indica el intervalo de confianza (≈80%%)." % target
    )

# — cargar histórico —
hist = None
dcol = None
if os.path.exists("artifacts/master.pkl"):
    m = pd.read_pickle("artifacts/master.pkl")
    for c in ["date","timestamp","datetime","fecha","created_at"]:
        if c in m.columns:
            dcol = c; break
    if dcol is not None and target in m.columns:
        m[dcol] = pd.to_datetime(m[dcol], errors="coerce")
        hist = m[[dcol, target]].dropna().rename(columns={dcol: "date", target: "y"})
        # agrega por día (si ya viene diario, solo ordena)
        hist = hist.groupby("date", as_index=False)["y"].sum().sort_values("date")

# — cargar forecast —
if not os.path.exists("artifacts/sarimax_forecast.pkl"):
    st.warning("No encuentro `artifacts/sarimax_forecast.pkl`. Corre `scripts/6_sarimax_forecasting.py`.")
else:
    fc = pd.read_pickle("artifacts/sarimax_forecast.pkl").copy()
    fc["date"] = pd.to_datetime(fc["date"], errors="coerce")
    fc = fc.dropna(subset=["date"]).sort_values("date")

    # selector de producto (si aplica)
    grp_cols = [c for c in ["product","product_name"] if c in fc.columns]
    if grp_cols:
        fc["_label"] = fc[grp_cols].astype(str).agg(" | ".join, axis=1)
        options = sorted(fc["_label"].unique().tolist())
        pick = st.selectbox("Filtrar producto", options) if options else None
        if pick:
            fc = fc[fc["_label"] == pick]
        # histórico por el mismo grupo (si tu master tiene esas columnas)
        if hist is not None and set(grp_cols).issubset(m.columns):
            mask = (m[grp_cols].astype(str).agg(" | ".join, axis=1) == pick) if pick else slice(None)
            mh = m.loc[mask, [dcol, target]].dropna()
            if not mh.empty:
                mh[dcol] = pd.to_datetime(mh[dcol], errors="coerce")
                hist = mh.groupby(dcol, as_index=False)[target].sum().rename(columns={dcol: "date", target: "y"}).sort_values("date")

    # — construir gráfico con Altair (ejes con títulos) —
    try:
        import altair as alt
        # histórico (si existe)
        charts = []
        if hist is not None and not hist.empty:
            ch_hist = alt.Chart(hist).mark_line(opacity=0.6).encode(
                x=alt.X("date:T", title="Tiempo (día)"),
                y=alt.Y("y:Q", title=f"Unidades ({target})")
            )
            charts.append(ch_hist)

        # banda de confianza
        if {"y_lo","y_hi"}.issubset(fc.columns):
            band = alt.Chart(fc).mark_area(opacity=0.15).encode(
                x=alt.X("date:T", title="Tiempo (día)"),
                y=alt.Y("y_lo:Q", title=f"Unidades ({target})"),
                y2="y_hi:Q"
            )
            charts.append(band)

        # línea de pronóstico (gruesa)
        ch_fc = alt.Chart(fc).mark_line(size=3).encode(
            x=alt.X("date:T", title="Tiempo (día)"),
            y=alt.Y("yhat:Q", title=f"Unidades ({target})")
        )
        charts.append(ch_fc)

        chart = alt.layer(*charts).resolve_scale(y='shared')
        st.altair_chart(chart, width='stretch')
    except Exception as e:
        st.info("Altair no está disponible; muestro solo línea de pronóstico.")
        st.line_chart(fc.set_index("date")[["yhat"]], height=300)

    # pie de modelo
    if os.path.exists("artifacts/sarimax_summary.json"):
        info = json.load(open("artifacts/sarimax_summary.json"))
        st.caption(
            f"Modelo: {info.get('status','?')} · Frecuencia: {info.get('freq_used','D')} · Observaciones: {info.get('n_obs','?')}"
        )

# — Buffer recomendado (p95) con explicación —
st.header("🧯 Buffer recomendado (p95)")
if not os.path.exists("artifacts/buffer_table.pkl"):
    st.warning("No encuentro `artifacts/buffer_table.pkl`. Corre `scripts/4_buffer_recommendation.py`.")
else:
    buf = pd.read_pickle("artifacts/buffer_table.pkl").copy()
    st.dataframe(buf, width='stretch')

    # explicación amigable (usa primera fila global o por producto seleccionado)
    row = None
    if "_label" in locals() and pick:
        # si tu buffer_table tiene columnas de producto, intenta filtrar
        possible_group_cols = [c for c in ["product","product_name","sku","item"] if c in buf.columns]
        if possible_group_cols:
            buf["_label"] = buf[possible_group_cols].astype(str).agg(" | ".join, axis=1)
            row = buf.loc[buf["_label"] == pick].head(1)
    if row is None or row.empty:
        row = buf.head(1)

    if not row.empty and {"p95","reco_buffer"}.issubset(row.columns):
        p95_val = float(row["p95"].iloc[0])
        reco = int(row["reco_buffer"].iloc[0])
        st.markdown(
            f"**¿Qué es el buffer p95?** Usamos el percentil 95 del consumo histórico para definir un stock de seguridad "
            f"que cubra la **demanda en picos** el 95% del tiempo. En tus datos actuales, `p95 ≈ {p95_val:,.0f}` → "
            f"**buffer recomendado = {reco}** unidades."
        )
