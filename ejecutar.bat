@echo off
setlocal

:: Obtener la ruta del script actual
set "scriptDir=%~dp0"

:: Definir la ruta del ejecutable de Python dentro del entorno virtual
set "pythonExe=%scriptDir%local_1\Scripts\python.exe"

:: Definir la ruta del archivo Python a ejecutar
set "pythonScript=%scriptDir%main.py"

:: Verificar si Python.exe existe en el entorno virtual
if exist "%pythonExe%" (
    echo Ejecutando Python desde el entorno virtual...
    "%pythonExe%" "%pythonScript%"
) else (
    echo El entorno virtual no está configurado correctamente.
    echo Asegúrate de que 'local_1' está en la misma carpeta.
)

:: Pausa para evitar que la ventana se cierre automáticamente
pause
