import sqlite3
from interact_user.general import submit_form
from data_processing.form_validator import validation_input_form
from utils.helpers import load_config_from_json


def question_user(question:str, tp = None):
    ans = input(question).strip()
    if not tp:
        return ans
    try:
        return tp(ans)
    except ValueError as e:
        print("La conversión falló, vuelva a intentar.")

class Register_Himns():
    path_database="./database/search_ref.db"#añadir que verifique ruta antes al crear.
    def __init__(self) -> None:
        pass

    @classmethod
    def _insert(cls, query:str, params:tuple):
        result = False
        try:
            with sqlite3.connect(cls.path_database) as conn:
                conn.execute(query, params or ())
                conn.commit()
                result = True
        
        except sqlite3.Error as e:
            #Agregar regitro para gaurdar log.
            result = False

        return result

    def add_himn(self, data:dict):
        dat_hymn = load_config_from_json("form_himn")

        while True: # Cambiar para que solo sea un número limitado de veces
            submit_form(dat_hymn)
            errors = validation_input_form(dat_hymn, show_errors=True)
            
            if errors:
                input("Presione enter para continuar...")
                continue
            
            else:
                print("Ingreso exitoso de los datos.")
                break
        return dat_hymn

        #titulo TEXT NOT NULL, 
        #numH_gen INTEGER, 
        #numH_aux INTEGER,
        #es_nuevo INTEGER,
        #sube_tono INTEGER,
        #id_himnario INTEGER,
        #modificado TEXT NOT NULL,

def test():
    dat_hymn = load_config_from_json("form_himn")
    
    print(dat_hymn)

    while True: # Cambiar para que solo sea un número limitado de veces
        submit_form(dat_hymn)
        errors = validation_input_form(dat_hymn, show_errors=True)
        
        if errors:
            input("Presione enter para continuar...")
            continue
        
        else:
            print("Ingreso exitoso de los datos.")
            break
    return dat_hymn
        