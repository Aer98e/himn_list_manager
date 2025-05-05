import sqlite3
from .file_names import R_BUSQUEDA
from utils.helpers import limpiar_texto1
from typing import Union
import os

def find_title(title_norm: str):
    '''
    Esta funcion recibe un titulo normalizado para buscar el titulo al que hace referencia dentro de la base de datos,
    puede haber mas de un titulo normalizado referenciando a un solo titulo.
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

def find_title_id(id: Union[int, list[int]]) -> list[str]:
    def verification():
        nonlocal id
        if not isinstance(id, int) and not isinstance(id, list):
            raise TypeError("El parametro debe ser de tipo Int o List")
        
        if isinstance(id, list):
            for num in id:
                if not isinstance(num, int):
                    raise TypeError('El argumento id debe contener valores Int')
        if isinstance(id, int):
            id = [id]
    
    verification()
    with sqlite3.connect(R_BUSQUEDA()) as conn:
        cursor = conn.cursor()
        consult=', '.join(['?']*len(id))

        cursor.execute(f'SELECT titulo FROM Himnos WHERE id IN ({consult})', id)
        res = cursor.fetchall()

    return [title[0] for title in res]


def find_data(title_norm: str, queries: list):
    '''
    Permite busqueda general de alguna columna  basandose en un titulo normalizado.
    La busqueda se dara en una base de datos especifica.

    Args:
    title_norm (str) :Es el valor con el que se buscaran los datos.
    queries (list[str]) : Es una lista de columnas de las que se retornara la busqueda.

    '''
    if not isinstance(queries, list):
        raise ValueError('El argumento queries debe ser de tipo list')
    
    querie = ", ".join([f"Himnos.{que}" for que in queries])

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

def update_search_list(title_norm:str, norm_match:str):
    '''
    Busca el id de un elemento para agregar otro con que use su misma clave foranea.

    Parámetros:
    title_norm (str): Elemento nuevo que se agregara a la base de datos.
    norm_match (str): Elemento buscar el id que se agregará con nuevo elemento.
    '''
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

def catch_normalize_titles():
    '''
    Busca en una base de datos especifica los registros de titulos normalizados.

    Retorno:
    (list)
    '''

    with sqlite3.connect(R_BUSQUEDA()) as conn:
        cursor = conn.cursor()
        cursor.execute(
        '''
        SELECT titulo_norm
        FROM Indice_busqueda
        ''')
        result = cursor.fetchall()
    return list(map(lambda x:x[0],result))

def extract_data_db(title):
    title_norm = limpiar_texto1(title)
    
    with sqlite3.connect(R_BUSQUEDA()) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id_himno FROM Indice_busqueda WHERE titulo_norm = ?', (title_norm,))
        result = cursor.fetchone()
        
        if result:
            id_himno = result[0]
            cursor.execute('''
            SELECT titulo, numH_uso, numH_nuevo, es_nuevo, sube_tono, id_himnario
            FROM Himnos
            WHERE id = ?
            ''', (id_himno,))
            result = cursor.fetchone()
            
        else:
            print(f'No se encontró el himno: {title}')
            return None
        
        title = result[0]
        num_B_P = result[1]
        num_N = str(result[2])
        new_H = result[3]
        up = result[4]

        if new_H:
            num_N+='::N'
        if up:
            num_N+='::U'
        
        if num_B_P and result[5] == 1:
            num_B_P = f'{num_B_P}::R'
        elif result[5] == 2:
            num_B_P = f'{num_B_P}::V'
        
        return[title, num_B_P, num_N]

def load_frequencies():
    '''
    Toma una base de datos especifica de la que extrae regustros de la frecuencia de uso de los himnos.

    Returns:
        list: Una lista con tuplas que contiene el id del himno, con su frecuencia util, y frecuencia real.
    '''
    with sqlite3.connect(R_BUSQUEDA()) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT id_himno, frec_util, frec_real
        FROM Frecuencias
        WHERE seguimiento = 1
        ''')
        result = cursor.fetchall()
    return result

def database_update(data_update):
    with sqlite3.connect(R_BUSQUEDA()) as conn:
        cursor = conn.cursor()
        cursor.executemany('''
            UPDATE Frecuencias
            SET frec_util = ?, frec_real = ?
            WHERE id_himno = ?
        ''', data_update)
        conn.commit() 

def main():
    pass

if __name__ =="__main__":
    main()
