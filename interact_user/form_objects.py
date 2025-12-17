from enum import Enum

class State(Enum):
    ERROR = False
    OK = True
    NONE = None

class Typ(Enum):
    Text = 'text'
    Bool = 'bool'
    Integer = 'integer'
    Option = 'enum'

class GeneralField():
    def __init__(self, title_i:str, optional_i=False, cnt_i='', type=Typ.Text) -> None:
        self.title = title_i
        self.type_i = type
        self.optional = optional_i
        self._content = [cnt_i]
        self.state:State = State.NONE
        self._error = ''

    @property
    def error(self):
        return self._error
    
    @error.setter
    def error(self, new_error):
        if new_error == '':
            self.state = State.OK
        else:
            self.state = State.ERROR
        
        self._error = new_error

    @property
    def content(self):
        return self._content[0]
    
    @content.setter
    def content(self, new_val):
        self._content.pop()
        self._content.append(new_val)

class EnumField(GeneralField):
    def __init__(self, title_i: str, options_i:list,
                 optional_i=False, cnt_i='') -> None:
        super().__init__(title_i, optional_i, cnt_i)
        self.type_i = Typ.Option
        self.options = []
        self.options.extend(options_i)

