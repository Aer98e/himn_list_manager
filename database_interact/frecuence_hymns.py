from .queries import find_data_by_normalized_title, load_tracked_hymn_frequencies, update_hymn_frequencies_in_db, find_titles_by_ids, register_hymn_usage
from data_processing.extractor import extract_table_titles
from data_processing.dataframe_constructor import recommend_hymns_based_on_history # New Import
from utils.helpers import affirmative_answers 
import os
from typing import List, Dict, Any, Set, Tuple, Optional 
import pandas as pd 
import logging
import datetime # New Import
from interact_user.general_objects import Hymn, DailyList, HymnSheet

# ... [Rest of imports and functions as exists] ...
# NOTE: To perform this replace cleanly, I will target the imports area and then the specific function.

# Since I can't put comments in ReplacementContent that break python syntax if I replace a block...
# I will break this into two replacements if possible, OR one big one if I replace the whole file content? No, file is big.
# I will use MultiReplace.

# 1. Update Imports
# 2. Update hymn_usage_analysis_assistant


# Get a logger for this module
logger = logging.getLogger(__name__)

def compile_hymn_usage_from_data_tables(data_tables_list: List[pd.DataFrame]) -> Dict[int, Dict[str, Any]]:
    """
    [CORREGIDO] Genera diccionario de uso priorizando la fecha ISO oculta en los metadatos.
    """
    # Constants for column/data indexing
    HYMN_ID_INDEX = 0
    HYMN_TITLE_INDEX = 1

    hymn_usage_details = {}
    
    for data_table_df in data_tables_list:
        # 1. RECUPERAR LA FECHA REAL (ISO) DE LOS METADATOS (Prioridad Alta)
        iso_date_str = data_table_df.attrs.get('iso_date')
        
        # Extracción normal (devuelve [fecha_texto, titulo1, ...])
        extracted_titles_and_date = extract_table_titles(data_table_df, normalize=True, include_date=True)
        
        if not extracted_titles_and_date:
            continue

        # Lógica de Selección de Fecha:
        if iso_date_str:
            current_date_str = iso_date_str # USAR LA FECHA REAL (ej. '2025-05-07')
        else:
            logger.warning(f"Metadato iso_date no encontrado. Usando fallback textual: '{extracted_titles_and_date[0]}'")
            current_date_str = extracted_titles_and_date[0] # Fallback peligroso

        normalized_hymn_titles = extracted_titles_and_date[1:]

        for norm_title in normalized_hymn_titles:
            hymn_info = find_data_by_normalized_title(norm_title, ['id', 'titulo']) 
            
            if hymn_info:
                hymn_id = hymn_info[HYMN_ID_INDEX]
                official_title = hymn_info[HYMN_TITLE_INDEX]
                
                if hymn_id in hymn_usage_details:
                    hymn_usage_details[hymn_id]['dates'].append(current_date_str)
                else:
                    hymn_usage_details[hymn_id] = {
                        'title': official_title,
                        'dates': [current_date_str]
                    }
            else:
                logger.warning(f"No database information found for normalized title: '{norm_title}'")
                
    return hymn_usage_details

def identify_and_display_hymn_duplications(hymn_frequencies_dict: Dict[int, Dict[str, Any]], display_on_console: bool = True) -> bool:
    """
    Checks the compiled hymn frequencies for duplicates within the current batch.
    
    Args:
        hymn_frequencies_dict: The dictionary returned by compile_hymn_usage_from_data_tables.
                               Format: {id: {'title': str, 'dates': [str, ...]}}
        display_on_console (bool): If True, prints detected duplications to the console.

    Returns:
        bool: True if duplications were found, False otherwise.
    """
    
    def _display_duplication_info_on_console(duplication_list: List[Dict[str, Any]]):
        """Helper function to print duplication details to the console."""
        if os.name == 'nt': # For Windows
            os.system('cls')
        else: # For Linux/MacOS
            os.system('clear')
        print("\n====================== HIMNOS DUPLICADOS ENCONTRADOS ======================\n")
        for hymn_entry in duplication_list:
            print(f"El himno '{hymn_entry['title']}' (ID: {hymn_entry['id']}) se usa {hymn_entry['times_used']} veces en estas fechas:")
            for date_str in hymn_entry['dates']:
                print(f"   - {date_str}")
            print("_________________________________________________________________")
        print('\n=======================================================================')
        input('Presione Enter para continuar...') 

    found_duplications = False
    duplication_details_list = []
    
    for hymn_id, data in hymn_frequencies_dict.items():
        dates = data.get('dates', [])
        if len(dates) > 1:
            found_duplications = True
            duplication_details_list.append({
                "id": hymn_id,
                "title": data.get('title', 'Unknown'),
                "times_used": len(dates),
                "dates": dates
            })
        
    if display_on_console and found_duplications:
        _display_duplication_info_on_console(duplication_details_list)
        
    return found_duplications

def process_and_update_hymn_frequencies(newly_compiled_frequencies: Dict[int, Dict[str, Any]], run_automatically: bool = False):
    '''
    Updates the hymn history in the database based on newly compiled frequency data.
    Registers usage events instead of updating counter integers.

    Args:
        newly_compiled_frequencies (Dict[int, Dict[str, Any]]): Hymn frequencies from the latest processed sheet.
        run_automatically (bool): If True, updates the database without user confirmation.
    '''
    
    if not run_automatically:
        print("Este proceso actualizará los registros de uso de himnos en la base de datos.")
        print("Esto afectará los análisis e informes futuros.")
        print("Solo proceda si la hoja de himnos actual es definitiva y correcta.\n")
        
        while True:
            user_confirmation = input("¿Desea continuar y actualizar la base de datos? (s/n): ").strip().lower()
            if user_confirmation in affirmative_answers:
                break
            elif user_confirmation == 'n':
                logger.warning('Actualización de la base de datos cancelada por el usuario.')
                return None 
            else:
                logger.warning("Respuesta no válida. Por favor, ingrese 's' para sí o 'n' para no.")
            
    # Iterate through the dictionary and register usage for each hymn
    for hymn_id, hymn_data in newly_compiled_frequencies.items():
        dates_list = hymn_data.get('dates', [])
        # 'dates' list should ideally contain ISO date strings now
        for date_iso in dates_list:
             # Basic validation or fallback could happen here if date_iso isn't actually ISO
             # But we assume previous steps handled it.
             # Call the registration function
             register_hymn_usage(hymn_id, date_iso)

    logger.info('Las frecuencias de los himnos han sido registradas en la base de datos (Historial_Uso).')

def hymn_usage_analysis_assistant(himns_sheet) -> bool:
    """
    Provides an interactive console interface for analyzing hymn usage patterns.
    Allows users to view:
        1. Hymns used in the current sheet that were also used in the last >=2 sheets.
        2. Hymns NOT used in the current sheet and the previous sheet.
        3. Recommended Hymns (based on 'Days Without Singing').
    The user can choose to re-process the current sheet (returns True) or continue (returns False).

    Args:
        hymn_ids_in_current_sheet (Set[int]): A set of hymn IDs present in the currently processed sheet.

    Returns:
        bool: True if the user opts to re-process the sheet, False to continue with the main workflow.
    """
    # NOTE: himns_sheet param name in internal code was 'hymn_ids_in_current_sheet' in older logic comments?
    # The caller passes `set(hymn_frequencies.keys())` which is a set of IDs.
    hymn_ids_in_current_sheet = himns_sheet
    
    def display_analysis_menu():
        """Prints the analysis options menu to the console."""
        if os.name == 'nt': os.system('cls')
        else: os.system('clear')
        print("================== Asistente de Análisis de Uso de Himnos ==================\n")
        print("\t1) Mostrar himnos usados recientemente y también en esta hoja.")
        print("\t2) Mostrar himnos NO usados en la(s) última(s) hoja(s) INCLUIDA esta.")
        print("\t3) Mostrar himnos RECOMENDADOS (Basado en 'Días sin cantar').")
        print("\t4) Re-procesar la hoja actual (ej. después de corrección manual de datos).")
        print("\t5) Continuar con la ejecución del programa.")
        print("____________________________________________________________________")
        user_choice = input('Ingrese el número de su opción: ').strip()
        return user_choice

    def display_analysis_results(results_list: List[Tuple[str, int]], report_type: str):
        """Formats and prints the analysis results."""
        if not results_list:
            print("\nNo se encontraron himnos que coincidan con sus criterios para este informe.")
            print("===============================================================")
            return
        
        print("\n======================== Resultados del Análisis =========================")
        if report_type == "recently_used" or report_type == "not_used_recently":
            current_group_val = results_list[0][1] 
            if current_group_val > 0:
                print(f'\n==== Usado en las Últimas {current_group_val} Hoja(s) ====')
            else:
                 print(f'\n==== No Usado Durante las Últimas {abs(current_group_val)} Hoja(s) ====')

            for i, (title, value) in enumerate(results_list):
                if value != current_group_val:
                    current_group_val = value
                    if current_group_val > 0:
                        print(f'\n==== Usado en las Últimas {current_group_val} Hoja(s) ====')
                    else:
                        print(f'\n==== No Usado Durante las Últimas {abs(current_group_val)} Hoja(s) ====')
                print(f'{i+1}. {title} (Factor de Uso: {value})')
        
        elif report_type == "recommended":
            print(f'\n==== Recomendaciones (Prioridad por tiempo sin cantar) ====')
            for i, (title, value) in enumerate(results_list):
                print(f'{i+1}. {title} (Días sin cantar: {value})')
            if len(results_list) >= 50:
                 print(f"...\n(Mostrando top 50 de {len(results_list)} candidatos)")
                 
        print("===============================================================")

    # Load all tracked hymn frequencies from DB (Still needed for legacy checks or hybrid logic)
    db_frequencies = load_tracked_hymn_frequencies() 
    db_freq_dict = {item[0]: {'useful': item[1], 'real': item[2]} for item in db_frequencies}
    
    # Prepare data for "Recently Used and In Current Sheet"
    # Hymns in current sheet AND have useful_freq > 1
    ids_used_recently_and_in_sheet = [
        h_id for h_id in hymn_ids_in_current_sheet 
        if h_id in db_freq_dict and db_freq_dict[h_id]['useful'] > 1
    ]
    useful_freq_for_recently_used = [db_freq_dict[h_id]['useful'] for h_id in ids_used_recently_and_in_sheet]

    # Prepare data for "Used Last Sheet but Not Current"
    ids_not_in_sheet_but_used_before = [
        h_id for h_id in db_freq_dict 
        if h_id not in hymn_ids_in_current_sheet and db_freq_dict[h_id]['useful'] < 0 
    ] 
    useful_freq_for_not_used = [db_freq_dict[h_id]['useful'] for h_id in ids_not_in_sheet_but_used_before]

    while True:
        user_choice = display_analysis_menu()
        report_data_to_show = []
        report_type = ""

        if user_choice == '1': # Recently used and in this sheet
            titles = find_titles_by_ids(ids_used_recently_and_in_sheet)
            report_data_to_show = list(zip(titles, useful_freq_for_recently_used))
            report_data_to_show.sort(key=lambda x: x[1], reverse=True)
            report_type = "recently_used"
            
        elif user_choice == '2': # Not used last sheet(s) and not this one
            titles = find_titles_by_ids(ids_not_in_sheet_but_used_before)
            report_data_to_show = list(zip(titles, useful_freq_for_not_used))
            report_data_to_show.sort(key=lambda x: x[1])
            report_type = "not_used_recently"
            
        elif user_choice == '3': # RECOMMENDED (New Logic)
            recommended_ids = recommend_hymns_based_on_history(datetime.date.today())
            
            # We want to display Titles + Days without singing.
            # Since recommend_hymns... only returns sorted IDs, we need to fetch info.
            # We can re-use get_hymns_with_last_date() logic or calculation helper, 
            # OR assume the list is already sorted by priority and just show them.
            # But the user wants to see "Days without singing" likely.
            
            # To be efficient, let's fetch usage dates again or improve `recommend_hymns` to return metadata.
            # But I should not modify `recommend_hymns` now if not needed.
            # I will just calculate days locally for display.
            
            from database_interact.queries import get_hymns_with_last_date
            all_history = dict(get_hymns_with_last_date()) # id -> iso_date
            
            today = datetime.date.today()
            calc_days = []
            valid_recommended_ids = []
            
            for rid in recommended_ids:
                last_iso = all_history.get(rid)
                if last_iso:
                    try:
                        d = datetime.date.fromisoformat(last_iso)
                        days = (today - d).days
                    except:
                        days = 9999
                else:
                    days = 99999 # Never sung
                
                calc_days.append(days)
                valid_recommended_ids.append(rid)
                
            titles = find_titles_by_ids(valid_recommended_ids)
            report_data_to_show = list(zip(titles, calc_days))
            # It is already sorted by the recommender, but zip might lose order if ids not ordered?
            # find_titles_by_ids usually returns list in order of IDs passed?
            # Queries implementation: "for title_id in ids_to_query: ... titles.append...". Yes, preserves order.
            
            report_type = "recommended"
            report_data_to_show = report_data_to_show[:50] # Show top 50 only
        
        elif user_choice == '4': # Re-process
            return True 
        
        elif user_choice == '5': # Continue
            return False 

        else:
            logger.warning(f'Se ingreso {user_choice}, y no es valido (ANALYSIS ASSISTANT)')
            print('\n\n\tOpción no válida. Por favor, intente de nuevo.\n')
            input('Presione Enter para volver al menú...')
            continue 
        
        display_analysis_results(report_data_to_show, report_type)
        input('\nPresione Enter para volver al menú de análisis...')
