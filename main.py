from data_processing.extraction import extract_data_frames
from database_interact.match_titles import process_and_match_new_hymn_titles
from data_processing.scheduler import generate_schedule_dates, filter_data_frames_by_date
from data_processing.formatting import generate_hymn_dataframes, assemble_master_dataframe, apply_excel_formatting
from database_interact.frecuence_hymns import compile_hymn_usage_from_data_tables, identify_and_display_hymn_duplications, process_and_update_hymn_frequencies, hymn_usage_analysis_assistant # Renamed
from interact_user.general import select_excel_file, get_save_excel_file_path
from utils.helpers import move_processed_file, affirmative_answers, load_config_from_json
import logging # Import the logging module

# --- Logger Setup ---
# Create a logger
logger = logging.getLogger(__name__) # Using __name__ is a common practice
logger.setLevel(logging.DEBUG) # Set the minimum logging level

# Create handlers (e.g., console and file)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO) # Console logs INFO and above

# Optional: File handler to log everything (DEBUG and above) to a file
# log_file_path = 'app_activity.log' # Consider making this path configurable
# file_handler = logging.FileHandler(log_file_path)
# file_handler.setLevel(logging.DEBUG)

# Create formatters and add them to handlers
# Simple format for console
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)

# More detailed format for file
# file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# file_handler.setFormatter(file_formatter)

# Add handlers to the logger
logger.addHandler(console_handler)
# logger.addHandler(file_handler)
# --- End Logger Setup ---

def main():
    logger.info('Iniciando la aplicación y el proceso de extracción de datos...')
    
    # Load extraction settings
    try:
        extraction_config = load_config_from_json('extraction_settings')
        hymn_identifier = extraction_config.get('hymn_identifier', 'R') 
        logger.debug(f"Identificador de himnos en uso: '{hymn_identifier}' (desde configuración).")
    except ValueError as e: 
        logger.error(f"No se pudo cargar la configuración de extracción: {e}. Usando identificador por defecto 'R'.")
        hymn_identifier = 'R'
    except Exception as e:
        logger.error(f"Error inesperado al cargar la configuración de extracción: {e}. Usando identificador por defecto 'R'.")
        hymn_identifier = 'R'

    file_path = select_excel_file() 
    if not file_path:
        logger.warning("No se seleccionó ningún archivo. Saliendo de la aplicación.")
        return 0
    
    while True:
        try:
            logger.info(f"Procesando archivo: {file_path}")
            data_tables = extract_data_frames(file_path, hymn_identifier, -1, (-2, 0)) 
            
            if not data_tables: 
                logger.error("No se pudieron extraer las tablas de datos del archivo. Verifique el formato y contenido del archivo.")
                return 1 
        
        except FileNotFoundError:
            logger.error(f"Error: El archivo '{file_path}' no fue encontrado.")
            return 1 
        except IOError as e:
            logger.error(f"Ocurrió un error de E/S al procesar el archivo: {e}", exc_info=True)
            return 1 
        except Exception as e: 
            logger.exception(f"Ocurrió un error inesperado durante la extracción de datos: {e}")
            return 1

        logger.info('Registrando títulos desconocidos...')
        not_found_hymns = process_and_match_new_hymn_titles(data_tables) 
        
        if not_found_hymns:
            logger.warning('=============== DATOS FALTANTES ===============')
            logger.warning('Los siguientes himnos no fueron encontrados y no pudieron ser emparejados:')
            for hymn_title in not_found_hymns: 
                logger.warning(f"- {hymn_title}")
            logger.warning('_________________________________________________')
            logger.warning('Para continuar, se requiere corrección manual o añadir estos títulos a la base de datos.\nUna vez corregido, puede re-procesar o continuar si el impacto es mínimo.')
            
            while True:
                answer = input('¿Desea re-procesar el archivo actual (r), continuar de todas formas (c) o salir (s)?: ').strip().lower()
                if answer in ["re-procesar", "reprocess", "r"]:
                    logger.info("El usuario eligió re-procesar. Reintentando extracción y procesamiento.")
                    break # Breaks inner loop to continue outer while loop
                elif answer in ["continuar", "c"] or affirmative_answers.intersection(set(answer.split())): # "si" or "si continuar"
                    logger.warning("El usuario eligió continuar a pesar de los títulos faltantes. Los resultados podrían estar incompletos.")
                    # To proceed with outer loop, we need to break this inner validation loop,
                    # and then the outer loop's `continue` will not be hit if this was the path.
                    # This means `not_found_hymns` path will be exited.
                    # To allow processing to continue *after* this block with the current data_tables:
                    not_found_hymns = None # Clear this to prevent re-entering this if block in the current iteration
                    break # Breaks inner loop, outer loop continues to next stage
                elif answer in ["salir", "s", "n", "no"]: # Explicit exit options
                    logger.info("El usuario eligió salir después de la advertencia de datos faltantes.")
                    return 0
                else:
                    logger.warning("Opción no válida. Por favor, ingrese 'r' para re-procesar, 'c' para continuar, o 's' para salir.")
            if answer in ["re-procesar", "reprocess", "r"]: # If re-process was chosen
                continue # Continue the main `while True` loop from the beginning

        logger.info('Registrando himnos del archivo...')
        hymn_frequencies = compile_hymn_usage_from_data_tables(data_tables) 

        logger.info('Buscando duplicaciones...')
        duplications_found = identify_and_display_hymn_duplications(hymn_frequencies) 
        if not duplications_found:
            logger.info('No se encontraron repeticiones de himnos en la hoja actual.')
        
        reinitialize_process = hymn_usage_analysis_assistant(set(hymn_frequencies.keys())) 
        if not reinitialize_process:
            break 
    
    logger.info("Registrando frecuencias de himnos de la hoja en la base de datos...")
    process_and_update_hymn_frequencies(hymn_frequencies) 

    logger.info("Organizando datos para la hoja final de Excel...")
    correct_dates = generate_schedule_dates(data_tables) 
    filtered_tables = filter_data_frames_by_date(data_tables, correct_dates) 
    new_dataframes = generate_hymn_dataframes(filtered_tables) 
    master_dataframe = assemble_master_dataframe(new_dataframes, limit=3) 

    while True:
        sheet_title = input("¿Qué título llevará la hoja de himnos (no el nombre del archivo)?: ").strip()
        if sheet_title:
            break
        else:
            logger.warning("El título de la hoja no puede estar vacío. Por favor, ingrese un título.")


    logger.info("Generando nuevo archivo Excel con formato...")
    temp_excel_dir = 'file_procces' 
    temp_excel_filename = 'temp_schedule.xlsx' 
    apply_excel_formatting(master_dataframe, sheet_title, temp_dir=temp_excel_dir) 
    
    logger.info("Solicitando al usuario la ubicación final para guardar...")
    final_save_path = get_save_excel_file_path() 
    if final_save_path:
        try:
            move_processed_file(final_save_path, source_folder=temp_excel_dir, source_filename=temp_excel_filename) 
            logger.info(f"Archivo Excel final guardado y movido exitosamente a: {final_save_path}")
        except Exception as e:
            logger.error(f"Falló el mover el archivo procesado a la ubicación final: {e}", exc_info=True)
    else:
        logger.warning("Guardado cancelado por el usuario. El archivo formateado permanece en el directorio temporal (si no se limpió).")

    
def test():
    logger.debug("Función de prueba ejecutada.")

if __name__ == '__main__':
    logger.info("Aplicación iniciada directamente desde main.")
    main()
    logger.info("Aplicación finalizada.")
