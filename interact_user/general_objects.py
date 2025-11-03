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

class Characteristics_Hymn():
    def __init__(self) -> None:
        self.number = 0
        self.is_new = False
        self.traspose = False
        self.hymnal_use = Hymnal.NONE

class Hymn(Characteristics_Hymn):
    _hymns_cache = {}

    def __new__(cls, *args) -> Self:
        clave = tuple(args)
        if clave in cls._hymns_cache:
            return cls._hymns_cache[clave]
        instancia = super().__new__(cls)
        cls._hymns_cache[clave] = instancia
        return instancia

    def __init__(self, title:str, id:int) -> None:
        super().__init__()
        self.__title = title
        self.__id = id

    @property
    def title(self): return self.__title

    @property
    def id(self): return self.__id

    def __str__(self): return self.__title

    @property
    def debug_info(self):
        return f"Hymn(title:{self.title}, id:{self.id})"
    
    # def __eq__(self, value:Self) -> bool: #type: ignore
    #     return self.id == value.id
    
    # def __hash__(self) -> int:
    #     return self.id
        

class DailyList():
    size_max = 6
    def __init__(self, date_n:dt) -> None:
        self.__date: dt = date_n
        self.__hymn_list:list[Hymn] = []
        self.__full = False
        self.__active = True
        self.priority = 0

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

    def revise_size(self):
        if len(self.hymn_list) == DailyList.size_max:
            self.__full = True
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
    def append(self, hymn:Hymn):#Agregar decorador de verificacion de rango
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

    def _duplicate(self, daily: DailyList):
        return [day for day in self.__daily_lists if day.date == daily.date]

    def append(self, daily_list:DailyList):
        duplication = self._duplicate(daily_list)
        daily_list.priority = len(duplication) + 1 if duplication else 1 

        self.__daily_lists.append(daily_list)

        self.update_positions()
        
    def _extract_hymns(self, new_daily: DailyList):
        return [hymn for hymn in new_daily]

    def update_positions(self):
        self.__daily_lists.sort()
    
    def reposition(self, index, new_index):
        if self.__daily_lists[index] == self.__daily_lists[new_index]:
            self.__daily_lists[index].priority = 0
            daily_list = self.__daily_lists.pop(index)
            self.__daily_lists.insert(new_index, daily_list)
            self._reload_positions()
        else:
            raise ValueError("No se puedo cambiar el orden si no coincide las fechas.")
    
    def _reload_positions(self):
        for day in (d for d in self.__daily_lists if d.priority == 0):
            family = self._duplicate(day)
            for i, member in enumerate(family, 1):
                member.priority = i

    def __str__(self) -> str:
        return f"{self.title} [\n{',\n'.join(str(day_li) for day_li in self.__daily_lists)}\n]"