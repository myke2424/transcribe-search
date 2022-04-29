import logging
from collections import defaultdict
from datetime import timedelta
from pathlib import Path
from typing import Callable, Dict, List, Protocol, Tuple

from google.cloud import speech
from google.cloud.speech_v1.types import RecognizeResponse
from utils import build_result_table, print_table
from video import VideoFile

logger = logging.getLogger(__name__)
Timestamp = Tuple[timedelta, timedelta]


class Transcription:
    def __init__(self) -> None:
        # Store list of timestamps word, i.e. transcription[word] = [(start_time, end_time), ...]
        # use for word search
        self._words: Dict[str, List[Timestamp]] = defaultdict(list)

    def add_word_and_timestamp(self, word: str, start_time: timedelta, end_time: timedelta) -> None:
        self._words[word].append((start_time, end_time))

    def search_word(self, word: str) -> None:
        """Search the transcription for the word and display the results"""
        if self._words[word] is None:
            return

        logger.info(f"Found {len(self._words[word])} results for ({word}) search")
        table = build_result_table(word)

        for i, timestamp in enumerate(self._words[word]):
            start, end = timestamp
            table.add_row(f"{i + 1}", f"{start.total_seconds()}", f"{end.total_seconds()}")
        print_table(table)

        def search_phrase(self, phrase: str) -> None:
            """Search the transcription for the phrase and display the results"""
            pass


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
        response: RecognizeResponse,
    ) -> Transcription:
        """Build the transcription dict structure"""
        transcription = Transcription()
        for result in response.results:
            for res in result.alternatives[0].words:
                transcription.add_word_and_timestamp(word=res.word, start_time=res.start_time, end_time=res.end_time)
        return transcription

    def transcribe(self, file_path: Path) -> Transcription:
        logger.debug(f"Transcribing file: '{file_path}'")
        video = VideoFile(file_path)
        audio = speech.RecognitionAudio(content=video.get_audio_content())
        config = {
            **self.default_cfg_kwargs,
            "sample_rate_hertz": video.audio_data.sampling_rate,
            "audio_channel_count": video.audio_data.channels,
        }

        # If the file is greater than 60 seconds, use asynchronous speech recognition, otherwise use sync
        _recognize: Callable = (
            self._client.long_running_recognize
            if video.audio_data.duration > self.SYNC_THRESHOLD
            else self._client.recognize
        )

        response = _recognize(config=config, audio=audio)
        logger.debug(f"google transcription response: {response}")

        return self._build_transcription_from_response(response)
