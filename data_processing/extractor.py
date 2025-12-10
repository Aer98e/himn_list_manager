import pandas as pd
import numpy as np
from utils.helpers import normalize_text # Changed from limpiar_texto1
from .constants import COLUMN_INDEX

# Get a logger for this module

def extract_data_frames(file_path: str, identifier: str,
                        review_offset: int, column_slice: tuple[int, int]):
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
       
    df = pd.read_excel(file_path, header=None)
        
    numpy_array = df.to_numpy()     # Para poder buscar con máscara.
    identifier_mask = numpy_array == identifier
    
    extracted_data_frames = []
    for row, col in np.argwhere(identifier_mask):  
        row_increment = 0
        while True:
            if row + row_increment >= numpy_array.shape[0]:
                break
            
            current_cell_value = numpy_array[row + row_increment, col + review_offset]
            
            if pd.isna(current_cell_value) or str(current_cell_value).strip() == '':
                break
            row_increment += 1  # Expand the row range downwards

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
    
    titles:list[str] = table_df.iloc[start_row:, column_index].to_list()
    
    if normalize:
        normalized_titles = list( map(normalize_text, titles) )
        if include_date and titles: # If a date is included, it should not be normalized
            normalized_titles[0] = titles[0] 
        return normalized_titles
    else:
        return titles

def main():
    # Example usage or testing can go here
    pass

if __name__ == "__main__":
    main()
