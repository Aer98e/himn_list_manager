from .queries import find_data_by_normalized_title, load_tracked_hymn_frequencies, update_hymn_frequencies_in_db, find_titles_by_ids
from data_processing.extraction import extract_table_titles
from utils.helpers import affirmative_answers # Renamed from ans_y
# from interact_user.test import show_duplications_UI # This UI function might need separate refactoring or review
import os
from typing import List, Dict, Any, Set, Tuple, Optional # For type hinting
import pandas as pd # For type hinting DataFrames
import logging

# Get a logger for this module
logger = logging.getLogger(__name__)

def compile_hymn_usage_from_data_tables(data_tables_list: List[pd.DataFrame]) -> Dict[int, Dict[str, Any]]:
    """
    Generates a dictionary detailing hymn usage (title and dates used) from a list of data tables.

    Args:
        data_tables_list (List[pd.DataFrame]): A list of pandas DataFrames, where each DataFrame
                                              represents a table of hymns for a specific set of dates.
                                              Titles are expected in the second column (index 1).

    Returns:
        Dict[int, Dict[str, Any]]: A dictionary where keys are hymn IDs.
                                   Each value is another dictionary with:
                                       'title': The hymn's official title.
                                       'dates': A list of date strings when the hymn is scheduled.
    
    Structure of the returned dictionary:
    {
        hymn_id_1: {
            'title': 'Hymn Title A',
            'dates': ['DATE_STR_1', 'DATE_STR_2']
        },
        hymn_id_2: {
            'title': 'Hymn Title B',
            'dates': ['DATE_STR_3']
        },
        ...
    }
    """
    # Constants for column/data indexing
    TITLE_COLUMN_INDEX = 1
    HYMN_ID_INDEX = 0
    HYMN_TITLE_INDEX = 1

    hymn_usage_details = {}
    for data_table_df in data_tables_list:
        # Extract titles, including the date from the first row, and normalize them
        # `extract_table_titles` is assumed to return a list where the first item is the date string
        # and subsequent items are normalized hymn titles.
        extracted_titles_and_date = extract_table_titles(data_table_df, TITLE_COLUMN_INDEX, normalize=True, include_date=True)
        
        if not extracted_titles_and_date:
            continue # Skip if no data was extracted

        current_date_str = extracted_titles_and_date[0]
        normalized_hymn_titles = extracted_titles_and_date[1:]

        for norm_title in normalized_hymn_titles:
            # Fetch hymn ID and official title using the normalized title
            # `find_data_by_normalized_title` is assumed to return (id, title) or None
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
                logger.warning(f"No database information found for normalized title: '{norm_title}' during frequency compilation.") # Replaced print
                
    return hymn_usage_details


def identify_and_display_hymn_duplications(hymn_frequencies: Dict[int, Dict[str, Any]], display_on_console: bool = True) -> bool:
    """
    Identifies hymns used multiple times based on the frequency data.
    Optionally prints the duplications to the console.

    Args:
        hymn_frequencies (Dict[int, Dict[str, Any]]): A dictionary structured like the output of
                                                     `compile_hymn_usage_from_data_tables`.
        display_on_console (bool): If True, prints detected duplications to the console.

    Returns:
        bool: True if duplications were found, False otherwise.
    """
    if not isinstance(hymn_frequencies, dict):
        raise ValueError("The 'hymn_frequencies' argument must be a dictionary.")
    
    def _display_duplication_info_on_console(duplication_list: List[Dict[str, Any]]):
        """Helper function to print duplication details to the console."""
        if os.name == 'nt': # For Windows
            os.system('cls')
        else: # For Linux/MacOS
            os.system('clear')
        
        logger.info("\n====================== HIMNOS DUPLICADOS ENCONTRADOS ======================\n")
        for hymn_entry in duplication_list:
            logger.info(f"El himno '{hymn_entry['title']}' (ID: {hymn_entry['id']}) se usa {hymn_entry['times_used']} veces en estas fechas:")
            for date_str in hymn_entry['dates']:
                logger.info(f"   - {date_str}")
            logger.info("_________________________________________________________________")
        logger.info('\n=======================================================================')
        input('Presione Enter para continuar...') # Translated

    found_duplications = False
    duplication_details_list = []
    
    for hymn_id, usage_data in hymn_frequencies.items():
        number_of_times_used = len(usage_data['dates'])
        if number_of_times_used > 1:
            found_duplications = True
            duplication_details_list.append({
                "id": hymn_id,
                "title": usage_data['title'],
                "times_used": number_of_times_used,
                "dates": usage_data['dates']
            })
            
    if display_on_console and found_duplications:
        _display_duplication_info_on_console(duplication_details_list)
        # Consider calling show_duplications_UI(duplication_details_list) here if it's meant to be part of this flow.
        
    return found_duplications

def process_and_update_hymn_frequencies(newly_compiled_frequencies: Dict[int, Dict[str, Any]], run_automatically: bool = False):
    '''
    Updates the hymn frequency records in the database based on newly compiled frequency data.
    It adjusts 'useful_frequency' (recent usage trend) and 'real_frequency' (overall count).

    Args:
        newly_compiled_frequencies (Dict[int, Dict[str, Any]]): Hymn frequencies from the latest processed sheet.
                                                               Structure is like output of `compile_hymn_usage_from_data_tables`.
        run_automatically (bool): If True, updates the database without user confirmation.

    Notes:
        - 'Useful frequency' logic:
            - If a hymn is in `newly_compiled_frequencies`:
                - If useful_freq was < 0 (not used recently), it's set to 1.
                - If useful_freq was >= 0, it's incremented by 1.
            - If a hymn is NOT in `newly_compiled_frequencies`:
                - If useful_freq was > 0 (was used recently), it's set to 0.
                - If useful_freq was <= 0, it's decremented by 1.
        - 'Real frequency' is incremented by the number of times the hymn appears in the current sheet.
    '''
    
    def calculate_frequency_updates(
        previous_db_frequencies: List[Tuple[int, int, int]],
        current_sheet_frequencies: Dict[int, Dict[str, Any]]
    ) -> List[Tuple[int, int, int]]:
        """
        Calculates the new useful and real frequencies for each hymn.
        """
        # Constants for indexing tuples from `load_tracked_hymn_frequencies`
        DB_ID_IDX = 0
        DB_USEFUL_FREQ_IDX = 1
        DB_REAL_FREQ_IDX = 2 

        database_updates_pending = []

        for db_hymn_freq_tuple in previous_db_frequencies:
            hymn_id = db_hymn_freq_tuple[DB_ID_IDX]
            useful_freq = db_hymn_freq_tuple[DB_USEFUL_FREQ_IDX]
            real_freq = db_hymn_freq_tuple[DB_REAL_FREQ_IDX]

            if hymn_id in current_sheet_frequencies:
                # Hymn is in the current sheet
                useful_freq = 1 if useful_freq < 0 else useful_freq + 1
                real_freq += len(current_sheet_frequencies[hymn_id]['dates'])
            else:
                # Hymn is NOT in the current sheet
                useful_freq = 0 if useful_freq > 0 else useful_freq - 1
            
            # Order for update_hymn_frequencies_in_db: (useful_freq, real_freq, hymn_id)
            database_updates_pending.append((useful_freq, real_freq, hymn_id))
            
        return database_updates_pending
    
    # Load existing frequencies for hymns being tracked
    previous_frequencies_from_db = load_tracked_hymn_frequencies()
    
    # Calculate the updates needed based on previous and new data
    updates_to_apply = calculate_frequency_updates(previous_frequencies_from_db, newly_compiled_frequencies)

    if not run_automatically:
        logger.info("Este proceso actualizará los registros de uso de himnos en la base de datos.")
        logger.info("Esto afectará los análisis e informes futuros.")
        logger.info("Solo proceda si la hoja de himnos actual es definitiva y correcta.\n")
        
        while True:
            user_confirmation = input("¿Desea continuar y actualizar la base de datos? (s/n): ").strip().lower()
            if user_confirmation in affirmative_answers:
                break
            elif user_confirmation == 'n':
                logger.warning('Actualización de la base de datos cancelada por el usuario.')
                return None 
            else:
                logger.warning("Respuesta no válida. Por favor, ingrese 's' para sí o 'n' para no.")
            
    update_hymn_frequencies_in_db(updates_to_apply)
    logger.info('Las frecuencias de los himnos han sido actualizadas en la base de datos.')

        
def hymn_usage_analysis_assistant(hymn_ids_in_current_sheet: Set[int]) -> bool:
    """
    Provides an interactive console interface for analyzing hymn usage patterns.
    Allows users to view:
        1. Hymns used in the current sheet that were also used in the last >=2 sheets.
        2. Hymns NOT used in the current sheet but were used in the previous sheet.
        3. Least frequently used hymns overall.
    The user can choose to re-process the current sheet (returns True) or continue (returns False).

    Args:
        hymn_ids_in_current_sheet (Set[int]): A set of hymn IDs present in the currently processed sheet.

    Returns:
        bool: True if the user opts to re-process the sheet, False to continue with the main workflow.
    
    Raises:
        TypeError: If `hymn_ids_in_current_sheet` is not a set.
    """
    if not isinstance(hymn_ids_in_current_sheet, set):
        raise TypeError('The input `hymn_ids_in_current_sheet` must be a Set.')
    
    def display_analysis_menu():
        """Prints the analysis options menu to the console."""
        if os.name == 'nt': os.system('cls')
        else: os.system('clear')
        logger.info("================== Asistente de Análisis de Uso de Himnos ==================\n")
        logger.info("\t1) Mostrar himnos usados recientemente y también en esta hoja.")
        logger.info("\t2) Mostrar himnos usados en la(s) última(s) hoja(s) pero NO en esta.")
        logger.info("\t3) Mostrar himnos menos usados en general.")
        logger.info("\t4) Re-procesar la hoja actual (ej. después de corrección manual de datos).")
        logger.info("\t5) Continuar con la ejecución del programa.")
        logger.info("____________________________________________________________________")
        user_choice = input('Ingrese el número de su opción: ').strip()
        return user_choice

    def display_analysis_results(results_list: List[Tuple[str, int]], report_type: str):
        """Formats and prints the analysis results."""
        if not results_list:
            logger.info("\nNo se encontraron himnos que coincidan con sus criterios para este informe.")
            logger.info("===============================================================")
            return
        
        logger.info("\n======================== Resultados del Análisis =========================")
        if report_type == "recently_used" or report_type == "not_used_recently":
            current_group_val = results_list[0][1] 
            if current_group_val > 0:
                logger.info(f'\n==== Usado en las Últimas {current_group_val} Hoja(s) ====')
            else:
                 logger.info(f'\n==== No Usado Durante las Últimas {abs(current_group_val)} Hoja(s) ====')

            for i, (title, value) in enumerate(results_list):
                if value != current_group_val:
                    current_group_val = value
                    if current_group_val > 0:
                        logger.info(f'\n==== Usado en las Últimas {current_group_val} Hoja(s) ====')
                    else:
                        logger.info(f'\n==== No Usado Durante las Últimas {abs(current_group_val)} Hoja(s) ====')
                logger.info(f'{i+1}. {title} (Factor de Uso: {value})')
        
        elif report_type == "least_used":
            logger.info(f'\n==== Conteo General de Uso ====')
            for i, (title, value) in enumerate(results_list):
                logger.info(f'{i+1}. {title} (Total de Veces Usado: {value})')
                
        logger.info("===============================================================")

    # Load all tracked hymn frequencies from DB
    db_frequencies = load_tracked_hymn_frequencies() # Returns list of (id, useful_freq, real_freq)
    # Convert to a dictionary for easier lookup: {id: {'useful': val, 'real': val}}
    db_freq_dict = {item[0]: {'useful': item[1], 'real': item[2]} for item in db_frequencies}
    
    # Prepare data for "Least Frequently Used" report (sorted by real frequency)
    real_freq_sorted_list = sorted(db_frequencies, key=lambda x: x[2]) # Sort by real_freq (index 2)

    # Prepare data for "Recently Used and In Current Sheet"
    # Hymns in current sheet AND have useful_freq > 1 (meaning used in at least 2 prior consecutive sheets)
    ids_used_recently_and_in_sheet = [
        h_id for h_id in hymn_ids_in_current_sheet 
        if h_id in db_freq_dict and db_freq_dict[h_id]['useful'] > 1
    ]
    useful_freq_for_recently_used = [db_freq_dict[h_id]['useful'] for h_id in ids_used_recently_and_in_sheet]

    # Prepare data for "Used Last Sheet but Not Current"
    # Hymns NOT in current sheet AND have useful_freq < 0 (meaning not used in this one, maybe others before)
    # Specifically, useful_freq == -1 would mean used in the one just before this, but not this.
    # useful_freq < 1 (i.e. 0 or negative) means not used in the *immediately* preceding recorded period for sure.
    ids_not_in_sheet_but_used_before = [
        h_id for h_id in db_freq_dict 
        if h_id not in hymn_ids_in_current_sheet and db_freq_dict[h_id]['useful'] < 0 
    ] # useful_freq < 0 indicates a trend of non-usage.
    useful_freq_for_not_used = [db_freq_dict[h_id]['useful'] for h_id in ids_not_in_sheet_but_used_before]

    while True:
        user_choice = display_analysis_menu()
        report_data_to_show = []
        report_type = ""

        if user_choice == '1': # Recently used and in this sheet
            titles = find_titles_by_ids(ids_used_recently_and_in_sheet)
            report_data_to_show = list(zip(titles, useful_freq_for_recently_used))
            # Sort by useful frequency, descending (most recent/frequent first)
            report_data_to_show.sort(key=lambda x: x[1], reverse=True)
            report_type = "recently_used"
            
        elif user_choice == '2': # Used last sheet(s) but not this one
            titles = find_titles_by_ids(ids_not_in_sheet_but_used_before)
            report_data_to_show = list(zip(titles, useful_freq_for_not_used))
            # Sort by useful frequency, ascending (most "missed" first, i.e., more negative)
            report_data_to_show.sort(key=lambda x: x[1])
            report_type = "not_used_recently"
            
        elif user_choice == '3': # Least used overall
            TOP_N_LEAST_USED = 25 # Define how many to show
            ids_for_least_used = [item[0] for item in real_freq_sorted_list[:TOP_N_LEAST_USED]]
            real_freq_values = [item[2] for item in real_freq_sorted_list[:TOP_N_LEAST_USED]]
            titles = find_titles_by_ids(ids_for_least_used)
            report_data_to_show = list(zip(titles, real_freq_values))
            # Already sorted by real frequency by `real_freq_sorted_list`
            report_type = "least_used"
        
        elif user_choice == '4': # Re-process
            return True # Signal to the caller to re-process
        
        elif user_choice == '5': # Continue
            return False # Signal to the caller to continue

        else:
            logger.warning('\n\n\tOpción no válida. Por favor, intente de nuevo.\n')
            input('Presione Enter para volver al menú...')
            continue # Re-display menu
        
        display_analysis_results(report_data_to_show, report_type)
        input('\nPresione Enter para volver al menú de análisis...')
   
# Comments from original code that might be relevant or can be discarded:
# -Mostrar que himnos estoy usando y ya he usado en las dos ultimas hojas/podriamos_
# tener prioridad en los himnos que se repiten mas de una vez en la hoja actual.
# (Show hymns I'm using that I've also used in the last two sheets / we could prioritize hymns repeated in the current sheet.)
# -Mostrar que himnos no he usado desde la anterior vez.
# (Show hymns I haven't used since the last time.)
# -Mostrar himnos por debajo del promedio(no usados).
# (Show hymns below average usage / not used.)
# These seem to be initial thoughts for the analysis assistant's features.
