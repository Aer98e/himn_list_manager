import sqlite3
from .file_names import R_BUSQUEDA
from utils.helpers import limpiar_texto1

def find_simil(simil):
    with sqlite3.connect(R_BUSQUEDA()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT Himnos.titulo
            FROM Himnos
            JOIN Indice_busqueda ON Himnos.id=Indice_busqueda.id_himno
            WHERE Indice_busqueda.titulo_norm = ?
            ''',(simil,))
        res = cursor.fetchone()
    return res[0]

def update_search_list(title_norm, norm_match):
    with sqlite3.connect(R_BUSQUEDA()) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id_himno FROM Indice_busqueda WHERE titulo_norm = ?', (norm_match,))
        indice = cursor.fetchone()
        if indice is not None:
            cursor.execute('INSERT INTO Indice_busqueda(id_himno, titulo_norm) VALUES(?, ?)', (indice[0], title_norm))
            conn.commit()
        else:
            print(f'No se encontro :: {norm_match} en la base de datos.')

def Buscar_Columna(nameDB, nameTB, category):
    """Este metodo se encarga de entregar una lista de todas las celdas de una columna de una base de datos.

    Arg:
        nameDB:     nombre de la base de datos a examinar.
        nameTB:     noimbre de la tabla de la base de datso a examinar.
        category:   nombre de la columna a registrar.
    
    """
    with sqlite3.connect(nameDB) as conex:
        cursor = conex.cursor()
        consult = f'''
        SELECT {category}
        FROM {nameTB}
        '''
        cursor.execute(consult)
        result = cursor.fetchall()
    return [res[0] for res in result]

def extract_data_db(title):
    title_norm = limpiar_texto1(title)
    
    with sqlite3.connect(R_BUSQUEDA()) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id_himno FROM Indice_busqueda WHERE titulo_norm = ?', (title_norm,))
        result = cursor.fetchone()
        
        if result:
            id_himno = result[0]
            cursor.execute('''
            SELECT titulo, numH_uso, numH_nuevo
            FROM Himnos
            WHERE id = ?
            ''', (id_himno,))
            result = cursor.fetchone()
            return result
        else:
            print(f'No se encontró el himno: {title}')
            return None

def main():
    pass

if __name__ =="__main__":
    main()
