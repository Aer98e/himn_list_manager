import sqlite3
from .file_names import R_BUSQUEDA
from utils.helpers import limpiar_texto1

def find_title(title_norm):
    '''
    Esta funcion recibe un titulo normalizado para buscar el titulo al que hace referencia dentro de la base de datos() puede haber ma de un titulo normalizado referenciando a un solo titulo.
    '''
    with sqlite3.connect(R_BUSQUEDA()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT Himnos.titulo
            FROM Himnos
            JOIN Indice_busqueda ON Himnos.id=Indice_busqueda.id_himno
            WHERE Indice_busqueda.titulo_norm = ?
            ''',(title_norm,))
        res = cursor.fetchone()
    return res[0]

def find_data(title_norm, queries:list):
    '''
    Permite busqueda general de alguna columna  basandose en un titulo normalizado
    '''
    if not isinstance(queries, list):
        raise ValueError('El argumento queries debe ser de tipo list')
    
    querie = f"Himnos.{queries[0]}, " + ", ".join([f"Himnos.{que}" for que in queries[1:]])

    with sqlite3.connect(R_BUSQUEDA()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            f'''
            SELECT {querie}
            FROM Himnos
            JOIN Indice_busqueda ON Himnos.id=Indice_busqueda.id_himno
            WHERE Indice_busqueda.titulo_norm = ?
            ''',(title_norm,))
        res = cursor.fetchone()
    if len(queries)>1:
        return res
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

def update_frec_hymns(frecuences):
    pass

def main():
    pass

if __name__ =="__main__":
    main()
