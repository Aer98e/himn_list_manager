import pandas as pd
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to sys.path to ensure imports work correctly if run from root
sys.path.append(os.getcwd())

from database_interact.frecuence_hymns import compile_hymn_usage_from_data_tables

class TestIsoDatePriority(unittest.TestCase):
    
    @patch('database_interact.frecuence_hymns.find_data_by_normalized_title')
    @patch('database_interact.frecuence_hymns.extract_table_titles')
    def test_prefers_iso_date_over_text(self, mock_extract, mock_db):
        print("\n=== INICIANDO TEST: PRIORIDAD DE FECHA ISO ===")
        
        # 1. CONFIGURACIÓN DEL ESCENARIO (El problema real)
        # Fecha visible (MALA): Lo que ve el usuario en Excel
        visible_text_date = "MIERCOLES 7"
        # Fecha oculta (BUENA): Lo que calculó el Scheduler
        hidden_iso_date = "2025-05-07"
        
        # Creamos un DataFrame simulado
        df_dummy = pd.DataFrame()
        # Inyectamos la fecha buena en los metadatos (la solución propuesta)
        df_dummy.attrs['iso_date'] = hidden_iso_date
        
        # 2. MOCKING (Simular respuestas de funciones externas para aislar la prueba)
        # Simulamos que extract_table_titles devuelve la fecha MALA (texto)
        mock_extract.return_value = [visible_text_date, "HIMNO_TEST_NORM"]
        
        # Simulamos que la base de datos encuentra el himno (ID 100)
        mock_db.return_value = (100, "Himno Oficial")

        # 3. EJECUCIÓN
        print(f"[INPUT] DataFrame con:\n - Visible: '{visible_text_date}'\n - Oculto (attrs): '{hidden_iso_date}'")
        result = compile_hymn_usage_from_data_tables([df_dummy])
        
        # 4. VERIFICACIÓN (La hora de la verdad)
        # Recuperamos la fecha que el sistema decidió usar
        # result es {100: {'title': 'Himno Oficial', 'dates': ['2025-05-07']}}
        if 100 not in result:
            self.fail("El himno ID 100 no fue encontrado en los resultados.")
            
        extracted_dates = result[100]['dates']
        used_date = extracted_dates[0]
        
        print(f"[RESULTADO] El sistema guardó la fecha: '{used_date}'")
        
        # ASERCIÓN: Debe ser igual a la fecha oculta, NO a la visible
        try:
            self.assertEqual(used_date, hidden_iso_date, 
                             f"FALLO: El sistema usó '{used_date}' en lugar de la fecha ISO '{hidden_iso_date}'")
            print("TEST EXITOSO: El sistema ignoró el texto visible y usó la fecha ISO correcta.")
        except AssertionError as e:
            print("TEST FALLIDO")
            raise e

if __name__ == '__main__':
    unittest.main()
