from .queries import find_data, load_frequencies, database_update, find_title_id
from data_processing.extraction import extract_table_titles
from utils.helpers import ans_y
from interact_user.test import show_duplications_UI
import os

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

def show_duplications(frequencies: dict, show: bool=True):
    """
    Muestra duplicaciones y devuelve una lista con los datos encontrados.

    Args:
    frequiencies (dict): Es un diccionario que usa como keys indices unicos de una base de datos, y como valores guarda el titulo(extraido de la base de datos) y las fechas(segun la hoja revisada) en las que se usa el himno.
    show (bool): Si está activo mostrará mensajes en consola hacerca de los resultados.
    """
    
    if not isinstance(frequencies, dict):
        raise ValueError("El parámetro 'frequency' debe ser un diccionario.")
    
    def showed(duplications):
        os.system('cls')
        print("\n====================== DUPLICACIONES ======================\n")
        for dupl in duplications:
            print(f"El himno '{dupl['title']}' ha sido usado {len(dupl['dates'])} veces:")
            for date in dupl['dates']:
                print(f"   - {date}")
            print("_______________________________________________________")
        print('\n===============================================================')


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
    if show:
        showed(duplications)
    # show_duplications_UI(duplications)
    # return confirmation, duplications
    return confirmation

def update_frequency_hymns(new_freq, automatic: bool = False):
    '''
    Actualiza una base de datos especifica segun los datos de frecuencia extraidos de la ultima hoja procesada.

    Args:
        new_freq (dict): Las frecuencias que se añadiran a la base de datos
        automatic (bool): Si está activo actualizará la base de datos sin realizar una consulta antes.

    Notes:
        Para asignar la frecuencia util solo se tiene en cuenta la ultima vez que fue usado el himno.
    '''
    def update_frequencies(prev_freq:list[tuple]):
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

    if not automatic:
        ans = input("Este proceso registrará los himnos de la hoja actual en la base de datos\nesto se reflejara en próximas ejecuciones.\nSolo realizar con una hoja que no tendra mas modificaciónes.\n\n¿Deseas continuar?: ").strip()
        if ans.lower() not in ans_y:
            print('No se completó la actualización de la base de datos.')
            return None
    database_update(data_update)
        
def analysis_assistant(ids_master: set):
    if not isinstance(ids_master, set):
        raise TypeError('El parametro ingresado no es de tipo Set.')
    
    def interface():
        os.system('cls')
        print("================== Registro de uso de Himnos ==================\n")
        print("\t1) Himnos que ya han sido usados en al menos las 2 ultimas hojas.")
        print("\t2) Himnos que no han sido usados en la ultima hoja.")
        print("\t3) Himnos muy poco usados.")
        print("\t4) Salir.")

        ans = input('Ingrese el número de su opción: ').strip()
        return ans
    def show_results(results: list):
        dividing:int = results[0][1]
        print("===============================================================")
        print(f'\n==== {abs(dividing)+1} Hojas ====')
        for i, res in enumerate(results):
            if dividing != res[1]:
                dividing = res[1]
                print(f'\n==== {abs(dividing)+1} Hojas ====')

            print(f'{i+1}. {res[0]}({res[1]}).')
            # print(f'{i+1}. {res[0]}.')
        print("===============================================================")

    #   fq = frecucencia || ut = util || rl = real
    prev_freq = load_frequencies()
    dict_prev_freq = {dat[0]: {'freq_util':dat[1], 'freq_real':dat[2]} for dat in prev_freq}
    
    fq_rl = [(id, freq['freq_real']) for id, freq in dict_prev_freq.items()]
    fq_rl.sort(key=lambda x:x[1])

    id_sheet = [id for id in dict_prev_freq if id in ids_master]
    id_used = list(filter(lambda id :dict_prev_freq[id]['freq_util'] > 1, id_sheet))
    fq_ut_used = [dict_prev_freq[id]['freq_util'] for id in id_used]

    id_no_sheet = [id for id in dict_prev_freq if id not in ids_master]
    id_no_used = list(filter(lambda id :dict_prev_freq[id]['freq_util'] < 1, id_no_sheet))
    fq_ut_no_used = [dict_prev_freq[id]['freq_util'] for id in id_no_used]

    
    while True:
        ans = interface()
        if ans == '1':
            titles = find_title_id(id_used)
            result = list(zip(titles, fq_ut_used))
            result.sort(key=lambda x:x[1], reverse=True)

        elif ans == '2':
            titles = find_title_id(id_no_used)
            result = list(zip(titles, fq_ut_no_used))
            result.sort(key=lambda x:x[1])
            
        elif ans == '3':
            limit = 25
            titles = find_title_id([dat[0] for dat in fq_rl[:limit]])
            result = list(zip(titles, [dat[1] for dat in fq_rl[:limit]]))
        
        elif ans == '4':
            break

        else:
            print('\n\n\t=_=_= ¡Error! =_=_= Opción Invalida =_=_= Intente Nuevamente =_=_=\n\n')
            continue

        show_results(result)
        
        input('Presione una tecla para continuar...')
        # ans_2 = input('\n\tDesea finalizar?: ').strip()
        # if ans_2.lower()  in ans_y:
        #     break

   

    
    
        # -Mostrar que himnos estoy usando y ya he usado en las dos ultimas hojas/podriamos_
        # tener prioridad en los himnos que se repiten mas de una vez en la hoja actual.
        # -Mostrar que himnos no he usado desde la anterior vez.
        # -Mostrar himnos por debajo del promedio(no usados).
