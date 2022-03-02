import asyncio
import sys
import time
from pathlib import Path
root = Path(__file__).parent.parent
sys.path.append(str(root))
from src.tools import clear_offsets

def long():
    time.sleep(3)
    print("long is done!")

def run():
    async def worker():
        print("worker started")
        await long()
        print("worker finished")

    test_loop = asyncio.get_event_loop()
    test_loop.run_until_complete(worker())

if __name__ == "main":
    clear_offsets()

