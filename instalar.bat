@echo off
title Instalacion del sistema de fraude LightGBM

cd /d "%~dp0"

echo ============================================
echo CREANDO ENTORNO VIRTUAL
echo ============================================

if not exist ".venv" (
    python -m venv .venv
)

echo.
echo ============================================
echo ACTIVANDO ENTORNO
echo ============================================

call .venv\Scripts\activate.bat

echo.
echo ============================================
echo ACTUALIZANDO PIP
echo ============================================

python -m pip install --upgrade pip

echo.
echo ============================================
echo INSTALANDO DEPENDENCIAS
echo ============================================

python -m pip install -r backend\requirements.txt

echo.
echo ============================================
echo VERIFICANDO DEPENDENCIAS
echo ============================================

python -m pip check

echo.
echo Instalacion finalizada.
pause