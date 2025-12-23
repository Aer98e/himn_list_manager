import sqlite3
from .file_names import R_BUSQUEDA # Retains original name, assuming it's a specific resource locator
from utils.helpers import normalize_text # Changed from limpiar_texto1
from typing import Union, Any, List, Tuple, Optional
import os
import sqlite3 # Ensure sqlite3 is imported for the module
import logging

# Get a logger for this module
logger = logging.getLogger(__name__)

# Helper function to execute queries, reducing redundancy
def _execute_query(db_path_func: callable, query: str, params: Optional[tuple] = None,
                   fetch_one: bool = False, fetch_all: bool = False, commit: bool = False) -> Any:
    """
    Executes a given SQL query against the database specified by db_path_func.

    Args:
        db_path_func (callable): A function that returns the database file path (e.g., R_BUSQUEDA).
        query (str): The SQL query to execute.
        params (Optional[tuple]): Parameters to substitute into the query. Defaults to None.
        fetch_one (bool): If True, fetches one row.
        fetch_all (bool): If True, fetches all rows.
        commit (bool): If True, commits the transaction (for INSERT, UPDATE, DELETE).

    Returns:
        Any: The result of the query (single row, all rows, or None).

    Raises:
        ValueError: If both fetch_one and fetch_all are True.
    """
    if fetch_one and fetch_all:
        raise ValueError("Cannot set both fetch_one and fetch_all to True.")
    
    db_path = db_path_func() # Get the database path
    conn = None # Initialize conn to None
    try:
        conn = sqlite3.connect(db_path)
        # Set timeout to prevent 'database is locked' errors for concurrent access if it becomes an issue.
        # conn.timeout = 10 # 10 seconds, adjust as needed. Not strictly necessary for single-threaded app.
        cursor = conn.cursor()
        cursor.execute(query, params or ())

        if commit:
            conn.commit()

        if fetch_one:
            return cursor.fetchone()
        if fetch_all:
            return cursor.fetchall()
        return None # For operations like INSERT/UPDATE without fetch, or if no fetch type specified
    except sqlite3.OperationalError as e:
        # Handles errors like "database is locked", "no such table", "database disk image is malformed"
        logger.error(f"SQLite OperationalError in _execute_query (DB: {db_path}, Query: {query}): {e}", exc_info=True) # Replaced print
        return None # Or an empty list if fetch_all was expected by caller
    except sqlite3.IntegrityError as e:
        # Handles errors like "UNIQUE constraint failed"
        logger.error(f"SQLite IntegrityError in _execute_query (DB: {db_path}, Query: {query}): {e}", exc_info=True) # Replaced print
        raise # Re-raising might be appropriate if the caller needs to know about constraint violations
    except sqlite3.Error as e: # Catch other sqlite3 related errors
        logger.error(f"An unexpected SQLite error occurred in _execute_query (DB: {db_path}, Query: {query}): {e}", exc_info=True) # Replaced print
        return None # Or an empty list
    finally:
        if conn:
            conn.close()


def find_title_by_normalized_text(normalized_title: str) -> Optional[str]:
    '''
    Retrieves the original hymn title corresponding to a given normalized title.
    Multiple normalized titles can reference a single original title.

    Args:
        normalized_title (str): The normalized title to search for.

    Returns:
        Optional[str]: The original hymn title if found, otherwise None.
    '''
    query = """
        SELECT H.titulo
        FROM Himnos H
        JOIN Indice_busqueda IB ON H.id = IB.id_himno
        WHERE IB.titulo_norm = ?
    """
    result = _execute_query(R_BUSQUEDA, query, params=(normalized_title,), fetch_one=True)
    return result[0] if result else None

def find_titles_by_ids(title_ids: Union[int, List[int]]) -> List[str]:
    """
    Retrieves hymn titles for a given ID or list of IDs.

    Args:
        title_ids (Union[int, List[int]]): A single hymn ID or a list of hymn IDs.

    Returns:
        List[str]: A list of hymn titles corresponding to the given IDs.

    Raises:
        TypeError: If title_ids is not an int or a list of ints.
    """
    if isinstance(title_ids, int):
        ids_to_query = [title_ids]
    elif isinstance(title_ids, list):
        if not all(isinstance(item, int) for item in title_ids):
            raise TypeError('All elements in title_ids list must be integers.')
        ids_to_query = title_ids
    else:
        raise TypeError("title_ids must be an integer or a list of integers.")

    if not ids_to_query:
        return []

    # Using a placeholder for each ID to prevent SQL injection, though less critical for IDs.
    # However, _execute_query currently only supports a single param tuple for execute.
    # For multiple IDs, we might need to adjust _execute_query or call it multiple times.
    # For simplicity here, calling it multiple times, which is less efficient for many IDs.
    titles = []
    for title_id in ids_to_query:
        query = 'SELECT titulo FROM Himnos WHERE id = ?'
        result = _execute_query(R_BUSQUEDA, query, params=(title_id,), fetch_one=True)
        if result:
            titles.append(result[0])

        else:
            logger.critical("Un himno no se encontro en la base de datos, esto rompe la presentacion de frecuencias.")
            raise ValueError("Un himno no se encontro en la base de datos, esto rompe la presentacion de frecuencias.")
    return titles


def find_data_by_normalized_title(normalized_title: str, columns_to_fetch: List[str]) -> Optional[Union[tuple, Any]]:
    '''
    Performs a general search for specified columns based on a normalized title.

    Args:
        normalized_title (str): The normalized title to search by.
        columns_to_fetch (List[str]): A list of column names from the 'Himnos' table to retrieve.

    Returns:
        Optional[Union[tuple, Any]]: A tuple of the fetched data if multiple columns are requested,
                                     a single value if one column is requested, or None if not found.
    Raises:
        ValueError: If columns_to_fetch is not a list or is empty.
    '''
    if not isinstance(columns_to_fetch, list) or not columns_to_fetch:
        raise ValueError('columns_to_fetch must be a non-empty list of column names.')
    
    # SECURITY N0TE: columns_to_fetch are directly embedded into the SQL query.
    # This is safe if columns_to_fetch comes from a trusted source (e.g., hardcoded list).
    # If columns_to_fetch could be influenced by external input, it MUST be validated
    # against a whitelist of allowed column names to prevent SQL injection.
    select_columns = ", ".join([f"H.{col}" for col in columns_to_fetch])
    query = f"""
        SELECT {select_columns}
        FROM Himnos H
        JOIN Indice_busqueda IB ON H.id = IB.id_himno
        WHERE IB.titulo_norm = ?
    """
    result = _execute_query(R_BUSQUEDA, query, params=(normalized_title,), fetch_one=True)

    if result:
        return result if len(columns_to_fetch) > 1 else result[0]
    return None

def add_to_search_index(new_normalized_title: str, existing_normalized_title_match: str):
    '''
    Adds a new normalized title to the search index, linking it to the same hymn ID
    as an existing normalized title.

    Args:
        new_normalized_title (str): The new normalized title to add.
        existing_normalized_title_match (str): An existing normalized title whose hymn ID will be used.
    '''
    # First, get the hymn_id from the existing normalized title
    id_query = 'SELECT id_himno FROM Indice_busqueda WHERE titulo_norm = ?'
    result = _execute_query(R_BUSQUEDA, id_query, params=(existing_normalized_title_match,), fetch_one=True)

    if result:
        hymn_id = result[0]
        # Insert the new normalized title with the fetched hymn_id
        insert_query = 'INSERT INTO Indice_busqueda (id_himno, titulo_norm) VALUES (?, ?)'
        _execute_query(R_BUSQUEDA, insert_query, params=(hymn_id, new_normalized_title), commit=True)
    else:
        logger.warning(f'Could not find hymn ID for :: {existing_normalized_title_match} in the database to add new title.') # Replaced print


def get_column_values(db_name_func: callable, table_name: str, column_name: str) -> List[Any]:
    """
    Retrieves all values from a specific column in a given table and database.

    Args:
        db_name_func (callable): Function that returns the path to the database (e.g., R_BUSQUEDA).
        table_name (str): The name of the table to query.
        column_name (str): The name of the column from which to fetch values.

    Returns:
        List[Any]: A list of values from the specified column.
    """
    # SECURITY NOTE: table_name and column_name are directly embedded into the SQL query.
    # This is safe if these names come from a trusted, controlled source (e.g., hardcoded values,
    # internal mappings). If table_name or column_name could be influenced by any external input,
    # they MUST be validated against a whitelist of allowed table/column names to prevent SQL injection.
    query = f"SELECT {column_name} FROM {table_name}"
    results = _execute_query(db_name_func, query, fetch_all=True)
    return [row[0] for row in results if row] if results else []

def get_all_normalized_titles() -> List[str]:
    '''
    Fetches all recorded normalized titles from the search index database.

    Returns:
        List[str]: A list of all normalized titles.
    '''
    # query = 'SELECT titulo_norm FROM Indice_busqueda'
    # results = _execute_query(R_BUSQUEDA, query, fetch_all=True)

    # return [row[0] for row in results if row] if results else []
    results = get_column_values(R_BUSQUEDA, "Indice_busqueda", "titulo_norm")
    return results


def extract_hymn_data_for_display(title: str) -> Optional[List[str]]:
    """
    Extracts and formats hymn data for display purposes based on the original title.
    This involves normalizing the title, finding its ID, and then retrieving
    associated data, applying specific formatting rules.

    Args:
        title (str): The original hymn title.

    Returns:
        Optional[List[str]]: A list containing formatted [title, usage_number, new_number_indicator],
                             or None if the hymn is not found.
    """
    normalized_title = normalize_text(title)
    
    # Get hymn_id using the normalized title
    id_query = 'SELECT id_himno FROM Indice_busqueda WHERE titulo_norm = ?'
    id_result = _execute_query(R_BUSQUEDA, id_query, params=(normalized_title,), fetch_one=True)
    
    if not id_result:
        logger.warning(f'Hymn not found for display: {title} (Normalized: {normalized_title})') # Replaced print
        return None
        
    hymn_id = id_result[0]
    
    # Get hymn details
    details_query = """
        SELECT titulo, numH_uso, numH_nuevo, es_nuevo, sube_tono, id_himnario
        FROM Himnos
        WHERE id = ?
    """
    data_result = _execute_query(R_BUSQUEDA, details_query, params=(hymn_id,), fetch_one=True)

    if not data_result:
        # This case should ideally not happen if id_result was successful, implies data inconsistency
        logger.error(f'Hymn data not found for ID: {hymn_id} (Title: {title}) though ID was found via normalized title.') # Replaced print
        return None
        
    original_title, usage_hymn_num, new_hymn_num, is_new_hymn, transpose_up, hymnary_id = data_result
    
    # Format new hymn number string
    new_hymn_num_str = str(new_hymn_num) if new_hymn_num is not None else ""
    if is_new_hymn: # es_nuevo
        new_hymn_num_str += '::N'
    if transpose_up: # sube_tono
        new_hymn_num_str += '::U'
    
    # Format usage hymn number string based on hymnary_id
    usage_hymn_num_str = str(usage_hymn_num) if usage_hymn_num is not None else ""
    if usage_hymn_num: # Only add suffix if num_B_P exists
        if hymnary_id == 1: # Himnario de Bautista (Baptist Hymnal)
            usage_hymn_num_str += '::R' # Red book indicator
        elif hymnary_id == 2: # Himnario Popular (Popular Hymnal)
            usage_hymn_num_str += '::V' # Green book indicator (assuming V stands for Verde/Green)
        
    return [original_title, usage_hymn_num_str, new_hymn_num_str]

def load_tracked_hymn_frequencies() -> List[Tuple[int, int, int]]:
    '''
    Loads hymn frequencies for hymns that are marked for tracking.

    Returns:
        List[Tuple[int, int, int]]: A list of tuples, where each tuple contains
                                     (hymn_id, useful_frequency, real_frequency).
    '''
    query = """
        SELECT id_himno, frec_util, frec_real
        FROM Frecuencias
        WHERE seguimiento = 1 
    """ # seguimiento = 1 means tracking is enabled
    return _execute_query(R_BUSQUEDA, query, fetch_all=True) or []


def update_hymn_frequencies_in_db(frequency_data_updates: List[Tuple[int, int, int]]):
    """
    Updates hymn frequencies in the database.

    Args:
        frequency_data_updates (List[Tuple[int, int, int]]): A list of tuples,
            where each tuple is (new_useful_frequency, new_real_frequency, hymn_id).
            Note the order for executemany.
    """
    if not frequency_data_updates:
        return

    query = """
        UPDATE Frecuencias
        SET frec_util = ?, frec_real = ?
        WHERE id_himno = ?
    """
    # For executemany, the _execute_query helper is not directly used as it's designed for single executions.
    # Direct sqlite3 usage is appropriate here.
    db_path = R_BUSQUEDA()
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.executemany(query, frequency_data_updates)
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"SQLite error during bulk update_hymn_frequencies_in_db (DB: {db_path}): {e}", exc_info=True) # Replaced print
        # Log error, potentially raise a custom exception or handle
    finally:
        if conn:
            conn.close()

def getId_by_normTitle(title_norm:str):
    query = """
    SELECT id_himno
    FROM Indice_busqueda
    WHERE titulo_norm = ?
    """
    res = _execute_query(R_BUSQUEDA, query, (title_norm,), fetch_one=True)
    return res[0]


def ensure_history_table_exists():
    """
    Creates the 'Historial_Uso' table if it does not exist.
    """
    query = """
    CREATE TABLE IF NOT EXISTS Historial_Uso (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_himno INTEGER NOT NULL,
        fecha_uso TEXT NOT NULL,
        tipo_evento TEXT,
        FOREIGN KEY (id_himno) REFERENCES Himnos(id)
    );
    """
    _execute_query(R_BUSQUEDA, query, commit=True)
    logger.info("Checked/Created 'Historial_Uso' table.")


def register_hymn_usage(hymn_id: int, date_iso: str, event_type: str = 'unknown'):
    """
    Registers the usage of a hymn on a specific date and event type.

    Args:
        hymn_id (int): The ID of the hymn.
        date_iso (str): The date in ISO-8601 format (YYYY-MM-DD).
        event_type (str): The type of event (e.g., 'sunday_service', 'test_migration').
    """
    query = """
    INSERT INTO Historial_Uso (id_himno, fecha_uso, tipo_evento)
    VALUES (?, ?, ?)
    """
    _execute_query(R_BUSQUEDA, query, params=(hymn_id, date_iso, event_type), commit=True)
    logger.info(f"Registered usage for hymn {hymn_id} on {date_iso} ({event_type}).")


def get_hymns_with_last_date() -> List[Tuple[int, Optional[str]]]:
    """
    Retrieves hymns with their last usage date.
    Returns a list of tuples (hymn_id, last_usage_date).
    """
    query = """
    SELECT H.id, MAX(HU.fecha_uso) as ultima_fecha
    FROM Himnos H
    LEFT JOIN Historial_Uso HU ON H.id = HU.id_himno
    GROUP BY H.id
    """
    # Note: Using LEFT JOIN to include hymns even if they haven't been used yet, 
    # though the requirement wording "JOIN" overlaps, the intent "Asignar fecha" usually implies we want to know for all or those with history.
    # The validation script expects a list where d[0] is ID and d[1] is date.
    
    results = _execute_query(R_BUSQUEDA, query, fetch_all=True)
    return results or []


def get_usage_on_date(date_iso: str) -> List[int]:
    """
    Retrieves the list of hymn IDs used on a specific date.

    Args:
        date_iso (str): The date in ISO-8601 format (YYYY-MM-DD).

    Returns:
        List[int]: A list of hymn IDs.
    """
    query = "SELECT id_himno FROM Historial_Uso WHERE fecha_uso = ?"
    results = _execute_query(R_BUSQUEDA, query, params=(date_iso,), fetch_all=True)
    return [row[0] for row in results] if results else []

def main():
    # Example usage or testing can go here
    # Test find_title_by_normalized_text
    # title = find_title_by_normalized_text("a dios sea gloria")
    # print(f"Found title: {title}")

    # Test find_titles_by_ids
    # titles_single = find_titles_by_ids(1)
    # print(f"Titles for ID 1: {titles_single}")
    # titles_multiple = find_titles_by_ids([1, 2, 3])
    # print(f"Titles for IDs 1,2,3: {titles_multiple}")

    # Test get_all_normalized_titles
    # all_norm_titles = get_all_normalized_titles()
    # print(f"All normalized titles count: {len(all_norm_titles)}")

    # Test extract_hymn_data_for_display
    # hymn_display_data = extract_hymn_data_for_display("A DIOS SEA GLORIA") # Use an actual title from your DB
    # print(f"Display data for 'A DIOS SEA GLORIA': {hymn_display_data}")
    pass

if __name__ == "__main__":
    main()
