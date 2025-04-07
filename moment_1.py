import pandas as pd
import Internal
import sys
import recicle as rec
import sqlite3
from  difflib import SequenceMatcher
from recicle import Management_Text as Text
from recicle import Management_SQLite as M_SQ
import numpy as np
import datetime
from rapidfuzz import fuzz, process
from os import system
import re

R_GENERAL = 'Registro_General_Himnos_2.db'
R_BUSQUEDA = 'search_ref.db'
COL_TIT = 0


def Extraer_Cuadros(file, identifier='R'):
    """
    Extracts rectangular sections (cuadros) from an Excel file based on a specific identifier.
    This function reads an Excel file into a NumPy array and identifies regions of interest
    starting with a specific identifier (default is 'R'). It dynamically determines the size
    of each region and extracts it as a DataFrame.
    Args:
        file (str): The path to the Excel file to be processed.
        identifier (str, optional): The identifier used to locate the starting points of the
            regions of interest. Defaults to 'R'.
    Returns:
        list: A list of DataFrames, where each DataFrame represents a rectangular section
        (cuadro) extracted from the Excel file. Only sections with more than 2 rows are included.
    Notes:
        - The function assumes that the identifier is located in a single cell and that the
          region of interest extends downward until an empty or NaN cell is encountered.
        - The extracted regions include two columns to the left of the identifier column.
        - The function skips regions with 2 or fewer rows.
    """
    # Leer el archivo Excel en un DataFrame
    df = pd.read_excel(file, header=None)
    numpy_array = df.to_numpy()

    mask_R = numpy_array == identifier  # Crear una máscara para detectar 'R'
    cuadros = []

    # Iterar por las posiciones donde se encuentra 'R'
    for row, col in np.argwhere(mask_R):  # `np.argwhere` encuentra las posiciones de 'R'
        fila_aum = 0  # Contador de filas incluidas en el cuadro
        while True:
            # Verificar si estamos dentro del rango de filas y si la fila no está vacía
            if row + fila_aum >= numpy_array.shape[0]:  # Evitar índice fuera de rango
                break
            cell_current = numpy_array[row + fila_aum, col-1]  # Seleccionar la fila actual
            if pd.isna(cell_current) or cell_current=='':  # Si la fila está vacía, detener
                break
            fila_aum += 1  # Expandir el rango de filas hacia abajo

        # Extraer el cuadro desde 'R' y las filas dinámicas encontradas
        cuadro = numpy_array[row:row + fila_aum, col - 2:col]  # Ajustar columnas según lo necesario
        if cuadro.shape[0] > 2:
            cuadros.append(pd.DataFrame(cuadro))  # Convertir a DataFrame para procesarlo fácilmente

    return cuadros

def extract_table_titles(cuadro:pd.DataFrame, ind_column:int, norm = False):
    """
    Extracts and optionally normalizes titles from a specified column in a DataFrame.
    Args:
        cuadro (pd.DataFrame): The DataFrame containing the data.
        ind_column (int): The index of the column from which to extract titles.
        norm (bool, optional): If True, normalizes the extracted titles using 
            `Text.limpiar_texto1`. Defaults to True.
    Returns:
        list: A list of tuples containing normalized and original titles if `norm` is True,
                or an list if `norm` is False.
    """
    resultados=[]
    
    titles = cuadro.iloc[1:, ind_column].to_list()

    
    if norm:
        # data_norm = [(Text.limpiar_texto1(title), title) for title in titles]
        data_norm = [Text.limpiar_texto1(title) for title in titles]
        resultados = data_norm

    else:
        return titles

    return resultados

def find_simil(simil):
    with sqlite3.connect(R_BUSQUEDA) as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT Himnos.titulo
            FROM Himnos
            JOIN Indice_busqueda ON Himnos.id=Indice_busqueda.id_himno
            WHERE Indice_busqueda.titulo_norm = ?
            ''',(simil,))
        res = cursor.fetchone()
    return res[0]

def update_search_list(title_norm, norm_match):
    with sqlite3.connect(R_BUSQUEDA) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id_himno FROM Indice_busqueda WHERE titulo_norm = ?', (norm_match,))
        indice = cursor.fetchone()
        if indice is not None:
            cursor.execute('INSERT INTO Indice_busqueda(id_himno, titulo_norm) VALUES(?, ?)', (indice[0], title_norm))
            conn.commit()
        else:
            print(f'No se encontro :: {norm_match} en la base de datos.')

def add_titles_stranges(cuadros):
    """
    add_titles_stranges(cuadros)
    This function processes a list of hymn titles, compares them with an existing database, 
    and updates the database with new titles or matches similar ones. It uses fuzzy matching 
    to find the best matches for new titles and allows for manual confirmation of matches.
    Parameters:
        cuadros (list): A list of data structures containing hymn titles to be processed.
    Returns:
        list: A list of hymn titles that could not be matched or updated in the database.
    Functions:
        - extract_titles(): Extracts hymn titles from the input `cuadros` and returns them as a set.
        - init_master(): Initializes the master list and set of normalized titles from the database.
        - init_slave(master_set_norm): Extracts and normalizes titles from the input, 
          and identifies new titles not present in the master set.
        - generate_match_matrix(slave_util, master_list_norm): Generates a match matrix 
          using fuzzy matching to compare new titles with the master list.
        - find_best_match(match_matrix, master_list_norm): Finds the best matches for each 
          new title based on the match matrix.
        - update_database(best_matches, index, slave_list, not_find): Updates the database 
          with the best matches or prompts the user for manual confirmation if no strong match is found.
    Notes:
        - The function uses fuzzy matching with a score cutoff of 60 to identify potential matches.
        - Titles with a match score of 85 or higher are automatically updated in the database.
        - For lower scores, the user is prompted to confirm if the titles are the same.
        - Titles that cannot be matched or confirmed are added to the `not_find` list.
    """
    def extract_titles():
        TITLE_COLUMN = 1
        slave_set = set()
        for cuadro in cuadros:
            titles = extract_table_titles(cuadro, TITLE_COLUMN, norm=False)
            slave_set.update(titles)
        
        return slave_set

    def init_master():
        master_list_norm = M_SQ.Buscar_Columna(R_BUSQUEDA, 'Indice_busqueda', 'titulo_norm')
        master_set_norm = {title for title in master_list_norm}
        master_list_norm = list(master_set_norm)

        return master_list_norm, master_set_norm
    
    def init_slave(master_set_norm):
        slave_set = extract_titles()
        slave_dict = {Text.limpiar_texto1(title): title for title in slave_set}
        slave_util = set(slave_dict.keys()) - master_set_norm
        if not slave_util:
            print('No hay himnos nuevos')
            return None, None
        slave_list = [slave_dict[title] for title in slave_util]
        return slave_list, slave_util
    
    def generate_match_matrix(slave_util, master_list_norm):
        match_matrix = process.cdist(slave_util, master_list_norm, scorer = fuzz.partial_ratio, score_cutoff = 60)
        return match_matrix

    def find_best_match(match_matrix, master_list_norm):
        best_matches = []
        for i, row in enumerate(match_matrix):
            best_index = np.argsort(row)[::-1][:5]
            best_matches.append([(master_list_norm[j], row[j]) for j in best_index])
        return best_matches
    
    def update_database(best_matches, title_slave, title_slave_norm, not_find):
        RATIO = 1
        TITLE = 0
        find = False
        for i, match_a in enumerate(best_matches):
            if match_a[RATIO] >= 85:
                update_search_list(title_slave_norm, match_a[TITLE])
                break
            
            possible_match = find_simil(match_a[TITLE])
            print('----------------------------------')
            print("Son el mismo himno?")
            print(f'--{title_slave}')
            print(f'--{possible_match}')	
            ans = input('_________________(S/N): ').strip()
            print("")

            if ans.lower() in rec.ans_y:
                update_search_list(title_slave_norm, match_a[TITLE])
            
            elif not find and i == len(best_matches)-1:
                not_find.append(title_slave)
            

    master_list_norm, master_set_norm = init_master()
    slave_list, slave_util = init_slave(master_set_norm)

    if slave_util is None:
        return
    
    match_matrix = generate_match_matrix(slave_util, master_list_norm)

    best_matches_row = find_best_match(match_matrix, master_list_norm)
    
    slave_list_norm = list(slave_util)
    not_find = []
    for i, best_matches in enumerate(best_matches_row):
        update_database(best_matches, slave_list[i], slave_list_norm[i], not_find)
    
    return not_find

def correction_days(cuadros, month = None, year = None):
    def _extract_days(cuadros):
        days = []
        for cuadro in cuadros:
            day = cuadro.iat[0, 0]
            day = str(day)
            num = re.search(r'\d+', day)
            if num is not None:
                days.append(int(num[0]))
            else:
                print('Un cuadro no tiene fecha.')
        return days

    dates = []

    weeken=['LUNES', 'MARTES', 'MIÉRCOLES', 'JUEVES', 'VIERNES', 'SABADO', 'DOMINGO']
    today = datetime.date.today()
    

    year = today.year if year is None else year
    month = today.month if month is None else month
    print(f'año:{year}, mes {month}')

    day_list = _extract_days(cuadros)
    afternoon = False

    for i, day in enumerate(day_list):
        table_date = datetime.date(year, month, day)
        if table_date < today:#El igual permitira trabajar ese mismo dia o no.
            dates.append(None)
        else:
            day_ind = table_date.weekday()
            temp_date = f'{weeken[day_ind]} {day:02}'

            if afternoon:
                dates.append(f'{temp_date} T')
                afternoon = False
            
            elif i < len(day_list)-1:
                if day == day_list[i+1]:
                    day == day_list[i+1]
                    dates.append(f'{temp_date} M')
                    afternoon = True
                    continue
                dates.append(temp_date)
            
            else:
                dates.append(temp_date)
    return dates
    
def filter_tables_day(cuadros, corrector):
    cuadros_new=[]
    for i in range(len(cuadros)):
        if corrector[i] is None:
            continue
        cuadros[i].iat[0, 0] = corrector[i]
        cuadros_new.append(cuadros[i].copy())
    return cuadros_new

def concatenate_dataframes(df_list, limit = 3):
    def _add_empty_columns(df_list, limit=3):
        """
        Agrupa DataFrames en listas y añade columnas vacías según un límite.

        Args:
            df_list (list): Lista de DataFrames.
            limit (int): Número máximo de DataFrames por grupo.

        Returns:
            list: Lista de listas de DataFrames agrupados.
        """
        current_group = []
        grouped_dataframes = []
        group_counter = 0

        for i, df in enumerate(df_list):
            df = df.copy()
            df.reset_index(drop=True, inplace=True)  # Reinicia el índice del DataFrame
             # Copia el DataFrame original para evitar modificarlo directamente
            group_counter+=1

            if i < len(df_list)-1:

                if group_counter < limit:
                    df['empty'] = None
                
                else:
                    group_counter = 0
                    current_group.append(df)
                    grouped_dataframes.append(current_group)
                    current_group = []
                    continue
                
                current_group.append(df)
            
            else:
                current_group.append(df)
                grouped_dataframes.append(current_group)
        
        return grouped_dataframes

    def _concatenate_column(pack_row):
        rows_list = []

        for row in pack_row:
            result = pd.concat(row, axis=1, ignore_index=True)  # Apila las columnas
            rows_list.append(result)

        return rows_list

    def _concatenate_row(rows_list):
        empty_row = pd.DataFrame({col:[None] for col in rows_list[0].columns})  # Crea una fila vacía con las mismas columnas que el primer DataFrame
        with_empty_row = []
        for i, df in enumerate(rows_list):
            with_empty_row.append(df)
            if i < len(rows_list) - 1:
                with_empty_row.append(empty_row)
                
        result = pd.concat(with_empty_row, ignore_index=True)  # Apila las filas
        return result

    pack_rows = _add_empty_columns(df_list, limit)
    rows_list = _concatenate_column(pack_rows)
    # for row in rows_list:
    #     print(row)
    #     print('----------------------------------')
    df_master = _concatenate_row(rows_list)
    return df_master


def main():
    cuadros = Extraer_Cuadros('Himnos 2025 marzo.xlsx')
    no_find = add_titles_stranges(cuadros)
    if no_find:
        print('No se encontraron los siguientes himnos:')
        print(no_find)

    # result = correction_days(cuadros)
    # cuadros_new = filter_tables_day(cuadros, result)
    # df_master = concatenate_dataframes(cuadros_new, limit=3)

    # df_master = df_master.fillna("-")

    # print(df_master)

    
    


    




if __name__ == '__main__':
    main()