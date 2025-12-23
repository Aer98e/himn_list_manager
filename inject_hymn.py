
import sqlite3
from database_interact.file_names import R_BUSQUEDA

def inject_test_hymn():
    try:
        conn = sqlite3.connect(R_BUSQUEDA())
        cursor = conn.cursor()
        
        # Check if ID 999 exists
        cursor.execute("SELECT id FROM Himnos WHERE id = 999")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO Himnos (id, titulo, numH_uso, id_himnario) VALUES (999, 'Himno Smoke Test', 1, 1)")
            conn.commit()
            print("Injected 'Himno Smoke Test' (ID 999).")
        else:
            print("'Himno Smoke Test' (ID 999) already exists.")
            
        cursor.execute("SELECT id FROM Himnos WHERE id = 998")
        if not cursor.fetchone():
             cursor.execute("INSERT INTO Himnos (id, titulo, numH_uso, id_himnario) VALUES (998, 'Otro Himno', 2, 1)")
             conn.commit()
             print("Injected 'Otro Himno' (ID 998).")
        
        conn.close()
    except Exception as e:
        print(f"Error injecting: {e}")

if __name__ == "__main__":
    inject_test_hymn()
