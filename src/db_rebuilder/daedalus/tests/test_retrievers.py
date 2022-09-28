import pytest
from daedalus.retrievers import retrieve_biomart, retrieve_tcdb

@pytest.mark.slow
@pytest.mark.skip
def test_biomart_retriever():
    data = retrieve_biomart()

    assert type(data) is dict
    assert data is not {}

@pytest.mark.slow
def test_tcdb_retriever():
    data = retrieve_tcdb()

    assert type(data) is dict
    assert data is not {}
