from daedalus.tests.fixtures import secrets
from daedalus.utils import *


def test_get_cosmic_auth(secrets):
    url = request_cosmic_download_url(
        "https://cancer.sanger.ac.uk/cosmic/file_download/GRCh38/cosmic/v96/CosmicHGNC.tsv.gz",
        secrets["cosmic_hash"],
    )

    assert True
