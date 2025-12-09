from .match_titles import calculate_similarity_matrix
from .match_titles import find_top_n_matches_from_matrix
from .queries import get_all_normalized_titles
from .queries import find_title_by_normalized_text
from .queries import getId_by_normTitle
from utils.helpers import normalize_text
from interact_user.general import submit_form
from interact_user.form_objects import GeneralField, EnumField
from data_processing.validations import validation_input_form


def _consult_user():
    field=GeneralField("Título del himno")
    submit_form([field])
    return field.content

def _select_user(matches:list):
    field = EnumField("Opción seleccionada (para reintentar use 'r')", options_i=['r'])

    _titles=[]
    while True:
        for i, match in enumerate(matches, 1):
            if match in _titles: continue   # Estas lineas solo son momentanias 
            _titles.append(match)           # se eliminaran al limitar titulos
                                            # normalizados únicos.
            print(f"{i}) {match}")
            field.options.append(str(i))
        
        submit_form([field])
        error = validation_input_form([field], show_errors=True)
        
        if not error:
            break

        else:
            field.options=['r']
            _titles = []


    if field.content != 'r':
        idx = int(field.content)-1
        return idx
    else:
        raise NotImplemented
        pass # Aun no implementado

        

def _find_matches(user_in):
    all_norm = get_all_normalized_titles()
    
    similarity_matrix = calculate_similarity_matrix(
        [normalize_text(user_in)], all_norm)
    return find_top_n_matches_from_matrix(similarity_matrix[0], all_norm)


def searcher_db(category='title', filter=None):    
    print("======== BUSCADOR  ========")
    user_in = _consult_user()
    _matches = [match[0] for match in _find_matches(user_in)]
    matches = [find_title_by_normalized_text(match) for match in _matches]

    idx  = _select_user(matches)

    return getId_by_normTitle(_matches[idx])

      
