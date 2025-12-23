from .queries import find_data_by_normalized_title, load_tracked_hymn_frequencies, update_hymn_frequencies_in_db, find_titles_by_ids, get_total_hymns
from data_processing.extractor import extract_table_titles
from utils.helpers import affirmative_answers # Renamed from ans_y
# from interact_user.test import show_duplications_UI # This UI function might need separate refactoring or review
import os
from typing import List, Dict, Any, Set, Tuple, Optional # For type hinting
import pandas as pd # For type hinting DataFrames
import logging
from interact_user.general_objects import Hymn, DailyList, HymnSheet
from datetime import date
from interact_user.general import menu, print_message, _bar
from enum import Enum

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
    HYMN_ID_INDEX = 0
    HYMN_TITLE_INDEX = 1

    hymn_usage_details = {}
    for data_table_df in data_tables_list:
        # Extract titles, including the date from the first row, and normalize them
        # `extract_table_titles` is assumed to return a list where the first item is the date string
        # and subsequent items are normalized hymn titles.
        extracted_titles_and_date = extract_table_titles(data_table_df, normalize=True, include_date=True)
        
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

def identify_and_display_hymn_duplications(hymns_sheet:HymnSheet, display_on_console: bool = True) -> bool:
    """
    Bsuca en la hoja de himnos, para encontrar himnos duplicados, opcionalmente los imuestra en pantalla.

    Args:
        hymns_sheet: Un objeto HymnSheet que contiene un lista cargada.
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
        input('Presione Enter para continuar...') # Translated

    found_duplications = False
    duplication_details_list = []
    
    register = {himn:[] for himn in hymns_sheet.hymns_list} # Para regsitrar cuantas veces se usa un mismo himno.

    for day in hymns_sheet:
        for himn in day.hymn_list:
            register[himn].append(day)
    
    register_f = {key:value for key, value in register.items() if len(value) > 1} #Filtra los himnso que han sido usados mas de una vez.
    for himn_f, days in register_f.items():
        found_duplications = True
        duplication_details_list.append({
            "id": himn_f.id,
            "title": himn_f.title,
            "times_used": len(days),
            "dates": [date.date for date in days]
        })
        
    if display_on_console and found_duplications:
        _display_duplication_info_on_console(duplication_details_list)
        # Consider calling show_duplications_UI(duplication_details_list) here if it's meant to be part of this flow.
        
    return found_duplications

#   ======================================================================================================================
#                                   ACTUALIZAR INDICADORES DE FRECUENCIAS
#   ======================================================================================================================

def _calculate_new_frecuencies(id:int, date:date, last_record:dict):
    """
    Con los nuevos datos calcula las modificaciones que se haran en la tabla Frecuencias de la Base de Datos

    :param id: Id que apunta en la base de datos al himno que esta seindo procesado.
    :type id: int
    :param date: Fecha del cuadro al que pertenece el himno procesado.
    :type date: date
    :param last_record: Último registro guardado del himno procesado.
    :type last_record: dict
    """
    prev_last =    last_record['last'] #Revisar indices o optar por otro metodo
    prev_real =    last_record['real']
    prev_average = last_record['average']

    new_last = date
    new_real = prev_real + 1

    prev_last_d = date.fromisoformat(prev_last)
    diff = (new_last - prev_last_d).days
    new_average = (prev_average*prev_real+diff)/new_real

    return {
        id:{
            "last" : new_last,
            "real" : new_real,
            "average" : new_average
        }}

def _update_warning():
    """
    Muestra en pantalla la advertencia de que se modificará la base de datos y espera respuesta del usuario.
    """
    print("Este proceso actualizará los registros de uso de himnos en la base de datos.")
    print("Esto afectará los análisis e informes futuros.")
    print("Solo proceda si la hoja de himnos actual es definitiva y correcta.\n")
    
    while True:
        user_confirmation = input("¿Desea continuar y actualizar la base de datos? (s/n): ").strip().lower()
        
        if   user_confirmation in affirmative_answers: return True
        elif user_confirmation == 'n':                 return False 
        else: print("Respuesta no válida. Por favor, ingrese 's' para sí o 'n' para no.")    

def update_frecuency_register(hymn_sheet:HymnSheet):
    """
    Actualiza el registro de frecuencias de la base de datos.
    Antes advierte al ususario para continuar o cancelar operacion.
    
    :param hymn_sheet: Objeto que representa una hoja(programa de himnos)
    :type hymn_sheet: HymnSheet
    """
    if not _update_warning():
        return None
    
    updates = {}
    for day in hymn_sheet:
        h_date = day.date
        for himn in day:
            last_record = load_tracked_hymn_frequencies(himn.id)
            new_data = _calculate_new_frecuencies(himn.id, h_date, last_record)
            updates.update(new_data)
    
    update_hymn_frequencies_in_db(updates)

#   ======================================================================================================================
#                                   ASISTENTE DE ANALISIS DE HIMNOS
#   ======================================================================================================================

def _get_differences_days(hymn, current_date:date):
    if isinstance(hymn, int):
        hymn_id = hymn
    elif isinstance(hymn, Hymn):
        hymn_id = hymn.id
    else:
        raise ValueError
    
    last_record = load_tracked_hymn_frequencies(hymn_id)
    last_date = date.fromisoformat(last_record['last'])
    diffence = current_date-last_date
    return diffence.days

def _get_hymns_already_used(hymn_sheet:HymnSheet):
    hymns_used = []
    
    for day in hymn_sheet:
        for hymn in day:
            differece_days = _get_differences_days(hymn, day.date)
            hymns_used.append((hymn, differece_days))
            hymns_used.sort(key = lambda x:x[1])
    return hymns_used

def _get_hymns_unused(hymn_sheet:HymnSheet):
    hymns_unused = []

    hymns = set(hymn_sheet.hymns_list)
    hymns_id = [hymn.id for hymn in hymns]
    for i in range(1, get_total_hymns()+1):
        if i in hymns_id:
            continue
        difference_days = _get_differences_days(i, date.today())
        title = find_titles_by_ids(i)[0]
        hymns_unused.append((title, difference_days))
        hymns_unused.sort(key = lambda x:x[1], reverse=True)
    return hymns_unused

def _get_hymns_least_used(hymn_sheet:HymnSheet):
    title = 'Falta implementar :)'
    total_days_used = 0
    return[(title, total_days_used)]

def _display_frecuency_menu():
    """Prints the analysis options menu to the console."""
    if os.name == 'nt': os.system('cls')
    else: os.system('clear')
    
    ans = menu(
    "Mostrar himnos usados recientemente y también en esta hoja.",
    "Mostrar himnos NO usados en la(s) última(s) hoja(s) INCLUIDA esta.",
    "Mostrar himnos menos usados en general.",
    "Re-procesar la hoja actual (ej. después de corrección manual de datos).",
    "Continuar con la ejecución del programa.",
    title = "Asistente de Análisis de Uso de Himnos")
    
    return ans

class mode(Enum):
    ALREADY = "already_used"
    UNUSED = "unused"
    LEAST = "least_used"

def _get_register(hymns_sheet:HymnSheet, type_c: mode):
    """Formats and prints the analysis results."""
    collectors = {
        mode.ALREADY: _get_hymns_already_used,
        mode.UNUSED:  _get_hymns_unused,
        mode.LEAST:   _get_hymns_least_used
    }        

    def _create_register(data:tuple, idx = 1)->Dict[int, List]:
        keys = set([dat[idx] for dat in data])
        return {key:[] for key in keys}
    
    def _fill_register(register:dict, data:tuple):
        for dat in data:
            register[dat[1]].append(dat[0])

    collector = collectors[type_c]

    data = collector(hymns_sheet) # type: ignore

    if data:
        register = _create_register(data)
        _fill_register(register, data)
        return register

def _display_register(register:dict, type_p:mode):
    printers = {
        mode.ALREADY: lambda amount, days: f"{amount} himnos usados hace {days} días.",
        mode.UNUSED:  lambda amount, days: f"{amount} himnos no usados en {days} días.",
        mode.LEAST:   lambda amount, times: f"{amount} himnos usados solo {times} veces."
    }
    subtitle_f = printers[type_p]

    print(_bar(text="Resultados del Análisis"))

    for days, titles in register.items():
        
        subtitle = _bar(subtitle_f(len(titles), days), c="*")
        print(subtitle)
        for i, title in enumerate(titles, 1):
            print(f"\t{i}) {title}")
        
    print(_bar())

def hymn_usage_analysis_assistant(hymns_sheet, restart:list[bool]):
    while True:
        user_choice = _display_frecuency_menu()
        report_type:mode

        if user_choice == '1': # Recently used and in this sheet
            report_type = mode.ALREADY
            
        elif user_choice == '2': # Not used last sheet(s) and not this one
            report_type = mode.UNUSED
            
        elif user_choice == '3': # Least used overall
            report_type = mode.LEAST
        
        elif user_choice == '4': # Re-process
            restart[0] = True # Signal to the caller to re-process
            break
        
        elif user_choice == '5': # Continue
            restart[0] = False # Signal to the caller to continue
            break

        else:
            logger.warning(f'Se ingreso {user_choice}, y no es valido (ANALYSIS ASSISTANT)')
            print('\n\n\tOpción no válida. Por favor, intente de nuevo.\n')
            input('Presione Enter para volver al menú...')
            continue # Re-display menu
        
        register = _get_register(hymns_sheet, report_type)
        if register:
            _display_register(register, report_type)

        else:
            #No existe un regsitro
            pass

        input('\nPresione Enter para volver al menú de análisis...')
