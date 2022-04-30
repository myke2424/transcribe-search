import pytest

from transcribe import utils


def test_create_timedelta_fgom_timestamp():
    timestamp = "2:10:08"
    got = utils.create_timedelta_from_timestamp(timestamp)

    assert str(got) == timestamp
