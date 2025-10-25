This repository is a scaffold for the Smart Catering Intelligence System (SCIS) — an integrated solution to handle Expiration Date Management, Consumption Prediction, and Productivity Estimation for airline catering.
from ortools.sat.python import cp_model
import pandas as pd
from pathlib import Path


PROC = Path("data/processed")




def simple_assign(exp_df: pd.DataFrame, forecast_df: pd.DataFrame):
# exp_df: columns [Product_ID, LOT_Number, Expiry_Date, Quantity]
# forecast_df: columns [Flight_ID, Product_ID, Predicted_Quantity]
model = cp_model.CpModel()
assignments = {}
# Build indices
lots = list(exp_df.itertuples(index=False))
flights = list(forecast_df.itertuples(index=False))


# Example boolean variable x[i][j] = assign lot i to flight j
x = {}
for i, lot in enumerate(lots):
for j, flight in enumerate(flights):
x[(i,j)] = model.NewBoolVar(f"x_{i}_{j}")
# Constraints: don't assign more than available and satisfy flight needs approximately
# (This is a placeholder: implement real constraints at hackathon)
model.Maximize(sum(x[(i,j)] for i in range(len(lots)) for j in range(len(flights))))
solver = cp_model.CpSolver()
solver.Solve(model)
return {}


--- src/dashboard/app.py ---
"""Streamlit demo app (very lightweight) to show a couple of KPIs and sample predictions.
Run: streamlit run src/dashboard/app.py
"""
import streamlit as st
import pandas as pd
from pathlib import Path


PROC = Path("data/processed")


st.set_page_config(page_title="SCIS Demo", layout="wide")
st.title("Smart Catering Intelligence System - Demo")


st.sidebar.header("Data")
if (PROC / "flight_consumption.parquet").exists():
fc = pd.read_parquet(PROC / "flight_consumption.parquet")
st.sidebar.success("flight_consumption loaded")
else:
st.sidebar.warning("flight_consumption.parquet not found in data/processed")


if st.button("Show sample consumption"):
if 'fc' in locals():
st.dataframe(fc.head(20))
else:
st.info("Run ETL first and place files in data/processed")


st.header("Quick KPIs")
col1, col2, col3 = st.columns(3)
col1.metric("Flights (sample)", fc['Flight_ID'].nunique() if 'fc' in locals() else "-")
col2.metric("Products (sample)", fc['Product_ID'].nunique() if 'fc' in locals() else "-")
col3.metric("Avg Consumed (sample)", round(fc['Quantity_Consumed'].mean(),2) if 'fc' in locals() else "-")


st.markdown("---")
st.info("This app is a minimal demo. Extend with plots, error tables, and optimization outputs.")


--- notebooks/01_data_cleaning.ipynb ---
# Notebook placeholder: EDA and cleaning steps. Use pandas/polars and ydata-profiling for summaries.


--- notebooks/02_feature_engineering.ipynb ---
# Notebook placeholder: create features for consumption, expiration, and productivity models.


--- notebooks/03_model_training.ipynb ---
# Notebook placeholder: training experiments with CatBoost, LightGBM, and NeuralProphet.
