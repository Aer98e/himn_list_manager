import pandas as pd
from .extraction import extract_table_titles
from database_interact.queries import extract_data_db

def concatenate_dataframes(df_list, limit = 3):
    def _add_empty_columns(df_list, limit=3):
        """
        Agrupa DataFrames en listas, cada una sera una fila, y añade columnas vacías según un límite.
        Esta funcion aun mantiene los dataframes en una lista, sin concatenarlos.

        Args:
            df_list (list): Lista de DataFrames.
            limit (int): Número máximo de DataFrames por grupo.

        Returns:
            list: Lista de filas de DataFrames agrupados.
        """
        current_group = []
        grouped_dataframes = []
        limit_counter = 0

        for i, df_i in enumerate(df_list):
            df:pd.DataFrame = df_i.copy()      # Copia el DataFrame original para evitar modificarlo directamente
            df.reset_index(drop=True, inplace=True)     # Reinicia el índice del DataFrame
            limit_counter += 1

            if i < len(df_list)-1:

                if limit_counter < limit:
                    df['empty'] = None
                
                else:
                    limit_counter = 0
                    current_group.append(df)
                    grouped_dataframes.append(current_group)
                    current_group = []
                    continue
                
                current_group.append(df)
            
            else:
                current_group.append(df)
                grouped_dataframes.append(current_group)
        
        return grouped_dataframes

    def _concatenate_column(row_packet_list):
        row_list = []

        for row_pack in row_packet_list:
            result = pd.concat(row_pack, axis=1, ignore_index=True)  # Apila las columnas formando una fila
            row_list.append(result)

        return row_list

    def _concatenate_row(rows_list):
        empty_row = pd.DataFrame({col:[None] for col in rows_list[0].columns})  # Crea una fila vacía con las mismas columnas que el primer DataFrame
        with_empty_row = []
        for i, df in enumerate(rows_list):
            with_empty_row.append(df)
            if i < len(rows_list) - 1:
                with_empty_row.append(empty_row)
                
        result = pd.concat(with_empty_row, ignore_index=True)  # Apila las filas
        return result

    rows_pack = _add_empty_columns(df_list, limit)
    rows_list = _concatenate_column(rows_pack)
    df_master = _concatenate_row(rows_list)
    return df_master

def generate_news_df(cuadros):
    new_df_list=[]

    def generate_df(date):
        columns_text=[['', date, 'B & P', 'N']]
        new_df = pd.DataFrame(columns_text)
        return new_df
    
    def add_data(df, data):
        index = len(df)
        new_row_content = [index]
        for dat in data:
            if dat is not None:
                new_row_content.append(dat)
            else:
                new_row_content.append('-')
        df.loc[index] = new_row_content

    for cuadro in cuadros:
        titles_cuadro = extract_table_titles(cuadro, 1, complete=True)
        new_df = generate_df(titles_cuadro[0])

        for title in titles_cuadro[1:]:
            data_curr = extract_data_db(title)
            if data_curr:
                add_data(new_df, data_curr)
            else:
                raise ValueError(f'No se encontró el himno: {title}')
        new_df_list.append(new_df)

    return new_df_list

def main():
    pass

if __name__ =="__main__":
    main()
