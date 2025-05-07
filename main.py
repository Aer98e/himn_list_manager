from data_processing.extraction import Extraer_Cuadros
from database_interact.match_titles import add_titles_stranges
from data_processing.scheduler import get_correct_days, filter_tables_day
from data_processing.formatting import generate_news_df, concatenate_dataframes, formating
from database_interact.frecuence_hymns import generate_list_frequencies, show_duplications, update_frequency_hymns, analysis_assistant
from interact_user.general import select_file, saved_file
from utils.helpers import present_new_file, ans_y
import sys
import os
from database_interact.queries import catch_normalize_titles, find_title_id

def main():
    print('\nExtrayendo datos...')
    path_file = select_file()
    if not path_file:
        return 0
    while True:
        cuadros = Extraer_Cuadros(path_file, 'R', -1, (-2, 0))
        
        print('\nRegistrando titulos desconocidos...')
        no_find = add_titles_stranges(cuadros)
        
        if no_find:
            print('\n=============== DATOS INEXISTENTES ===============')
            print('No se encontraron los siguientes himnos:')
            print(no_find)
            print('_________________________________________________')
            print('Para continuar con el procesamiento se debe corregir manualmente.\n',
                  'Una vez corregido se puede continuar.')
            ans = input('Desea continuar?: ').strip()
            if ans not in ans_y:
                return 0
            else:
                continue

        print('\nRegistrando himnos del archivo...')
        frequencies = generate_list_frequencies(cuadros)

        print('\nBuscando duplicaciones...')
        duplications = show_duplications(frequencies)
        if not duplications:
            print('No se encontro repeticion de himnos.')
        
        reinitialize = analysis_assistant(set(frequencies.keys()))
        if not reinitialize:
            break
    
    print("\nRegistrando hoja de himnos...")
    update_frequency_hymns(frequencies)

    print("\nOrganizando datos...")
    new_dates = get_correct_days(cuadros)
    filter_cuadros = filter_tables_day(cuadros, new_dates)
    new_cuadros = generate_news_df(filter_cuadros)
    df_master = concatenate_dataframes(new_cuadros, limit=3)

    name_sheet = input("Que titulo llevará la hoja de himnos(no archivo): ").strip()

    print("\nGenerando nuevo archivo...")
    formating(df_master, name_sheet)

    path_new = saved_file()
    present_new_file(path_new)

    
def test():
    print(6%5)

if __name__ == '__main__':
    main()
