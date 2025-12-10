from data_processing.extractor import extract_table_titles
from utils.helpers import normalize_text, affirmative_answers
from rapidfuzz import fuzz, process
from .queries import add_to_search_index, find_title_by_normalized_text, get_all_normalized_titles
import numpy as np
from typing import List, Set, Tuple, Optional, Dict
import pandas as pd

def extract_unique_original_titles_from_frames(data_frames: List[pd.DataFrame]) -> Set[str]:
    """Helper to extract all unique (non-normalized) hymn titles from the input DataFrames."""
    original_titles_set: Set[str] = set()
    for frame_df in data_frames:
        titles_in_frame = extract_table_titles(frame_df)
        original_titles_set.update(titles_in_frame)
    return original_titles_set

def get_existing_normalized_titles_from_db() -> Tuple[List[str], Set[str]]:
    """Helper to fetch all normalized titles from the database."""
    db_normalized_titles_list = get_all_normalized_titles()
    db_normalized_titles_set = set(db_normalized_titles_list)
    return list(db_normalized_titles_set), db_normalized_titles_set

def identify_new_titles_to_process(
    data_frames: List[pd.DataFrame],
    saved_normalized_set: Set[str]
) -> Tuple[Optional[List[str]], Optional[List[str]]]:
    """
    Normalizes extracted original titles and filters out those already in the database.
    Returns a list of original new titles and a list of their normalized versions.
    """
    all_original_titles: set[str] = extract_unique_original_titles_from_frames(data_frames)
    new_normalized_to_original_map: Dict[str, str] = {}
    for title in all_original_titles:
        normalized = normalize_text(title)
        if normalized not in saved_normalized_set:
            new_normalized_to_original_map[normalized] = title

    if not new_normalized_to_original_map:
        return None, None

    new_normalized_list = list(new_normalized_to_original_map.keys())
    original_titles_for_processing = [new_normalized_to_original_map[norm] for norm in new_normalized_list]
    return original_titles_for_processing, new_normalized_list

def calculate_similarity_matrix(
    new_normalized_titles: List[str],
    existing_normalized_titles: List[str]
) -> np.ndarray:
    """Generates a similarity matrix using fuzzy partial ratio matching.
        Recordemos que primer parametro son filas, y segundo columnas"""
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
    best_match_indices = np.argsort(similarity_matrix_row)[::-1][:top_n]
    top_matches = [
        (existing_normalized_titles[i], float(similarity_matrix_row[i]))
        for i in best_match_indices if similarity_matrix_row[i] > 0
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
    HIGH_CONFIDENCE_THRESHOLD = 85.0

    match_found_and_confirmed = False
    for matched_db_norm_title, match_score in top_matches_for_new_title:
        db_original_title_for_match = find_title_by_normalized_text(matched_db_norm_title)
        if db_original_title_for_match is None:
            continue

        if match_score >= HIGH_CONFIDENCE_THRESHOLD:
            add_to_search_index(normalized_new_title, matched_db_norm_title)
            match_found_and_confirmed = True
            break

        print('----------------------------------')
        print(f"Posible coincidencia para el nuevo himno: '{original_new_title}'")
        print(f"Con el himno existente: '{db_original_title_for_match}' (Normalizado: '{matched_db_norm_title}')")
        print(f"Puntuación de coincidencia: {match_score:.2f}")

        while True:
            user_confirmation = input(f"¿Son estos himnos el mismo? '{original_new_title}' Y '{db_original_title_for_match}' (s/n): ").strip().lower()
            if user_confirmation in affirmative_answers or user_confirmation == 'n':
                break
            print("Respuesta no válida. Por favor, ingrese 's' para sí o 'n' para no.")

        if user_confirmation in affirmative_answers:
            add_to_search_index(normalized_new_title, matched_db_norm_title)
            match_found_and_confirmed = True
            break

    if not match_found_and_confirmed:
        unmatched_titles_list.append(original_new_title)

def process_and_match_new_hymn_titles(data_frames: List[pd.DataFrame]) -> Optional[List[str]]:
    """
    Processes hymn titles from a list of DataFrames, identifies new/unrecognized titles
    by comparing against existing normalized titles in the database, and attempts to match
    them using fuzzy string matching. Updates the database search index for confirmed matches.
    """ 
    db_master_normalized_list, db_master_normalized_set = get_existing_normalized_titles_from_db()
    original_new_titles_list, normalized_new_titles_list = identify_new_titles_to_process(data_frames, db_master_normalized_set)

    if not original_new_titles_list or not normalized_new_titles_list:
        return None

    similarity_matrix = calculate_similarity_matrix(normalized_new_titles_list, db_master_normalized_list)

    unmatched_original_titles: List[str] = []
    for i, new_title_norm in enumerate(normalized_new_titles_list):
        original_form_of_new_title = original_new_titles_list[i]
        similarity_scores_for_current_new_title = similarity_matrix[i]
        top_matches = find_top_n_matches_from_matrix(similarity_scores_for_current_new_title, db_master_normalized_list)

        if not top_matches:
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
    pass

if __name__ == "__main__":
    main()
