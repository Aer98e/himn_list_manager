import pandas as pd
import Internal


def Extraer_Cuadros(file):
    data_f = pd.read_excel(file)

    cuadrosDF=[]

    for i in range(len(data_f)):
        for j in range(len(data_f.columns)):
            fila_aum = 1
            if data_f.iat[i, j] == 'R':
                continuar = True
                while continuar:
                    continuar = False
                    for col_a in range(-1, 3):
                        try:
                            revise = data_f.iat[i + fila_aum, j + col_a]
                        except:
                            print("__________________________________")
                            print("============ EXEPTION ============")
                            print("__________________________________")
                            break
                        if revise !=  "" and pd.notna(revise):
                            fila_aum += 1
                            continuar = True
                            break
                cuadrosDF.append(data_f.iloc[i:i+fila_aum, j-1:j+3].fillna("-"))

    return cuadrosDF



cuadros = Extraer_Cuadros('Himnos 2025 marzo.xlsx')

for cuadro in cuadros:
    print(cuadro)
                


