import re
import unicodedata
import shutil
import os
import json

ans_y = ('y', 's', '1', 'yes', 'si')

def limpiar_texto1(texto:str):
    texto = texto.lower()
    texto = re.sub(r'[^\w\s]', '', texto)
    texto = re.sub(r'\s+', '', texto)
    texto = unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('utf-8')
    
    return texto

def present_new_file(new_path:str):
    path = os.path.join('file_procces', 'moment.xlsx')
    shutil.move(path, new_path)
    shutil.rmtree('file_procces')

def load_config(name:str) -> dict:
    files=[]
    for file in os.listdir('configs'):
        if file.endswith('.json'):
            files.append(os.path.splitext(file)[0])
    
    if name not in files:
        raise ValueError("Aun no existe el archivo buscado")
 
    file = os.path.join('configs', f'{name}.json')

    with open(file, mode='r') as config:
        conf = json.load(config)
    return conf

def save_config(config, name):
    path = os.path.join('configs', f'{name}.json')
    with open(path, mode='w') as file:
        json.dump(config, file, indent=4)

def main():
    pass

if __name__ =="__main__":
    main()
