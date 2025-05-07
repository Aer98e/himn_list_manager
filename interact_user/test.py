import tkinter as tk
from tkinter import ttk

def show_duplications_UI(pack:dict):
    def cambiar_texto(event):
        dates = [(data['title'], data['dates']) for data in pack]
        dates_used = [f"{dat[0]}\n\n"+"\n".join(dat[1]) for dat in dates]
        
        """Cambia el contenido del texto según la pestaña activa."""
        pestaña_activa = notebook.index(notebook.select())

        texto_var.set(dates_used[pestaña_activa])  # Se actualiza el texto en el Label

    # Crear ventana principal
    ventana = tk.Tk()
    ventana.title("Pestañas en Tkinter")

    # Crear un Notebook (pestañas)
    notebook = ttk.Notebook(ventana)
    notebook.pack(expand=True, fill="both", padx=10, pady=10)

    # Crear pestañas
    pestañas = [f"{i+1}" for i in range(len(pack))]
    for nombre in pestañas:
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=nombre)

    # Crear un Label en lugar de un Entry
    texto_var = tk.StringVar()
    etiqueta = tk.Label(ventana, textvariable=texto_var, font=("Arial", 12), padx=10, pady=10)
    etiqueta.pack()

    notebook.bind("<<NotebookTabChanged>>", cambiar_texto)

    ventana.mainloop()
