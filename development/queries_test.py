import sqlite3

def print_sql_table(table:str):
    conn = sqlite3.connect("database/search_ref.db")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,))
        result = cursor.fetchall()
    except:
        result="No existe"
        conn.close()

    print(result[0])
    conn.close()

"""
    CREATE TABLE Himnos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL, 
        numH_gen INTEGER, 
        numH_aux INTEGER,
        es_nuevo INTEGER,
        sube_tono INTEGER,
        id_himnario INTEGER,
        modificado TEXT NOT NULL,
    )

    CREATE TABLE "Frecuencias"(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_himno INTEGER NOT NULL,
        seguimiento INTEGER NOT NULL,
        uso_real INTEGER NOT NULL,
        uso_ult TEXT NOT NULL,
        uso_prom INTEGER NOT NULL,
        modificado TEXT NOT NULL,

        FOREIGN KEY (id_himno) REFERENCES Himnos(id) ON DELETE CASCADE
    )

    CREATE TABLE Indice_busqueda(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_himno INTEGER NOT NULL,
        titulo_norm TEXT NOT NULL,
        modificado TEXT NOT NULL,
        FOREIGN KEY (id_himno) REFERENCES Himnos(id) ON DELETE CASCADE
    )
"""




# Manda señal de modificacion:
#   -Puedes agreagr un himno
#   -Puedes activar o desactivar:
#       - seguimiento de cierto himno.
#       - si sube de tono
#       - si es nuevo.
#   - Ver modificaciones por fecha:
#   - Deshacer modificaciones recientes.
#   - Ver titulos normalizados
#   - Eliminar titulos normalizados



#   En algun momento quedré cambiar el seguimiento de un himno  ( )
#   Deshcaer mi ultimo cambio.                                  ( )
#   Ver que acciones se realizaron por ultima vez.              ( )
#   Cambiar si es nuevo, si sube de tono,                       ( )
#   Administrar titulos noramalizados                           ( )
#   Añadir un himno.                                            ( )