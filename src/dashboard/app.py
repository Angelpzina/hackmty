import streamlit as st
import pandas as pd
from pathlib import Path

PROC = Path("data/processed")

st.set_page_config(page_title="SCIS Demo", layout="wide")
st.title("Smart Catering Intelligence System - Demo")

# --- Inicio: pantalla introductoria antes de mostrar predicciones ---
if "mostrar_intro" not in st.session_state:
    st.session_state.mostrar_intro = True

def continuar():
    st.session_state.mostrar_intro = False

if st.session_state.mostrar_intro:
    st.markdown("## HackMTY_2025 🎯 Objetivo")
    st.markdown(
        "Desarrollar un sistema integral que predice la demanda diaria de productos "
        "(alimentos y bebidas), genera un buffer de seguridad basado en datos históricos "
        "y visualiza los resultados en una aplicación interactiva en Streamlit."
    )
    st.write("")  # separación visual
    if st.button("Continuar"):
        continuar()
    # No continuar con el resto de la app hasta que el usuario pulse "Continuar"
    st.stop()
# --- Fin: pantalla introductoria ---

# Sidebar & carga de datos (se ejecuta una vez que el usuario ha pulsado "Continuar")
st.sidebar.header("Data")
flight_file = PROC / "flight_consumption.parquet"

if flight_file.exists():
    try:
        fc = pd.read_parquet(flight_file)
        st.sidebar.success("flight_consumption cargado desde data/processed")
    except Exception as e:
        st.sidebar.error(f"Error al leer {flight_file.name}: {e}")
else:
    st.sidebar.warning(f"{flight_file.name} no encontrado en data/processed")

st.sidebar.markdown("---")
st.sidebar.info("Si no hay datos, ejecuta el ETL y coloca los archivos en data/processed")

# Mostrar muestra de consumo si se solicita
if st.button("Show sample consumption"):
    if 'fc' in locals():
        st.dataframe(fc.head(20))
    else:
        st.warning("No hay datos cargados para mostrar. Revisa data/processed.")

# Quick KPIs (ejemplo simple)
st.header("Quick KPIs")
col1, col2, col3 = st.columns(3)
col1.metric("Flights (sample)", int(fc['Flight_ID'].nunique()) if 'fc' in locals() and 'Flight_ID' in fc.columns else "-")
col2.metric("Products (sample)", int(fc['Product_ID'].nunique()) if 'fc' in locals() and 'Product_ID' in fc.columns else "-")
col3.metric("Avg Consumed (sample)", round(float(fc['Quantity_Consumed'].mean()), 2) if 'fc' in locals() and 'Quantity_Consumed' in fc.columns else "-")

st.markdown("---")
st.info("This app is a minimal demo. Extend with plots, error tables, and optimization outputs.")
