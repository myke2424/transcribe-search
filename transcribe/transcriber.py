from typing import Protocol, Callable
from dataclasses import dataclass
from google.cloud import speech
from moviepy.editor import AudioFileClip
from metadata import VideoFile
from collections import defaultdict
from google.cloud.speech_v1.types import RecognizeResponse


class Transcriber(Protocol):
    def transcribe(self, filename: str) -> None:
        """Transcribe audio file to text"""


# transcription is a dict, key = word; val = list of start and end time tuples

class Searchable(Protocol):
    def search_word(self, word: str):
        """ Search for all occurrences of the word in the transcription """

    def search_phrase(self, transcription, phrase: str):
        """ Search for all occurrences of the phrase in the transcription """


class Transcription:
    def __init__(self):
        self.word_times = defaultdict(list)

    def search_word(self, word):
        if self.word_times[word] is None:
            print(f"Word: {word} doesn't exist in transcription")
            return

        for idx, start_time, end_time_ in enumerate(self.word_times[word]):
            print(f"{idx+1}.occurence")


    def search_phrase(self, phrase):
        pass


class GoogleVideoTranscriber:
    SYNC_THRESHOLD = 60000

    def __init__(self):
        self._client = speech.SpeechClient()
        self.default_cfg_kwargs = {
            "encoding": speech.RecognitionConfig.AudioEncoding.LINEAR16,
            "language_code": "en-US",
            "enable_word_time_offsets": True,
        }

    def _parse_response(self, response: RecognizeResponse):
        transcription = defaultdict(list)
        for result in response.results:
            for res in result.alternatives[0].words:
                transcription[res.word].append((res.start_time, res.end_time))
                print(
                    f"Word: {res.word}, start_time: {res.start_time.total_seconds()}, end_time: {res.end_time.total_seconds()}")


    def transcribe(self, file_path: str):
        video = VideoFile(file_path)
        audio = speech.RecognitionAudio(content=video.get_audio_content())
        config = {**self.default_cfg_kwargs, "sample_rate_hertz": video.audio_data.sampling_rate,
                  "audio_channel_count": video.audio_data.channels}

        # If the file is greater than 60 seconds, use asynchronous speech recognition, otherwise use sync
        _recognize: Callable = (
            self._client.long_running_recognize if video.audio_data.duration > self.SYNC_THRESHOLD else self._client.recognize
        )

        response = _recognize(config=config, audio=audio)
        self._parse_response(response)
