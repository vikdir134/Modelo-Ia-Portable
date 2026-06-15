@echo off
setlocal

title Backend - LightGBM + SHAP + Superagente

cd /d "%~dp0"

set "PYTHON=%~dp0.venv\Scripts\python.exe"
set "MODELO=%~dp0backend\artefactos_lightgbm\modelo_fraude_lightgbm_portable.joblib"
set "API=%~dp0backend\api_lightgbm_xai.py"

echo ============================================
echo BACKEND DEL SISTEMA DE FRAUDE
echo ============================================
echo.

if not exist "%PYTHON%" (
    echo ERROR: No se encontro Python dentro de .venv
    echo.
    echo Ejecuta primero instalar.bat
    echo.
    pause
    exit /b 1
)

if not exist "%MODELO%" (
    echo ERROR: No se encontro el modelo portable:
    echo.
    echo %MODELO%
    echo.
    pause
    exit /b 1
)

if not exist "%API%" (
    echo ERROR: No se encontro:
    echo.
    echo %API%
    echo.
    pause
    exit /b 1
)

cd /d "%~dp0backend"

echo Modelo encontrado correctamente.
echo.
echo Backend:
echo http://127.0.0.1:8000
echo.
echo Aplicacion:
echo http://127.0.0.1:8000/app/
echo.
echo Documentacion:
echo http://127.0.0.1:8000/docs
echo.
echo Para detener el sistema presiona CTRL+C
echo ============================================
echo.

"%PYTHON%" -m uvicorn api_lightgbm_xai:app --host 127.0.0.1 --port 8000

echo.
echo El servidor se ha detenido.
pause

endlocal