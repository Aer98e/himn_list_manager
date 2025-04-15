import re
import datetime
ROW_DATE = 0
COLUMN_DATE = 1

def get_correct_days(cuadros, month = None, year = None):    
    WEEKEN = ['LUNES', 'MARTES', 'MIÉRCOLES', 'JUEVES', 'VIERNES', 'SABADO', 'DOMINGO']
    def extract_days(cuadros):
        days = []
        for cuadro in cuadros:
            day = cuadro.iat[ROW_DATE, COLUMN_DATE]
            day = str(day)
            num = re.search(r'\d+', day)
            if num is not None:
                days.append(int(num[0]))
            else:
                print(f'No se pudo extraer el día de la cadena: {day}')
                # raise ValueError()
        return days

    def get_text_day(date:datetime.date):
        day = date.day
        week_num = date.weekday()
        return f'{WEEKEN[week_num]} {day:02}'

    dates = []
    # Obtener fecha actual
    today = datetime.date.today()
    year = today.year if year is None else year
    month = today.month if month is None else month
    # print(f'año:{year}, mes {month}')

    day_list = extract_days(cuadros)
    afternoon = False

    for i, day in enumerate(day_list):
        table_date = datetime.date(year, month, day)
        if table_date < today:#El igual permitira trabajar ese mismo dia o no.
            dates.append(None)
            continue
        
        text_date = get_text_day(table_date)

        if afternoon:
            text_date += ' T'
            afternoon = False
        
        elif i < len(day_list)-1 and day == day_list[i+1]:  
            text_date += ' M'
            afternoon = True
        
        dates.append(text_date)
    return dates
    
def filter_tables_day(cuadros, new_dates):
    """Crea una lista de dataframes(cuadros de himnos), usando la fecha para filtrar cuadros pasados.
    Arg:
        cuadros: Lista de dataframes(cuadros de himnos).
        new_dates: Lista de fechas filtradas. 
    Returns:
        new_cuadros: Lista de dataframes(cuadros de himnos) filtrados por fecha.
    
    Se debe tener a consideración que new_dates, debe ser filtrado con la función
    get_correct_days, y que está pensado exclusivamente para cuadros de un tipo.
    """
    new_cuadros = []
    for i in range(len(cuadros)):
        if new_dates[i] is None:
            continue
        cuadros[i].iat[ROW_DATE, COLUMN_DATE] = new_dates[i]
        new_cuadros.append(cuadros[i].copy())
    return new_cuadros

def main():
    pass

if __name__ =="__main__":
    main()
