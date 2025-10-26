#!/bin/bash

# ========================================
# SCIS - Quick Start Script
# HackMTY 2025
# ========================================

echo "🚀 SCIS - Smart Catering Intelligence System"
echo "============================================="
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar Python
echo "🔍 Verificando Python..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
    echo -e "${GREEN}✅ Python3 encontrado${NC}"
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
    echo -e "${GREEN}✅ Python encontrado${NC}"
else
    echo -e "${RED}❌ Python no encontrado. Por favor instala Python 3.8+${NC}"
    exit 1
fi

# Verificar versión de Python
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "   Versión: $PYTHON_VERSION"
echo ""

# Crear directorios necesarios
echo "📁 Creando directorios..."
mkdir -p data
mkdir -p artifacts
echo -e "${GREEN}✅ Directorios creados${NC}"
echo ""

# Instalar dependencias
echo "📦 Instalando dependencias..."
$PYTHON_CMD -m pip install --upgrade pip -q
$PYTHON_CMD -m pip install -r requirements.txt -q
$PYTHON_CMD -m pip install streamlit plotly -q

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Dependencias instaladas${NC}"
else
    echo -e "${RED}❌ Error al instalar dependencias${NC}"
    exit 1
fi
echo ""

# Verificar si existen datos
DATA_EXISTS=false
if [ -f "data/[HackMTY2025]_ConsumptionPrediction_Dataset_v1.xlsx" ] && \
   [ -f "data/[HackMTY2025]_ExpirationDateManagement_Dataset_v1.xlsx" ] && \
   [ -f "data/[HackMTY2025]_ProductivityEstimation_Dataset_v1.xlsx" ]; then
    echo -e "${GREEN}✅ Archivos de datos encontrados${NC}"
    DATA_EXISTS=true
else
    echo -e "${YELLOW}⚠️  No se encontraron archivos de datos${NC}"
    echo ""
    read -p "¿Deseas generar datos de prueba? (s/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[SsYy]$ ]]; then
        echo "🎲 Generando datos de prueba..."
        $PYTHON_CMD crear_datos_prueba.py
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Datos de prueba generados${NC}"
            DATA_EXISTS=true
        else
            echo -e "${RED}❌ Error al generar datos${NC}"
        fi
    fi
fi
echo ""

# Ejecutar pipeline si hay datos
if [ "$DATA_EXISTS" = true ]; then
    echo "🔄 ¿Deseas ejecutar el pipeline de procesamiento ahora?"
    read -p "   (Esto puede tardar 30-60 segundos) (s/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[SsYy]$ ]]; then
        echo "⚙️  Ejecutando pipeline..."
        
        echo "   [1/5] Cargando datos..."
        $PYTHON_CMD scripts/1_setup_load.py
        
        echo "   [2/5] Creando timeline..."
        $PYTHON_CMD scripts/2_master_timeline.py
        
        echo "   [3/5] Entrenando modelo..."
        $PYTHON_CMD scripts/3_model_training.py
        
        echo "   [4/5] Calculando buffers..."
        $PYTHON_CMD scripts/4_buffer_recommendation.py
        
        echo "   [5/5] Generando pronósticos..."
        $PYTHON_CMD scripts/6_sarimax_forecasting.py
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Pipeline completado exitosamente${NC}"
        else
            echo -e "${YELLOW}⚠️  Algunos pasos del pipeline fallaron${NC}"
            echo "   (Puedes ejecutar el pipeline desde la app después)"
        fi
    fi
fi
echo ""

# Iniciar aplicación
echo "============================================="
echo "🎉 TODO LISTO!"
echo "============================================="
echo ""
echo "📱 Iniciando Streamlit app..."
echo ""
echo -e "${GREEN}La aplicación se abrirá automáticamente en tu navegador${NC}"
echo -e "${YELLOW}URL: http://localhost:8501${NC}"
echo ""
echo "Para detener la app: Ctrl+C"
echo ""
echo "============================================="
echo ""

# Esperar 2 segundos antes de abrir
sleep 2

# Iniciar Streamlit
streamlit run app_complete.py

# Mensaje de cierre
echo ""
echo "============================================="
echo "👋 ¡Gracias por usar SCIS!"
echo "   HackMTY 2025"
echo "============================================="