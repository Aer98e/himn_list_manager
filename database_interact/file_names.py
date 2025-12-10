import os
from pathlib import Path

def check_location(fun):
    def wrapper():
        file = Path('database')
        if file.exists():
            return fun()
        else:
            raise FileNotFoundError
    return wrapper

@check_location
def R_BUSQUEDA():
    return "database/search_ref.db"

@check_location
def R_GENERAL():
    return "database/Registro_General_Himnos_2.db"

def main():
    pass

if __name__ == "__main__":
    main()

