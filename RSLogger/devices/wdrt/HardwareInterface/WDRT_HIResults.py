import asyncio
from time import sleep

class Master:
    def __init__(self):
        self.fpath = None
        self.loop = asyncio.get_running_loop()

    def _threaded_write(self, fpath, data):
        try:
            with open(fpath, 'a') as outfile:
                outfile.writelines(data)
        except (PermissionError, OSError):
            sleep(.05)
            self._threaded_write(fpath, data)
            print("Permission Error, retrying")

    async def write(self, unit_id, data, timestamp):
        if self.fpath:
            data = f"wDRT,{unit_id},{timestamp},{data}"
            await self.loop.run_in_executor(None, self._threaded_write, self.fpath, data)
