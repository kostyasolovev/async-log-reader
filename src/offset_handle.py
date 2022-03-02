import sys
from os import path
from pathlib import Path
from ast import literal_eval
root = Path(__file__).parent.parent
sys.path.append(str(root))
from src import tools
from src.read_config import config
import src.logger as Logger

class OffsetHandlerType():
    '''types: Oracle bd = 'B'/ text file = 'F'.'''
    def __init__(self, type='F'):
        if type not in ('B', 'F'):
            print(TypeError("OffsetHandler's type must be 'B' for BerkeleyDB or 'F' for text file writing"))
            #здесь должна быть проверка Беркли
            #если она есть - используем ее

def fetch_offsets():
    '''Подготавливает оффсеты при первом запуске\n
    Fetches logs' offsets at starting of the program'''
    #fetch maxoffsets
    maxoffsets, startoffsets = {}, {}
    logs_to_read = tools.get_files(config.files)
    for log in logs_to_read:
        try:
            with open(log, 'r') as file:
                maxoffsets[log] = len(file.readlines())
        except:
            Logger.error(PermissionError("Permission denied: {}".format(log))) #### TODO: change print to log
    Logger.debug("There are {} logs/files to read".format(len(maxoffsets.items())))
    #fetch startoffsets
    if path.isfile('etc/offsets.dict'):
        with open('etc/offsets.dict') as file:
            try:
                temp_offsets = literal_eval(file.readline())
                for log in maxoffsets: 
                    if log in temp_offsets:
                        if temp_offsets[log] <= maxoffsets[log]:
                            startoffsets[log] = temp_offsets[log]
                        else:
                            startoffsets[log] = 0
            except:
                for log in maxoffsets:
                    startoffsets[log] = 0
    else:
        for log in logs_to_read:
            startoffsets[log] = 0
    #print("startoffsets are {}".format(startoffsets))
    return startoffsets

startoffsets = fetch_offsets()
