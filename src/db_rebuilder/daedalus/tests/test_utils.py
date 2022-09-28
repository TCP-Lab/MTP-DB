from daedalus.utils import *
from daedalus.tests.fixtures import secrets

def test_cache():
    cache_obj = ResourceCache(None)

    assert cache_obj._ResourceCache__data == {}

    with ResourceCache("__mock") as mock_data:
        assert mock_data == "banana"
    
    assert cache_obj._ResourceCache__data == {"__mock": "banana"}

def test_get_cosmic_auth(secrets):
    url = request_cosmic_download_url(
        "https://cancer.sanger.ac.uk/cosmic/file_download/GRCh38/cosmic/v96/CosmicHGNC.tsv.gz",
        secrets["cosmic_hash"]
    )

    assert True
