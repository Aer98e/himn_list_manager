import re
import datetime
from typing import List, Optional, Any # For type hinting
import pandas as pd # For type hinting DataFrames
import logging
from .constants import COLUMN_INDEX

# Constants for accessing date elements in DataFrames
DATE_ROW_INDEX = 0
DATE_COLUMN_INDEX = 0

# Weekday names in Spanish, as used by the original get_text_day function.
# Consider localizing or making this configurable if supporting multiple languages.
WEEKDAY_NAMES_ES = ['LUNES', 'MARTES', 'MIÉRCOLES', 'JUEVES', 'VIERNES', 'SÁBADO', 'DOMINGO']

logger=logging.getLogger(__name__)

def generate_schedule_dates(data_frames: List[pd.DataFrame], month: Optional[int] = None, year: Optional[int] = None) -> List[Optional[tuple]]:    
    """
    Generates a list of tuples containing formatted date strings and ISO date strings 
    for scheduling based on day numbers extracted from a list of DataFrames. 
    It filters out past dates and adds 'M' (Morning) or 'T' (Afternoon) suffixes for same-day events.

    Args:
        data_frames (List[pd.DataFrame]): A list of DataFrames, where each DataFrame is expected
                                         to have a date cell at [DATE_ROW_INDEX, DATE_COLUMN_INDEX]
                                         from which the day number is extracted.
        month (Optional[int]): The month to use for constructing dates. Defaults to the current month.
        year (Optional[int]): The year to use for constructing dates. Defaults to the current year.

    Returns:
        List[Optional[tuple]]: A list of tuples (formatted_date_text, iso_date_str) 
                               e.g., ("LUNES 01 M", "2023-10-01") or None for dates that are in the past.
    """
    
    def extract_day_numbers_from_frames(frames: List[pd.DataFrame]) -> List[int]:
        """Helper function to extract day numbers from the date cell of each DataFrame."""
        day_numbers = []
        for frame in frames:
            # Access the cell expected to contain the date information
            date_cell_value = str(frame.iat[DATE_ROW_INDEX, DATE_COLUMN_INDEX])
            # Search for the first sequence of digits in the cell value
            match = re.search(r'\d+', date_cell_value)
            if match:
                day_numbers.append(int(match.group(0)))
            else:
                # Log or handle cases where day number cannot be extracted
                logger.error(f"Uno de los frames no contenia un numero, por defecto se usará 0. ({date_cell_value})")
                day_numbers.append(0)
                # Consider raising a ValueError or appending a placeholder if critical
        return day_numbers

    def format_date_text(date_obj: datetime.date) -> str:
        """Helper function to format a date object into 'WEEKDAY DD' string."""
        day_of_month = date_obj.day
        weekday_index = date_obj.weekday() # Monday is 0 and Sunday is 6
        return f'{WEEKDAY_NAMES_ES[weekday_index]} {day_of_month:02}'

    schedule_dates_data = [] # Stores (text, iso) tuples or None
    current_date = datetime.date.today()
    
    # Use provided month/year or default to current month/year
    effective_year = year if year is not None else current_date.year
    effective_month = month if month is not None else current_date.month

    extracted_day_numbers = extract_day_numbers_from_frames(data_frames)
    is_afternoon_slot = False # Flag to track if the next event is an afternoon slot for a duplicated day

    for i, day_num in enumerate(extracted_day_numbers):
        try:
            event_date = datetime.date(effective_year, effective_month, day_num)
        except ValueError as e:
            # Handle invalid dates (e.g., February 30th)
            logger.error(f"Invalid date created for day {day_num}, month {effective_month}, year {effective_year}: {e}")
            schedule_dates_data.append(None) # Or some other error indicator
            continue

        # Skip processing for dates in the past
        if event_date < current_date:
            schedule_dates_data.append(None)
            continue
        
        formatted_date_text = format_date_text(event_date)
        iso_date_str = event_date.isoformat()

        if is_afternoon_slot:
            formatted_date_text += ' T' # Append 'T' for Tarde (Afternoon)
            is_afternoon_slot = False # Reset flag
        # Check if the next day number is the same as the current one, indicating morning/afternoon slots
        elif (i < len(extracted_day_numbers) - 1) and (day_num == extracted_day_numbers[i+1]):  
            formatted_date_text += ' M' # Append 'M' for Mañana (Morning)
            is_afternoon_slot = True # Set flag for the next iteration
        
        schedule_dates_data.append((formatted_date_text, iso_date_str))
        
    return schedule_dates_data
    
def filter_data_frames_by_date(data_frames: List[pd.DataFrame], schedule_dates: List[Optional[tuple]]) -> List[pd.DataFrame]:
    """
    Filters a list of DataFrames based on a corresponding list of schedule dates.
    Only DataFrames whose schedule date is not None are kept. 
    The date cell in the kept DataFrames is updated with the new schedule date string.
    The ISO date is attached to the DataFrame metadata (d.attrs['iso_date']).

    Args:
        data_frames (List[pd.DataFrame]): The list of DataFrames to filter.
        schedule_dates (List[Optional[tuple]]): A list of generated schedule date tuples (text, iso).
                                              Must correspond index-wise to data_frames.

    Returns:
        List[pd.DataFrame]: A new list containing only the DataFrames for valid, future dates,
                            with their date cells updated and metadata attached.
    
    Note:
        It's crucial that `schedule_dates` is generated by a function like `generate_schedule_dates`
        and aligns with the `data_frames` list.
    """
    if len(data_frames) != len(schedule_dates):
        logger.critical("The length of data_frames and schedule_dates lists must be identical.")
        raise ValueError("The length of data_frames and schedule_dates lists must be identical.")

    filtered_data_frames = []
    for i, frame in enumerate(data_frames):
        if schedule_dates[i] is None: # Skip if the date was filtered out (e.g., past date)
            continue
        
        date_text, iso_date = schedule_dates[i]

        # Create a copy to avoid modifying the original DataFrame in the input list
        updated_frame = frame.copy()
        # Update the date cell with the new formatted schedule date string
        updated_frame.iat[DATE_ROW_INDEX, DATE_COLUMN_INDEX] = date_text
        # Attach ISO date to metadata
        updated_frame.attrs['iso_date'] = iso_date
        
        filtered_data_frames.append(updated_frame)
        
    return filtered_data_frames

def main():
    # Example Usage (assuming you have some sample DataFrames)
    # Sample DataFrames (replace with actual data loading or creation)
    # df1 = pd.DataFrame({0: ['Some data', 'Data'], 1: ['Día 25', 'More data']}) 
    # df2 = pd.DataFrame({0: ['Some data', 'Data'], 1: ['Día 25', 'More data']}) # Same day for M/T test
    # df3 = pd.DataFrame({0: ['Some data', 'Data'], 1: ['Día 1', 'Old data']}) # Past date (if current day > 1)
    # df4 = pd.DataFrame({0: ['Some data', 'Data'], 1: ['Día 28', 'Future data']})

    # sample_frames = [df1, df2, df3, df4]
    
    # current_month = datetime.date.today().month
    # current_year = datetime.date.today().year

    # generated_dates = generate_schedule_dates(sample_frames, month=current_month, year=current_year)
    # print("Generated Schedule Dates:", generated_dates)
    
    # filtered_frames = filter_data_frames_by_date(sample_frames, generated_dates)
    # print(f"\nNumber of original frames: {len(sample_frames)}")
    # print(f"Number of filtered frames: {len(filtered_frames)}")
    # for i, frame in enumerate(filtered_frames):
    #     print(f"\nFiltered Frame {i+1} (Date: {frame.iat[DATE_ROW_INDEX, DATE_COLUMN_INDEX]}):")
    #     print(frame)
    pass

if __name__ == "__main__":
    main()
