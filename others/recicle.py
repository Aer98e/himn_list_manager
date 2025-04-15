import os
import pickle
import shutil
import pandas as pd
from typing import Union, Callable
import re
import unicodedata
import sqlite3
import sys
import difflib

ans_y = ('y', 's', '1', 'yes', 'si')

def limpiar_texto1(texto):
    texto = texto.lower()
    texto = re.sub(r'[^\w\s]', '', texto)
    texto = re.sub(r'\s+', '', texto)
    texto = unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('utf-8')
    
    return texto

def limpiar_texto2(texto):
    # Eliminar tildes y acentos
    texto_sin_tildes = unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('utf-8')

    # Eliminar caracteres no deseados (comas, puntos, signos, etc.)
    texto_limpio = re.sub(r'[^a-zA-Z\s]', '', texto_sin_tildes)

    return texto_limpio


class Management_Text():

    @staticmethod
    def limpiar_texto1(texto):
        texto = texto.lower()
        texto = re.sub(r'[^\w\s]', '', texto)
        texto = re.sub(r'\s+', '', texto)
        texto = unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('utf-8')
        
        return texto

    @staticmethod
    def limpiar_texto2(texto):
        # Eliminar tildes y acentos
        texto_sin_tildes = unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('utf-8')

        # Eliminar caracteres no deseados (comas, puntos, signos, etc.)
        texto_limpio = re.sub(r'[^a-zA-Z\s]', '', texto_sin_tildes)

        return texto_limpio

    @staticmethod
    def _compare_two_text(textM:str, textS:str):
        simi = difflib.SequenceMatcher(None, textM, textS)
        return simi.ratio()

    @classmethod
    def search_coindicenses(cls, text_list:list, searched:str):
        """Esta funcion se encarga de revisar la similitud de una palabra con una lista de palabras.
        Arg:
            text_list: La lista de palabras que se deben revisar.
            searched: la palabra que se buscara.

        Returns:
            [(ratio, index)...] -> ratio es la similitud[0-1], y index el indice de la lista a quien corresponde ratio.
            esta lista de tuplas esta ordenana desendentemente(ratio).
        
        """
        coincidences=[]
        
        for i in range(len(text_list)):
            ratio_coin = cls._compare_two_text(text_list[i], searched)
            coincidences.append((ratio_coin, i))
        
        coincidences_or = sorted(coincidences, key=lambda x: x[0], reverse=True)
        return coincidences_or

class Sa_Lo_Objects():
    ans_y = ('y', 's', '1', 'yes', 'si')
    path=['saved_objects', 'saved_objects\\temp']

    @staticmethod
    def _get_list_files(path):
        files=[file for file in os.listdir(path) if file.endswith('.pkl')]
        return files

    @staticmethod
    def _exist_file(files, searched):
        for file in files:
            if searched == os.path.splitext(file)[0]:
                return file
        return False
    @classmethod
    def saved_object(cls, object_s, name:str):
        if not isinstance(name, str):
            raise TypeError('El argumento "name" solo debe ser una cadena.')
        
        def _prepare_environment():
            if not os.path.exists(cls.path[0]):
                os.makedirs(cls.path[1], exist_ok=True)
            
            files = cls._get_list_files(cls.path[0])

            file = cls._exist_file(files, name)
            if file:
                ans = input("El archivo que deseas agregar ya existe, deseas sobreescribirlo?: ")
                if ans.lower() not in cls.ans_y:
                    path_f=os.path.join(cls.path[0], file)
                    path_del=os.path.join(cls.path[1], file)
                    try:
                        os.remove(path_del)
                    except:
                        pass
                    shutil.move(path_f, cls.path[1])

        _prepare_environment()

        path_saved = os.path.join(cls.path[0], name + '.pkl')
        with open(path_saved, 'wb') as file:
            pickle.dump(object_s, file)

    @classmethod
    def load_object(cls, name:str):
        if not isinstance(name, str):
            raise TypeError('El argumento "name" solo debe ser una cadena.')
        
        files = cls._get_list_files(cls.path[0])
        file = cls._exist_file(files, name)
        path_file=os.path.join(cls.path[0], file)
        
        if file:
            with open(path_file, 'rb') as file:
                loaded = pickle.load(file)
            return loaded
        
        else:
            raise('No se encontró un objeto con ese nombre.')

class ManagementDF():

    @staticmethod
    def packing_data(data_frame:pd.DataFrame, keys:list, coincidence:Union[tuple, int]):
        """Se encarga de buscar en un dataframe los valores que estan en (keys).
        Esto lo hace a travez del argumento 'coincidence', devuelve un diccionario con los resultados de los 'keys' buscados.
        Solo devolvera los datos de la primera coincidencia (en caso hayan varias coincidencias).

        Arg:
            data_frame: El donde se buscará los datos.
            keys: Las categorias donde se buscaran los datos.
            coincidence: La condicion o ubicacion de los datos:
                coincidense => (categoria[str], coincidencia[str]) or (indice[int])
        """
        pack={}

        if isinstance(coincidence, tuple):
            categoryC = coincidence[0]
            keywordC = coincidence[1]
            
            for key in keys:
                dat = data_frame[data_frame[categoryC]==keywordC][key].to_list()
                dat = dat[0]
                pack[key] = dat
        
        elif isinstance(coincidence,int):
            keywordC = coincidence

            for key in keys:
                dat = data_frame.at[keywordC, key]
                pack[key] = dat

        else:
            raise("Error en el argumento coincidence")
        
        return pack
    
    @staticmethod
    def comparate_dict_DF(dictM:dict, dictS:dict, keyID:str, keys:list, revise:pd.DataFrame = None, mode_segure = True):
        def _present_result(ans):
            print(f"==============={keyID}: {dictM[keyID]}===============")
            for i, a in enumerate(ans):
                if a != True:
                    print(f"{keys[i]}:\t{a}")
            
        def _data_correct(ans):
            indices = revise.loc[revise[keyID] == dictS[keyID]].index.to_list()

            for i, a in enumerate(ans):
                if a != True:
                    for inx in indices:
                        revise.at[inx, keys[i]] = dictM[keys[i]]
        
        ans = []
        error = False

        for key in keys:
            if dictM[key] == dictS[key]:
                ans.append(True)
            else:
                ans.append(dictM[key])
                error = True

        if revise is not None:
            _data_correct(ans)
                
        if mode_segure:
            if error:
                _present_result(ans)
            else:
                print(f"Dicionarios Iguales ::: {keyID}: {dictM[keyID]}")

def duplicate_to_list(list_eval, mode, normalize_fun:Callable = None):
    """Esta funcion revisa la lista 'list_eval' para encontrar elementos que se repitan usando una funcion de normalizacion de texto para una comparacion mas precisa.

    Arg:
    list_eval -> La lista a evaluar.
    mode -> Puede tener solo dos modos:
      'use': Retorna tuplas con los indices que coinciden.
      'view': Muestra los indices que coinciden.
    nomralize_fun -> En caso de querer usar una funcion para normalizar los textos al comparar.
    """
    def _present_duplicate(indexes:list):
        print(f"======== Elementos similares: {len(indexes)} ========")
        for ind in indexes:
           print(f"\t-{list_eval[ind]}({ind})")
    
    # ==== REVISIÓN DE ERRORES ====
    if mode not in ['view', 'use']:
        raise("El parámetro 'mode' debe ser 'view' o 'use'.")
    
    if normalize_fun is not None:
        list_eval_NOR = [normalize_fun(li) for li in list_eval]
    else:
        raise("No se encontro una funcion de limpieza de texto.")
    
    # ==== BUSQUEDA DE RECURRENCIAS ====
    duplicate = False
    register = {}

    for i, li in enumerate(list_eval_NOR):
        if li in register:
            register[li].append(i)
        
        else:
            register[li]=[i]

    # ==== LIMPIEZA DE REGISTRO ====
    keys_to_del=[key for key, value in register.items() if len(value) == 1]
    for key in keys_to_del:
        del register[key]
    
    # ==== USO DE RESULTADOS ====
    if not register:
        print("==== No se encontraron dupicados ====")

    if mode == "view":
        for value in register.values():
            _present_duplicate(value)   
    elif mode == 'use':
            return [tuple(i for i in li) for li in register.values()]

def search_tuple_list(tupleL, searched, ind:int):
    """Busca un valor en una lista de tuplas devolviendo si se encontro y su indice en tal caso.
    Arg:
        tupleL: lista de tuplas donde se buscara.
        searched: valor buscado
        ind: indice de tupla donde se buscará.
    """
    for i, tuple in enumerate(tupleL):
        if searched == tuple[ind]:
            return True, i
    return False, None

class Compare_texts():
    @staticmethod
    def comparar_cadenas(textS:str, textC:str, comp_elem=False, norm_call:Callable = None, word_line = 10, lines_error = 4):
        def _present(corrected_text):
            printer = " ".join(corrected_text)
            cont = 0
            for c in printer:
                print(c, end="")
                if c == " ":
                    cont += 1
                    if cont % word_line == 0:
                        print("")


        # Convertir las cadenas en listas de palabras
        textS_L = textS.strip().split()
        textC_L = textC.strip().split()

        # Encontrar las palabras diferentes
        corrected_text=[]
        error = False

        if comp_elem:
            print("Primera oración: ",len(textS_L), " || Segunda oración: ",len(textC_L))

        s = 0
        for c in range(len(textC_L)):
            
            if textS_L[s] == textC_L[c]:
                corrected_text.append(textC_L[c])
                s += 1

            else:
                error = True
                corrected_text.append(f"({textC_L[c]})")
                if norm_call(textC_L[c]) != norm_call(textS_L[s]):
                    for i in range(1, lines_error + 1):
                        try:
                            if norm_call(textC_L[c]) == norm_call(textS_L[s+i]):
                                s += i
                                break
                        except:
                            break
                else:
                    s += 1

        if error:
            _present(corrected_text)
        else:
            print("No se encontraron errores.")

    @classmethod
    def compare_interactive(cls, norm:Callable):
        def comparar():
            print("Ingrese la version a probar: ")
            prueba=sys.stdin.read()
            cls.comparar_cadenas(prueba, correccion, norm_call = norm)
        while True:
            print("Ingrese la version corregida: ")
            correccion = sys.stdin.read()
            while True:
                comparar(correccion)
                ans=input("Reintentar?: ").strip()
                if ans.lower() not in ans_y:
                    break
            ans=input("Comenzar de nuevo?: ").strip()
            if ans.lower() not in ans_y:
                break

class Management_SQLite():
    
    @staticmethod
    def analize_table_DB(name_DB, tableDB):
        conn = sqlite3.connect(name_DB)
        cursor = conn.cursor()

        print(f"\nEstructura de la tabla {tableDB}:")
        cursor.execute(f"PRAGMA table_info({tableDB});")
        columnas = cursor.fetchall()
        for columna in columnas:
            print(columna)

        conn.close()

    @staticmethod
    def Analize_DB(name_DB):
        conn = sqlite3.connect(name_DB)
        cursor = conn.cursor()

        # Obtener una lista de todas las tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tablas = cursor.fetchall()

        # Imprimir los nombres de las tablas
        print("Tablas en la base de datos:")
        for tabla in tablas:
            print(tabla[0])

        # Obtener la estructura de cada tabla
        for tabla in tablas:
            print(f"\nEstructura de la tabla {tabla[0]}:")
            cursor.execute(f"PRAGMA table_info({tabla[0]});")
            columnas = cursor.fetchall()
            for columna in columnas:
                print(columna)

        # Cerrar la conexión
        conn.close()
    @staticmethod
    def Buscar_Columna(nameDB, nameTB, category):
        """Este metodo se encarga de entregar una lista de todas las celdas de una columna de una base de datos.

        Arg:
            nameDB:     nombre de la base de datos a examinar.
            nameTB:     noimbre de la tabla de la base de datso a examinar.
            category:   nombre de la columna a registrar.
        
        """
        with sqlite3.connect(nameDB) as conex:
            cursor = conex.cursor()
            consult=f'''
            SELECT {category}
            FROM {nameTB}
            '''
            cursor.execute(consult)
            result = cursor.fetchall()
        return [res[0] for res in result]
    
    @staticmethod
    def Buscar_Coincidencia(searchedC:str, namesDB:tuple, coincidence:tuple):
        """
        Args:
            searched: nombre de la categoria a buscar.
            namesDB: (nameDB, nameTB)
            coincidence: (categoria, contenido)
        """
        if len(namesDB) != 2:
            raise ValueError("namesDB debe contener exactamente 2 elementos: (nameDB, nameTB)")
        
        if len(coincidence) != 2:
            raise ValueError("coincidence debe contener exactamente 2 elementos: (categoría, contenido)")
        
        with sqlite3.connect(namesDB[0]) as conex:
            cursor = conex.cursor()
            consult=f'''
            SELECT {searchedC}
            FROM {namesDB[1]}
            WHERE {coincidence[0]} = ?
            '''
            cursor.execute(consult,(coincidence[1],))
            result = cursor.fetchall()
        if len(result) == 1:
            return result[0][0]
        return [res[0] for res in result]

def main():
    def Corrections_Data_F1(nameDB, nameTB, category, name:str):
        dats = Management_SQLite.Buscar_Columna(nameDB, nameTB, category)
        dats_correction=[]
        print("========= CORRECCION ===========")
        for dat in dats:
            datC = dat
            if dat == "" or dat == None:
                dats_correction.append((dat, datC))
                continue
            print(dat)
            ans = input("Corregir?: ")
            if ans.lower() in ans_y:        
                datC = input("Ingresa la corrección: ").strip()
            dats_correction.append((dat, datC))
            os.system('cls')
        Sa_Lo_Objects.saved_object(dats_correction, name)
    
    def Corrections_Data_F2(nameDB, nameTB, category, name:str):
        dats = Sa_Lo_Objects.load_object(name)
        with sqlite3.connect(nameDB) as conn:
            cursor = conn.cursor()
            for dat in dats:
                cursor.execute(
                    f'''
                    UPDATE {nameTB}
                    SET {category} = ?
                    WHERE {category} = ?
                ''',(dat[1], dat[0])
                )
            conn.commit()

    def Correction_DF():
        indice = pd.read_excel('Indice_2.xlsx')
        titulosS = indice['NOMBRE'].to_list()
        titulosM = Management_SQLite.Buscar_Columna("Registro_Himnos.db", 'Registro_Hymn', 'title')
        titulosSN = [Management_Text.limpiar_texto1(tit) for tit in titulosS]
        titulosMN = [Management_Text.limpiar_texto1(tit) for tit in titulosM]
        
        for i, revise in enumerate(titulosS):
            if revise not in titulosM:
                coincidencias = Management_Text.search_coindicenses(titulosMN, titulosSN[i])
                for coin in coincidencias:
                    if coin[0] == 1.0:
                        indice.at[i, 'NOMBRE'] = titulosM[coin[1]]
                        break
                    ans = input(f"El himno '{titulosS[i]}' se refiere a '{titulosM[coin[1]]}'?: ")
                    if ans.lower() in ans_y:
                        # input(f"Asignar {indice.at[i, 'NOMBRE']}, el valor de {titulosM[coin[1]]}")
                        indice.at[i, 'NOMBRE'] = titulosM[coin[1]]
                        break
        indice.to_excel('Indice_2.xlsx', index=False)

    def comparate_list(lista_1, lista_2, ind):
        if len(lista_1) == len(lista_2):
            for i in range(len(lista_1)):
                if lista_1[i][ind] != lista_2[i][ind]:
                    print(f'LISTA DIFIERE EN EL ELEMENTO {i}]')
                    return False
        else:
            print("LISTAS NO TIENEN LA MISMA CANTIDAD DE ELEMENTOS.")
            return False
        return True

    # Management_SQLite.Analize_DB("Registro_General_Himnos_2.db")
    # indices = Sa_Lo_Objects.load_object('indices_himnos')
    
    
    
   
            
                  


if __name__ == "__main__":
    main() 