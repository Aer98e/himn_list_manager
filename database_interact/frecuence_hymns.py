from .file_names import R_BUSQUEDA
from .queries import find_title, find_data, load_frequencies, database_update
from data_processing.extraction import extract_table_titles
from utils.helpers import ans_y

def generate_list_frequencies(data_tables_list):
    TITLE_COLUMN = 1
    ID_IDX = 0
    TITLE_IDX = 1

    frequencies_table = {}
    for data_table in data_tables_list:
        data = extract_table_titles(data_table, TITLE_COLUMN, norm=True, complete=True)
        date = data[0]
        for title_norm in data[1:]:
            hymn_data = find_data(title_norm, ['id', 'titulo'])
            if hymn_data:
                id_hymn = hymn_data[ID_IDX]
                if hymn_data[ID_IDX] in frequencies_table:
                    frequencies_table[id_hymn]['dates'].append(date)
                else:
                    frequencies_table[id_hymn] = {
                        'title':hymn_data[TITLE_IDX],
                        'dates':[date]
                    }
            else:
                print(f"Advertencia: No se encontró información para '{title_norm}'")
    return frequencies_table

'''
La estructura de frecuences es:
    {
    id_himno:{
        'title': titulo_himno
        'dates': lista_fechas
        }
        ...
    }
'''

def show_duplications(frequencies):
    """
    Muestra duplicaciones y devuelve una lista con los datos encontrados.
    """
    
    if not isinstance(frequencies, dict):
        raise ValueError("El parámetro 'frequency' debe ser un diccionario.")
    
    confirmation = False
    duplications = []
    
    for id_hymn, data in frequencies.items():
        times = len(data['dates'])
        if times > 1:
            confirmation = True
            title = data['title']
            
            duplications.append({
                "id": id_hymn,
                "title": title,
                "times_used": times,
                "dates": data['dates']
            })
            
            print(f"El himno '{title}' ha sido usado {times} veces:")
            for date in data['dates']:
                print(f"   - {date}")
            print("_______________________________________________________")
    
    # return confirmation, duplications
    return confirmation

def update_frequency_hymns(new_freq):
    def update_frequencies(prev_freq):
        ID_IDX = 0
        FREQ_UTIL_IDX = 1
        FREQ_REAL_IDX = 2 

        data_update = []

        for freq_hymn in prev_freq:
            id_hymn = freq_hymn[ID_IDX]
            freq_util = freq_hymn[FREQ_UTIL_IDX]
            freq_real = freq_hymn[FREQ_REAL_IDX]

            if id_hymn in new_freq:
                freq_util = 1 if freq_util < 0 else freq_util+1
                freq_real += len(new_freq[id_hymn]['dates'])

            else:
                freq_util = 0 if freq_util > 0 else freq_util-1

            data_update.append((freq_util, freq_real, id_hymn))
        return data_update
    
    prev_freq = load_frequencies()
    data_update = update_frequencies(prev_freq)
    ans = input("Este proceso modificará la base de datos.\n ¿Deseas continuar?: ").strip()
    if ans.lower() in ans_y:
        database_update(data_update)
    else:
        print('No se completó la actualización de la base de datos.')
