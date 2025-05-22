import re
import unicodedata
import shutil
import os
import json
from typing import Any, Dict # Added for type hinting
import logging

# Get a logger for this module
logger = logging.getLogger(__name__)

# Define a tuple of affirmative answers for wider use.
# These are typically used for processing user input.
affirmative_answers = ('y', 's', '1', 'yes', 'si', 'true', 'ok', 'okay')

def normalize_text(text: Any) -> str:
    """
    Normalizes a given text by converting it to lowercase, removing punctuation,
    stripping extra whitespace, and removing diacritics (accents).

    Args:
        text (Any): The input text to normalize. It will be converted to a string
                    if it's not already one.

    Returns:
        str: The normalized text.

    Raises:
        TypeError: If the input text cannot be converted to a string.
    """
    if not isinstance(text, str):
        try:
            text = str(text)  # Attempt to convert non-string input to string
        except Exception as e: # Catch any exception during conversion
            raise TypeError(f'The data type to process must be convertible to text. Error: {e}')
    
    text = text.lower()  # Convert to lowercase
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation (keeps word characters and spaces)
    text = re.sub(r'\s+', '', text)  # Remove all whitespace (including spaces, tabs, newlines)
    
    # Normalize Unicode characters to their base form (e.g., 'é' to 'e')
    # NFD (Normalization Form D) decomposes characters into base characters and combining diacritical marks.
    # encode('ascii', 'ignore') removes characters that cannot be represented in ASCII (like diacritics).
    # decode('utf-8') converts the byte string back to a Python string.
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8')
    
    return text

def move_processed_file(new_file_path: str, source_folder: str = 'file_procces', source_filename: str = 'moment.xlsx'):
    """
    Moves a processed file from a temporary location to a specified new path and
    removes the temporary source folder.

    Args:
        new_file_path (str): The destination path (including filename) for the processed file.
        source_folder (str, optional): The name of the temporary folder where the processed
                                       file is currently located. Defaults to 'file_procces'.
        source_filename (str, optional): The name of the processed file in the source_folder.
                                         Defaults to 'moment.xlsx'.
    """
    # Construct the full current path of the file to be moved
    current_path = os.path.join(source_folder, source_filename)
    
    try:
        # Ensure the destination directory exists, create if not
        destination_directory = os.path.dirname(new_file_path)
        if not os.path.exists(destination_directory) and destination_directory: # Check if dirname is not empty
            os.makedirs(destination_directory, exist_ok=True) # Add exist_ok=True

        shutil.move(current_path, new_file_path)  # Move the file
        logger.info(f"Successfully moved '{current_path}' to '{new_file_path}'.") # Replaced print
        
        # Remove the temporary source folder and its contents
        if os.path.exists(source_folder): # Check if source_folder still exists
            shutil.rmtree(source_folder)
            logger.info(f"Successfully removed temporary folder '{source_folder}'.") # Replaced print
            
    except FileNotFoundError:
        logger.error(f"Error in move_processed_file: Source file '{current_path}' not found.") # Replaced print
    except IOError as e:
        logger.error(f"An I/O error occurred in move_processed_file: {e}", exc_info=True) # Replaced print
    except Exception as e: # Catch any other unexpected errors
        logger.error(f"An unexpected error occurred in move_processed_file: {e}", exc_info=True) # Replaced print


def load_config_from_json(config_name: str) -> Dict[Any, Any]:
    """
    Loads a configuration dictionary from a JSON file located in the 'configs' directory.

    Args:
        config_name (str): The name of the configuration file (without the .json extension).

    Returns:
        Dict[Any, Any]: The loaded configuration dictionary.

    Raises:
        ValueError: If the specified configuration file does not exist in 'configs/'.
    """
    # List available .json configuration files in the 'configs' directory
    available_configs = []
    configs_dir = 'configs'
    if os.path.exists(configs_dir) and os.path.isdir(configs_dir):
        for f_name in os.listdir(configs_dir):
            if f_name.endswith('.json'):
                available_configs.append(os.path.splitext(f_name)[0]) # Get filename without extension
    
    if config_name not in available_configs:
        # It's better to return a default or raise a specific custom error
        # than to raise ValueError directly in some contexts.
        # For now, ValueError is kept as per existing behavior.
        raise ValueError(f"The requested configuration file '{config_name}.json' does not exist in '{configs_dir}/'. "
                         f"Available configs: {available_configs}")
 
    config_file_path = os.path.join(configs_dir, f'{config_name}.json')

    try:
        with open(config_file_path, mode='r', encoding='utf-8') as config_file: # Specify UTF-8 encoding
            configuration = json.load(config_file)
        return configuration
    except FileNotFoundError:
        # This case should ideally be caught by the available_configs check, but good for robustness.
        logger.error(f"Configuration file '{config_file_path}' not found.") # Replaced print
        raise # Re-raise FileNotFoundError or a custom error
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from '{config_file_path}': {e}", exc_info=True) # Replaced print
        # Depending on policy, could return default config, raise custom error, or exit.
        raise # Re-raise for now
    except IOError as e:
        logger.error(f"I/O error reading configuration file '{config_file_path}': {e}", exc_info=True) # Replaced print
        raise # Re-raise for now


def save_config_to_json(configuration_data: Dict[Any, Any], config_name: str):
    """
    Saves a configuration dictionary to a JSON file in the 'configs' directory.
    The JSON file is pretty-printed with an indent of 4 spaces.

    Args:
        configuration_data (Dict[Any, Any]): The configuration dictionary to save.
        config_name (str): The name for the configuration file (without the .json extension).
    """
    configs_dir = 'configs'
    try:
        if not os.path.exists(configs_dir):
            os.makedirs(configs_dir, exist_ok=True) # Create 'configs' directory if it doesn't exist

        config_file_path = os.path.join(configs_dir, f'{config_name}.json')
        with open(config_file_path, mode='w', encoding='utf-8') as file: # Specify UTF-8 encoding
            json.dump(configuration_data, file, indent=4)
        logger.info(f"Configuration successfully saved to '{config_file_path}'.") # Replaced print
    except IOError as e:
        logger.error(f"I/O error writing configuration to '{config_file_path}': {e}", exc_info=True) # Replaced print
        # Potentially raise a custom error or handle as per application policy
    except Exception as e:
        logger.error(f"An unexpected error occurred while saving configuration to '{config_file_path}': {e}", exc_info=True) # Replaced print


def main():
    # Example usage or testing can go here
    # Test normalize_text
    # print(normalize_text("¡Hola, Mundo! Esto es una prueba 123."))
    # print(normalize_text("DébORA"))

    # Test load_config_from_json (assuming a 'test_config.json' exists in 'configs/')
    # try:
    #     test_cfg_data = {"key": "value", "number": 123}
    #     save_config_to_json(test_cfg_data, "test_config")
    #     loaded_cfg = load_config_from_json("test_config")
    #     print(f"Loaded config: {loaded_cfg}")
    # except ValueError as e:
    #     print(e)
    # except Exception as e:
    #     print(f"An unexpected error occurred: {e}")
    pass

if __name__ == "__main__":
    main()
