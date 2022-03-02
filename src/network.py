import asyncio
import logging
import aiohttp
import sys
from pathlib import Path
root = Path(__file__).parent.parent
sys.path.append(str(root))
import src.control as control
from src.tools import STOP, commit_offsets
from src.settings import online_check_time
from src.read_config import config
import src.logger as Logger
from src.offset_handle import startoffsets

OFFLINE = control.Offline()

class Storages():
    '''Stores information about storages'''
    def __init__(self, addrs):
        self._storages=[]
        for i in addrs:
            if i._addr in self._storages:
                continue
            self._storages.append(i)

    @property
    def addrs(self):
        return self._storages

    def add(self, new_storage):
        if type(new_storage) != Address:
            Logger.error(TypeError("Wrong item to add. Storages must contain only Addresses!"))
        self._storages.append(new_storage)

    def __repr__(self):
        s = []
        for i in self._storages:
            s.append(i._addr)
        return str(s)
        
class Address():
    '''Stores information about specific host'''
    def __init__(self, addr=None):
        self._addr = addr

    @property
    def addr(self):
        return str(self._addr)

    def __repr__(self):
        return str(self._addr)

class UpperAvailiable(Address):
    def __init__(self, addr=None, online=False, place=100):
        Address.__init__(self, addr)
        self._isonline = online
        self._place = place
    
    def set(self, addr=None, online=False, place=100):
        self._addr = addr
        self._isonline = online
        self._place = place
    
    @property
    def isonline(self):
        return self._isonline
    @property
    def place(self):
        return self._place

S = Storages([Address(i) for i in config.storages])
up_availiable = UpperAvailiable()

async def online_check():
    '''The function checks online status of hosts contained in 
    config.storages host by host consistently config's order. 
    When it meets online host, it breaks inner loop and appoints
    this host the UpperAvailiable host'''
    async with aiohttp.ClientSession() as session:
        while True:
            if STOP.status:
                break
            for index, addr in enumerate(S._storages[:up_availiable.place+1]):
                try:
                    async with session.get(addr.addr+'/status') as request:
                        stat = request.status
                        if stat == 200:
                            up_availiable.set(addr, True, index)
                            Logger.debug("host [{}] is online. It was appointed the up_availiable host".format(addr.addr))
                            ok = True
                            break
                        else:
                            ok = False                   
                except:
                    Logger.warning("cannot connect to host {}".format(addr.addr)) 
                    ok = False
            if not ok:
                OFFLINE.change(True)
                up_availiable.set(None, False)
            else:
                OFFLINE.change(False)
            await asyncio.sleep(online_check_time)      
#TODO: test this func
async def post(data):
    '''sends messages to host'''
    while True:
        if STOP.status:
            logging.warning("Program stopped. All temporary data wont be sent")
            break
        elif OFFLINE.status:
            logging.warning("All hosts are offline. Program will wait for atleast one online host")
            await asyncio.sleep(online_check_time)
        else:
            logging.debug("Posting a batch...")
            async with aiohttp.ClientSession() as session: #TODO: one session per application
                await session.post(up_availiable.addr+'/proto', data = data)
            await asyncio.wait([asyncio.ensure_future(commit_offsets(startoffsets=startoffsets))])
            break

    #if not up_availiable.isonline: #TODO change algorythm
    #    await asyncio.sleep(online_check_time)
    #else:
    #    print("posting a batch")
    #    async with aiohttp.ClientSession() as session: #нужна одна сессия на программу, как это сделать в асинке пока не понятно
    #        await session.post(up_availiable.addr+'/proto', data = data)
