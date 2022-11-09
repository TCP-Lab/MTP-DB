from daedalus.tests.fixtures import secrets
from daedalus.utils import *


def test_get_cosmic_auth(secrets):
    url = request_cosmic_download_url(
        "https://cancer.sanger.ac.uk/cosmic/file_download/GRCh38/cosmic/v96/CosmicHGNC.tsv.gz",
        secrets["cosmic_hash"],
    )

    assert True


def test_parse_ensembl_ids():
    tests = {
        "ENSE12345678912": {"tip": "E", "num": 12345678912, "ver": None},
        "ENSG12345678912": {"tip": "G", "num": 12345678912, "ver": None},
        "ENSP12345678912": {"tip": "P", "num": 12345678912, "ver": None},
        "ENSR12345678912": {"tip": "R", "num": 12345678912, "ver": None},
        "ENST12345678912": {"tip": "T", "num": 12345678912, "ver": None},
        "ENSGT12345678912": {"tip": "GT", "num": 12345678912, "ver": None},
        "ENSFM12345678912": {"tip": "FM", "num": 12345678912, "ver": None},
        "ENSE12345678912.12": {"tip": "E", "num": 12345678912, "ver": 12},
        "ENSG12345678912.12": {"tip": "G", "num": 12345678912, "ver": 12},
        "ENSP12345678912.12": {"tip": "P", "num": 12345678912, "ver": 12},
        "ENSR12345678912.12": {"tip": "R", "num": 12345678912, "ver": 12},
        "ENST12345678912.12": {"tip": "T", "num": 12345678912, "ver": 12},
        "ENSGT12345678912.12": {"tip": "GT", "num": 12345678912, "ver": 12},
        "ENSFM12345678912.12": {"tip": "FM", "num": 12345678912, "ver": 12},
    }

    for key, value in tests.items():
        result = split_ensembl_ids(key)

        assert result.full_id == key
        assert result.identifier == value["num"]
        assert result.type_letter_prefix == value["tip"]
        assert result.version_number == value["ver"]
