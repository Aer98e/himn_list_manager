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
        id INTEGER PRIMARY KEY AUTOINCREMENT, # Para tener consistencia deben mantenerse los id.
        titulo TEXT NOT NULL, 
        numH_gen INTEGER,  #(numH_nuevo) -> anterior base de datos
        numH_aux INTEGER,  #(numH_uso)   -> anterior base de datos
        es_nuevo INTEGER,
        sube_tono INTEGER,
        id_himnario INTEGER,
        modificado TEXT NOT NULL,
    )

    CREATE TABLE "Frecuencias"(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_himno INTEGER NOT NULL,
        seguimiento INTEGER NOT NULL,
        uso_real INTEGER NOT NULL,  # Cantidad de veces usado.
        uso_ult TEXT NOT NULL,      # Fecha de último uso "DD-MM-AA"
        uso_prom INTEGER NOT NULL,  # Promedio en dias de cada cuanto tiempo se usa.
        modificado TEXT NOT NULL,   # Cuanado se modificó esta fila "DD-MM-AA"

        FOREIGN KEY (id_himno) REFERENCES Himnos(id) ON DELETE CASCADE
    )

    CREATE TABLE Indice_busqueda(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_himno INTEGER NOT NULL,
        titulo_norm TEXT NOT NULL, # En util.helpers, se encuentra una funcion
                                    # para normalizar los titulos, sino solo los copiamos.
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