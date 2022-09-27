from copy import deepcopy
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

CPUS = multiprocessing.cpu_count()

def run(callable):
    return callable()

def get_mock_data():
    return "banana"

class CacheKeyError(Exception):
    pass

class ResourceCache:
    __hooks = {
        "__mock": get_mock_data
    }
    __data = {}
    __populated = False

    def __init__(self, key) -> None:
        self.target_key = key

    def populate(self):
        with ProcessPoolExecutor(CPUS) as pool:
            # Just to be sure the orders are ok
            keys = deepcopy(list(self.__hooks.keys()))
            workers = [self.__hooks[key] for key in keys]

            items = pool.map(run, workers)
        
        for key, value in zip(self.__hooks.keys(), items):
            self.__data[key] = value

    
    def __enter__(self):
        if self.target_key not in self.__hooks.keys():
            raise CacheKeyError(f"Invalid key: {self.__key}")
        
        if self.__populated is False:
            self.populate()

        return deepcopy(self.__data[self.target_key])

    
    def __exit__(self, exc_type, exc, tb):
        pass
