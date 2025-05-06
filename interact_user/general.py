import tkinter as tk
from tkinter import filedialog

  # Ocultar la ventana principal
def select_file(show_path=False):
    root = tk.Tk()
    root.withdraw()

    path_file = filedialog.askopenfilename(title="Selecciona el archivo Excel a procesar.",
                                            filetypes=[("Archivos Excel", "*.xlsx *.xls")])
    if show_path:
        print("Carpeta seleccionada:", path_file)
        
    return path_file
