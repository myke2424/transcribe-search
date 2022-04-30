import datetime
import json
import logging
import math
from collections import defaultdict
from datetime import timedelta
from pathlib import Path
from typing import Dict, List, Optional, Protocol, Tuple

import speech_recognition as sr
from google.cloud import speech
from google.cloud.speech_v1.types import RecognizeResponse
from rich.progress import track

from . import utils
from .config import Config
from .video import VideoFile

logger = logging.getLogger(__name__)
Timestamp = Tuple[timedelta, timedelta]


class Transcription:
    def __init__(self, words: Optional[dict] = None) -> None:
        # Store list of timestamps word, i.e. transcription[word] = [(start_time, end_time), ...]
        # use for word search
        self._words: Dict[str, List[Timestamp]] = words or defaultdict(list)
        utils.make_dir(Config.GENERATED_FILES_DIR)

    @classmethod
    def from_json(cls, json_file_path: str) -> "Transcription":
        """Create transcription object from json file, used when results are cached"""
        path = Path(json_file_path)

        if not path.is_file():
            raise FileNotFoundError(f"JSON File: {json_file_path} doesnt exist")

        if path.suffix != ".json":
            logger.error("Failed to create transcription object from json, file isn't of type json")
            raise ValueError(f"File: {json_file_path} is not a valid json file")

        with open(str(path)) as file:
            words_json = json.load(file)

        for word, timestamps in words_json.items():
            for i in range(len(timestamps)):
                start, end = timestamps[i]
                timestamps[i] = (
                    utils.create_timedelta_from_timestamp(start),
                    utils.create_timedelta_from_timestamp(end),
                )

        return cls(words=words_json)

    def add_word_and_timestamp(self, word: str, start_time: timedelta, end_time: timedelta) -> None:
        """Append word with timestamp to dict"""
        logger.debug(f"Adding to transcription: Word=({word}), start=({start_time}), end=({end_time})")
        self._words[word].append((start_time, end_time))

    def search_word(self, word: str) -> None:
        """Search the transcription for the word and display the results"""
        logger.info(f"Searching for word: {word}")

        if self._words[word] is None:
            logger.debug(f"Word: {word} doesn't exist in transcription")
            return

        logger.info(f"Found {len(self._words[word])} results for ({word}) search")
        table = utils.build_result_table(word)

        for i, timestamp in enumerate(self._words[word]):
            start, end = timestamp
            table.add_row(f"{i + 1}", f"{start}", f"{end}")
        utils.print_table(table)

    def to_json_file(self, filename: str) -> None:
        """Serialize transcription and save to json file"""
        path = Path(f"{Config.GENERATED_FILES_DIR}/{filename}.json")
        with open(path, "w") as x:
            json.dump(self._words, x, default=str)  # default str so datetime is serializable

    def search_phrase(self, phrase: str) -> None:
        """Search the transcription for the phrase and display the results"""
        raise NotImplementedError


class Transcriber(Protocol):
    def transcribe(self, filename: str) -> Transcription:
        """Transcribe audio file to text"""


class GoogleVideoTranscriber:
    SYNC_THRESHOLD = 60000

    def __init__(self) -> None:
        self._client = speech.SpeechClient()
        self.default_cfg_kwargs = {
            "encoding": speech.RecognitionConfig.AudioEncoding.LINEAR16,
            "language_code": "en-US",
            "enable_word_time_offsets": True,
        }

    @staticmethod
    def _build_transcription_from_response(
        response: RecognizeResponse, transcription: Transcription, chunk_id: int, offset: int
    ) -> None:
        """Build the transcription dict structure"""
        for result in response.results:
            for res in result.alternatives[0].words:
                # chunk_id * offset equal current time in video
                start = res.start_time + datetime.timedelta(seconds=(chunk_id * offset))
                end = res.end_time + datetime.timedelta(seconds=(chunk_id * offset))
                transcription.add_word_and_timestamp(word=res.word, start_time=start, end_time=end)

    def transcribe(self, file_path: Path) -> Transcription:
        logger.debug(f"Transcribing file: '{file_path}'")
        video = VideoFile(file_path)
        audio_content, audio_file_name = video.get_audio_content()
        config = {
            **self.default_cfg_kwargs,
            "sample_rate_hertz": video.audio_data.sampling_rate,
            "audio_channel_count": video.audio_data.channels,
        }

        transcription = Transcription()
        for i in track(range(int(math.ceil(video.audio_data.duration_minutes))), description="Transcribing..."):
            with sr.AudioFile(audio_file_name) as source:
                # create 60-second chunks, so we don't go over the speech to text MB request limit
                chunk = sr.Recognizer().record(source, offset=i * Config.OFFSET, duration=Config.FILE_CHUNK_DURATION)
                audio = speech.RecognitionAudio(content=chunk.frame_data)

                operation = self._client.long_running_recognize(config=config, audio=audio)

                logger.debug(f"Waiting for chunk {i} to complete...")
                response = operation.result(timeout=90)
                self._build_transcription_from_response(response, transcription, i, Config.OFFSET)
        transcription.to_json_file(filename=video.filename_no_ext)
        return transcription
