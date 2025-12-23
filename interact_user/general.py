# import tkinter as tk
from tkinter import filedialog
import os
from utils.helpers import load_config_from_json, save_config_to_json # Renamed functions
import functools
from typing import Callable, Any, Optional # For type hinting
import logging
from .form_objects import EnumField
from data_processing.form_validator import validation_input_form

# Get a logger for this module
logger = logging.getLogger(__name__)

# Configuration file name for storing the last used path
PATH_CONFIG_NAME = 'path_file'

def get_initial_directory_from_config() -> Optional[str]:
    """
    Retrieves the last used directory path from the configuration file.
    If the path in the config is invalid or not set, defaults to the user's home directory.

    Returns:
        Optional[str]: The initial directory path to use for file dialogs, or None if
                       the config file itself is missing or fundamentally misconfigured
                       (though load_config_from_json might raise ValueError first).
    """
    try:
        config = load_config_from_json(PATH_CONFIG_NAME)
        saved_path = config.get("path") # Use .get for safer access
        
        if saved_path and os.path.exists(saved_path) and os.path.isdir(saved_path): # Check if path exists and is a directory
            return saved_path
        elif saved_path: # Path exists in config but is not a valid directory
             logger.warning(f"Saved path '{saved_path}' in '{PATH_CONFIG_NAME}.json' is invalid. Defaulting to home directory.") # Replaced print
    except ValueError: # Config file might not exist or is malformed
        logger.warning(f"Configuration file '{PATH_CONFIG_NAME}.json' not found or invalid. Defaulting to home directory.") # Replaced print
    except Exception as e: # Catch other potential errors during config loading
        logger.error(f"Error loading path configuration from '{PATH_CONFIG_NAME}.json': {e}. Defaulting to home directory.", exc_info=True) # Replaced print

    return os.path.expanduser("~") # Default to user's home directory


def update_last_directory_path_decorator(func: Callable) -> Callable:
    """
    A decorator that wraps file dialog functions. It retrieves the initial directory
    from config, calls the wrapped function, and then saves the directory of the
    selected/saved file path back to the configuration.

    Args:
        func (Callable): The file dialog function to wrap (e.g., select_excel_file, save_excel_file).

    Returns:
        Callable: The wrapped function.
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> str:
        # Get initial directory from config, or default if not found/invalid
        initial_dir = get_initial_directory_from_config()
        
        # Call the original function (e.g., select_file, saved_file)
        # Pass initial_dir to the wrapped function if it accepts it.
        # Some filedialog functions might not accept initial_dir if it's None,
        # so only pass it if it's a valid path.
        if initial_dir and 'initialdir' not in kwargs: # Ensure we don't override if already provided
             kwargs['initialdir'] = initial_dir
        
        selected_path = func(*args, **kwargs) # Call the decorated function
        
        # If a path was selected/returned, update the config with its directory
        if selected_path and isinstance(selected_path, str): # Check if a path was actually returned
            try:
                # Ensure config exists or create a default one before updating path
                try:
                    config = load_config_from_json(PATH_CONFIG_NAME)
                except ValueError: # Config file doesn't exist, create a default one
                    config = {"path": ""} 
                
                config["path"] = os.path.dirname(selected_path) # Get directory from the full path
                save_config_to_json(config, PATH_CONFIG_NAME)
            except Exception as e:
                logger.error(f"Error saving path configuration to '{PATH_CONFIG_NAME}.json': {e}", exc_info=True) # Replaced print
        else:
            # Handle cases where no file was selected (e.g., dialog cancelled)
            # selected_path might be an empty tuple or string depending on Tkinter version/dialog
            if not selected_path: # Check if selected_path is empty or None
                 logger.info("No file selected or operation cancelled by user. Last path not updated.") # Replaced print
        
        return selected_path if selected_path else "" # Ensure string return, even if empty
    return wrapper


@update_last_directory_path_decorator
def select_excel_file(initialdir: Optional[str] = None, show_selected_path_in_console: bool = False) -> str:
    """
    Opens a file dialog for the user to select an Excel file.
    The initial directory for the dialog is determined by the decorator.

    Args:
        initialdir (Optional[str]): The initial directory for the dialog. (Managed by decorator)
                                    This is kept for compatibility with the decorator's structure.
        show_selected_path_in_console (bool): If True, prints the selected file path to the console.

    Returns:
        str: The full path of the selected Excel file. Returns an empty string if cancelled.
    """
    # Hide the root Tkinter window as it's not needed for just a dialog
    # root = tk.Tk()
    # root.withdraw()
    
    file_path = filedialog.askopenfilename(
        title="Seleccionar archivo Excel para procesar", # Translated to Spanish
        filetypes=[("Archivos Excel", "*.xlsx *.xls"), ("Todos los archivos", "*.*")], # Added "All files" option
        initialdir=initialdir # This will be set by the decorator
    )
    
    if show_selected_path_in_console and file_path: # Check if a path was returned
        logger.info(f"File selected by user: {file_path}") # Replaced print

    return file_path if file_path else "" # Ensure consistent return type (string)

@update_last_directory_path_decorator
def get_save_excel_file_path(initialdir: Optional[str] = None, show_selected_path_in_console: bool = False) -> str:
    """
    Opens a file dialog for the user to specify a path to save an Excel file.
    The initial directory for the dialog is determined by the decorator.

    Args:
        initialdir (Optional[str]): The initial directory for the dialog. (Managed by decorator)
        show_selected_path_in_console (bool): If True, prints the chosen save path to the console.

    Returns:
        str: The full path where the file should be saved. Returns an empty string if cancelled.
    """
    # Hide the root Tkinter window
    # root = tk.Tk()
    # root.withdraw()
    
    file_path = filedialog.asksaveasfilename(
        title="Guardar archivo como...", # Translated to Spanish
        defaultextension=".xlsx",
        filetypes=[("Archivos Excel", "*.xlsx")],
        initialdir=initialdir # This will be set by the decorator
    )
    
    if show_selected_path_in_console and file_path:
        logger.info(f"Save location selected by user: {file_path}") # Replaced print
        
    return file_path if file_path else "" # Ensure consistent return type

def submit_form(fields: list):
    """
    Esta funcion debe recibir una lista de diccionarios con los campos:
    title: str, type: str, optional: bool, y content:str
    """
    for field in fields:
        title = field.title
        type_in = field.type_i
        optional = field.optional
        content = field.content

        consult = f" Ingrese {title} ({type_in})"
        if optional:
            consult += " [Opcional]"
        if content:
            consult+=f" [{content}]"
        consult+=': '

        ans = input(consult).strip()

        if ans:
            field.content = ans

def _display_menu(*args, title = "Menú"):
    print(f"================== {title} ==================\n")
    for i, arg in enumerate(args, start = 1):
        print(f"\t{i}) {arg}")
    print("____________________________________________________________________")

def menu(*args, title = "Menú"):
    _display_menu(*args, title = title)
    field = EnumField("número de su opción", [str(i) for i in range(1, len(args)+1)])
    while True:
        submit_form([field])
        validation_input_form([field], True)
        if field.error == '': # Si no hay error
            break

    return field.content

def _bar(text='', leng=70, c="="):
        size = (leng-len(text))
        bar = c * (size//2)
        text = f" {text} " if text else text
        return bar + text + bar

def print_message(message:str, title='', limit_len=70):
    print(_bar(title, limit_len), "\n")
    print(message, "\n")
    print(_bar(leng=limit_len))
