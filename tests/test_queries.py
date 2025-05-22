import unittest
from unittest.mock import patch, MagicMock, call
import sqlite3 # Important for asserting specific sqlite3 errors
import sys
import os

# Add project root to sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database_interact import queries # Main module to test
from database_interact.file_names import R_BUSQUEDA # Used by functions in queries.py

# Mock logger for all tests in this module to avoid console output during tests
# and to allow assertions on logger calls if needed.
# This will mock the logger obtained by logging.getLogger(__name__) in queries.py
@patch('database_interact.queries.logger', MagicMock())
class TestQueries(unittest.TestCase):
    
    # --- Test _execute_query indirectly via public functions ---
    # The _execute_query logic is tested by verifying:
    # 1. Correct parameters passed to cursor.execute.
    # 2. Correct fetchone/fetchall/commit calls.
    # 3. Handling of sqlite3.Error (e.g., returning None or raising specific errors).

    @patch('database_interact.queries.sqlite3.connect')
    @patch('database_interact.queries.R_BUSQUEDA') 
    def test_find_title_by_normalized_text_found(self, mock_r_busqueda, mock_connect):
        mock_r_busqueda.return_value = "test_db_path.db"
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("Amazing Grace",)
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        result = queries.find_title_by_normalized_text("amazinggrace")

        mock_r_busqueda.assert_called_once()
        mock_connect.assert_called_once_with("test_db_path.db")
        expected_sql = """
        SELECT H.titulo
        FROM Himnos H
        JOIN Indice_busqueda IB ON H.id = IB.id_himno
        WHERE IB.titulo_norm = ?
    """
        mock_cursor.execute.assert_called_once_with(unittest.mock.ANY, ("amazinggrace",))
        # To check SQL, normalize whitespace in both expected and actual
        self.assertEqual(' '.join(expected_sql.split()), ' '.join(mock_cursor.execute.call_args[0][0].split()))
        self.assertEqual(result, "Amazing Grace")

    @patch('database_interact.queries.sqlite3.connect')
    @patch('database_interact.queries.R_BUSQUEDA')
    def test_find_title_by_normalized_text_not_found(self, mock_r_busqueda, mock_connect):
        mock_r_busqueda.return_value = "test_db_path.db"
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None # Simulate not found
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        result = queries.find_title_by_normalized_text("nonexistent")
        
        mock_connect.assert_called_once_with("test_db_path.db")
        mock_cursor.execute.assert_called_once()
        self.assertIsNone(result)

    @patch('database_interact.queries.sqlite3.connect', side_effect=sqlite3.OperationalError("DB lock"))
    @patch('database_interact.queries.R_BUSQUEDA')
    def test_find_title_by_normalized_text_db_error(self, mock_r_busqueda, mock_connect):
        mock_r_busqueda.return_value = "test_db_path.db"
        # _execute_query should catch the error, log it, and return None
        result = queries.find_title_by_normalized_text("anytitle")
        self.assertIsNone(result)
        # Could also assert logger.error was called if logger is not fully mocked out.

    @patch('database_interact.queries.sqlite3.connect')
    @patch('database_interact.queries.R_BUSQUEDA')
    def test_find_titles_by_ids_single_int(self, mock_r_busqueda, mock_connect):
        mock_r_busqueda.return_value = "test_db_path.db"
        mock_cursor = MagicMock()
        # Simulate multiple calls to fetchone if _execute_query is called per ID
        mock_cursor.fetchone.side_effect = [("Title One",), ("Title Two",)] 
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        result = queries.find_titles_by_ids(1)
        self.assertEqual(result, ["Title One"])
        mock_cursor.execute.assert_called_once_with('SELECT titulo FROM Himnos WHERE id = ?', (1,))

    @patch('database_interact.queries.sqlite3.connect')
    @patch('database_interact.queries.R_BUSQUEDA')
    def test_find_titles_by_ids_list_of_ints(self, mock_r_busqueda, mock_connect):
        mock_r_busqueda.return_value = "test_db_path.db"
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [("Title One",), ("Title Two",)]
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        result = queries.find_titles_by_ids([1, 2])
        self.assertEqual(result, ["Title One", "Title Two"])
        self.assertEqual(mock_cursor.execute.call_count, 2)
        mock_cursor.execute.assert_any_call('SELECT titulo FROM Himnos WHERE id = ?', (1,))
        mock_cursor.execute.assert_any_call('SELECT titulo FROM Himnos WHERE id = ?', (2,))

    def test_find_titles_by_ids_invalid_input(self):
        with self.assertRaises(TypeError):
            queries.find_titles_by_ids("not_an_int_or_list")
        with self.assertRaises(TypeError):
            queries.find_titles_by_ids([1, "invalid", 3])
            
    @patch('database_interact.queries.sqlite3.connect')
    @patch('database_interact.queries.R_BUSQUEDA')
    def test_find_data_by_normalized_title_found_multiple_cols(self, mock_r_busqueda, mock_connect):
        mock_r_busqueda.return_value = "test_db_path.db"
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1, "Hymn Title", "Other Data")
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        result = queries.find_data_by_normalized_title("hymntitle", ["id", "titulo", "col3"])
        
        expected_sql_select_part = "SELECT H.id, H.titulo, H.col3" # Order matters for comparison
        # Normalize whitespace for comparison
        actual_sql_call = ' '.join(mock_cursor.execute.call_args[0][0].split())
        self.assertTrue(expected_sql_select_part in actual_sql_call)
        self.assertEqual(mock_cursor.execute.call_args[0][1], ("hymntitle",))
        self.assertEqual(result, (1, "Hymn Title", "Other Data"))

    @patch('database_interact.queries.sqlite3.connect')
    @patch('database_interact.queries.R_BUSQUEDA')
    def test_find_data_by_normalized_title_found_single_col(self, mock_r_busqueda, mock_connect):
        mock_r_busqueda.return_value = "test_db_path.db"
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("Hymn Title Only",) # Note tuple for single item
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        result = queries.find_data_by_normalized_title("hymntitle", ["titulo"])
        self.assertEqual(result, "Hymn Title Only")

    def test_find_data_by_normalized_title_invalid_input(self):
        with self.assertRaises(ValueError):
            queries.find_data_by_normalized_title("title", []) # Empty list for columns
        with self.assertRaises(ValueError):
            queries.find_data_by_normalized_title("title", "not_a_list")


    @patch('database_interact.queries.sqlite3.connect')
    @patch('database_interact.queries.R_BUSQUEDA')
    def test_add_to_search_index_existing_match_found(self, mock_r_busqueda, mock_connect):
        mock_r_busqueda.return_value = "test_db_path.db"
        mock_cursor = MagicMock()
        # First call to _execute_query (SELECT id_himno)
        mock_cursor.fetchone.return_value = (123,) # Existing hymn_id
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        queries.add_to_search_index("new_norm_title", "existing_norm_title")

        self.assertEqual(mock_cursor.execute.call_count, 2)
        # Check first call (SELECT)
        select_sql = 'SELECT id_himno FROM Indice_busqueda WHERE titulo_norm = ?'
        mock_cursor.execute.assert_any_call(select_sql, ("existing_norm_title",))
        # Check second call (INSERT)
        insert_sql = 'INSERT INTO Indice_busqueda (id_himno, titulo_norm) VALUES (?, ?)'
        mock_cursor.execute.assert_any_call(insert_sql, (123, "new_norm_title"))
        mock_connection.commit.assert_called_once() # Commit should be called for the insert

    @patch('database_interact.queries.sqlite3.connect')
    @patch('database_interact.queries.R_BUSQUEDA')
    def test_add_to_search_index_no_existing_match(self, mock_r_busqueda, mock_connect):
        mock_r_busqueda.return_value = "test_db_path.db"
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None # Simulate existing_normalized_title_match not found
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        queries.add_to_search_index("new_norm_title", "non_existent_norm_title")
        
        mock_cursor.execute.assert_called_once_with('SELECT id_himno FROM Indice_busqueda WHERE titulo_norm = ?', ("non_existent_norm_title",))
        mock_connection.commit.assert_not_called() # No insert, so no commit

    @patch('database_interact.queries.sqlite3.connect')
    @patch('database_interact.queries.R_BUSQUEDA')
    def test_get_column_values(self, mock_r_busqueda, mock_connect):
        mock_r_busqueda.return_value = "test_db_path.db"
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("Val1",), ("Val2",), ("Val3",)]
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        # Note: R_BUSQUEDA is passed as the callable db_name_func
        results = queries.get_column_values(R_BUSQUEDA, "MyTable", "MyColumn")

        mock_r_busqueda.assert_called_once() # Called by _execute_query via db_name_func
        mock_connect.assert_called_once_with("test_db_path.db")
        mock_cursor.execute.assert_called_once_with("SELECT MyColumn FROM MyTable", ())
        self.assertEqual(results, ["Val1", "Val2", "Val3"])

    @patch('database_interact.queries.sqlite3.connect')
    @patch('database_interact.queries.R_BUSQUEDA')
    def test_get_all_normalized_titles(self, mock_r_busqueda, mock_connect):
        mock_r_busqueda.return_value = "test_db_path.db"
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("norm_title1",), ("norm_title2",)]
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        results = queries.get_all_normalized_titles()
        
        mock_cursor.execute.assert_called_once_with('SELECT titulo_norm FROM Indice_busqueda', ())
        self.assertEqual(results, ["norm_title1", "norm_title2"])

    @patch('database_interact.queries.sqlite3.connect')
    @patch('database_interact.queries.R_BUSQUEDA')
    @patch('database_interact.queries.normalize_text') # Mock normalize_text to control its output
    def test_extract_hymn_data_for_display_found(self, mock_normalize_text, mock_r_busqueda, mock_connect):
        mock_normalize_text.return_value = "normalized_test_title"
        mock_r_busqueda.return_value = "test_db_path.db"
        
        mock_cursor = MagicMock()
        # Side effect for multiple execute calls in extract_hymn_data_for_display
        # 1. Get hymn_id
        # 2. Get hymn details
        mock_cursor.fetchone.side_effect = [
            (101,), # Result for id_query (hymn_id)
            ("Test Title", "UsageNum", "NewNum", True, True, 1) # Result for details_query (es_nuevo=True, sube_tono=True, id_himnario=1)
        ]
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        result = queries.extract_hymn_data_for_display("Test Title Input")

        mock_normalize_text.assert_called_once_with("Test Title Input")
        
        id_query_sql = 'SELECT id_himno FROM Indice_busqueda WHERE titulo_norm = ?'
        details_query_sql_part = "SELECT titulo, numH_uso, numH_nuevo, es_nuevo, sube_tono, id_himnario" # Check part of it
        
        self.assertEqual(mock_cursor.execute.call_count, 2)
        mock_cursor.execute.assert_any_call(id_query_sql, ("normalized_test_title",))
        # Check that the second execute call contains the details query part
        actual_details_sql_call = ' '.join(mock_cursor.execute.call_args_list[1][0][0].split())
        self.assertTrue(details_query_sql_part in actual_details_sql_call)
        self.assertEqual(mock_cursor.execute.call_args_list[1][0][1], (101,)) # Params for details query
        
        self.assertEqual(result, ["Test Title", "UsageNum::R", "NewNum::N::U"])

    @patch('database_interact.queries.sqlite3.connect')
    @patch('database_interact.queries.R_BUSQUEDA')
    def test_load_tracked_hymn_frequencies(self, mock_r_busqueda, mock_connect):
        mock_r_busqueda.return_value = "test_db_path.db"
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [(1, 5, 10), (2, -1, 3)]
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        results = queries.load_tracked_hymn_frequencies()
        
        expected_sql_part = "SELECT id_himno, frec_util, frec_real FROM Frecuencias WHERE seguimiento = 1"
        actual_sql_call = ' '.join(mock_cursor.execute.call_args[0][0].split())
        self.assertTrue(expected_sql_part.split() == actual_sql_call.split()) # Compare tokenized
        self.assertEqual(results, [(1, 5, 10), (2, -1, 3)])

    @patch('database_interact.queries.sqlite3.connect')
    @patch('database_interact.queries.R_BUSQUEDA')
    def test_update_hymn_frequencies_in_db(self, mock_r_busqueda, mock_connect):
        mock_r_busqueda.return_value = "test_db_path.db"
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection # This mock_connect is for the sqlite3.connect call within the function itself

        update_data = [(5, 10, 1), (-1, 3, 2)]
        queries.update_hymn_frequencies_in_db(update_data)
        
        expected_sql_part = "UPDATE Frecuencias SET frec_util = ?, frec_real = ? WHERE id_himno = ?"
        actual_sql_call = ' '.join(mock_cursor.executemany.call_args[0][0].split())
        self.assertTrue(expected_sql_part.split() == actual_sql_call.split())
        
        self.assertEqual(mock_cursor.executemany.call_args[0][1], update_data)
        mock_connection.commit.assert_called_once()

    @patch('database_interact.queries.sqlite3.connect', side_effect=sqlite3.Error("DB update failed"))
    @patch('database_interact.queries.R_BUSQUEDA')
    def test_update_hymn_frequencies_in_db_error(self, mock_r_busqueda, mock_connect):
        mock_r_busqueda.return_value = "test_db_path.db"
        # This test implicitly checks if the finally block closes the connection
        # by not crashing due to an unclosed mock connection if an error occurs.
        # Also checks if logger.error was called.
        
        update_data = [(5, 10, 1)]
        # We expect the function to catch the sqlite3.Error and log it.
        # It should not re-raise the error unless explicitly designed to.
        try:
            queries.update_hymn_frequencies_in_db(update_data)
        except sqlite3.Error:
            self.fail("update_hymn_frequencies_in_db should handle sqlite3.Error internally.")
        
        # To verify logging, you'd typically un-mock the logger for this specific test or use a more advanced mock.
        # For now, we assume the logger.error call (added in previous steps) works.

if __name__ == '__main__':
    unittest.main()
