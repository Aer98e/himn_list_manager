from data_processing.extraction import Extraer_Cuadros
from database_interact.match_titles import add_titles_stranges
from data_processing.scheduler import get_correct_days, filter_tables_day
from data_processing.formatting import generate_news_df, concatenate_dataframes
from database_interact.frecuence_hymns import generate_list_frecuences, show_duplications
import sys

def main():
    cuadros = Extraer_Cuadros('Himnos 2025 Abril.xlsx')
    no_find = add_titles_stranges(cuadros)
    if no_find:
        print('No se encontraron los siguientes himnos:')
        print(no_find)
    
    frequencies = generate_list_frecuences(cuadros)
    show_duplications(frequencies)

    sys.exit()
    new_dates = get_correct_days(cuadros)
    filter_cuadros = filter_tables_day(cuadros, new_dates)
    new_cuadros = generate_news_df(filter_cuadros)

    df_master = concatenate_dataframes(new_cuadros, limit=3)
    df_master.to_excel('pruebas_3.xlsx', index=False, header=False)

if __name__ == '__main__':
    main()
