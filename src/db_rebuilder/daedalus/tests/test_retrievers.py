import pytest
from daedalus.retrievers import (
    ResourceCache,
    retrieve_biomart,
    retrieve_cosmic_genes,
    retrieve_iuphar,
    retrieve_tcdb,
)
from daedalus.tests.fixtures import secrets
from daedalus.utils import make_cosmic_hash


@pytest.mark.slow
def test_biomart_retriever():
    data = retrieve_biomart()

    assert type(data) is dict
    assert data is not {}


def test_tcdb_retriever():
    data = retrieve_tcdb()

    assert type(data) is dict
    assert data is not {}


def test_cosmic_retrievers(secrets):
    data = retrieve_cosmic_genes(secrets["cosmic_hash"])

    assert True


def test_cosmic_hash(secrets):
    new_hash = make_cosmic_hash(secrets["cosmic_username"], secrets["cosmic_password"])
    assert secrets["cosmic_hash"] == new_hash


def test_iuphar_retriever():
    data = retrieve_iuphar()

    assert True


def dummy():
    return "Dummy data"


def test_cache():
    keys = {"dummy1": dummy, "dummy2": dummy}

    cache_obj = ResourceCache(keys)

    assert cache_obj._ResourceCache__data == {}

    with cache_obj("dummy1") as mock_data:
        assert mock_data == "Dummy data"

    assert cache_obj._ResourceCache__data == {
        "dummy1": "Dummy data",
        "dummy2": "Dummy data",
    }
