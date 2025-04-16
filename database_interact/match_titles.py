from data_processing.extraction import extract_table_titles
from utils.helpers import limpiar_texto1, ans_y
from rapidfuzz import fuzz, process
from .queries import update_search_list, find_title, Buscar_Columna
from .file_names import R_BUSQUEDA
import numpy as np

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
        master_list_norm = Buscar_Columna(R_BUSQUEDA(), 'Indice_busqueda', 'titulo_norm')
        master_set_norm = {title for title in master_list_norm}
        master_list_norm = list(master_set_norm)

        return master_list_norm, master_set_norm
    
    def init_slave(master_set_norm):
        slave_set = extract_titles()
        slave_dict = {limpiar_texto1(title): title for title in slave_set}
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
    
    def update_database(best_matches, title_slave, title_slave_norm, not_find:list):
        RATIO = 1
        TITLE = 0
        find = False
        for i, match_a in enumerate(best_matches):
            if match_a[RATIO] >= 85:
                update_search_list(title_slave_norm, match_a[TITLE])
                break
            
            possible_match = find_title(match_a[TITLE])
            print('----------------------------------')
            print("Son el mismo himno?")
            print(f'--{title_slave}')
            print(f'--{possible_match}')	
            ans = input('_________________(S/N): ').strip()
            print("")

            if ans.lower() in ans_y:
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

def main():
    pass

if __name__ =="__main__":
    main()
