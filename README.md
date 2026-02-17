# 🚀 SCIS - Instrucciones Completas 

## 📋 PASO 1: Crea estos archivos

Copia y pega el contenido de cada archivo que te di arriba en tu carpeta `HackMTY_2025/`

### Estructura final que debes tener:

```
HackMTY_2025/
├── app_complete.py           ← ARCHIVO PRINCIPAL
├── crear_datos_prueba.py     ← Generador de datos
├── requirements.txt          ← Dependencias
├── quick_start.sh            ← Para Mac/Linux
├── quick_start.bat           ← Para Windows
├── README.md                 ← Documentación
├── data/                     ← Aquí van tus Excel
└── scripts/                  ← (Ya los tienes)
    ├── 1_setup_load.py
    ├── 2_master_timeline.py
    ├── 3_model_training.py
    ├── 4_buffer_recommendation.py
    └── 6_sarimax_forecasting.py
```

---

## 🎯 PASO 2: Instalación Rápida

### En Windows:
```cmd
# Abre CMD o PowerShell en la carpeta HackMTY_2025
pip install pandas numpy scikit-learn matplotlib openpyxl joblib streamlit plotly statsmodels

# Ejecuta esto:
quick_start.bat
```

### En Mac/Linux:
```bash
# Abre Terminal en la carpeta HackMTY_2025
pip install pandas numpy scikit-learn matplotlib openpyxl joblib streamlit plotly statsmodels

# Dale permisos al script:
chmod +x quick_start.sh

# Ejecuta esto:
./quick_start.sh
```

---

## 🎮 PASO 3: Usa la App

### Si NO tienes los archivos Excel todavía:

```bash
# 1. Genera datos de prueba
python crear_datos_prueba.py

# 2. Abre la app
streamlit run app_complete.py
```

### Si YA tienes los 3 archivos Excel:

```bash
# 1. Copia tus 3 Excel a la carpeta data/
#    - [HackMTY2025]_ConsumptionPrediction_Dataset_v1.xlsx
#    - [HackMTY2025]_ExpirationDateManagement_Dataset_v1.xlsx
#    - [HackMTY2025]_ProductivityEstimation_Dataset_v1.xlsx

# 2. Abre la app
streamlit run app_complete.py

# 3. En la app (en el navegador), click en el botón:
#    "🚀 Run Complete Pipeline"
```

---

## ✅ ¡Eso es todo!

La app se abrirá en tu navegador en: **http://localhost:8501**

Verás 4 pestañas:
1. 🏠 Overview - Resumen general
2. 📅 Expiration Management - Gestión de caducidad
3. 📈 Consumption Prediction - Pronósticos de consumo
4. ⏱️ Productivity Estimation - Estimación de productividad

---

## 🆘 Si algo falla:

### Error: "command not found: streamlit"
```bash
pip install streamlit plotly
```

### Error: "No such file: data/..."
```bash
# Genera datos de prueba:
python crear_datos_prueba.py
```

### Error: "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

---

## 📦 Descarga Rápida de Archivos

Si quieres que te envíe cada archivo por separado para copiar y pegar, dime y te los paso uno por uno. Los archivos clave son:

1. **app_complete.py** (el más importante)
2. **crear_datos_prueba.py**
3. **requirements.txt**

¿Quieres que te los pase ahora?
