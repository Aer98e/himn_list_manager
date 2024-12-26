import pandas as pd
import os

ans_y=('s', 'S', '1')

def File_Searcher():
    while True:
        file_name = input("Nombre del archivo: ").strip()
        if not os.path.isfile(f"{file_name}.xlsx"):
            input("==============ERROR DE BUSQUEDA, VUELVE A INTENTAR==================")
            os.system('cls')
        else:    
            return file_name


while True:
    mistake = False
    df = pd.read_excel(f'{file_name}.xlsx')
    l_ind = pd.read_excel("Indice.xlsx")
    df = df.fillna('')
    l_ind = l_ind.fillna('')
    
    Hymns_List = []
    for idx, cell in df.iterrows():
        for col in df.columns:
            if cell[col]=='R':
                col_idx=df.columns.get_loc(col)
                pos_index = 1
                day = df.at[idx, df.columns[col_idx-1]]

                while True:
                    index = df.at[idx+pos_index, df.columns[col_idx - 2]]
                    title = df.at[idx+pos_index, df.columns[col_idx - 1]]
                    
                    if index and title and pd.notna(title) and pd.notna(index):   
                        nR = df.at[idx+pos_index, col]
                        nV = df.at[idx+pos_index, df.columns[col_idx + 1]]
                        nN = df.at[idx+pos_index, df.columns[col_idx + 2]]
                        
                        try:
                            lR = l_ind[l_ind['NOMBRE'] == title]['R'].values[0]
                            lV = l_ind[l_ind['NOMBRE'] == title]['V'].values[0]
                            lN = l_ind[l_ind['NOMBRE'] == title]['N'].values[0]

                        except:
                            print(f"No se encontró el himno \"{title}\", en la lista.")
                            try:
                                name = l_ind[l_ind['N'] == nN]['NOMBRE'].values[0]
                                print(f"Es probable que el titulo buscado sea: {name}.")

                            except:
                                pass
                    
                        if nR != lR or nV != lV or nN != lN:
                            nR = lR
                            nV = lV
                            nN = lN
                            mistake = True
                            print(f"Error --- {day} -> {title}: {nR} {nV} {nN}\n")
                        
                        Hymns_List.append((nN, title, day))
                        pos_index = pos_index + 1
                        nR = nV = nN = lR = lV = lN = 0

                        if len(df)<=idx+pos_index:
                            break
                    else:
                        break
    if mistake:
        ans = input("Desea corregir los datos?: ")
        if ans not in ans_y:
            os.system('cls')
            break
    else:
        os.system('cls')
        break
    os.system('cls')
    


Registro_Times = {}

for i, himno in enumerate(Hymns_List):
    num, title, dia = himno
    if not Registro_Times.get(num):
        Registro_Times[num] = [i]
    else:
        Registro_Times[num].append(i)

for key, value in Registro_Times.items():
    if len(value) > 1:
        mess = f"El himno == {Hymns_List[value[0]][1]} == se repite {len(value)} veces, los dias:\n"
        for val in value:
            mess+=Hymns_List[val][2]
            mess+="\n"
        print(mess)
        input("Continuar...")
        os.system('cls')
