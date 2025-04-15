import os

def R_BUSQUEDA():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "database", "search_ref.db")
    return db_path

def R_GENERAL():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "database", 'Registro_General_Himnos_2.db')
    return db_path

def main():
    pass

if __name__ == "__main__":
    main()

