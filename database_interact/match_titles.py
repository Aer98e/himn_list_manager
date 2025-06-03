from data_processing.extraction import extract_table_titles
from utils.helpers import normalize_text, affirmative_answers # Functions renamed
from rapidfuzz import fuzz, process
from .queries import add_to_search_index, find_title_by_normalized_text, get_all_normalized_titles # Functions renamed
# R_BUSQUEDA is not directly used here anymore as queries handle DB path.
# Buscar_Columna is not used here.
import numpy as np
from typing import List, Set, Tuple, Optional, Dict, Any # For type hinting
import pandas as pd # For type hinting DataFrames
import logging

# Get a logger for this module
logger = logging.getLogger(__name__)


def process_and_match_new_hymn_titles(data_frames: List[pd.DataFrame]) -> Optional[List[str]]:
    """
    Processes hymn titles from a list of DataFrames, identifies new/unrecognized titles
    by comparing against existing normalized titles in the database, and attempts to match
    them using fuzzy string matching. Updates the database search index for confirmed matches.

    Args:
        data_frames (List[pd.DataFrame]): A list of pandas DataFrames, each typically representing
                                         a table of hymns from an input file. Titles are expected
                                         in the second column (index 1).

    Returns:
        Optional[List[str]]: A list of original hymn titles that could not be automatically or
                             manually matched and added to the database. Returns None if no
                             new/unrecognized titles were found to process.
    
    Detailed Workflow:
    1.  Extracts all unique original hymn titles from the input `data_frames`.
    2.  Loads all existing normalized hymn titles from the database to serve as the "master list".
    3.  Normalizes the extracted original titles and identifies which ones are "new" (not in the master list).
    4.  If new titles are found:
        a.  Generates a similarity matrix between new normalized titles and existing normalized titles using fuzzy matching.
        b.  For each new title, finds the top 5 best matches from the existing titles.
        c.  Iterates through these best matches:
            i.  If a match score is >= 85 (high confidence), automatically adds the new normalized title to the
                search index, linking it to the matched existing hymn.
            ii. If a match score is lower, it presents the original new title and the potential matched original
                title (retrieved from DB) to the user for manual confirmation (Yes/No).
            iii. If confirmed by the user, the new title is added to the search index.
            iv. If no suitable match is found or confirmed after checking all top 5, the original new title is
                added to a `unmatched_titles` list.
    5.  Returns the list of `unmatched_titles`.
    """

    def extract_unique_original_titles_from_frames() -> Set[str]:
        """Helper to extract all unique (non-normalized) hymn titles from the input DataFrames."""
        original_titles_set: Set[str] = set()
        for frame_df in data_frames:
            # `extract_table_titles` with norm=False returns original titles
            titles_in_frame = extract_table_titles(frame_df, normalize=False)
            original_titles_set.update(titles_in_frame)
        return original_titles_set

    def get_existing_normalized_titles_from_db() -> Tuple[List[str], Set[str]]:
        """Helper to fetch all normalized titles from the database."""
        # `get_all_normalized_titles` is assumed to return a list of strings
        db_normalized_titles_list = get_all_normalized_titles()
        db_normalized_titles_set = set(db_normalized_titles_list)
        # Return both list (maintains order if needed) and set (for fast lookups)
        return list(db_normalized_titles_set), db_normalized_titles_set 
    
    def identify_new_titles_to_process(
        existing_normalized_set: Set[str]
    ) -> Tuple[Optional[List[str]], Optional[List[str]]]:
        """
        Normalizes extracted original titles and filters out those already in the database.
        Returns a list of original new titles and a list of their normalized versions.
        """
        all_original_titles_set = extract_unique_original_titles_from_frames()
        # Create a mapping from normalized title to original title for new titles
        # This helps retain the original form for display and for the `unmatched_titles` list.
        new_normalized_to_original_map: Dict[str, str] = {}
        for title in all_original_titles_set:
            normalized = normalize_text(title)
            if normalized not in existing_normalized_set:
                 # If multiple original titles normalize to the same string, this will keep only one.
                 # This is usually fine as the goal is to add the normalized form to the DB.
                new_normalized_to_original_map[normalized] = title

        if not new_normalized_to_original_map:
            logger.info('No new hymn titles found to process during title matching.') # Replaced print
            return None, None # No new titles
            
        new_normalized_list = list(new_normalized_to_original_map.keys())
        # Ensure original_titles_for_processing corresponds to new_normalized_list
        original_titles_for_processing = [new_normalized_to_original_map[norm] for norm in new_normalized_list]
        
        return original_titles_for_processing, new_normalized_list
    
    def calculate_similarity_matrix(
        new_normalized_titles: List[str], 
        existing_normalized_titles: List[str]
    ) -> np.ndarray:
        """Generates a similarity matrix using fuzzy partial ratio matching."""
        # `process.cdist` calculates distances (or similarities) between all pairs.
        # `fuzz.partial_ratio` is good for finding substrings or when parts of strings match.
        # `score_cutoff=60` means only scores >= 60 will be considered non-zero in the matrix.
        similarity_matrix = process.cdist(
            new_normalized_titles, 
            existing_normalized_titles, 
            scorer=fuzz.partial_ratio, 
            score_cutoff=60
        )
        return similarity_matrix

    def find_top_n_matches_from_matrix(
        similarity_matrix_row: np.ndarray, 
        existing_normalized_titles: List[str],
        top_n: int = 5
    ) -> List[Tuple[str, float]]:
        """For a single row of the similarity matrix, finds the top N best matches."""
        # `np.argsort` returns indices that would sort the array. `[::-1]` reverses for descending.
        best_match_indices = np.argsort(similarity_matrix_row)[::-1][:top_n]
        # Create list of (matched_title_norm, score)
        top_matches = [
            (existing_normalized_titles[j], float(similarity_matrix_row[j])) 
            for j in best_match_indices if similarity_matrix_row[j] > 0 # Ensure score > 0
        ]
        return top_matches
    
    def attempt_database_update_for_new_title(
        top_matches_for_new_title: List[Tuple[str, float]], 
        original_new_title: str, 
        normalized_new_title: str, 
        unmatched_titles_list: List[str]
    ):
        """
        Attempts to update the database for a single new title based on its top matches.
        Handles automatic updates for high-confidence matches and user confirmation for others.
        """
        MATCH_SCORE_INDEX = 1
        NORMALIZED_TITLE_MATCH_INDEX = 0
        HIGH_CONFIDENCE_THRESHOLD = 85.0 # Score for automatic matching

        match_found_and_confirmed = False
        for i, (matched_db_norm_title, match_score) in enumerate(top_matches_for_new_title):
            db_original_title_for_match = find_title_by_normalized_text(matched_db_norm_title)
            if db_original_title_for_match is None: # Should not happen if matched_db_norm_title is valid, but good check
                logger.warning(f"No se pudo encontrar el título original para el título normalizado '{matched_db_norm_title}' en la base de datos. Omitiendo esta coincidencia.")
                continue

            if match_score >= HIGH_CONFIDENCE_THRESHOLD:
                logger.info(f"Coincidencia de alta confianza para '{original_new_title}' con el existente '{db_original_title_for_match}' (Puntuación: {match_score:.2f}). Añadiendo automáticamente al índice de búsqueda.")
                add_to_search_index(normalized_new_title, matched_db_norm_title)
                match_found_and_confirmed = True
                break # Exit after the first high-confidence match
            
            # For lower scores, ask user (using logger for prompts that are part of this flow)
            logger.debug(f'Se cree que {db_original_title_for_match} se compara a {original_new_title}.')
            print('----------------------------------')
            print(f"Posible coincidencia para el nuevo himno: '{original_new_title}'")
            print(f"Con el himno existente: '{db_original_title_for_match}' (Normalizado: '{matched_db_norm_title}')")
            print(f"Puntuación de coincidencia: {match_score:.2f}")
            
            while True:
                user_confirmation = input(f"¿Son estos himnos el mismo? '{original_new_title}' Y '{db_original_title_for_match}' (s/n): ").strip().lower()
                if user_confirmation in affirmative_answers or user_confirmation == 'n': # 'n' is a valid negative answer
                    break
                print("Respuesta no válida. Por favor, ingrese 's' para sí o 'n' para no.")
                logger.warning("Se ingresó una respuesta no valida para una posible coincidencia de títulos.")
            
            if user_confirmation in affirmative_answers:
                logger.info(f"El usuario confirmó la coincidencia para '{original_new_title}' con '{db_original_title_for_match}'. Añadiendo al índice de búsqueda.")
                add_to_search_index(normalized_new_title, matched_db_norm_title)
                match_found_and_confirmed = True
                break # Confirmed by user
            
        if not match_found_and_confirmed:
            # If loop finishes without a confirmed match (either auto or manual)
            unmatched_titles_list.append(original_new_title)
            
    # Main logic for process_and_match_new_hymn_titles
    
    # 1. Get existing normalized titles from DB
    db_master_normalized_list, db_master_normalized_set = get_existing_normalized_titles_from_db()
    
    # 2. Identify new titles to process (original and normalized forms)
    original_new_titles_list, normalized_new_titles_list = identify_new_titles_to_process(db_master_normalized_set)

    # 3. If no new titles, nothing more to do
    if not original_new_titles_list or not normalized_new_titles_list:
        return None # Or an empty list: []
    
    # 4. Calculate similarity matrix for new titles against existing DB titles
    similarity_matrix = calculate_similarity_matrix(normalized_new_titles_list, db_master_normalized_list)

    unmatched_original_titles: List[str] = []
    # 5. For each new title, find its best matches and attempt to update DB
    for i, new_title_norm in enumerate(normalized_new_titles_list):
        original_form_of_new_title = original_new_titles_list[i]
        # Get the similarity scores for the current new title against all DB titles
        similarity_scores_for_current_new_title = similarity_matrix[i]
        
        top_matches = find_top_n_matches_from_matrix(similarity_scores_for_current_new_title, db_master_normalized_list)
        
        if not top_matches: # No matches found above the cutoff score
            unmatched_original_titles.append(original_form_of_new_title)
            continue

        attempt_database_update_for_new_title(
            top_matches, 
            original_form_of_new_title, 
            new_title_norm, 
            unmatched_original_titles
        )
    
    return unmatched_original_titles if unmatched_original_titles else None


def main():
    # Example usage (requires setup with DataFrames and a populated database)
    # df1 = pd.DataFrame({'colA': [1,2], 'colB': ["Gloria a Dios", "Oh Ven Emanuel"]})
    # df2 = pd.DataFrame({'colA': [3,4], 'colB': ["A Dios Sea La Gloria", "Nuevo Himno Inventado"]})
    # sample_data_frames = [df1, df2]
    
    # print("Starting title matching process...")
    # unmatched = process_and_match_new_hymn_titles(sample_data_frames)
    # if unmatched:
    #     print("\nTitles that could not be matched:")
    #     for title in unmatched:
    #         print(f"- {title}")
    # else:
    #     print("\nAll new titles were processed or no new titles found.")
    pass

if __name__ == "__main__":
    main()
