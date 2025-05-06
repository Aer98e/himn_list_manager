from data_processing.extraction import Extraer_Cuadros
from database_interact.match_titles import add_titles_stranges
from data_processing.scheduler import get_correct_days, filter_tables_day
from data_processing.formatting import generate_news_df, concatenate_dataframes, formating
from database_interact.frecuence_hymns import generate_list_frequencies, show_duplications, update_frequency_hymns, analysis_assistant
import sys
from database_interact.queries import catch_normalize_titles, find_title_id

def main():
    print('Extrayendo datos...')
    cuadros = Extraer_Cuadros('Himnos 2025 Abril.xlsx', 'R', -1, (-2, 0))
    
    print('Añadiendo titulos nuevos...')
    no_find = add_titles_stranges(cuadros)
    
    if no_find:
        print('No se encontraron los siguientes himnos:')
        print(no_find)

    print('Generando lista de frecuencias(hojas)...')
    frequencies = generate_list_frequencies(cuadros)

    # print('Mostrando duplicaciones...')
    # show_duplications(frequencies)
    
    # analysis_assistant(frequencies)
    # print('Actualizando datos...')

    # update_frequency_hymns(frequencies)

    new_dates = get_correct_days(cuadros)
    filter_cuadros = filter_tables_day(cuadros, new_dates)
    new_cuadros = generate_news_df(filter_cuadros)

    df_master = concatenate_dataframes(new_cuadros, limit=3)

    formating(df_master, 'Himnos Mayo')
    
def test():
    print(6%5)

if __name__ == '__main__':
    main()
