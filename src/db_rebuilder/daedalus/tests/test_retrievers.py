import pytest
from daedalus.retrievers import retrieve_biomart

@pytest.mark.slow
def test_biomart_retriever():
    data = retrieve_biomart()

    assert type(data) == "dict"
    assert data is not {}

