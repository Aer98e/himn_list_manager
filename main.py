import pandas as pd
import os

ans_y=('s', 'S', '1', 'si', 'SI')

def File_Searcher():
    while True:
        file_name = input("Nombre del archivo: ").strip()
        if not os.path.isfile(f"{file_name}.xlsx"):
            input("==============ERROR DE BUSQUEDA, VUELVE A INTENTAR==================")
            os.system('cls')
        else:    
            return file_name

def Mistake_Searcher(file_name):
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
    return Hymns_List, mistake

def Correction_Query():
    ans = input("Desea corregir los datos?: ")
    return ans in ans_y


def Duplication_Record(Hymns_List):
    record = {}

    for i, himno in enumerate(Hymns_List):
        num, title, dia = himno
        if not record.get(num):
            record[num] = [i]
        else:
            record[num].append(i)
    return record

def Show_Duplications(record, Hymns_List):
    confirmation = False
    for key, value in record.items():
        if len(value) > 1:
            confirmation = True
            mess = f"El himno == {Hymns_List[value[0]][1]} == se repite {len(value)} veces, los dias:\n"
            for val in value:
                mess+=Hymns_List[val][2]
                mess+="\n"
            print(mess)
            input("Continuar...")
            os.system('cls')
    return confirmation

def main():
    file_name = File_Searcher()

    while True:
        Hymns_List, mistake = Mistake_Searcher(file_name)
        if mistake:
            if not Correction_Query():
                os.system('cls')
                break
        else:
            os.system('cls')
            break

    record = Duplication_Record(Hymns_List)    
    if not Show_Duplications(record, Hymns_List):
        input("No se encontraron duplicaciones...")
    
    
if __name__ == "__main__":
    main()