import pandas as pd
import numpy as np
from utils.helpers import limpiar_texto1

def Extraer_Cuadros(file, identifier = 'R'):
    """
    Extracts rectangular sections (cuadros) from an Excel file based on a specific identifier.
    This function reads an Excel file into a NumPy array and identifies regions of interest
    starting with a specific identifier (default is 'R'). It dynamically determines the size
    of each region and extracts it as a DataFrame.
    Args:
        file (str): The path to the Excel file to be processed.
        identifier (str, optional): The identifier used to locate the starting points of the
            regions of interest. Defaults to 'R'.
    Returns:
        list: A list of DataFrames, where each DataFrame represents a rectangular section
        (cuadro) extracted from the Excel file. Only sections with more than 2 rows are included.
    Notes:
        - The function assumes that the identifier is located in a single cell and that the
          region of interest extends downward until an empty or NaN cell is encountered.
        - The extracted regions include two columns to the left of the identifier column.
        - The function skips regions with 2 or fewer rows.
    """
    # Leer el archivo Excel en un DataFrame
    df = pd.read_excel(file, header=None)
    numpy_array = df.to_numpy()

    mask_R = numpy_array == identifier  # Crear una máscara para detectar 'R'
    cuadros = []

    # Iterar por las posiciones donde se encuentra 'R'
    for row, col in np.argwhere(mask_R):  # `np.argwhere` encuentra las posiciones de 'R'
        fila_aum = 0  # Contador de filas incluidas en el cuadro
        while True:
            # Verificar si estamos dentro del rango de filas y si la fila no está vacía
            if row + fila_aum >= numpy_array.shape[0]:  # Evitar índice fuera de rango
                break
            cell_current = numpy_array[row + fila_aum, col-1]  # Seleccionar la fila actual
            if pd.isna(cell_current) or cell_current=='':  # Si la fila está vacía, detener
                break
            fila_aum += 1  # Expandir el rango de filas hacia abajo

        # Extraer el cuadro desde 'R' y las filas dinámicas encontradas
        cuadro = numpy_array[row:row + fila_aum, col - 2:col]  # Ajustar columnas según lo necesario
        if cuadro.shape[0] > 2:
            cuadros.append(pd.DataFrame(cuadro))  # Convertir a DataFrame para procesarlo fácilmente

    return cuadros

def extract_table_titles(cuadro:pd.DataFrame, ind_column:int, norm = False, complete=False):
    """
    Extracts and optionally normalizes titles from a specified column in a DataFrame.
    Args:
        cuadro (pd.DataFrame): The DataFrame containing the data.
        ind_column (int): The index of the column from which to extract titles.
        norm (bool, optional): If True, normalizes the extracted titles using 
            `Text.limpiar_texto1`. Defaults to True.
    Returns:
        list: A list of tuples containing normalized and original titles if `norm` is True,
                or an list if `norm` is False.
    """
    resultados=[]

    num_row = 0 if complete else 1
    
    titles = cuadro.iloc[num_row:, ind_column].to_list()

    
    if norm:
        # data_norm = [(Text.limpiar_texto1(title), title) for title in titles]
        data_norm = [limpiar_texto1(title) for title in titles]
        resultados = data_norm

    else:
        return titles

    return resultados

def main():
    pass

if __name__ =="__main__":
    main()
