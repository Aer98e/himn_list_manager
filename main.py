import pandas as pd
import os
import Internal




def File_Searcher():
    while True:
        file_name = input("Nombre del archivo: ").strip()
        if not os.path.isfile(f"{file_name}.xlsx"):
            input("==============ERROR DE BUSQUEDA, VUELVE A INTENTAR==================")
            os.system('cls')
        else:    
            return file_name

def Mistake_Searcher(file_name, l_ind):
    mistake = False
    df = pd.read_excel(f'{file_name}.xlsx')
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

def Correction_Query(ans_y):
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

def Record_Status_Updater(record_master:dict, record:dict):
    for key in record_master:
        if key in record:
            repetitions = len(record[key])
            record_master[key][1] += repetitions
            record_master[key][0] = 1 if record_master[key][0] < 0 else record_master[key][0] + 1
        else:
            record_master[key][0] = 0 if record_master[key][0] > 0 else record_master[key][0] - 1
    return record_master

def Show_Record_Statistic(l_ind, record_master):
    statistic = {'used':[], 'not_used':[]}

    def Filtering_According_Incidents():
        for element in record_master:
            incidence = record_master[element][0]
            title = l_ind[l_ind['N'] == element]['NOMBRE'].values[0]

            if incidence < -1:
                text = f"El himno {title} se no se ha usado en las {incidence * -1} ultimas hojas"
                statistic['not_used'].append(text)
            
            elif incidence > 1:
                text = f"El himno {title} ya se ha usado en las {incidence} ultimas hojas"
                statistic['used'].append(text)
    
    def Printer_ST():
        if not statistic['used'] and not statistic['not_used']:
            print("No hay descompensacion en el uso de los himnos")
            return None
        
        print("===========ESTADÍSTICAS============\n")
        for text in statistic['used']:
            print(text)
        print()
        for text in statistic['not_used']:
            print(text)

    Filtering_According_Incidents()
    Printer_ST()

def Record_Update_Query(ans_y, record_master):
    ans = input("Desea hacer una actualizacion del registro maestro?: ").strip()
    if ans in ans_y:
        Internal.Update_Record(record_master)

def main():
    ans_y=('s', 'S', '1', 'si', 'SI')
    Frecuency_Master_Record = Internal.Read_Record()
    file_name = File_Searcher()
    l_ind = pd.read_excel("Indice.xlsx")

    while True:
        Hymns_List, mistake = Mistake_Searcher(file_name, l_ind)
        if mistake:
            if not Correction_Query(ans_y):
                os.system('cls')
                break
        else:
            os.system('cls')
            break

    record = Duplication_Record(Hymns_List)    
    if not Show_Duplications(record, Hymns_List):
        input("No se encontraron duplicaciones...")

    record_master = Record_Status_Updater(Frecuency_Master_Record.copy(),record)
    Show_Record_Statistic(l_ind, record_master)
    Record_Update_Query(ans_y, record_master)

    
if __name__ == "__main__":
    main()