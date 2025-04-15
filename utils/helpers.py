import re
import unicodedata

ans_y = ('y', 's', '1', 'yes', 'si')

def limpiar_texto1(texto:str):
    texto = texto.lower()
    texto = re.sub(r'[^\w\s]', '', texto)
    texto = re.sub(r'\s+', '', texto)
    texto = unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('utf-8')
    
    return texto
def main():
    pass

if __name__ =="__main__":
    main()
