from datetime import datetime
import time
import asyncio
import time
from itertools import zip_longest
import src.tools as tools
from src.read_config import config
import src.messages_pb2 as Messages
import src.network as network
from src.network import OFFLINE
from src.tools import STOP
import src.settings as settings
from src.offset_handle import startoffsets
from src.logger import LOG as Logger #logger settings are in logger.py, default level is "DEBUG"

myHost = tools.get_host()
#startoffsets initialized in offset_handle
BATCH = [] #batch of messages to handling and sending to server
koroutines = [] #list of current koroutines

async def coordinator():
    '''запускает log_reader для каждого лога, следит за появлением новых логов\n
    Launches readers for each log, watches for new logs'''
    Logger.debug("coordinator started")
    if len(koroutines) != 0:
        await asyncio.sleep(settings.wait_for_new_files) #300 seconds
    new_tasks = []
    #get list of files to read
    logs_to_read = tools.get_files(config.files) #TODO: translate into async
    for i in range(len(logs_to_read)-1, 0, -1):
        try:
            with open(logs_to_read[i], 'r') as file:
                _ = file.readline()
        except:
            Logger.error(PermissionError("Cannot read file, permission denied: {}".format(logs_to_read[i])))
            logs_to_read.remove(logs_to_read[i])
    #checking for new files, creates koroutine for each file
    #new koroutine is recorded in list of koroutines
    for log in logs_to_read:
        if log not in koroutines:
            new_tasks.append(asyncio.create_task(log_reader(log)))
            koroutines.append(log)
    #cosidering "await" command blocks everything under itself and
    #koroutines works infinitly it's hard to create such koroutines
    #in cycle mode. The possible solution is to run coordinator (watcher) recursively
    new_tasks.append(asyncio.create_task(coordinator()))
    await asyncio.wait(new_tasks)
    
async def log_reader(log_name):
    '''Coroutine opens log as stream, reads all available lines and checks if file was rewrited'''
    Logger.debug('Reader started reading [{}]'.format(log_name))
    if log_name not in startoffsets:
        startoffsets[log_name] = 0
    with open(log_name, 'r') as file:
        while True:
            if STOP.status or not file.readable():
                break
            elif OFFLINE.status:
                await asyncio.sleep(settings.online_check_time)
            else:
                #reader uses two methods of reading: fast (swallow its whole) and slow (reading line by line very precise and accurate)
                #1st method used right after koroutine starting or when file was rewrited (whole file is unread and we can simply swallow it)
                #it works as shown below: read all availiable lines, parse them, then create 2D array with following columns: line of the log and name of the log
                temp = [*zip_longest(file.read().splitlines()[startoffsets[log_name]:], '', fillvalue=str(log_name))]
                startoffsets[log_name] += len(temp)
                BATCH.extend(temp)
                #2nd method: reading line by line
                while not STOP.status:
                    if OFFLINE.status:
                        await asyncio.sleep(settings.online_check_time)
                    else:
                        #try to read a new line
                        s = file.readline()
                        if s != "":
                            BATCH.append((s, str(log_name)))
                            startoffsets[log_name] += 1
                        else:
                            #also check the previous byte
                            #if it is empty -> file was rewrited
                            #we reset offsets and go back to fast reading phase
                            file.seek(file.tell()-2)
                            prev = file.readline()
                            if prev == "":
                                file.seek(0, 0)
                                startoffsets[log_name] = 0
                                break
                            else:
                                await asyncio.sleep(1)
    koroutines.remove(log_name)
    Logger.debug("Reader stopped reading [{}]".format(log_name))
    await asyncio.sleep(0)

async def batch_handler():
    '''Sends batches to server concurently'''
    Logger.debug("BatchHandler started")
    while not STOP.status:
        _start = time.time()
        Logger.debug("current length of the batch: {}".format(len(BATCH))) 
        tasks = []
        while len(BATCH)>0: #you are free to change this condition. Low value leads high precision but low productivity and vice-versa
            if STOP.status:
                break
            elif OFFLINE.status:
                await asyncio.sleep(settings.online_check_time)
            else:
                #if there is atleast one online host batcher will send data parts
                Logger.debug("Batcher tries to send a data. Storage offline status: <{}>".format(OFFLINE.status))
                #devide sending data into parts down to MAX_BATCH_SIZE
                if len(BATCH) >= settings.MAX_BATCH_SIZE: 
                    m = Messages.Batch()
                    m.IP = tools.IP._ip
                    m.identification = settings.BIO
                    m.hostName = myHost
                    for i in range(settings.MAX_BATCH_SIZE):
                        item = m.lines.add()
                        item.content = BATCH[i][0]
                        item.time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                        item.log = BATCH[i][1]
                    data = m.SerializeToString()
                    tasks.append(asyncio.create_task(network.post(data)))
                    BATCH = BATCH[settings.MAX_BATCH_SIZE:]
                    await asyncio.sleep(0)
                else:
                    le = len(BATCH)
                    m = Messages.Batch()
                    m.IP = tools.IP._ip
                    m.identification = settings.BIO
                    m.hostName = myHost
                    for i in range(le):
                        item = m.lines.add()
                        item.content = BATCH[i][0]
                        item.time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                        item.log = BATCH[i][1]
                    data = m.SerializeToString()
                    tasks.append(asyncio.create_task(network.post(data)))
                    BATCH = BATCH[le:]
                    Logger.debug("Batcher has sent availiable messages, worktime: {:.3f}".format(time.time()-_start))
        if len(tasks) != 0:
            await asyncio.wait(tasks)
        else:
            await asyncio.sleep(settings.ask_data_time) #TODO: check and consider cycle time
             
Logger.info('Program started')
ioloop = asyncio.get_event_loop()
tasks = [ioloop.create_task(coordinator()), ioloop.create_task(tools.timer(settings.WORKTIME)), \
    ioloop.create_task(network.online_check()), ioloop.create_task(batch_handler())]
ioloop.run_until_complete(asyncio.wait(tasks))
ioloop.close()
