from datetime import date as dt
from typing import Self
from enum import Enum

class CapacityExceededError(Exception):
    def __init__(self, num) -> None:
        super().__init__(f"Se superó el límite({num}) de elementos.")


class Hymnal(Enum):
    BAPTIST = "Bautista"
    POPULAR = "Popular"
    NONE = ""

class _Characteristics_Hymn():
    def __init__(self) -> None:
        self.number = 0
        self.is_new = False
        self.traspose = False
        self.hymnal_use = Hymnal.NONE
        """
        Cada himno tiene un:
          'number': Que hace referecia a un himnario o lista general.
          'is_new': Nos indica si el himno se considera nuevo (cuando la congregacion recien lo está conociendo.)
          'traspose': Nos indica si el himno cambia de tonalidad durante su ejecución.
          'hymnal_use': Es específico para el caso en el que se usen otros himnarios, y se requiera saber a cual corresponde el himno.
        """

class Hymn(_Characteristics_Hymn):
    _hymns_cache = {}

    def __new__(cls, *args) -> Self:
        uniKey = tuple(args)
        if uniKey in cls._hymns_cache:
            return cls._hymns_cache[uniKey]
        instancia = super().__new__(cls)
        cls._hymns_cache[uniKey] = instancia
        return instancia

    def __init__(self, title:str, id:int) -> None:
        super().__init__()
        self.__title = title
        self.__id = id # El id no necesariamente corresponde a un indice físico
                       #  pero debe ser consistente entre multiples bases de datos.

    @property
    def title(self): return self.__title

    @property
    def id(self): return self.__id

    def __str__(self): return self.__title

    @property
    def debug_info(self):
        return f"Hymn (title:{self.title}, id:{self.id})"

class DailyList():
    size_max = 6
    def __init__(self, date_n:dt) -> None:
        self.__date: dt = date_n
        self.__hymn_list:list[Hymn] = []
        self.__full = False     # Nos indica si se alcanzo el límite de elementos.
        self.__active = True    # Util en procesamiento posterior ya que ignora este DailyList.
        self.priority = 0       # Util para ordenamiento de DailyList con misma fecha.

    def verify_size(func): #type: ignore
        def wrapper(self, *args, **kwargs):
            if self.full:
                raise CapacityExceededError(DailyList.size_max)
            func(self, *args, **kwargs) # type: ignore
            if (len(self.__hymn_list) == DailyList.size_max):
                self.__full = True
        return wrapper

    @property
    def date(self): return self.__date

    @date.setter
    def date(self, new_date: dt):
        self.__date = new_date

    @property
    def hymn_list(self): return self.__hymn_list

    @property
    def active(self): return self.__active

    @property
    def full(self): return self.__full

    # def revise_size(self):
    #     if len(self.hymn_list) == DailyList.size_max:
    #         self.__full = True
            # raise CapacityExceededError(DailyList.size_max)

    @verify_size #type: ignore
    def insert(self, index, hymn):
        self.__hymn_list.insert(index, hymn)

    def __getitem__(self, index): return self.__hymn_list[index]

    def __delitem__(self, index):
        if self.full:
            self.__full = False
        del self.__hymn_list[index]

    def __len__(self): return len(self.__hymn_list)

    def __iter__(self): return iter(self.__hymn_list)

    @verify_size #type: ignore
    def append(self, hymn:Hymn):
        self.__hymn_list.append(hymn)
    
    def reposition(self, index:int, new_index:int):
        if (index > DailyList.size_max-1 or new_index > DailyList.size_max-1):
            raise IndexError("Indice fuera de rango.")
        
        hymn = self.__hymn_list.pop(index)
        self.__hymn_list.insert(new_index, hymn)
    
    def __eq__(self, other: Self) -> bool: #type: ignore
        return self.date == other.date

    def __lt__(self, other: Self):
        if self.date == other.date:
            return self.priority < other.priority
        return self.date < other.date
    
    def __str__(self) -> str:
        return f"{self.__date} [{', '.join(str(hymn) for hymn in self.__hymn_list)}]"

class HymnSheet():
    def __init__(self, title:str) -> None:
        self.__daily_lists: list[DailyList] = []
        self.title = title

    @property
    def hymns_list(self):
        result=[]
        for list_h in self.__daily_lists:
            result.extend(list_h)
        return set(result)
    
    def __getitem__(self, index): return self.__daily_lists[index]

    def __delitem__(self, index): del self.__daily_lists[index]
        
    def __len__(self): return len(self.__daily_lists)

    def __iter__(self): return iter(self.__daily_lists)

    def _duplicate(self, daily: DailyList): # Lista cuantos DailyList hay que tengan la fecha del objeto ingresado.
        return [day for day in self.__daily_lists if day.date == daily.date]

    def append(self, daily_list:DailyList):
        duplication = self._duplicate(daily_list)
        daily_list.priority = len(duplication) + 1 if duplication else 1 

        self.__daily_lists.append(daily_list)

        self.update_positions()
        
    # def _extract_hymns(self, new_daily: DailyList):
    #     return [hymn for hymn in new_daily]

    def update_positions(self):
        self.__daily_lists.sort()

    def _reload_positions(self):
        for day in (d for d in self.__daily_lists if d.priority == 0):
            family = self._duplicate(day)
            for i, member in enumerate(family, 1):
                member.priority = i
    
    def reposition(self, index, new_index):
        if self.__daily_lists[index] == self.__daily_lists[new_index]: # Al comparar la igualdad de dos DailyList
                                                                       #  solo se tiene en cuenta la fecha.
            self.__daily_lists[index].priority = 0      # Esto indica que requiere reload_positions
            daily_list = self.__daily_lists.pop(index)
            self.__daily_lists.insert(new_index, daily_list)
            self._reload_positions()
        else:
            raise ValueError("No se puede cambiar el orden si no coincide las fechas.")

    def __str__(self) -> str:
        return f"{self.title} [\n{',\n'.join(str(day_li) for day_li in self.__daily_lists)}\n]"