import concurrent.futures
import copy
import datetime
import functools
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

    @classmethod
    def from_json_file(cls, json_file_path: str) -> "Transcription":
        """Create transcription object from json file, used when results are cached"""
        path = Path(json_file_path)

        if not path.is_file():
            raise FileNotFoundError(f"JSON File: {json_file_path} doesnt exist")

        if path.suffix != ".json":
            logger.error("Failed to create transcription object from json, file isn't of type json")
            raise ValueError(f"File: {json_file_path} is not a valid json file")

        with open(str(path)) as file:
            words_json = json.load(file)

        words = cls._build_words_from_json(words_json)

        return cls(words=words)

    @classmethod
    def from_json(cls, transcription_json: dict) -> "Transcription":
        """Create transcription from json"""
        words = cls._build_words_from_json(transcription_json)
        return cls(words)

    @staticmethod
    def _build_words_from_json(words_json: dict) -> dict:
        """Build word dict structure from json (need to parse deltatime objs)"""
        words = copy.deepcopy(words_json)
        for word, timestamps in words.items():
            for i in range(len(timestamps)):
                start, end = timestamps[i]
                timestamps[i] = (
                    utils.create_timedelta_from_timestamp(start),
                    utils.create_timedelta_from_timestamp(end),
                )
        return words

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
        # Implement trie data structure for phrase search
        raise NotImplementedError


class Transcriber(Protocol):
    def transcribe(self, filename: str) -> Transcription:
        """Transcribe audio file to text"""


class GoogleVideoTranscriber:
    SYNC_THRESHOLD = 60000
    AUDIO_CHUNK_TIME_LIMIT = 60
    OFFSET = 60

    def __init__(self) -> None:
        self._client = speech.SpeechClient()
        self.default_cfg_kwargs = {
            "encoding": speech.RecognitionConfig.AudioEncoding.LINEAR16,
            "language_code": "en-US",
            "enable_word_time_offsets": True,
        }

    def _create_file_chunks(self, audio_file: sr.AudioFile, total_duration: int) -> List[sr.AudioData]:
        """Create a list of file chunks, where each chunk is chunk_time_limit in length, default 60seconds"""
        recorder = sr.Recognizer()
        chunks = []
        for i in range(total_duration):
            with sr.AudioFile(audio_file) as source:
                # offset is the time the audio chunk starts
                chunk = recorder.record(
                    source, offset=i * self.AUDIO_CHUNK_TIME_LIMIT, duration=self.AUDIO_CHUNK_TIME_LIMIT
                )
                chunks.append(chunk)
        return chunks

    def _build_transcription_obj_from_response(
        self, response: RecognizeResponse, transcription: Transcription, chunk_id: int
    ) -> None:
        """Build the transcription data structure"""
        for result in response.results:
            for res in result.alternatives[0].words:
                # chunk_id * audio chunk time limit = current time in video
                start = utils.trunc_microseconds(
                    res.start_time + datetime.timedelta(seconds=(chunk_id * self.AUDIO_CHUNK_TIME_LIMIT))
                )
                end = utils.trunc_microseconds(
                    res.end_time + datetime.timedelta(seconds=(chunk_id * self.AUDIO_CHUNK_TIME_LIMIT))
                )
                transcription.add_word_and_timestamp(word=res.word, start_time=start, end_time=end)

    def _make_transcription(
        self, audio_chunk: sr.AudioData, chunk_id: int, transcription: Transcription, config: dict
    ) -> None:
        """Make the request to transcribe the audio to text and build the transcription data structure"""
        audio = speech.RecognitionAudio(content=audio_chunk.frame_data)
        logger.debug(f"Making request for audio file chunk {chunk_id}")
        response = self._client.recognize(config=config, audio=audio)
        self._build_transcription_obj_from_response(response, transcription, chunk_id)

    def transcribe(self, file_path: Path) -> Transcription:
        """Transcribe video to text"""
        logger.debug(f"Transcribing file: '{file_path}'")
        video = VideoFile(file_path)
        audio_content, audio_file_path = video.generate_audio_content()
        config = {
            **self.default_cfg_kwargs,
            "sample_rate_hertz": video.audio_data.sampling_rate,
        }

        total_duration = int(math.ceil(video.audio_data.duration_minutes))

        audio_chunks = self._create_file_chunks(audio_file=audio_file_path, total_duration=total_duration)
        chunk_ids = list(range(len(audio_chunks)))
        transcription = Transcription()

        make_transcription_fn = functools.partial(self._make_transcription, transcription=transcription, config=config)

        # Make transcription requests in parallel using thread pool
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(make_transcription_fn, audio_chunks, chunk_ids)

        transcription.to_json_file(filename=video.filename_no_ext)
        return transcription
