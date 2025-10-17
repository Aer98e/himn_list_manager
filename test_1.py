from interact_user.general_objects import Hymn, DailyList, HymnSheet
from datetime import date
import database_interact.queries as qu
import data_processing.extraction as ex



def generate_sheet(tables, year=None, month=None):
    today = date.today()
    y = today.year if not year else year
    m = today.month if not month else month
    sheet = HymnSheet("New page")

    for table in tables:
        result = ex.extract_table_titles(table, normalize=True, include_date=True)

        day_li = DailyList(date(y, m, int(result[0])))

        for t in result[1:]:
            result = qu.find_data_by_normalized_title(t, ["id", "titulo"])
            if result:
                himn = Hymn(result[1], result[0])
                day_li.append(himn)
        
        sheet.append(day_li)
    return sheet