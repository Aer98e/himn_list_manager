import pandas as pd
import Internal
import sys
import recicle as rec
import sqlite3
from  difflib import SequenceMatcher
from recicle import Management_Text as Text
from recicle import Management_SQLite as M_SQ
import datetime
from os import system
import re

R_GENERAL = 'Registro_General_Himnos_2.db'
R_BUSQUEDA = 'search_ref.db'
COL_TIT = 0


def Extraer_Cuadros(file):
    data_f = pd.read_excel(file)

    cuadrosDF=[]

    for i in range(len(data_f)):
        for j in range(len(data_f.columns)):
            fila_aum = 1
            if data_f.iat[i, j] == 'R':
                continuar = True
                while continuar:
                    continuar = False
                    for col_a in range(-1, 3):
                        try:
                            revise = data_f.iat[i + fila_aum, j + col_a]
                        except IndexError:
                            print(f"Índice fuera de rango en la fila {i + fila_aum}, columna {j + col_a}")
                            break
                        if revise !=  "" and pd.notna(revise):
                            fila_aum += 1
                            continuar = True
                            break
                cuadrosDF.append(data_f.iloc[i:i+fila_aum, j-1:j+3].fillna("-"))

    return [cuadro for cuadro in cuadrosDF if len(cuadro) > 2]

def extract_table_titles(cuadro, norm = True):
    resultados=[]
    if len(cuadro)<2:
        return None
    
    for i in range(1, len(cuadro)):
        resultados.append(cuadro.iat[i,COL_TIT])
    
    if norm:
        data_norm = [(Text.limpiar_texto1(res), res) for res in resultados]
        resultados = data_norm

    return resultados

def find_simil(simil):
    with sqlite3.connect(R_BUSQUEDA) as conn:
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

def update_search_list(title_norm, title_m):
    with sqlite3.connect(R_BUSQUEDA) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM Himnos WHERE titulo = ?', (title_m,))
        indice = cursor.fetchone()
        if indice is not None:
            cursor.execute('INSERT INTO Indice_busqueda(id_himno, titulo_norm) VALUES(?, ?)', (indice[0], title_norm))
            conn.commit()
        else:
            print(f'No se encontro :: {title_m}')

def add_titles_stranges(cuadros):

    li_tit_m = M_SQ.Buscar_Columna(R_BUSQUEDA, 'Indice_busqueda', 'titulo_norm')

    for cuadro in cuadros:
        system('cls')

        if len(cuadro) < 2:#Para no buscar en una tabla vacia de menos de 2 filas
            continue

        for fila in range(1, len(cuadro)):
            coincidences = []
            title_s = cuadro.iat[fila, COL_TIT]
            title_s_norm = Text.limpiar_texto1(title_s)

            # print(f"::: Buscando ::: {title_s}")
            find = False

            for title_m_norm in li_tit_m:
                if title_s_norm == title_m_norm:
                    # print("Encontrado...\n")
                    find = True
                    break
                    
                else:
                    simil = SequenceMatcher(None, title_m_norm, title_s_norm).ratio()
                    coincidences.append((simil, title_m_norm))

            if not find:
                print(f'El himno {title_s} no se encontró.')
                coincidences_ord = sorted(coincidences, key = lambda x : x[0], reverse = True)
                for coin in coincidences_ord[0:5]:
                    #Considerar ya no preguntar para coincidencais del 0.8
                    tit_sim = find_simil(coin[1])

                    print('==== ¿Son similares? ====')
                    print(f'--{title_s}')
                    print(f'--{tit_sim}')
                    ans = input('_________________(S/N): ').strip()

                    if ans.lower() in rec.ans_y:
                        update_search_list(title_s_norm, tit_sim)
                        cuadro.iat[fila, COL_TIT] = tit_sim
                        break

def correction_days(cuadros, month = None, year = None):
    def _extract_days(cuadros):
        days = []
        for cuadro in cuadros:
            day = cuadro.iat[0, 0]
            day = str(day)
            num = re.search(r'\d+', day)
            if num is not None:
                days.append(int(num[0]))
            else:
                print('Un cuadro no tiene fecha.')
        return days

    dates = []

    weeken=['LUNES', 'MARTES', 'MIÉRCOLES', 'JUEVES', 'VIERNES', 'SABADO', 'DOMINGO']
    today = datetime.date.today()
    

    year = today.year if year is None else year
    month = today.month if month is None else month
    print(f'año:{year}, mes {month}')

    day_list = _extract_days(cuadros)
    afternoon = False

    for i, day in enumerate(day_list):
        table_date = datetime.date(year, month, day)
        if table_date < today:#El igual permitira trabajar ese mismo dia o no.
            dates.append(None)
        else:
            day_ind = table_date.weekday()
            temp_date = f'{weeken[day_ind]} {day:02}'

            if afternoon:
                dates.append(f'{temp_date} T')
                afternoon = False
            
            elif i < len(day_list)-1:
                if day == day_list[i+1]:
                    day == day_list[i+1]
                    dates.append(f'{temp_date} M')
                    afternoon = True
                    continue
                dates.append(temp_date)
            
            else:
                dates.append(temp_date)
    return dates
    
def filter_tables_day(cuadros, corrector):
    cuadros_new=[]
    for i in range(len(cuadros)):
        if corrector[i] is None:
            continue
        cuadros[i].iat[0, 0] = corrector[i]
        cuadros_new.append(cuadros[i].copy())
    return cuadros_new

def concatenate_dataframes(df_list, limit = 3):
    def _add_empty_columns(df_list, limit=3):
        """
        Agrupa DataFrames en listas y añade columnas vacías según un límite.

        Args:
            df_list (list): Lista de DataFrames.
            limit (int): Número máximo de DataFrames por grupo.

        Returns:
            list: Lista de listas de DataFrames agrupados.
        """
        current_group = []
        grouped_dataframes = []
        group_counter = 0

        for i, df in enumerate(df_list):
            df = df.copy()
            df.reset_index(drop=True, inplace=True)  # Reinicia el índice del DataFrame
             # Copia el DataFrame original para evitar modificarlo directamente
            group_counter+=1

            if i < len(df_list)-1:

                if group_counter < limit:
                    df['empty'] = None
                
                else:
                    group_counter = 0
                    current_group.append(df)
                    grouped_dataframes.append(current_group)
                    current_group = []
                    continue
                
                current_group.append(df)
            
            else:
                current_group.append(df)
                grouped_dataframes.append(current_group)
        
        return grouped_dataframes

    def _concatenate_column(pack_row):
        rows_list = []

        for row in pack_row:
            result = pd.concat(row, axis=1, ignore_index=True)  # Apila las columnas
            rows_list.append(result)

        return rows_list

    def _concatenate_row(rows_list):
        empty_row = pd.DataFrame({col:[None] for col in rows_list[0].columns})  # Crea una fila vacía con las mismas columnas que el primer DataFrame
        with_empty_row = []
        for i, df in enumerate(rows_list):
            with_empty_row.append(df)
            if i < len(rows_list) - 1:
                with_empty_row.append(empty_row)
                
        result = pd.concat(with_empty_row, ignore_index=True)  # Apila las filas
        return result

    pack_rows = _add_empty_columns(df_list, limit)
    rows_list = _concatenate_column(pack_rows)
    # for row in rows_list:
    #     print(row)
    #     print('----------------------------------')
    df_master = _concatenate_row(rows_list)
    return df_master


def main():
    cuadros = Extraer_Cuadros('Himnos 2025 marzo.xlsx')
    result = correction_days(cuadros)
    cuadros_new = filter_tables_day(cuadros, result)
    df_master = concatenate_dataframes(cuadros_new, limit=3)

    df_master = df_master.fillna("-")

    print(df_master)

    
    


    




if __name__ == '__main__':
    main()