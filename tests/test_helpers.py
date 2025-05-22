import unittest
from utils.helpers import normalize_text, affirmative_answers # assuming affirmative_answers might be tested or used by other tests later
import os # Will be needed for other tests in this file

class TestNormalizeText(unittest.TestCase):

    def test_simple_lowercase(self):
        self.assertEqual(normalize_text("hello world"), "helloworld")

    def test_with_uppercase(self):
        self.assertEqual(normalize_text("Hello World"), "helloworld")

    def test_with_punctuation(self):
        self.assertEqual(normalize_text("Hello, World!"), "helloworld")

    def test_with_leading_trailing_spaces(self):
        self.assertEqual(normalize_text("  hello world  "), "helloworld")

    def test_with_multiple_spaces_between_words(self):
        self.assertEqual(normalize_text("hello   world"), "helloworld")

    def test_with_accented_characters(self):
        self.assertEqual(normalize_text("canción"), "cancion")
        self.assertEqual(normalize_text("DébORA"), "debora")
        self.assertEqual(normalize_text("JÉSUS É AMIGO"), "jesuseamigo")

    def test_already_normalized(self):
        self.assertEqual(normalize_text("helloworld"), "helloworld")

    def test_empty_string(self):
        self.assertEqual(normalize_text(""), "")

    def test_with_numbers_as_string(self):
        self.assertEqual(normalize_text("test123"), "test123")

    def test_with_numbers_and_spaces(self):
        self.assertEqual(normalize_text("test 123"), "test123")

    def test_non_string_convertible_input_number(self):
        self.assertEqual(normalize_text(123), "123")
        self.assertEqual(normalize_text(12.34), "1234") # Note: period is removed

    def test_non_string_non_convertible_input_list(self):
        # The function currently converts list to string like "['item']" then normalizes.
        # This test documents current behavior. If this behavior is undesired, the function should be changed.
        self.assertEqual(normalize_text(["item", "another"]), "itemanother")

    def test_non_string_non_convertible_input_dict(self):
        # Similar to list, dicts are converted to string representation first.
        self.assertEqual(normalize_text({"key": "value"}), "keyvalue")

    def test_with_mixed_alphanumeric_and_punctuation(self):
        self.assertEqual(normalize_text("Test@123#Go!"), "test123go")
        
    # Test for TypeError is tricky because normalize_text tries to str(text)
    # If str() itself fails for some custom object without a __str__ method,
    # then a TypeError might occur from within str(), not directly from normalize_text's type check.
    # The current implementation of normalize_text is quite resilient to types due to the initial str() conversion.
    # A specific TypeError for "non-convertible" type is hard to achieve without modifying the function
    # to be more restrictive or by creating a custom object that fails str().

    # Example of a custom object that might cause issues if str() was not robust
    # class ProblematicObject:
    #     def __str__(self):
    #         raise TypeError("Cannot convert this object to string")
    #
    # def test_problematic_object(self):
    #     with self.assertRaisesRegex(TypeError, "The data type to process must be convertible to text"):
    #         normalize_text(ProblematicObject())

# --- Tests for Config Functions ---
from unittest.mock import patch, mock_open, MagicMock
import json # For testing json load/dump
from utils.helpers import load_config_from_json, save_config_to_json

class TestConfigFunctions(unittest.TestCase):

    @patch('utils.helpers.os.path.exists')
    @patch('utils.helpers.os.listdir')
    @patch('builtins.open', new_callable=mock_open, read_data='{"key": "value"}')
    def test_load_config_from_json_success(self, mock_file_open, mock_listdir, mock_path_exists):
        mock_path_exists.return_value = True # Assume 'configs' dir exists
        mock_listdir.return_value = ['test_config.json'] # Assume 'test_config.json' is in 'configs'
        
        config_data = load_config_from_json('test_config')
        
        mock_file_open.assert_called_once_with(os.path.join('configs', 'test_config.json'), mode='r', encoding='utf-8')
        self.assertEqual(config_data, {"key": "value"})

    @patch('utils.helpers.os.path.exists')
    @patch('utils.helpers.os.listdir')
    def test_load_config_from_json_file_not_found_in_listdir(self, mock_listdir, mock_path_exists):
        mock_path_exists.return_value = True
        mock_listdir.return_value = ['another_config.json'] # 'test_config' is not listed
        
        with self.assertRaisesRegex(ValueError, "The requested configuration file 'test_config.json' does not exist"):
            load_config_from_json('test_config')

    @patch('utils.helpers.os.path.exists')
    @patch('utils.helpers.os.listdir')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_config_from_json_io_error_on_open(self, mock_file_open, mock_listdir, mock_path_exists):
        mock_path_exists.return_value = True
        mock_listdir.return_value = ['test_config.json']
        mock_file_open.side_effect = IOError("File system is angry")
        
        with self.assertRaises(IOError): # The function re-raises IOError
            load_config_from_json('test_config')

    @patch('utils.helpers.os.path.exists')
    @patch('utils.helpers.os.listdir')
    @patch('builtins.open', new_callable=mock_open, read_data='{"key": "value", "malformed}') # Malformed JSON
    def test_load_config_from_json_decode_error(self, mock_file_open, mock_listdir, mock_path_exists):
        mock_path_exists.return_value = True
        mock_listdir.return_value = ['test_config.json']
        
        with self.assertRaises(json.JSONDecodeError): # The function re-raises JSONDecodeError
            load_config_from_json('test_config')

    @patch('utils.helpers.os.path.exists') # Mock os.path.exists for save_config_to_json
    @patch('builtins.open', new_callable=mock_open)
    @patch('utils.helpers.json.dump')
    def test_save_config_to_json_success(self, mock_json_dump, mock_file_open, mock_os_path_exists):
        mock_os_path_exists.return_value = True # Assume 'configs' dir exists or is created
        
        config_data_to_save = {"new_key": "new_value"}
        save_config_to_json(config_data_to_save, 'new_config')
        
        mock_file_open.assert_called_once_with(os.path.join('configs', 'new_config.json'), mode='w', encoding='utf-8')
        mock_json_dump.assert_called_once_with(config_data_to_save, mock_file_open(), indent=4)

    @patch('utils.helpers.os.path.exists', return_value=False) # 'configs' dir does not exist
    @patch('utils.helpers.os.makedirs') # Mock makedirs
    @patch('builtins.open', new_callable=mock_open)
    @patch('utils.helpers.json.dump')
    def test_save_config_to_json_creates_dir(self, mock_json_dump, mock_file_open, mock_os_makedirs, mock_os_path_exists):
        config_data_to_save = {"another_key": "another_value"}
        save_config_to_json(config_data_to_save, 'another_config')
        
        mock_os_makedirs.assert_called_once_with('configs', exist_ok=True)
        mock_file_open.assert_called_once_with(os.path.join('configs', 'another_config.json'), mode='w', encoding='utf-8')
        mock_json_dump.assert_called_once_with(config_data_to_save, mock_file_open(), indent=4)


# --- Tests for File Movement ---
from utils.helpers import move_processed_file
import shutil # For patching

class TestMoveProcessedFile(unittest.TestCase):

    @patch('utils.helpers.os.path.dirname')
    @patch('utils.helpers.os.path.exists')
    @patch('utils.helpers.os.makedirs')
    @patch('utils.helpers.shutil.move')
    @patch('utils.helpers.shutil.rmtree')
    def test_move_processed_file_success_no_dest_dir(
        self, mock_rmtree, mock_move, mock_makedirs, mock_path_exists, mock_dirname
    ):
        # Scenario: Destination directory does NOT exist, source folder exists
        mock_dirname.return_value = 'destination_parent_dir'
        # First call to os.path.exists is for destination_directory, second for source_folder
        mock_path_exists.side_effect = [False, True] 
        
        source_folder = 'temp_source'
        source_filename = 'file.xlsx'
        new_file_path = 'destination_parent_dir/final_file.xlsx'
        
        move_processed_file(new_file_path, source_folder=source_folder, source_filename=source_filename)
        
        mock_dirname.assert_called_once_with(new_file_path)
        mock_makedirs.assert_called_once_with('destination_parent_dir', exist_ok=True)
        mock_move.assert_called_once_with(os.path.join(source_folder, source_filename), new_file_path)
        mock_rmtree.assert_called_once_with(source_folder)

    @patch('utils.helpers.os.path.dirname')
    @patch('utils.helpers.os.path.exists')
    @patch('utils.helpers.os.makedirs') # Should not be called if dest dir exists
    @patch('utils.helpers.shutil.move')
    @patch('utils.helpers.shutil.rmtree')
    def test_move_processed_file_success_dest_dir_exists(
        self, mock_rmtree, mock_move, mock_makedirs, mock_path_exists, mock_dirname
    ):
        # Scenario: Destination directory DOES exist, source folder exists
        mock_dirname.return_value = 'destination_parent_dir'
        # First call to os.path.exists is for destination_directory (True), second for source_folder (True)
        mock_path_exists.side_effect = [True, True]
        
        source_folder = 'temp_source'
        source_filename = 'file.xlsx'
        new_file_path = 'destination_parent_dir/final_file.xlsx'
        
        move_processed_file(new_file_path, source_folder=source_folder, source_filename=source_filename)
        
        mock_dirname.assert_called_once_with(new_file_path)
        mock_makedirs.assert_not_called() # Key check: makedirs not called
        mock_move.assert_called_once_with(os.path.join(source_folder, source_filename), new_file_path)
        mock_rmtree.assert_called_once_with(source_folder)

    @patch('utils.helpers.shutil.move', side_effect=FileNotFoundError("Mocked: Source not found"))
    @patch('utils.helpers.os.path.exists', return_value=True) # Assume dest dir exists
    @patch('utils.helpers.os.path.dirname', return_value='any_dest_dir')
    @patch('utils.helpers.logging.getLogger') # Mock the logger to check output
    def test_move_processed_file_source_not_found(self, mock_get_logger, mock_dirname, mock_path_exists, mock_move):
        # Configure the mock logger
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance

        source_folder = 'temp_source'
        source_filename = 'non_existent_file.xlsx'
        new_file_path = 'destination_parent_dir/final_file.xlsx'
        
        move_processed_file(new_file_path, source_folder=source_folder, source_filename=source_filename)
        
        expected_log_message_part = f"Error in move_processed_file: Source file '{os.path.join(source_folder, source_filename)}' not found."
        
        # Check if logger.error was called with a message containing the expected part
        called_with_correct_message = False
        for call_args in mock_logger_instance.error.call_args_list:
            if expected_log_message_part in call_args[0][0]:
                called_with_correct_message = True
                break
        self.assertTrue(called_with_correct_message, "Expected log message not found or incorrect.")


    @patch('utils.helpers.shutil.move')
    @patch('utils.helpers.shutil.rmtree', side_effect=IOError("Mocked: Cannot remove folder"))
    @patch('utils.helpers.os.path.exists', return_value=True)
    @patch('utils.helpers.os.path.dirname', return_value='any_dest_dir')
    @patch('utils.helpers.logging.getLogger')
    def test_move_processed_file_rmtree_fails(self, mock_get_logger, mock_dirname, mock_path_exists, mock_rmtree, mock_move):
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance
        
        source_folder = 'temp_source'
        source_filename = 'file.xlsx'
        new_file_path = 'destination_parent_dir/final_file.xlsx'
        
        move_processed_file(new_file_path, source_folder=source_folder, source_filename=source_filename)
        
        mock_move.assert_called_once() # Ensure move was attempted
        
        # Check if logger.error was called due to rmtree failure
        called_with_correct_message = False
        for call_args in mock_logger_instance.error.call_args_list:
            if "An I/O error occurred in move_processed_file" in call_args[0][0] and "Mocked: Cannot remove folder" in call_args[0][0]:
                called_with_correct_message = True
                break
        self.assertTrue(called_with_correct_message, "Expected log message for rmtree failure not found.")


if __name__ == '__main__':
    # This is to make it runnable from command line via `python tests/test_helpers.py`
    # For more complex test discovery, a test runner like pytest is recommended.
    # Adding the project root to sys.path for imports if running this file directly.
    import sys
    # Assuming the script is run from the project root or tests/ directory
    # This adds the project root to the Python path to resolve `from utils.helpers import ...`
    if os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) not in sys.path:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    unittest.main()
