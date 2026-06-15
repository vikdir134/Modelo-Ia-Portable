@echo off
setlocal

title Sistema de Fraude LightGBM y SHAP

cd /d "%~dp0"

set "PYTHON=%~dp0.venv\Scripts\python.exe"
set "MODELO=%~dp0backend\artefactos_lightgbm\modelo_fraude_lightgbm_portable.joblib"
set "INICIADOR=%~dp0iniciar_backend.bat"
set "FRONTEND=%~dp0frontend\index.html"

echo ============================================
echo INICIANDO SISTEMA DE FRAUDE
echo ============================================
echo.

if not exist "%PYTHON%" (
    echo ERROR: No se encontro el entorno virtual.
    echo.
    echo Ejecuta primero instalar.bat
    echo.
    pause
    exit /b 1
)

if not exist "%MODELO%" (
    echo ERROR: No se encontro el modelo:
    echo.
    echo %MODELO%
    echo.
    pause
    exit /b 1
)

if not exist "%INICIADOR%" (
    echo ERROR: No se encontro iniciar_backend.bat
    echo.
    pause
    exit /b 1
)

if not exist "%FRONTEND%" (
    echo ERROR: No se encontro frontend\index.html
    echo.
    pause
    exit /b 1
)

echo Abriendo el backend...
echo.

start "Backend LightGBM SHAP" cmd /k call "%INICIADOR%"

echo Esperando que FastAPI termine de cargar...
timeout /t 8 /nobreak > nul

echo Abriendo la aplicacion en el navegador...
start "" "http://127.0.0.1:8000/app/"

echo.
echo ============================================
echo SISTEMA INICIADO
echo ============================================
echo.
echo Aplicacion:
echo http://127.0.0.1:8000/app/
echo.
echo Documentacion:
echo http://127.0.0.1:8000/docs
echo.
echo No cierres la ventana del backend mientras
echo estes utilizando el programa.
echo ============================================
echo.

timeout /t 3 /nobreak > nul

endlocal