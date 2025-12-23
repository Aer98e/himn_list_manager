import sqlite3
import os
import sys

# Add the project root to the path so we can import modules
sys.path.append(os.getcwd())

from database_interact.file_names import R_BUSQUEDA

def cleanup_history():
    db_path = R_BUSQUEDA()
    print(f"Connecting to database at: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check invalid entries count before
    cursor.execute("SELECT COUNT(*) FROM Historial_Uso WHERE fecha_uso NOT LIKE '20%';")
    count_before = cursor.fetchone()[0]
    print(f"Invalid entries found: {count_before}")
    
    if count_before > 0:
        print("Deleting invalid entries...")
        cursor.execute("DELETE FROM Historial_Uso WHERE fecha_uso NOT LIKE '20%';")
        deleted_count = cursor.rowcount
        conn.commit()
        print(f"Deleted {deleted_count} entries.")
    else:
        print("No invalid entries to delete.")
        
    conn.close()

if __name__ == "__main__":
    cleanup_history()
