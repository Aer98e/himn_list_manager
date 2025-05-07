import tkinter as tk
from tkinter import filedialog
import os
from utils.helpers import load_config, save_config
import functools

def search_path():
    conf = load_config('path_file')
    initial_dir = os.path.expanduser("~") if not conf["path"] else conf["path"]
    return initial_dir

def verify_path(func):
    @functools.wraps(func)
    def wrapper(*arg, **keyargs):
        conf = load_config('path_file')
        initial_dir = os.path.expanduser("~") if not conf["path"] else conf["path"]

        path_final = func(initial_dir=initial_dir, *arg, **keyargs)
        
        conf["path"] = os.path.dirname(path_final)
        save_config(conf, 'path_file')

        return path_final
    return wrapper

  # Ocultar la ventana principal
@verify_path
def select_file(initial_dir = None, show_path=False):
    path_file = filedialog.askopenfilename(title="Selecciona el archivo Excel a procesar.",
                                          filetypes=[("Archivos Excel", "*.xlsx *.xls")],
                                          initialdir=initial_dir)
    if show_path:
        print("Carpeta seleccionada:", path_file)

    return path_file

@verify_path
def saved_file(initial_dir=None, show_path=False):
    path_file = filedialog.asksaveasfilename(title="Guardar archivo como...",
                                          defaultextension=".xlsx",
                                          initialdir = initial_dir)
    if show_path:
        print("Carpeta seleccionada:", path_file)
        
    return path_file