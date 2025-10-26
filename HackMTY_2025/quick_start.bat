@echo off
REM ========================================
REM SCIS - Quick Start Script (Windows)
REM HackMTY 2025
REM ========================================

echo.
echo ========================================
echo 🚀 SCIS - Smart Catering Intelligence
echo ========================================
echo.

REM Verificar Python
echo 🔍 Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python no encontrado. Por favor instala Python 3.8+
    pause
    exit /b 1
)
echo ✅ Python encontrado
python --version
echo.

REM Crear directorios
echo 📁 Creando directorios...
if not exist "data" mkdir data
if not exist "artifacts" mkdir artifacts
echo ✅ Directorios creados
echo.

REM Instalar dependencias
echo 📦 Instalando dependencias...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet
python -m pip install streamlit plotly --quiet
if %errorlevel% neq 0 (
    echo ❌ Error al instalar dependencias
    pause
    exit /b 1
)
echo ✅ Dependencias instaladas
echo.

REM Verificar archivos de datos
set DATA_EXISTS=0
if exist "data\[HackMTY2025]_ConsumptionPrediction_Dataset_v1.xlsx" (
    if exist "data\[HackMTY2025]_ExpirationDateManagement_Dataset_v1.xlsx" (
        if exist "data\[HackMTY2025]_ProductivityEstimation_Dataset_v1.xlsx" (
            echo ✅ Archivos de datos encontrados
            set DATA_EXISTS=1
        )
    )
)

if %DATA_EXISTS%==0 (
    echo ⚠️  No se encontraron archivos de datos
    echo.
    set /p GENERATE="¿Deseas generar datos de prueba? (s/n): "
    if /i "%GENERATE%"=="s" (
        echo 🎲 Generando datos de prueba...
        python crear_datos_prueba.py
        if %errorlevel% equ 0 (
            echo ✅ Datos de prueba generados
            set DATA_EXISTS=1
        ) else (
            echo ❌ Error al generar datos
        )
    )
)
echo.

REM Ejecutar pipeline si hay datos
if %DATA_EXISTS%==1 (
    echo 🔄 ¿Deseas ejecutar el pipeline de procesamiento ahora?
    set /p RUN_PIPELINE="   (Esto puede tardar 30-60 segundos) (s/n): "
    if /i "%RUN_PIPELINE%"=="s" (
        echo ⚙️  Ejecutando pipeline...
        echo.
        
        echo    [1/5] Cargando datos...
        python scripts\1_setup_load.py
        
        echo    [2/5] Creando timeline...
        python scripts\2_master_timeline.py
        
        echo    [3/5] Entrenando modelo...
        python scripts\3_model_training.py
        
        echo    [4/5] Calculando buffers...
        python scripts\4_buffer_recommendation.py
        
        echo    [5/5] Generando pronósticos...
        python scripts\6_sarimax_forecasting.py
        
        if %errorlevel% equ 0 (
            echo ✅ Pipeline completado exitosamente
        ) else (
            echo ⚠️  Algunos pasos del pipeline fallaron
            echo    (Puedes ejecutar el pipeline desde la app después)
        )
    )
)
echo.

REM Iniciar aplicación
echo =========================================
echo 🎉 TODO LISTO!
echo =========================================
echo.
echo 📱 Iniciando Streamlit app...
echo.
echo ✅ La aplicación se abrirá en tu navegador
echo 🌐 URL: http://localhost:8501
echo.
echo Para detener la app: Ctrl+C
echo.
echo =========================================
echo.

timeout /t 2 /nobreak >nul

REM Iniciar Streamlit
streamlit run app_complete.py

echo.
echo =========================================
echo 👋 ¡Gracias por usar SCIS!
echo    HackMTY 2025
echo =========================================
pause