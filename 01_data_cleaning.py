# EDA y limpieza de datasets de Smart Catering Intelligence

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Paths
RAW = Path("../data/raw")
PROC = Path("../data/processed")
PROC.mkdir(parents=True, exist_ok=True)

# ===============================
# 1️⃣ Expiration Date Management
# ===============================
def load_clean_expiration():
    df = pd.read_csv(RAW / "ExpirationDateManagement.csv")
    # Normalizar columnas
    df.columns = [c.strip() for c in df.columns]
    # Fechas
    df["Expiry_Date"] = pd.to_datetime(df["Expiry_Date"], errors='coerce')
    # Cantidad
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors='coerce').fillna(0).astype(int)
    # Duplicados
    df = df.drop_duplicates(subset=["Product_ID","LOT_Number","Expiry_Date"], keep='last')
    # Métricas iniciales
    df["days_to_expiry"] = (df["Expiry_Date"] - pd.Timestamp.today()).dt.days
    print("Expiration Dataset Info:")
    print(df.info())
    print(df.describe())
    # Guardar limpio
    df.to_parquet(PROC / "expiration.parquet", index=False)
    return df

exp_df = load_clean_expiration()
sns.histplot(exp_df['days_to_expiry'], bins=20)
plt.title("Distribución de días para caducar")
plt.show()


# ===============================
# 2️⃣ Consumption and Estimation
# ===============================
def load_clean_consumption():
    df = pd.read_csv(RAW / "ConsumptionAndEstimation.csv")
    df.columns = [c.strip() for c in df.columns]
    df["day"] = pd.to_datetime(df["day"], format="%Y%m%d", errors='coerce')
    for col in ["flights","passengers","max capacity"]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df["occupancy_ratio"] = df["passengers"] / df["max capacity"]
    print("Consumption Dataset Info:")
    print(df.info())
    print(df.describe())
    df.to_parquet(PROC / "daily.parquet", index=False)
    return df

daily_df = load_clean_consumption()
sns.lineplot(daily_df, x="day", y="occupancy_ratio")
plt.title("Ocupación diaria vs capacidad máxima")
plt.show()


# ===============================
# 3️⃣ Consumption Prediction
# ===============================
def load_clean_flight_consumption():
    df = pd.read_csv(RAW / "ConsumptionPrediction.csv")
    df.columns = [c.strip() for c in df.columns]
    df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
    numeric_cols = ["Passenger_Count","Standard_Specification_Qty","Quantity_Returned","Quantity_Consumed","Unit_Cost"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    # Feature engineering simple
    df["pax_ratio"] = df["Quantity_Consumed"] / df["Passenger_Count"].replace(0,1)
    print("Flight Consumption Info:")
    print(df.info())
    print(df.describe())
    df.to_parquet(PROC / "flight_consumption.parquet", index=False)
    return df

fc_df = load_clean_flight_consumption()
sns.histplot(fc_df['pax_ratio'], bins=20)
plt.title("Distribución de consumo por pasajero")
plt.show()


# ===============================
# 4️⃣ Productivity Estimation
# ===============================
def load_clean_productivity():
    df = pd.read_csv(RAW / "ProductivityEstimation.csv")
    df.columns = [c.strip() for c in df.columns]
    # Parse item lists
    df["Parsed_Items"] = df["Item_List"].apply(lambda s: [i.strip() for i in str(s).split(",")])
    df["Unique_Item_Count_calc"] = df["Parsed_Items"].apply(lambda l: len(set(l)))
    print("Productivity Dataset Info:")
    print(df.info())
    print(df.describe())
    df.to_parquet(PROC / "productivity.parquet", index=False)
    return df

prod_df = load_clean_productivity()
sns.histplot(prod_df['Unique_Item_Count_calc'], bins=15)
plt.title("Cantidad de items únicos por drawer")
plt.show()


# ===============================
# 5️⃣ Employee Efficiency
# ===============================
def load_clean_employee():
    df = pd.read_csv(RAW / "EmployeeEfficiency.csv")
    df.columns = [c.strip() for c in df.columns]
    df["Start_Time"] = pd.to_datetime(df["Start_Time"], errors='coerce')
    df["End_Time"] = pd.to_datetime(df["End_Time"], errors='coerce')
    df["Duration_Seconds"] = pd.to_numeric(df["Duration_Seconds"], errors='coerce')
    df["Items_Packed"] = pd.to_numeric(df["Items_Packed"], errors='coerce')
    df.to_parquet(PROC / "employee.parquet", index=False)
    print("Employee Efficiency Info:")
    print(df.info())
    print(df.describe())
    return df

emp_df = load_clean_employee()
sns.histplot(emp_df['Duration_Seconds'], bins=15)
plt.title("Distribución de duración de packing por empleado")
plt.show()

print("✅ EDA y limpieza base completados. Archivos guardados en data/processed/")
