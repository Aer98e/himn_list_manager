@echo off
setlocal

:: Obtener la ruta del script actual
set "scriptDir=%~dp0"

:: Definir la ruta del entorno virtual
set "venvDir=%scriptDir%local_1"

:: Definir la ruta del ejecutable de Python dentro del entorno virtual
set "pythonExe=%venvDir%\Scripts\python.exe"

:: Verificar si el entorno virtual existe, si no, crearlo
if not exist "%venvDir%" (
    echo Creando entorno virtual en %venvDir%...
    python -m venv "%venvDir%"
)

:: Activar el entorno virtual e instalar las dependencias
if exist "%pythonExe%" (
    echo Instalando dependencias desde requirements.txt...
    "%pythonExe%" -m pip install --upgrade pip
    "%pythonExe%" -m pip install -r "%scriptDir%requirements.txt"
) else (
    echo Error: No se pudo encontrar Python en el entorno virtual.
    exit /b 1
)

:: Definir la ruta del archivo Python a ejecutar
set "pythonScript=%scriptDir%main.py"

:: Ejecutar el script Python
if exist "%pythonScript%" (
    cls
    echo ==============================================================
    echo Ejecutando Python desde el entorno virtual...
    "%pythonExe%" "%pythonScript%"
) else (
    echo Error: No se encontró el script main.py.
)

:: Pausa para evitar que la ventana se cierre automáticamente
pause
