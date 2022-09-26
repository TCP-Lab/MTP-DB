import asyncio
from collections import defaultdict
from asyncio import Lock, Queue
from copy import deepcopy

import multiprocessing

CPUS = multiprocessing.cpu_count()

async def get_mock_data():
    return "banana"

class CacheKeyError(Exception):
    pass

async def retrieve_data(queue):
    pass

class ResourceCache:
    __hooks = {
        "__mock": get_mock_data
    }
    __locks = defaultdict(Lock)
    __write_lock = Lock()
    __data = {}
    __queue = Queue(CPUS)
    __task_started = False

    def __init__(self) -> None:
        if not self.__task_started:
            self.__task = asyncio.create_task(retrieve_data(self.__queue))
    
    async def put(self, key):
        async with self.__write_lock:
            self.__data[key] = "banana"


    async def get(self, key):
        try:
            return deepcopy(self.__data[ey])
        except KeyError:
            pass
        
        await self.__locks[key].acquire()
        await self.__queue.put(key)


    async def __aenter__(self):
        
        
        try:
            worker = await self.__hooks[self.__key]
        except KeyError:
            raise CacheKeyError(f"Invalid key: {self.__key}")
        
        await self.__queue.put()
        
        async with self.__write_lock:
            self.__data[self.__key] = insert
        
        return deepcopy(insert)

    
    async def __aexit__(self, exc_type, exc, tb):
        self.__locks[self.__key].release()
