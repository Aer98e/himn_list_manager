import pandas as pd
import numpy as np
from utils.helpers import limpiar_texto1

def Extraer_Cuadros(file, identifier:str, review:int, catch:tuple[int, int]):
    """
    Extracts rectangular sections (cuadros) from an Excel file based on a specific identifier.
    This function reads an Excel file into a NumPy array and identifies regions of interest
    starting with a specific identifier (default is 'R'). It dynamically determines the size
    of each region and extracts it as a DataFrame.
    Args:
        file (str): The path to the Excel file to be processed.
        identifier (str, optional): The identifier used to locate the starting points of the
            regions of interest.
        review (int): Its the row to verified(depending identifier).
        catch (tuple): Its selected region(depending identifier) using idx for columns(no incluye el ultimo indice).
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
            cell_current = numpy_array[row + fila_aum, col+review]  # Seleccionar la fila actual
            if pd.isna(cell_current) or cell_current=='':  # Si la fila está vacía, detener
                break
            fila_aum += 1  # Expandir el rango de filas hacia abajo

        # Extraer el cuadro desde 'R' y las filas dinámicas encontradas
        cuadro = numpy_array[row:row + fila_aum, col+catch[0]:col+catch[1]]  # Ajustar columnas según lo necesario
        if cuadro.shape[0] > 2:
            cuadros.append(pd.DataFrame(cuadro))  # Convertir a DataFrame para procesarlo fácilmente

    return cuadros

def extract_table_titles(cuadro: pd.DataFrame, ind_column: int, norm: bool = False, complete: bool=False):
    """
    Extracts and optionally normalizes titles from a specified column in a DataFrame.
    Args:
        cuadro (pd.DataFrame): The DataFrame containing the data.
        ind_column (int): The index of the column from which to extract titles.
        norm (bool, optional): If True, normalizes the extracted titles using 
            `Text.limpiar_texto1`. Defaults to True.
        complete(bool, optional): Id True, add date to return
    Returns:
        list: A list of tuples containing normalized and original titles if `norm` is True,
                or an list if `norm` is False.
    """
    resultados=[]

    num_row = 0 if complete else 1 #Esto es para incluir o no la fecha en al lista
    
    titles = cuadro.iloc[num_row:, ind_column].to_list()
    
    if norm:
        # data_norm = [(Text.limpiar_texto1(title), title) for title in titles]
        data_norm = list(map(limpiar_texto1, titles))
        if complete:
            data_norm[0] = titles[0]
        return data_norm
    else:
        return titles

def find_pattern(matriz_np: np.ndarray, patron: str):
    """Encuentra índices donde aparece el patrón en una matriz NumPy."""
    indices = np.argwhere(np.char.find(matriz_np, patron) >= 0)
    return indices

def clear_pattern(df: pd.DataFrame, indices: np.ndarray, patron: str):
    """Elimina el patrón de las celdas indicadas por los índices en el DataFrame."""
    for i, j in indices:
        df.iat[i, j] = df.iat[i, j].replace(patron, "")

def capture_change_idx(df_master:pd.DataFrame) -> dict[str, np.ndarray]:
    def clear_dataframe(df:pd.DataFrame, indices:dict, patterns:dict):
        for key, pattern in patterns.items():
            clear_pattern(df, indices[key], pattern)

    patterns={'red':'::R',
              'green':'::V',
              'new':'::N',
              'transpose':'::U',
              'sunday':'::D',
              'other_day':'::O'}
    
    matriz_np = df_master.copy().to_numpy(dtype=str)

    idx_patterns={}
    for key, pattern in patterns.items():
        idx_patterns[key] = find_pattern(matriz_np, pattern)
    
    clear_dataframe(df_master, idx_patterns, patterns)

    idx_patterns['transpose'][:, 1]-=3

    union=np.vstack((idx_patterns['new'], idx_patterns['new']+[0, -2]))
    idx_patterns['new']=union

    return idx_patterns

def main():
    pass

if __name__ =="__main__":
    main()
