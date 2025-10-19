import pytest
import sys
import os
# make sure the app src is importable when running tests from repo root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from app.nlp_interpreter import MaritimeNLPInterpreter


@pytest.fixture()
def nlp():
    return MaritimeNLPInterpreter()


def test_extract_datetime_full_date_time(nlp):
    parsed = nlp._extract_datetime("8PM on 02 January 2020", nlp.nlp("8PM on 02 January 2020"))
    assert parsed is not None
    assert "2020" in parsed


def test_extract_time_only(nlp):
    parsed = nlp._extract_datetime("At 12PM", nlp.nlp("At 12PM"))
    # Accept either a time-only string like '12:00:00' or a full datetime 'YYYY-MM-DD HH:MM:SS'
    assert parsed is not None
    assert ":" in parsed


def test_extract_duration(nlp):
    parsed = nlp._extract_datetime("10 hours 25 minutes", nlp.nlp("10 hours 25 minutes"))
    # Can be returned as an ISO-duration 'PT...' or as a datetime/time string depending on parser
    assert parsed is not None
    assert parsed.startswith("PT") or (":" in parsed)
