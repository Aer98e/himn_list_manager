
import sys
import os

# Add data_processing to path so main.py can import modules from it directly if it uses old-style imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'data_processing'))

import unittest.mock
import io
import builtins
import main

def run_smoke_test():
    print("=== SMOKE TEST START ===")
    
    # ------------------ PASS 1: LOAD and SAVE ------------------
    print("\n[Pass 1] Loading 'Himno Smoke Test' usage...")
    
    inputs_pass_1 = iter([
        "5", # Assistant: Continue (Option 5)
        "s", # Update Database Confirmation
        "Smoke Test Pass 1", # Sheet Title
        # "s", # If prompted to overwrite? get_save_excel_file_path usually implies interactive save, but mocked return path.
    ])
    
    def mock_input_1(prompt=""):
        print(f"[MOCK INPUT 1] Prompt: {prompt}")
        try:
             val = next(inputs_pass_1)
             print(f"[MOCK INPUT 1] Sending: {val}")
             return val
        except StopIteration:
             print("[MOCK INPUT 1] Sending EMPTY STRING (StopIteration)")
             return ""

    with unittest.mock.patch('interact_user.general.select_excel_file', return_value=os.path.abspath('input_day1.xlsx')), \
         unittest.mock.patch('interact_user.general.get_save_excel_file_path', return_value=os.path.abspath('output_pass1.xlsx')), \
         unittest.mock.patch('builtins.input', side_effect=mock_input_1):
        
        try:
            main.main()
            print("[Pass 1] Completed.")
        except Exception as e:
            print(f"[Pass 1] Failed with error: {e}")
            raise e

    # ------------------ PASS 2: CHECK RECOMMENDATIONS ------------------
    print("\n[Pass 2] Checking Recommendations (Should EXCLUDE 'Himno Smoke Test')...")
    
    # We want to capture stdout to see the recommendations list
    captured_output = io.StringIO()
    original_stdout = sys.stdout
    sys.stdout = captured_output
    
    inputs_pass_2 = iter([
        "3", # Assistant: Option 3 (Recommendations)
        "",  # "Presione Enter para volver..."
        "5", # Assistant: Option 5 (Continue)
        "s", # Update Database Confirmation
        "Smoke Test Pass 2" # Sheet Title
    ])
    
    def mock_input_2(prompt=""):
        # We can also log prompts to stderr if needed
        return next(inputs_pass_2)

    try:
        with unittest.mock.patch('interact_user.general.select_excel_file', return_value=os.path.abspath('input_day2.xlsx')), \
             unittest.mock.patch('interact_user.general.get_save_excel_file_path', return_value=os.path.abspath('output_pass2.xlsx')), \
             unittest.mock.patch('builtins.input', side_effect=mock_input_2):
            
            main.main()
            
    except Exception as e:
        sys.stdout = original_stdout
        print(f"[Pass 2] Failed with error: {e}")
        # raise e
    finally:
        sys.stdout = original_stdout

    # ------------------ ANALYSIS ------------------
    output_text = captured_output.getvalue()
    # print("DEBUG OUTPUT PASS 2:\n" + output_text)
    
    # Verify: "Himno Smoke Test" (ID 999) should NOT be in the recommendations list
    # Because it was used in Pass 1 (Today).
    
    if "Himno Smoke Test" in output_text:
        # Check context. Maybe it appears in "Recently Used" list if Option 1 was selected?
        # But we selected Option 3.
        # Wait, Option 3 output header is: "==== Recomendaciones (Prioridad por tiempo sin cantar) ===="
        # If it appears under that header, it's a FAIL.
        
        # Simple check: extract text between "Recomendaciones" and "Resultados del Análisis" end?
        # Assuming typical output structure.
        
        if "Himno Smoke Test" in output_text:
             # Check if it was listed with "Días sin cantar: 0" or similar?
             # If filter works (<30 days), it should NOT be there.
             print("❌ SMOKE TEST FAILED: 'Himno Smoke Test' appeared in the output (likely recommended).")
             print("Output snippet containing hymn:")
             start_idx = output_text.find("Himno Smoke Test")
             print(output_text[start_idx-50:start_idx+100])
    else:
         print("✅ SMOKE TEST PASSED: 'Himno Smoke Test' was NOT found in the recommendations.")
    
    # Optional: Verify "Días sin cantar" label presence
    if "Días sin cantar" in output_text:
        print("✅ Labels verified: 'Días sin cantar' present.")
    else:
        print("⚠️ Warning: 'Días sin cantar' label not found. Did Option 3 run?")

if __name__ == "__main__":
    run_smoke_test()
