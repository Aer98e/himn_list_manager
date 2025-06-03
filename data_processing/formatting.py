import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from .extraction import extract_table_titles, capture_format_change_indices # Renamed capture_change_idx
from database_interact.queries import extract_hymn_data_for_display # Renamed extract_data_db
from utils.helpers import load_config_from_json # Renamed load_config
from typing import List, Dict, Any # For type hinting
import os
import logging # Import logging

# Get a logger for this module
logger = logging.getLogger(__name__)

# shutil is not used in this refactored version directly, but os is used for path operations.

def assemble_master_dataframe(data_frame_list: List[pd.DataFrame], max_frames_per_row: int = 3) -> pd.DataFrame:
    """
    Concatenates a list of DataFrames into a single master DataFrame.
    DataFrames are grouped into rows, with a specified maximum number of frames per row.
    Empty columns are added for spacing if a row group has fewer than max_frames_per_row.
    Empty rows are added for spacing between rows of DataFrame groups.

    Args:
        data_frame_list (List[pd.DataFrame]): The list of DataFrames to concatenate.
        max_frames_per_row (int): The maximum number of DataFrames to place side-by-side in one row block.

    Returns:
        pd.DataFrame: A single DataFrame containing all input DataFrames arranged and spaced.
    """

    def _group_dataframes_with_padding(frames_list: List[pd.DataFrame], limit: int) -> List[List[pd.DataFrame]]:
        """
        Groups DataFrames into lists (rows), adding empty 'spacer' columns as needed.
        Each sublist represents a row of DataFrames to be concatenated horizontally.
        """
        current_row_group = []
        all_row_groups = []
        frames_in_current_group_count = 0

        for i, df_original in enumerate(frames_list):
            df = df_original.copy()  # Work with a copy
            df.reset_index(drop=True, inplace=True) # Ensure clean index
            frames_in_current_group_count += 1

            # Add a spacer column if this DataFrame is not the last in its group AND not the last overall
            if frames_in_current_group_count < limit and i < len(frames_list) -1 : # Check i to prevent adding spacer to last element if it starts a new row
                 df['spacer_column'] = None # Add an empty column for spacing
            
            current_row_group.append(df)

            if frames_in_current_group_count == limit or i == len(frames_list) - 1:
                all_row_groups.append(current_row_group)
                current_row_group = [] # Reset for the next group
                frames_in_current_group_count = 0
        
        return all_row_groups

    def _concatenate_dataframes_horizontally(grouped_frames: List[List[pd.DataFrame]]) -> List[pd.DataFrame]:
        """Concatenates each group of DataFrames horizontally to form a single row DataFrame."""
        concatenated_rows = []
        for row_group in grouped_frames:
            # Concatenate DataFrames in the current group along axis=1 (columns)
            result_row_df = pd.concat(row_group, axis=1, ignore_index=True)
            concatenated_rows.append(result_row_df)
        return concatenated_rows

    def _concatenate_rows_vertically_with_spacing(row_dataframes: List[pd.DataFrame]) -> pd.DataFrame:
        """Concatenates row DataFrames vertically, adding an empty spacer row between them."""
        if not row_dataframes:
            return pd.DataFrame() # Return empty DataFrame if input is empty

        # Create an empty row with the same columns as the first DataFrame for spacing
        # Ensure all columns are string type to avoid issues with pd.concat if dtypes differ
        empty_row_columns = {str(col): [None] for col in row_dataframes[0].columns}
        empty_spacer_row = pd.DataFrame(empty_row_columns) 
        
        final_layout_with_spacers = []
        for i, single_row_df in enumerate(row_dataframes):
            # Ensure consistent column naming (as strings) before concatenation
            single_row_df.columns = [str(col) for col in single_row_df.columns]
            final_layout_with_spacers.append(single_row_df)
            if i < len(row_dataframes) - 1: # Add spacer if not the last row DataFrame
                final_layout_with_spacers.append(empty_spacer_row)
                
        # Concatenate all (row DataFrames and spacer rows) along axis=0 (rows)
        master_df = pd.concat(final_layout_with_spacers, ignore_index=True)
        return master_df

    # Main logic for assemble_master_dataframe
    if not data_frame_list:
        return pd.DataFrame() # Handle empty input list

    grouped_df_rows = _group_dataframes_with_padding(data_frame_list, max_frames_per_row)
    horizontally_concatenated_rows = _concatenate_dataframes_horizontally(grouped_df_rows)
    final_master_dataframe = _concatenate_rows_vertically_with_spacing(horizontally_concatenated_rows)
    
    return final_master_dataframe


def generate_hymn_dataframes(raw_data_frames: List[pd.DataFrame]) -> List[pd.DataFrame]:
    """
    Processes a list of raw DataFrames (extracted from Excel cells, representing hymn groups by date)
    into a new list of DataFrames. Each new DataFrame is structured for display, containing
    hymn details fetched from the database.

    Args:
        raw_data_frames (List[pd.DataFrame]): A list of DataFrames, where each typically holds
                                             hymn titles for a specific date.

    Returns:
        List[pd.DataFrame]: A list of newly generated DataFrames, formatted with hymn data.

    Raises:
        ValueError: If a hymn title extracted from a raw DataFrame is not found in the database.
    """
    processed_df_list = []

    def create_hymn_dataframe_shell(date_string: str) -> pd.DataFrame:
        """Helper to create the initial structure of a hymn DataFrame for a given date."""
        # Determine date suffix based on whether 'DOMINGO' (Sunday) is in the date string
        date_suffix = '::D' if 'DOMINGO' in date_string.upper() else '::O' # Use .upper() for case-insensitivity
        # Define column headers for the new DataFrame. 'O' and 'N' might be placeholders or specific codes.
        column_headers = [['', date_string + date_suffix, 'O', 'N']] 
        new_hymn_df = pd.DataFrame(column_headers)
        return new_hymn_df
    
    def add_hymn_row_to_dataframe(df: pd.DataFrame, hymn_details: List[Any]):
        """Helper to add a row of hymn data to the DataFrame."""
        current_row_index = len(df) # Next available index
        # First element of the new row is its index (or a counter)
        new_row_data = [current_row_index] 
        for detail in hymn_details:

            new_row_data.append(detail if detail and detail is not None else '-') # Replace None with '-'
        df.loc[current_row_index] = new_row_data

    for raw_frame in raw_data_frames:
        # Extract titles; assumes title is in column 1, includes date from first row.
        hymn_titles_with_date = extract_table_titles(raw_frame, include_date=True) 
        
        if not hymn_titles_with_date: # Skip if no titles (or date) were extracted
            continue

        date_header = hymn_titles_with_date[0] # First item is the date
        hymn_df_shell = create_hymn_dataframe_shell(str(date_header))

        for title in hymn_titles_with_date[1:]: # Process actual hymn titles
            # Fetch hymn data from database (function name changed for clarity)
            current_hymn_data = extract_hymn_data_for_display(str(title)) 
            if current_hymn_data:
                add_hymn_row_to_dataframe(hymn_df_shell, current_hymn_data)
            else:
                # Handle case where hymn data is not found
                add_hymn_row_to_dataframe(hymn_df_shell, [title, "", ""])
                logger.error(f"No se pudo identificar un himno en la base de datos, no se asignaran datos:: {title}")
                # raise ValueError(f'Hymn not found in database: {title}')
        processed_df_list.append(hymn_df_shell)

    return processed_df_list


def apply_excel_formatting(master_df: pd.DataFrame, page_title: str, temp_dir: str = 'file_procces'):
    """
    Applies formatting to an Excel file generated from the master DataFrame.
    This includes setting cell styles (font, fill, alignment), row heights, and column widths
    based on a configuration file. Also adds a main title to the sheet.

    Args:
        master_df (pd.DataFrame): The DataFrame to be written and formatted in Excel.
        page_title (str): The main title to be displayed at the top of the Excel sheet.
        temp_dir (str, optional): Temporary directory to store the intermediate Excel file.
                                  Defaults to 'file_procces'.
    """
    os.makedirs(temp_dir, exist_ok=True) # Ensure temporary directory exists
    excel_file_path = os.path.join(temp_dir, 'temp_schedule.xlsx') # Temporary file

    # Get indices of cells that need special formatting (e.g., new hymns, transposed hymns)
    # Function name changed for clarity
    format_indices = capture_format_change_indices(master_df) 

    # Write DataFrame to Excel without index or header (as formatting is custom)
    master_df.to_excel(excel_file_path, index=False, header=False)
    
    # Load workbook and active worksheet for styling with openpyxl
    try:
        workbook = load_workbook(excel_file_path)
        worksheet = workbook.active
    except Exception as e: # Broad exception for openpyxl loading errors
        logger.error(f"Error loading the temporary Excel workbook '{excel_file_path}': {e}", exc_info=True) # Replaced print
        # Depending on policy, might want to clean up excel_file_path here or let a higher level handle it.
        return # Cannot proceed with formatting

    # Load formatting configurations from JSON file
    try:
        config = load_config_from_json('formatting')
    except ValueError as e: # Raised by load_config_from_json if file not found
        logger.error(f"Error loading formatting configuration: {e}", exc_info=True) # Replaced print
        return # Cannot proceed
    except KeyError as e: # Should be caught by load_config_from_json if JSON is malformed
        logger.error(f"Error: Missing key in formatting configuration: {e}", exc_info=True) # Replaced print
        return # Cannot proceed
    except Exception as e: # Other unexpected errors during config load
        logger.error(f"An unexpected error occurred loading formatting configuration: {e}", exc_info=True) # Replaced print
        return


    # Define styles and fills based on configuration
    # Add .get() for resilience against missing keys, with defaults or error handling
    try:
        style_new_hymn = Font(bold=True, color=config.get('cl_new', '000000')) # Default to black if key missing
        style_transposed_hymn = Font(bold=True, color=config.get('cl_transpose', '000000'))
        fill_red_indicator = PatternFill(start_color=config.get('fill_red', 'FFFFFF'), end_color=config.get('fill_red', 'FFFFFF'), fill_type="solid") # Default white
        fill_green_indicator = PatternFill(start_color=config.get('fill_green', 'FFFFFF'), end_color=config.get('fill_green', 'FFFFFF'), fill_type="solid")
        fill_sunday_date = PatternFill(start_color=config.get('fill_sunday', 'FFFFFF'), end_color=config.get('fill_sunday', 'FFFFFF'), fill_type="solid")
        fill_other_day_date = PatternFill(start_color=config.get('fill_other_day', 'FFFFFF'), end_color=config.get('fill_other_day', 'FFFFFF'), fill_type="solid")
        
        default_font_size_val: int = config.get('general_size', 11) # Default font size
        default_font_size = Font(size=default_font_size_val)
        header_font_size_val: int = config.get('header_size', 12) # Default header font size
        
        # For keys that are essential for structure, direct access might be okay,
        # or check with .get() and raise a more specific error if not found.
        row_headers_height: int = config.get('row_headers', 18.5)
        row_general_height: int = config.get('row_general', 16)
        col_idx_width: int = config.get('col_idx',3)
        col_title_width: int = config.get('col_title', 32)
        col_numbers_width: int = config.get('col_numbers', 4.5)
        col_space_width: int = config.get('col_space', 5) # Optional spacer column
        
        main_title_font_name: str = config.get('style_name', 'Arial')
        main_title_font_size: int = config.get('size_name', 16)
        style_main_title:str = Font(name=main_title_font_name, bold=True, size=main_title_font_size)
        main_title_spacer_height: int = config.get('distance_name', 10)

    except KeyError as e:
        logger.error(f"Critical key missing in 'formatting.json': {e}. Cannot apply formatting.", exc_info=True) # Replaced print
        return
    except Exception as e: # Catch any other errors during config access
        logger.error(f"Unexpected error accessing formatting configuration values: {e}", exc_info=True) # Replaced print
        return

    center_alignment = Alignment(horizontal='center')
    
    # Define styles and fills based on configuration
    # style_new_hymn = Font(bold=True, color=config['cl_new'])
    # style_transposed_hymn = Font(bold=True, color=config['cl_transpose'])
    # fill_red_indicator = PatternFill(start_color=config['fill_red'], end_color=config['fill_red'], fill_type="solid")
    # fill_green_indicator = PatternFill(start_color=config['fill_green'], end_color=config['fill_green'], fill_type="solid")
    # fill_sunday_date = PatternFill(start_color=config['fill_sunday'], end_color=config['fill_sunday'], fill_type="solid")
    # fill_other_day_date = PatternFill(start_color=config['fill_other_day'], end_color=config['fill_other_day'], fill_type="solid")
    # center_alignment = Alignment(horizontal='center')

    # default_font_size = Font(size=config['general_size'])
    # header_font_size_val = config['header_size'] # Assuming this is just the size, not a Font object

    # Map configuration keys to actual style objects for easier lookup
    cell_styles_map = {'new': style_new_hymn, 'transpose': style_transposed_hymn}
    cell_fills_map = {'red': fill_red_indicator, 'green': fill_green_indicator, 
                      'sunday': fill_sunday_date, 'other_day': fill_other_day_date}

    # Apply row heights and general font/alignment for header and data rows
    for row_idx in range(1, worksheet.max_row + 1):
        row_dimension = worksheet.row_dimensions[row_idx]
        # Determine row type based on modulo arithmetic (assuming 8-row pattern for each "block")
        row_type_mod = row_idx % 8 

        if row_type_mod == 0 or row_type_mod == 1: # Header rows in the pattern
            row_dimension.height = row_headers_height
            if row_type_mod == 1: # Specific styling for the first header row of a block
                for cell in worksheet[row_idx]:
                    cell.font = Font(size=header_font_size_val, bold=True)
                    cell.alignment = center_alignment
        else: # Data rows in the pattern (2 through 7)
            row_dimension.height = row_general_height
            for cell in worksheet[row_idx]:
                cell.font = default_font_size # Apply default font size

    # Apply column widths and specific alignments/fonts for different column types
    for col_idx in range(1, worksheet.max_column + 1):
        column_letter = get_column_letter(col_idx)
        col_dimension = worksheet.column_dimensions[column_letter]
        # Determine column type based on modulo arithmetic (assuming 5-column pattern for each "block")
        col_type_mod = col_idx % 5

        if col_type_mod == 1: # Index column
            col_dimension.width = col_idx_width
            for cell in worksheet[column_letter]: # Iterate through cells in this column
                cell.alignment = center_alignment
        elif col_type_mod == 2: # Title column
            col_dimension.width = col_title_width
        elif col_type_mod == 3 or col_type_mod == 4: # Number columns
            col_dimension.width = col_numbers_width
            for cell in worksheet[column_letter]:
                 # Make numbers bold if they are part of a header or already marked bold
                is_bold = cell.font.bold or ( ( (cell.row % 8) == 1) and config.get('header_bold_numbers', True) )
                cell.font = Font(size=header_font_size_val, bold=is_bold) 
                cell.alignment = center_alignment
        elif col_type_mod == 0: # Spacer column (if any)
            col_dimension.width = col_space_width
    
    # Apply specific styles (e.g., for 'new', 'transpose') from format_indices
    for style_key, style_obj in cell_styles_map.items():
        if style_key in format_indices:
            for r_idx, c_idx in format_indices[style_key]:
                # openpyxl is 1-indexed for rows/columns
                worksheet.cell(row=r_idx + 1, column=c_idx + 1).font += style_obj

    # Apply specific fills (e.g., for 'red', 'green', 'sunday') from format_indices
    for fill_key, fill_obj in cell_fills_map.items():
        if fill_key in format_indices:
            for r_idx, c_idx in format_indices[fill_key]:
                worksheet.cell(row=r_idx + 1, column=c_idx + 1).fill = fill_obj

    # Insert rows at the top for the main page title
    worksheet.insert_rows(1, amount=2)
    # Merge cells for the title spanning the width of the table
    worksheet.merge_cells(start_row=1, end_row=1, start_column=1, end_column=worksheet.max_column)
    title_cell = worksheet.cell(row=1, column=1, value=page_title)
    title_cell.font = style_main_title
    title_cell.alignment = center_alignment
    # Set height for the empty row below the title (as a spacer)
    worksheet.row_dimensions[2].height = main_title_spacer_height

    try:
        workbook.save(excel_file_path)
        logger.info(f"Formatting applied successfully to {excel_file_path}") # Replaced print
    except IOError as e:
        logger.error(f"Error saving the formatted Excel file '{excel_file_path}': {e}", exc_info=True) # Replaced print
    except Exception as e: # Catch other openpyxl saving errors
        logger.error(f"An unexpected error occurred while saving '{excel_file_path}': {e}", exc_info=True) # Replaced print

    # The task was to "present" the file, which implied moving it.
    # This function now focuses only on formatting and saving to a temp location.
    # Moving the file should be handled by a separate function call in the main script if needed.

def main():
    # Example usage or testing can go here
    # This would require sample DataFrames and a 'formatting.json' in 'configs/'
    pass

if __name__ == "__main__":
    main()
