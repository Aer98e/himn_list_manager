import pandas as pd
import numpy as np

def find_pattern_indices(numpy_matrix: np.ndarray, pattern: str) -> np.ndarray:
    """Finds indices where the pattern appears in a NumPy string matrix."""
    # np.char.find returns -1 if not found, >=0 if found.
    indices = np.argwhere(np.char.find(numpy_matrix.astype(str), pattern) >= 0)
    return indices

def clear_cells_with_pattern(df: pd.DataFrame, indices: np.ndarray, pattern: str):
    """Removes the pattern from the cells specified by the indices in the DataFrame."""
    for i, j in indices:
        if pd.notna(df.iat[i, j]) and isinstance(df.iat[i, j], str):
            df.iat[i, j] = df.iat[i, j].replace(pattern, "") # type: ignore

def capture_format_change_indices(master_df: pd.DataFrame) -> dict[str, np.ndarray]:
    """
    Identifies cells in a DataFrame that contain specific formatting patterns (e.g., ::R, ::V),
    removes these patterns from the cells, and returns a dictionary mapping pattern types
    to the indices where they were found.

    Args:
        master_df (pd.DataFrame): The DataFrame to process. This DataFrame is modified in place.

    Returns:
        dict[str, np.ndarray]: A dictionary where keys are pattern names (e.g., 'red', 'green')
                               and values are NumPy arrays of indices (row, col) where these
                               patterns were found. The indices for 'transpose' are adjusted,
                               and 'new' indices are duplicated for further processing.
    """
    def clear_dataframe_patterns(df: pd.DataFrame, pattern_indices_map: dict, patterns_map: dict):
        """Helper function to clear all specified patterns from the DataFrame."""
        for key, pattern_to_clear in patterns_map.items():
            if key in pattern_indices_map:
                clear_cells_with_pattern(df, pattern_indices_map[key], pattern_to_clear)

    # Define the patterns to search for
    patterns = {
        'red': '::R',
        'green': '::V',
        'new': '::N',
        'transpose': '::U', # Indicates a 'transposed' or 'moved' entry
        'sunday': '::D',    # Indicates a Sunday-specific entry
        'other_day': '::O'  # Indicates an entry for a day other than Sunday
    }
    
    # Work on a copy of the DataFrame's numpy representation for finding patterns
    numpy_matrix = master_df.astype(str).to_numpy() # Ensure string type for np.char.find

    pattern_indices = {}
    for key, pattern_str in patterns.items():
        pattern_indices[key] = find_pattern_indices(numpy_matrix, pattern_str)
    
    # Remove the patterns from the original DataFrame
    clear_dataframe_patterns(master_df, pattern_indices, patterns)

    # Special handling for 'transpose' pattern indices: adjust column index
    if 'transpose' in pattern_indices and pattern_indices['transpose'].size > 0:
        pattern_indices['transpose'][:, 1] -= 3 # Adjust column index, reason should be documented if known

    # Special handling for 'new' pattern indices: duplicate and shift for related cells
    if 'new' in pattern_indices and pattern_indices['new'].size > 0:
        # Assumes 'new' pattern relates to an adjacent cell (2 columns to the left)
        # This creates pairs of indices for each 'new' found: original and shifted
        union_new_indices = np.vstack((pattern_indices['new'], pattern_indices['new'] + [0, -2]))
        pattern_indices['new'] = union_new_indices

    return pattern_indices
