import sys
import os
import asyncio

os.chdir('F:/telegram-bot')
sys.path.insert(0, 'F:/telegram-bot')

from app.loader import Loader

async def main():
    await Loader.start()

if __name__ == "__main__":
    asyncio.run(main())
