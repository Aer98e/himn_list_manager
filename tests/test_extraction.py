import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
import os # For path joining if needed for helper data
import sys

# Assuming the script is run from the project root or tests/ directory
# This adds the project root to the Python path to resolve `from data_processing.extraction import ...`
if os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) not in sys.path:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_processing.extraction import extract_data_frames, extract_table_titles, capture_format_change_indices, find_pattern_indices, clear_cells_with_pattern
from utils.helpers import normalize_text # Needed for some tests if not mocking it

class TestExtractDataFrames(unittest.TestCase):

    @patch('data_processing.extraction.pd.read_excel')
    def test_extract_one_valid_block(self, mock_read_excel):
        # Mock DataFrame representing Excel data
        data = {
            0: ['Some info', 'R', 'Hymn1', 'Hymn2', 'Hymn3', None, 'R', 'Hymn4', 'Hymn5'],
            1: ['Date1', 'Data', 'Data', 'Data', 'Data', None, 'Date2', 'Data', 'Data'],
            2: ['Details', 'More', 'More', 'More', 'More', None, 'Details2', 'More', 'More'],
            3: ['ColOffset0', 'ColOffset1', 'ColOffset2', 'ColOffset3', 'ColOffset4', None, 'ColOffset0_2', 'ColOffset1_2', 'ColOffset2_2']
        }
        mock_df = pd.DataFrame(data)
        mock_read_excel.return_value = mock_df

        # Parameters for extract_data_frames
        # identifier 'R', review_offset 1 (relative to 'R's col, so col+1), column_slice (0 relative to 'R's col, 3 relative to 'R's col)
        # This means if 'R' is at (r,c), we check (r+i, c+1) for continuation
        # and extract columns [c+0, c+1, c+2]
        
        # If R is at (1,0), continuation check is on column 1 (0-indexed)
        # Slice will be from col 0 to col 2 (exclusive end)
        # Expected data from first block:
        #   R     Date1   Details
        #   Hymn1 Data    More
        #   Hymn2 Data    More
        #   Hymn3 Data    More
        # (Assuming identifier 'R' is in column 0, review_offset is 1, column_slice is (0,3) relative to R's column)
        # Let's adjust the slice and data to be clearer:
        # Identifier 'R', review_offset=0 (check R's own column for continuation, which is unusual, let's assume review_offset is for a *different* column)
        # Let's assume identifier='ID', review_offset is for a 'Data' column, and slice is for 'ID', 'Data', 'Details'
        
        # New scenario:
        # Identifier is in column 0. Review for continuation is in column 1. Slice is columns 0, 1, 2.
        # 'R' at (1,0). review_offset = 1 (col index 1). column_slice = (0,3) (relative to col of 'R')
        
        mock_data_scenario1 = {
            0: ['Header', 'R', 'Content1A', 'Content2A', 'Content3A', None, 'R', 'Content1B'], # Column for 'R'
            1: ['Date Header', 'Date A', 'D1', 'D2', 'D3', None, 'Date B', 'D1B'], # Column for review_offset & part of slice
            2: ['Detail Header', 'Detail A', 'Detail1', 'Detail2', 'Detail3', None, 'Detail B', 'Detail1B'], # Part of slice
            3: ['Extra', 'ExtraA', 'E1', 'E2', 'E3', None, 'ExtraB', 'E1B'] # Not in slice
        }
        mock_df_scenario1 = pd.DataFrame(mock_data_scenario1)
        mock_read_excel.return_value = mock_df_scenario1
        
        result_frames = extract_data_frames('dummy_path.xlsx', 'R', review_offset=1, column_slice=(0, 3))
        
        self.assertEqual(len(result_frames), 2) # Expecting two blocks
        
        # Check first block
        # R is at (1,0). Data starts from row 1. Ends before row 5 (None). Rows 1,2,3,4.
        # Columns extracted: 0, 1, 2
        expected_block1_data = {
            0: ['R', 'Content1A', 'Content2A', 'Content3A'],
            1: ['Date A', 'D1', 'D2', 'D3'],
            2: ['Detail A', 'Detail1', 'Detail2', 'Detail3']
        }
        expected_df1 = pd.DataFrame(expected_block1_data)
        pd.testing.assert_frame_equal(result_frames[0], expected_df1, check_dtype=False)

        # Check second block
        # R is at (6,0). Data starts from row 6. Ends before row 8 (implicit end of DF). Rows 6,7.
        # This block is 2 rows long, so it should be skipped by "if data_frame.shape[0] > 2"
        # Let's adjust data for the second block to be > 2 rows
        mock_data_scenario1_adjusted = {
            0: ['Header', 'R', 'C1A', 'C2A', 'C3A', None, 'R', 'C1B', 'C2B', 'C3B'], 
            1: ['Date Header', 'DA', 'D1A', 'D2A', 'D3A', None, 'DB', 'D1B', 'D2B', 'D3B'], 
            2: ['Detail Header', 'DetailA', 'Dt1A', 'Dt2A', 'Dt3A', None, 'DetailB', 'Dt1B', 'Dt2B', 'Dt3B'], 
            3: ['Extra', 'EA', 'E1A', 'E2A', 'E3A', None, 'EB', 'E1B', 'E2B', 'E3B'] 
        }
        mock_df_scenario1_adjusted = pd.DataFrame(mock_data_scenario1_adjusted)
        mock_read_excel.return_value = mock_df_scenario1_adjusted
        result_frames_adjusted = extract_data_frames('dummy_path.xlsx', 'R', review_offset=1, column_slice=(0, 3))
        
        self.assertEqual(len(result_frames_adjusted), 2)
        expected_block2_data = {
            0: ['R', 'C1B', 'C2B', 'C3B'],
            1: ['DB', 'D1B', 'D2B', 'D3B'],
            2: ['DetailB', 'Dt1B', 'Dt2B', 'Dt3B']
        }
        expected_df2 = pd.DataFrame(expected_block2_data)
        pd.testing.assert_frame_equal(result_frames_adjusted[1], expected_df2, check_dtype=False)


    @patch('data_processing.extraction.pd.read_excel')
    def test_no_identifier_found(self, mock_read_excel):
        mock_data = {0: ['A', 'B'], 1: ['C', 'D']}
        mock_df = pd.DataFrame(mock_data)
        mock_read_excel.return_value = mock_df
        
        result_frames = extract_data_frames('dummy.xlsx', 'NON_EXISTENT_ID', 0, (0,1))
        self.assertEqual(len(result_frames), 0)

    @patch('data_processing.extraction.pd.read_excel')
    def test_block_too_short(self, mock_read_excel):
        # Block is only 2 rows ('R' and 'Content1'), should be skipped.
        mock_data = {
            0: ['R', 'Content1'],
            1: ['DateInfo', 'D1']
        }
        mock_df = pd.DataFrame(mock_data)
        mock_read_excel.return_value = mock_df
        result_frames = extract_data_frames('dummy.xlsx', 'R', review_offset=1, column_slice=(0,2))
        self.assertEqual(len(result_frames), 0)

    @patch('data_processing.extraction.pd.read_excel')
    def test_empty_file_df(self, mock_read_excel):
        mock_df = pd.DataFrame()
        mock_read_excel.return_value = mock_df
        result_frames = extract_data_frames('dummy.xlsx', 'R', 0, (0,1))
        self.assertEqual(len(result_frames), 0)

    @patch('data_processing.extraction.pd.read_excel', side_effect=FileNotFoundError("Mocked FileNotFoundError"))
    def test_file_not_found_error(self, mock_read_excel):
        # The function itself catches FileNotFoundError and returns []
        result_frames = extract_data_frames('non_existent.xlsx', 'R', 0, (0,1))
        self.assertEqual(len(result_frames), 0)
        # We could also check logger output here if logger was passed or accessible

    @patch('data_processing.extraction.pd.read_excel', side_effect=Exception("Mocked general Excel error"))
    def test_general_excel_read_error(self, mock_read_excel):
        # The function catches general Exception during read_excel and returns []
        result_frames = extract_data_frames('corrupted.xlsx', 'R', 0, (0,1))
        self.assertEqual(len(result_frames), 0)

# More tests could be added for:
# - Identifier at various positions (edges of DataFrame)
# - review_offset leading to out-of-bounds (though current code structure might prevent error, just no block)
# - column_slice leading to out-of-bounds for some rows in a block (numpy slicing handles this gracefully)
# - Different data types in continuation column or identifier column

class TestExtractTableTitles(unittest.TestCase):
    def setUp(self):
        # Sample DataFrame to be used in tests
        self.sample_data = {
            0: ['Date Info', 'Hymn Title 1', 'Hymn Title 2', '  Another Hymn  '],
            1: ['2023-01-01', 'Original Title 1', 'Original Title 2', '  Original Spaced  ']
        }
        self.test_df = pd.DataFrame(self.sample_data)

        # Expected normalized titles (assuming normalize_text works as tested in test_helpers)
        self.normalized_hymn1 = normalize_text('Hymn Title 1')
        self.normalized_hymn2 = normalize_text('Hymn Title 2')
        self.normalized_spaced_hymn = normalize_text('  Another Hymn  ')
        self.normalized_original1 = normalize_text('Original Title 1')
        self.normalized_original2 = normalize_text('Original Title 2')
        self.normalized_spaced_original = normalize_text('  Original Spaced  ')


    def test_extract_titles_no_normalization_no_date(self):
        titles = extract_table_titles(self.test_df, column_index=0, normalize=False, include_date=False)
        self.assertEqual(titles, ['Hymn Title 1', 'Hymn Title 2', '  Another Hymn  '])

    def test_extract_titles_with_normalization_no_date(self):
        titles = extract_table_titles(self.test_df, column_index=0, normalize=True, include_date=False)
        self.assertEqual(titles, [self.normalized_hymn1, self.normalized_hymn2, self.normalized_spaced_hymn])

    def test_extract_titles_no_normalization_with_date(self):
        titles = extract_table_titles(self.test_df, column_index=0, normalize=False, include_date=True)
        self.assertEqual(titles, ['Date Info', 'Hymn Title 1', 'Hymn Title 2', '  Another Hymn  '])

    def test_extract_titles_with_normalization_with_date(self):
        # Date (first element) should remain un-normalized
        titles = extract_table_titles(self.test_df, column_index=0, normalize=True, include_date=True)
        self.assertEqual(titles, ['Date Info', self.normalized_hymn1, self.normalized_hymn2, self.normalized_spaced_hymn])

    def test_empty_dataframe(self):
        empty_df = pd.DataFrame()
        titles = extract_table_titles(empty_df, column_index=0)
        self.assertEqual(titles, [])

    def test_column_index_out_of_bounds(self):
        with self.assertRaises((IndexError, KeyError)): # Pandas can raise either depending on version/structure
             extract_table_titles(self.test_df, column_index=5)
    
    def test_dataframe_with_fewer_rows_than_start_row(self):
        # Create a DataFrame with only one row
        one_row_df = pd.DataFrame({0: ['Date Info Only']})
        # include_date=False means start_row=1. This DF has only row 0.
        titles = extract_table_titles(one_row_df, column_index=0, normalize=False, include_date=False)
        self.assertEqual(titles, [])
        
        # include_date=True means start_row=0
        titles_with_date = extract_table_titles(one_row_df, column_index=0, normalize=False, include_date=True)
        self.assertEqual(titles_with_date, ['Date Info Only'])


class TestPatternFunctions(unittest.TestCase):
    def test_find_pattern_indices(self):
        data = np.array([
            ['abc', 'def::R', 'ghi'],
            ['jkl::V', 'mno', 'pqr::R::N']
        ], dtype=str)
        
        indices_R = find_pattern_indices(data, '::R')
        self.assertTrue(np.array_equal(indices_R, np.array([[0,1],[1,2]])))
        
        indices_V = find_pattern_indices(data, '::V')
        self.assertTrue(np.array_equal(indices_V, np.array([[1,0]])))

        indices_N = find_pattern_indices(data, '::N')
        self.assertTrue(np.array_equal(indices_N, np.array([[1,2]])))

        indices_NotFound = find_pattern_indices(data, '::X')
        self.assertEqual(indices_NotFound.shape[0], 0) # Should be an empty array

    def test_clear_cells_with_pattern(self):
        data = {
            0: ['abc', 'jkl::V'],
            1: ['def::R', 'mno'],
            2: ['ghi', 'pqr::R::N']
        }
        df = pd.DataFrame(data)
        
        # Clear '::R'
        indices_R = np.array([[0,1],[1,2]]) # Note: DataFrame indices for this data would be (row, col) -> (1,0), (2,1) if using df.iat
                                          # But find_pattern_indices works on numpy, so it returns 0-based indices.
                                          # clear_cells_with_pattern uses df.iat, so indices must match df structure.
        # Let's re-create df to match typical find_pattern_indices output
        df_for_clear = pd.DataFrame([
            ['abc', 'def::R', 'ghi'],
            ['jkl::V', 'mno', 'pqr::R::N']
        ])
        
        indices_R_found = find_pattern_indices(df_for_clear.to_numpy(dtype=str), '::R') # [[0,1], [1,2]]
        clear_cells_with_pattern(df_for_clear, indices_R_found, '::R')
        self.assertEqual(df_for_clear.iat[0,1], 'def')
        self.assertEqual(df_for_clear.iat[1,2], 'pqr::N') # Only '::R' is removed

        # Clear '::V'
        indices_V_found = find_pattern_indices(df_for_clear.to_numpy(dtype=str), '::V') # [[1,0]]
        clear_cells_with_pattern(df_for_clear, indices_V_found, '::V')
        self.assertEqual(df_for_clear.iat[1,0], 'jkl')

class TestCaptureFormatChangeIndices(unittest.TestCase):
    def setUp(self):
        self.sample_df_data = {
            'A': ['Title', 'Hymn1::N', 'Hymn2', 'Hymn3::U'],
            'B': ['Date::D', '101::R', '102', '103::V'],
            'C': ['Info', 'OldNum1', 'OldNum2::N', 'OldNum3'], # Test '::N' not in typical hymn name col
            'D': ['Misc', 'X', 'Y::U', 'Z'] # Test '::U' not in typical hymn name col
        }
        self.df = pd.DataFrame(self.sample_df_data)
        self.original_df_copy = self.df.copy() # To check modification

    def test_capture_indices_and_clearing(self):
        # Expected indices before adjustments (based on 0-indexed numpy array from df)
        # 'new': (1,0), (2,2) -> from Hymn1::N, OldNum2::N
        # 'transpose': (3,0), (2,3) -> from Hymn3::U, Y::U
        # 'red': (1,1) -> from 101::R
        # 'green': (3,1) -> from 103::V
        # 'sunday': (0,1) -> from Date::D
        # 'other_day': none
        
        idx_map = capture_format_change_indices(self.df)

        # Verify 'new' indices (vstack doubles them and shifts second part by [0,-2])
        # Original 'new' indices: [[1,0], [2,2]]
        # After vstack and shift:
        #   [[1,0], [2,2],  <- original
        #    [1,-2], [2,0]] <- original + [0,-2]
        expected_new_indices = np.array([[1,0],[2,2],[1,-2],[2,0]])
        self.assertTrue(np.array_equal(np.sort(idx_map['new'], axis=0), np.sort(expected_new_indices, axis=0)))
        
        # Verify 'transpose' indices (original_col_idx - 3)
        # Original 'transpose': [[3,0], [2,3]] -> expected [[3, 0-3], [2, 3-3]] -> [[3,-3], [2,0]]
        expected_transpose_indices = np.array([[3,-3],[2,0]]) 
        self.assertTrue(np.array_equal(np.sort(idx_map['transpose'],axis=0), np.sort(expected_transpose_indices,axis=0)))

        expected_red_indices = np.array([[1,1]])
        self.assertTrue(np.array_equal(idx_map['red'], expected_red_indices))
        
        expected_green_indices = np.array([[3,1]])
        self.assertTrue(np.array_equal(idx_map['green'], expected_green_indices))

        expected_sunday_indices = np.array([[0,1]])
        self.assertTrue(np.array_equal(idx_map['sunday'], expected_sunday_indices))

        self.assertNotIn('other_day', idx_map or {}) # or check if it's empty array if key always exists

        # Verify patterns are cleared from the DataFrame
        self.assertEqual(self.df.iat[1,0], 'Hymn1')
        self.assertEqual(self.df.iat[2,2], 'OldNum2')
        self.assertEqual(self.df.iat[3,0], 'Hymn3')
        self.assertEqual(self.df.iat[2,3], 'Y')
        self.assertEqual(self.df.iat[1,1], '101')
        self.assertEqual(self.df.iat[3,1], '103')
        self.assertEqual(self.df.iat[0,1], 'Date')

    def test_no_patterns_found(self):
        df_no_patterns = pd.DataFrame({'A': ['Clean1', 'Clean2'], 'B': ['Data1', 'Data2']})
        original_copy = df_no_patterns.copy()
        idx_map = capture_format_change_indices(df_no_patterns)
        
        self.assertTrue(all(arr.size == 0 for arr in idx_map.values() if isinstance(arr, np.ndarray)))
        pd.testing.assert_frame_equal(df_no_patterns, original_copy) # DF should be unchanged


if __name__ == '__main__':
    unittest.main()
