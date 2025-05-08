import os
import subprocess
import shutil

def limpiar_pantalla():
    """Limpia la pantalla de la consola."""
    os.system("cls" if os.name == "nt" else "clear")

def verificar_git():
    """Verifica si Git está instalado."""
    if shutil.which("git") is None:
        print("Error: Git no está instalado. Instálalo para continuar.")
        exit(1)

def obtener_actualizaciones():
    """Verifica si hay actualizaciones en el repositorio y ejecuta git pull si es necesario."""
    print("Buscando actualizaciones en el repositorio...")
    subprocess.run(["git", "fetch"], check=True)

    # Verificar si el repositorio está actualizado
    resultado = subprocess.run(["git", "status", "-uno"], capture_output=True, text=True)
    if "Your branch is up to date" in resultado.stdout:
        print("No hay cambios en el repositorio.")
    else:
        print("Se encontraron actualizaciones. Ejecutando git pull...")
        subprocess.run(["git", "pull"], check=True)

if __name__ == "__main__":
    limpiar_pantalla()
    verificar_git()
    obtener_actualizaciones()
    input('Continuar...')