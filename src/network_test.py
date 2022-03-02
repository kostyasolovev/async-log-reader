import asyncio
import sys
from pathlib import Path
import aiohttp
from itertools import count

root = Path(__file__).parent.parent
sys.path.append(str(root))
import src.network as network
import src.logger as Logger

Logger.init_logger(log_name='etc/example.log')
print(network.S._storages)

async def checker():
    async with aiohttp.ClientSession() as session:
        while True:
            for index, addr in enumerate(network.S._storages[:network.up_availiable.place]):
                try:
                    async with session.get(addr.addr + "/status") as resp:
                        status = resp.status
                        if status == 200:
                            print(status)
                            network.up_availiable.set(addr, True, index)
                            print(network.up_availiable)
                            ok = True
                            break
                        else:
                            ok = False   
                                      
                except:
                    print("cannot connect to {}".format(addr.addr))
            if not ok:
                network.up_availiable.set(None, False, len(network.S._storages))
            await asyncio.sleep(5)


    
loop = asyncio.get_event_loop()
loop.run_until_complete(network.online_check())
loop.close()