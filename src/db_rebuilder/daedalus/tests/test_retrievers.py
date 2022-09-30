import pytest
from daedalus.retrievers import retrieve_biomart, retrieve_cosmic_genes, retrieve_iuphar, retrieve_tcdb
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
    assert secrets["cosmic_hash"] == make_cosmic_hash(secrets["cosmic_username"], secrets["cosmic_password"])

def test_iuphar_retriever():
    data = retrieve_iuphar()

    assert True

