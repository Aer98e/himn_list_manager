import pandas as pd
import Internal
import sys
import recicle
import sqlite3
from  difflib import SequenceMatcher


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
                        except:
                            print("__________________________________")
                            print("============ EXEPTION ============")
                            print("__________________________________")
                            break
                        if revise !=  "" and pd.notna(revise):
                            fila_aum += 1
                            continuar = True
                            break
                cuadrosDF.append(data_f.iloc[i:i+fila_aum, j-1:j+3].fillna("-"))

    return cuadrosDF


def Extraer_titulos_cuadro(cuadro, norm = True):
    resultados=[]
    if len(cuadro)<2:
        return None
    
    for i in range(1,len(cuadro)):
        resultados.append(cuadro.iat[i,0])
    
    if norm:
        data_norm = [(recicle.Management_Text.limpiar_texto1(res), res) for res in resultados]
        resultados = data_norm

    return resultados


def datos_busqueda():
    with recicle.sqlite3.connect(R_BUSQUEDA) as conn:
        cursor = conn.cursor()
        cursor.execute(
        '''
        SELECT Indice_busqueda.titulo_norm, Indice_busqueda.id, Himnos.titulo
        FROM Indice_busqueda
        JOIN Himnos ON Indice_Busqueda.id_himno = Himnos.id
        ''')
        resultados = cursor.fetchall()
    return resultados

R_GENERAL = 'Registro_General_Himnos_2.db'
R_BUSQUEDA = 'search_ref.db'
TITULO = 2
TITULO_NORM = 0
INDICE = 1


cuadros = Extraer_Cuadros('Himnos 2025 marzo.xlsx')

li_tit_S = Extraer_titulos_cuadro(cuadros[1])

li_dat_M = datos_busqueda()




#El proposito sera encontrar el indice de cada uno de los himnos.
for title_s in li_tit_S:
    coincidences = []
    print(f"::: Buscando ::: {title_s[1]}")
    find = False
    for m in li_dat_M:
        if title_s[0] == m[TITULO_NORM]:
            print("Encontrado...\n")
            find = True
            break
            #REvisar que los datos sean correctos
        else:
            simil = SequenceMatcher(None, m[TITULO_NORM], title_s[0]).ratio()
            coincidences.append((simil, m[TITULO]))
    if not find:
        print(f'El himno {title_s[1]} no se encontró.')
        coincidences_ord = sorted(coincidences, key = lambda x : x[0], reverse = True)
        for i in range(5):
            #Considerar ya no preguntar para coincidencais del 0.8
            print(f'El titulo buscado podria referirse a ({coincidences_ord[i]})')






