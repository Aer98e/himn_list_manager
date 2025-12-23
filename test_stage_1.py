from database_interact.queries import ensure_history_table_exists, register_hymn_usage, get_hymns_with_last_date
import sqlite3
from database_interact.file_names import R_BUSQUEDA

# 1. Ejecutar creación
ensure_history_table_exists()

# 2. Verificar estructura en BD
# (El agente debe mostrarte el output de esta consulta SQL)
# SQL: PRAGMA table_info(Historial_Uso);
# Resultado esperado: Columnas id, id_himno, fecha_uso, tipo_evento.
print("--- Verifying Table Structure ---")
try:
    db_path = R_BUSQUEDA()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(Historial_Uso);")
    columns = cursor.fetchall()
    for col in columns:
        print(col)
    conn.close()
except Exception as e:
    print(f"Error checking table structure: {e}")

# 3. Prueba de Inserción y Lectura
print("--- Testing Insertion and Retrieval ---")
try:
    # Insertar un dato falso para el himno ID 1
    register_hymn_usage(1, '2025-01-01', 'test_migration')
    datos = get_hymns_with_last_date()

    # Validación Lógica
    # Buscar el ID 1 en los resultados. Su fecha debe ser '2025-01-01'.
    # Note: get_hymns_with_last_date returns list of tuples (id, max_date)
    found = False
    for d in datos:
        if d[0] == 1 and d[1] == '2025-01-01':
            found = True
            break
    
    print("Prueba Etapa 1:", "EXITOSA" if found else "FALLIDA")
    if not found:
        print("Data found for ID 1 (if any):")
        for d in datos:
            if d[0] == 1:
                print(d)

except Exception as e:
    print(f"Error during testing: {e}")
