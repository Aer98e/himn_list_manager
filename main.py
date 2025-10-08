from data_processing.extraction import extract_data_frames
from database_interact.match_titles import process_and_match_new_hymn_titles
from data_processing.scheduler import generate_schedule_dates, filter_data_frames_by_date
from data_processing.formatting import generate_hymn_dataframes, assemble_master_dataframe, apply_excel_formatting
from database_interact.frecuence_hymns import compile_hymn_usage_from_data_tables, identify_and_display_hymn_duplications, process_and_update_hymn_frequencies, hymn_usage_analysis_assistant # Renamed
from interact_user.general import select_excel_file, get_save_excel_file_path
from utils.helpers import move_processed_file, affirmative_answers, load_config_from_json

def main():    
    # Load extraction settings
    extraction_config = load_config_from_json('extraction_settings')

    hymn_identifier = extraction_config.get('hymn_identifier', 'R') 
    file_path = select_excel_file() 
    while True:
        data_tables = extract_data_frames(file_path, hymn_identifier,
                                          review_offset = -1,
                                          column_slice = (-1, 0)
                                         ) 
        
        if not data_tables: 
            print("Nada que revisar.")
            return 1 

        # Registrando títulos desconocidos...
        not_found_hymns = process_and_match_new_hymn_titles(data_tables) 
        
        if not_found_hymns:
            # No se pudieron reconoces los titulos: {not_found_hymns}
            print('=============== DATOS FALTANTES ===============')
            print('Los siguientes himnos no fueron encontrados y no pudieron ser emparejados:')
            for hymn_title in not_found_hymns: 
                print(f"- {hymn_title}")
            print('_________________________________________________')
            print('Para continuar, se requiere corrección manual o añadir estos títulos a la base de datos.\nUna vez corregido, puede re-procesar o continuar si el impacto es mínimo.')
            
            while True:
                answer = input('¿Desea re-procesar el archivo actual (r), continuar de todas formas (c) o salir (s)?: ').strip().lower()
                if answer in ["re-procesar", "reprocess", "r"]:
                    # El usuario eligió re-procesar. Reintentando extracción y procesamiento.
                    break # Breaks inner loop to continue outer while loop
                elif answer in ["continuar", "c"] or affirmative_answers.intersection(set(answer.split())): # "si" or "si continuar"
                    # El usuario eligió continuar a pesar de los títulos faltantes. Los resultados podrían estar incompletos.
                    not_found_hymns = None # Clear this to prevent re-entering this if block in the current iteration
                    break # Breaks inner loop, outer loop continues to next stage
                elif answer in ["salir", "s", "n", "no"]: # Explicit exit options
                    # El usuario eligió salir después de la advertencia de datos faltantes.
                    return 0
                else:
                    # Se eligio {answer}, que es una respuesta inválida (Titulos no Emparejados)
                    print("Opción no válida. Por favor, ingrese 'r' para re-procesar, 'c' para continuar, o 's' para salir.")
            if answer in ["re-procesar", "reprocess", "r"]: # If re-process was chosen
                continue # Continue the main `while True` loop from the beginning

        # Registrando himnos del archivo...
        hymn_frequencies = compile_hymn_usage_from_data_tables(data_tables) 

        # Buscando duplicaciones...
        duplications_found = identify_and_display_hymn_duplications(hymn_frequencies) 
        if not duplications_found:
            # No se encontraron repeticiones de himnos en la hoja actual.
            pass
        
        reinitialize_process = hymn_usage_analysis_assistant(set(hymn_frequencies.keys())) 
        if not reinitialize_process:
            break 
    
    # Registrando frecuencias de himnos de la hoja en la base de datos...
    process_and_update_hymn_frequencies(hymn_frequencies) 

    # Organizando datos para la hoja final de Excel...
    correct_dates = generate_schedule_dates(data_tables, 9) 
    filtered_tables = filter_data_frames_by_date(data_tables, correct_dates) 
    new_dataframes = generate_hymn_dataframes(filtered_tables) 
    master_dataframe = assemble_master_dataframe(new_dataframes, max_frames_per_row=3) 

    while True:
        sheet_title = input("¿Qué título llevará la hoja de himnos (no el nombre del archivo)?: ").strip()
        if sheet_title:
            break
        else:
            # No se ingreso nada para el titulo de la hoja.
            print("El título de la hoja no puede estar vacío. Por favor, ingrese un título.")


    # Generando nuevo archivo Excel con formato...
    temp_excel_dir = 'file_procces' 
    temp_excel_filename = 'temp_schedule.xlsx' 
    apply_excel_formatting(master_dataframe, sheet_title, temp_dir=temp_excel_dir) 
    
    # Solicitando al usuario la ubicación final para guardar...
    final_save_path = get_save_excel_file_path() 
    if final_save_path:
        try:
            move_processed_file(final_save_path, source_folder=temp_excel_dir, source_filename=temp_excel_filename) 
            # Archivo Excel final guardado y movido exitosamente a: {final_save_path}
        except Exception as e:
            # Falló el mover el archivo procesado a la ubicación final: {e}
            pass
    else:
        # Guardado cancelado por el usuario. El archivo formateado permanece en el directorio temporal (si no se limpió).
        pass

    
if __name__ == '__main__':
    main()
    
