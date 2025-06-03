import pandas as pd
import numpy as np
from utils.helpers import normalize_text # Changed from limpiar_texto1
from .configs_constants import COLUMN_INDEX
import logging

# Get a logger for this module
logger = logging.getLogger(__name__)

def extract_data_frames(file_path: str, identifier: str, review_offset: int, column_slice: tuple[int, int]):
    """
    Extracts rectangular sections (data frames) from an Excel file based on a specific identifier.
    This function reads an Excel file into a NumPy array and identifies regions of interest
    starting with a specific identifier. It dynamically determines the size
    of each region and extracts it as a DataFrame.

    Args:
        file_path (str): The path to the Excel file to be processed.
        identifier (str): The identifier used to locate the starting points of the
            regions of interest (e.g., 'R').
        review_offset (int): Row offset from the identifier cell to check for content continuation.
                           For example, if identifier is at (row, col), it checks cell
                           (row + row_increment, col + review_offset).
        column_slice (tuple): A tuple (start_col_offset, end_col_offset) defining the column
                              range to extract relative to the identifier's column.
                              The end_col_offset is exclusive.
    Returns:
        list: A list of DataFrames, where each DataFrame represents a rectangular section
        extracted from the Excel file. Only sections with more than 2 rows are included.
        Returns an empty list if an error occurs during file reading or processing.
    Notes:
        - The function assumes that the identifier is located in a single cell and that the
          region of interest extends downward until an empty or NaN cell is encountered in the
          column specified by `review_offset`.
        - The function skips regions with 2 or fewer rows.
    """
    try:
        # Read the Excel file into a DataFrame
        df = pd.read_excel(file_path, header=None)
    except FileNotFoundError:
        logger.error(f"The file '{file_path}' was not found in extract_data_frames.") # Replaced print with logger
        return [] # Return empty list on error
    except Exception as e: # Catches other pandas/excel reading errors (e.g., xlrd.XLRDError, InvalidFileException)
        logger.error(f"Error reading Excel file '{file_path}': {e}", exc_info=True) # Replaced print, added exc_info for traceback
        return [] # Return empty list on error
        
    numpy_array = df.to_numpy()

    # Create a mask to detect the identifier. 
    # Assumes `identifier` is a simple string or number that can be directly compared.
    # `numpy_array` can contain mixed types; comparison behavior might vary if `identifier` is not string.
    # However, pd.read_excel by default tries to infer types, so text usually remains text.
    identifier_mask = numpy_array == identifier
    extracted_data_frames = []

    # Iterate through positions where the identifier is found
    for row, col in np.argwhere(identifier_mask):  # `np.argwhere` finds the positions of the identifier
        row_increment = 0  # Counter for rows included in the current data frame
        while True:
            # Check if we are within the row boundaries and if the cell is not empty
            if row + row_increment >= numpy_array.shape[0]:  # Avoid index out of range
                break
            # Cell to check for continuation based on review_offset.
            # This cell's content is critical for determining the vertical extent of the data block.
            # Expected to be a simple type (string, number, date) that becomes non-empty-string-like
            # or non-NaN to continue. If this cell contains complex objects or unexpected types
            # that don't evaluate cleanly with pd.isna or str().strip(), block detection might fail.
            current_cell_value = numpy_array[row + row_increment, col + review_offset]
            # If the cell is empty or NaN, stop expanding the current data frame
            if pd.isna(current_cell_value) or str(current_cell_value).strip() == '':
                break
            row_increment += 1  # Expand the row range downwards

        # Extract the data frame using the determined row span and specified column slice
        # The column slice is relative to the identifier's column.
        # Data types within this extracted `data_frame` are as inferred by pandas from Excel.
        # Subsequent processing of these DataFrames should be mindful of potentially mixed types.
        data_frame = numpy_array[row : row + row_increment, col + column_slice[0] : col + column_slice[1]]
        if data_frame.shape[0] > 2: # Only include data frames with more than 2 rows
            extracted_data_frames.append(pd.DataFrame(data_frame))  # Convert to DataFrame for easier processing

    return extracted_data_frames

def extract_table_titles(table_df: pd.DataFrame, normalize: bool = False, include_date: bool = False):
    """
    Extracts and optionally normalizes titles from a specified column in a DataFrame.

    Args:
        table_df (pd.DataFrame): The DataFrame containing the data.
        column_index (int): The index of the column from which to extract titles.
        normalize (bool, optional): If True, normalizes the extracted titles using
            `normalize_text`. Defaults to False.
        include_date (bool, optional): If True, includes the first row (assumed to be a date)
                                     in the returned list. Defaults to False.

    Returns:
        list: A list of titles. If `normalize` is True, the titles (except for the
              date if `include_date` is True and normalization is applied) are normalized.
    """
    # Determine the starting row index based on whether to include the date
    column_index = COLUMN_INDEX
    start_row = 0 if include_date else 1
    
    titles = table_df.iloc[start_row:, column_index].to_list()
    
    if normalize:
        normalized_titles = list(map(normalize_text, titles))
        if include_date and titles: # If a date is included, it should not be normalized
            normalized_titles[0] = titles[0] 
        return normalized_titles
    else:
        return titles

def find_pattern_indices(numpy_matrix: np.ndarray, pattern: str) -> np.ndarray:
    """Finds indices where the pattern appears in a NumPy string matrix."""
    # np.char.find returns -1 if not found, >=0 if found.
    indices = np.argwhere(np.char.find(numpy_matrix.astype(str), pattern) >= 0)
    return indices

def clear_cells_with_pattern(df: pd.DataFrame, indices: np.ndarray, pattern: str):
    """Removes the pattern from the cells specified by the indices in the DataFrame."""
    for i, j in indices:
        if pd.notna(df.iat[i, j]) and isinstance(df.iat[i, j], str):
            df.iat[i, j] = df.iat[i, j].replace(pattern, "")

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

def main():
    # Example usage or testing can go here
    pass

if __name__ == "__main__":
    main()
