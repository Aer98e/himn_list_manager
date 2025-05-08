import os
import subprocess
import hashlib

def limpiar_pantalla():
    """Limpia la pantalla de la consola."""
    os.system("cls" if os.name == "nt" else "clear")

def crear_entorno_virtual(venv_dir):
    """Verifica si el entorno virtual existe, si no, lo crea."""
    if not os.path.exists(venv_dir):
        print(f"Creando entorno virtual en {venv_dir}...")
        subprocess.run(["python", "-m", "venv", venv_dir], check=True)

def calcular_hash(archivo):
    """Calcula el hash MD5 de un archivo."""
    if not os.path.exists(archivo):
        return None
    with open(archivo, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def actualizar_dependencias(python_exe, req_file, req_hash_file):
    """Verifica si requirements.txt cambió y actualiza las dependencias si es necesario."""
    nuevo_hash = calcular_hash(req_file)
    prev_hash = None
    
    if os.path.exists(req_hash_file):
        with open(req_hash_file, "r") as f:
            prev_hash = f.read().strip()
    
    if nuevo_hash != prev_hash:
        print("Cambios detectados en requirements.txt. Actualizando dependencias...")
        subprocess.run([python_exe, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        subprocess.run([python_exe, "-m", "pip", "install", "-r", req_file], check=True)
        with open(req_hash_file, "w") as f:
            f.write(nuevo_hash)
    else:
        print("requirements.txt no ha cambiado. No se actualizarán las dependencias.")

def ejecutar_programa(python_exe, main_script):
    """Ejecuta el script principal si existe."""
    if os.path.exists(main_script):
        print("Ejecutando main.py...")
        subprocess.run([python_exe, main_script], check=True)
    else:
        print("Error: No se encontró el script main.py.")

if __name__ == "__main__":
    limpiar_pantalla()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    venv_dir = os.path.join(script_dir, "local_1")
    python_exe = os.path.join(venv_dir, "Scripts", "python.exe")
    req_file = os.path.join(script_dir, "requirements.txt")
    req_hash_file = os.path.join(script_dir, "requirements.hash")
    main_script = os.path.join(script_dir, "main.py")

    crear_entorno_virtual(venv_dir)
    actualizar_dependencias(python_exe, req_file, req_hash_file)
    ejecutar_programa(python_exe, main_script)