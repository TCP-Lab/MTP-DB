import pytest

from daedalus.retrievers import (
    ResourceCache,
    retrieve_biomart,
    retrieve_cosmic_genes,
    retrieve_go,
    retrieve_iuphar,
    retrieve_tcdb,
)
from daedalus.utils import make_cosmic_hash
from tests.fixtures import secrets


@pytest.mark.slow
@pytest.mark.download
def test_biomart_retriever():
    data = retrieve_biomart()

    assert type(data) is dict
    assert data is not {}


@pytest.mark.download
def test_tcdb_retriever():
    data = retrieve_tcdb()

    assert type(data) is dict
    assert data is not {}


@pytest.mark.download
@pytest.mark.secrets
def test_cosmic_retrievers(secrets):
    data = retrieve_cosmic_genes(secrets["cosmic_hash"])

    assert True


@pytest.mark.secrets
def test_cosmic_hash(secrets):
    new_hash = make_cosmic_hash(secrets["cosmic_username"], secrets["cosmic_password"])
    assert secrets["cosmic_hash"] == new_hash


@pytest.mark.download
def test_iuphar_retriever():
    data = retrieve_iuphar()

    assert True


@pytest.mark.download
def test_go_retriever():
    data = retrieve_go()

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
