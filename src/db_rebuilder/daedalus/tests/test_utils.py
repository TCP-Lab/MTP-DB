from daedalus.utils import *

def test_cache():
    cache_obj = ResourceCache(None)

    assert cache_obj._ResourceCache__data == {}

    with ResourceCache("__mock") as mock_data:
        assert mock_data == "banana"
    
    assert cache_obj._ResourceCache__data == {"__mock": "banana"}
