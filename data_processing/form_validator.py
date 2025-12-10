from interact_user.form_objects import GeneralField, Typ, EnumField

def validation_input_form(fields:list[GeneralField], show_errors = False):
    errors = {}

    for field in fields:
        title = field.title       # Titulo del campo.
        type_in = field.type_i    # Solo se admite: text, integer, bool
        optional = field.optional # bool indicador de campo opcional
        content = field.content   # Entrada del usuario para el campo.

        if not content or str(content).lower() == 'none':
            if not optional:
                field.error = "Este campo es obligatorio."
                errors[title] = "Este campo es obligatorio."
            else:
                field.content = None
                field.error = ''

        elif type_in == Typ.Text:
            field.error = ''
            continue

        elif type_in == Typ.Integer:
            try:
                result = int(content)
                field.content = result
                field.error = ''

            except ValueError:
                errors[title] = f"El valor ({content}), no se puede convertir a entero."
                field.error = f"El valor ({content}), no se puede convertir a entero."

        elif type_in == 'bool':
            if isinstance(content, bool):
                field.error = ''
                continue

            elif content.lower() in ('y', 'yes', 'sí', '1', 'si'):
                field.content = True
                field.error = ''
                
            elif content.lower() in ('n', 'no', '0'):
                field.content = False
                field.error = ''

            else:
                errors[title] = f"La entrada {content}, no se puede interpretar como 'si' o 'no'"
                field.error = f"La entrada {content}, no se puede interpretar como 'si' o 'no'"
        
        elif type_in == "enum":
            if not isinstance(field, EnumField):
                errors[title] = f"El tipo 'enum', debe ser instancia de EnumField"
                field.error = f"El tipo 'enum', debe ser instancia de EnumField"

            elif content not in field.options:
                errors[title] = f"La entrada {content} no es valida para este campo."
                field.error = f"La entrada {content} no es valida para este campo."
            
            else:
                field.error = ''
        
        else:
            raise ValueError(f"El typo: {type_in} no está implementado")
        
    if errors and show_errors:
        print("=================== ERRORS =====================")
        for field, error in errors.items():
            print(f"Error: ({field}) [{error}]")
        print("________________________________________________")

    return errors