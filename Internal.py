import pickle
import shutil
import os

def Read_Record():
    with open('Frecuency_Master_Record.pkl', 'rb') as file:
        Frecuency_Master_Record = pickle.load(file)
    return Frecuency_Master_Record

def _Clean_Temp_Folder():
    try:
        if os.path.isfile("Temp/Frecuency_Master_Record.pkl"):
            os.remove("Temp/Frecuency_Master_Record.pkl")
    except:
        pass
def _Save_Previous_Record():
    shutil.move("Frecuency_Master_Record.pkl", "Temp/Frecuency_Master_Record.pkl")

def Restore_Previous_Record():
    shutil.move("Temp/Frecuency_Master_Record.pkl" ,"Frecuency_Master_Record.pkl")

def Update_Record(record):
    _Clean_Temp_Folder()
    _Save_Previous_Record()

    with open('Frecuency_Master_Record.pkl', 'wb') as file:
        record = pickle.load(file)
    print("Archivo guardado con exito")