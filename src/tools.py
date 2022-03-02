import asyncio
import datetime
import time
import os
from socket import gethostname, gethostbyname
import sys
from pathlib import Path
#from concurrent.futures import FIRST_COMPLETED, ALL_COMPLETED
import aiohttp

root = Path(__file__).parent.parent
sys.path.append(str(root))
from src import control, logger

class myIP():
    def __init__(self, ip=gethostbyname(gethostname())):
        self._ip = ip
    def set(self, new_ip):
        self._ip = new_ip
    def __repr__(self):
        return str(self._ip)

IP = myIP()
STOP = control.Stop()

def get_files(paths):
    files = []
    for key, mask in paths:
        temp = [os.fspath(file) for file in Path(key).rglob(mask)]
        for path in temp:
            if path not in files:
                files.append(path)
    return files

def get_host():
    #def get_ip(): 
        #return get('https://api.ipify.org').text
    return gethostname()

async def timer(worktime):
    start = time.time()
    if worktime == 0:
        await asyncio.sleep(0)
    else:
        await asyncio.sleep(worktime)
        logger.info('Time to stop.\nProgram stoped at {}, total worktime is {:.2f}'.format(datetime.now().strftime("%H:%M:%S"), time.time()-start))
        STOP.turn()

async def commit_offsets(startoffsets):
    with open('etc/offsets.dict', 'w') as file:
        file.write(str(startoffsets))
    logger.debug("offsets were commited")
    await asyncio.sleep(0)

def clear_offsets():
    with open('etc/offsets.dict', 'w') as file:
        file.write("")
    print("offsets deleted")

def _get_ip():
    '''Make GET-requests concurently. Returns info about user's IP'''
    from collections import namedtuple
    from socket import inet_aton
    
    logger.debug("getting user's IP...")
    Service = namedtuple('Service', ('name', 'url', 'ip_attr'))
    SERVICES = (
        Service('httpbin.org', 'http://httpbin.org/ip', 'origin'),
        Service('ipify', 'https://api.ipify.org?format=json', 'ip'),
        Service('ip-api', 'http://ip-api.com/json', 'query'),
        Service('test-broken', 'http://no-way-this-is-going-to-work.com/json', 'ip')
    )
    async def fetch_ip(session, service):
        try:
            async with session.get(service.url) as response:
                ip = await response.json()
                return ip[service.ip_attr]
        except:
            logger.warning("service {} is unresponding".format(service.name))
            return "service {} is unresponding".format(service.name)

    async def main():
        async with aiohttp.ClientSession() as session:
            tasks = [fetch_ip(session, service) for service in SERVICES]
            for _, future in enumerate(asyncio.as_completed(tasks)):
                result = await future
                try:
                    inet_aton(result)
                    IP.set(result)
                except:
                    logger.warning("service answer '{}' is incorrect".format(result))

    test_loop = asyncio.get_event_loop()
    test_loop.run_until_complete(main())
#fill the IP
_get_ip()

if __name__ == "__main__":
    clear_offsets()
