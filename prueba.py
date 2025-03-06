import pandas as pd

def excel_to_dict(file_name):
    # Leer el archivo Excel
    df = pd.read_excel(f'{file_name}.xlsx')

    # Seleccionar columnas desde 'NOMBRE' en adelante
    df = df.loc[:, 'NOMBRE':]

    # Crear una lista de diccionarios, uno por cada fila
    list_of_dicts = []
    for _, row in df.iterrows():
        fila_dict = {}
        for col in df.columns:
            fila_dict[col] = row[col]
        list_of_dicts.append(fila_dict)
    
    return list_of_dicts

# Nombre del archivo (sin extensión)
archivo = 'Indice'

# Convertir y obtener la lista de diccionarios
lista_diccionarios = excel_to_dict(archivo)

# Imprimir los diccionarios
for dic in lista_diccionarios:
    print(dic)
