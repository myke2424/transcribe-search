from typing import Protocol, Callable, Dict, List, Tuple
from datetime import timedelta
from dataclasses import dataclass
from google.cloud import speech
from moviepy.editor import AudioFileClip
from metadata import VideoFile
from collections import defaultdict
from google.cloud.speech_v1.types import RecognizeResponse

from rich.console import Console
from rich.table import Table

Timestamp = Tuple[timedelta, timedelta]


class Transcription:
    def __init__(self):
        # Store list of timestamps word, i.e. transcription[word] = [(start_time, end_time), ...]
        # use for word search
        self._words: Dict[str, List[Timestamp]] = defaultdict(list)

    def add_word_and_timestamp(self, word: str, start_time: timedelta, end_time: timedelta) -> None:
        self._words[word].append((start_time, end_time))

    def search_word(self, word: str) -> None:
        if self._words[word] is None:
            return

        table = Table(title="Search Result Table")
        table.add_column("Occurrence", style="cyan")
        table.add_column("Start Time", style="magenta")
        table.add_column("EndTime", justify="right", style="green")

        print(f"Search for word: ({word}) results - {len(self._words[word])} occurrences \n")
        for i, timestamp in enumerate(self._words[word]):
            start, end = timestamp
            table.add_row(f"{i + 1}", f"{start.total_seconds()}", f"{end.total_seconds()}")

        console = Console()
        console.print(table)

        def search_phrase(self, phrase):
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
    def _build_transcription_from_response(response: RecognizeResponse) -> Transcription:
        """ Build the transcription dict structure """
        transcription = Transcription()
        for result in response.results:
            for res in result.alternatives[0].words:
                transcription.add_word_and_timestamp(word=res.word, start_time=res.start_time,
                                                     end_time=res.end_time)
        return transcription

    def transcribe(self, file_path: str) -> Transcription:
        video = VideoFile(file_path)
        audio = speech.RecognitionAudio(content=video.get_audio_content())
        config = {**self.default_cfg_kwargs, "sample_rate_hertz": video.audio_data.sampling_rate,
                  "audio_channel_count": video.audio_data.channels}

        # If the file is greater than 60 seconds, use asynchronous speech recognition, otherwise use sync
        _recognize: Callable = (
            self._client.long_running_recognize if video.audio_data.duration > self.SYNC_THRESHOLD else self._client.recognize
        )

        response = _recognize(config=config, audio=audio)
        return self._build_transcription_from_response(response)
