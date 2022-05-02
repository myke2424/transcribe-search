import pytest
import uuid
import os
import json

from datetime import timedelta
from transcribe import transcriber


@pytest.fixture
def transcription_json():
    json_ = {
        "test": [["0:00:00", "0:00:05"], ["0:00:05", "0:00:10"], ["0:10:00", "0:10:05"]],
        "midterm": [["1:00:00", "1:00:05"], ["2:10:00", "2:10:08"]],
    }

    return json_


@pytest.fixture
def transcription_expected():
    transcription_words = {
        "test": [
            (timedelta(hours=0, minutes=0, seconds=0), timedelta(hours=0, minutes=0, seconds=5)),
            (timedelta(hours=0, minutes=0, seconds=5), timedelta(hours=0, minutes=0, seconds=10)),
            (timedelta(hours=0, minutes=10, seconds=0), timedelta(hours=0, minutes=10, seconds=5)),
        ],
        "midterm": [
            (timedelta(hours=1, minutes=0, seconds=0), timedelta(hours=1, minutes=0, seconds=5)),
            (timedelta(hours=2, minutes=10, seconds=0), timedelta(hours=2, minutes=10, seconds=8)),
        ],
    }

    transcription = transcriber.Transcription(transcription_words)

    return transcription


def test_deserialization(transcription_json, transcription_expected):
    test_json_file = f"test-{str(uuid.uuid4())}.json"
    with open(test_json_file, 'w') as f:
        json.dump(transcription_json, f)

    transcriber.Transcription.from_json_file(test_json_file) == transcription_expected
    os.remove(test_json_file)