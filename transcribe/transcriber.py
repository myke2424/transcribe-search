from typing import Protocol

from google.cloud import speech
from moviepy.editor import AudioFileClip
from metadata import VideoFile


class Transcriber(Protocol):
    def transcribe(self, filename: str) -> None:
        """Transcribe audio file to text"""


# maybe use context manager to create wav file, after transcription is over, delete it

class GoogleVideoTranscriber:
    SYNC_THRESHOLD = 60000

    def __init__(self):
        self._client = speech.SpeechClient()
        self._config = {
            "encoding": speech.RecognitionConfig.AudioEncoding.LINEAR16,
            "language_code": "en-US",
            "enable_word_time_offsets": True,
        }

    def transcribe(self, file_path: str):
        video = VideoFile(file_path)
        content = video.get_audio_content()
        audio = speech.RecognitionAudio(content=content)

        _cfg = {**self._config, "sample_rate_hertz": video.audio_data.sampling_rate,
                "audio_channel_count": video.audio_data.channels}
        # If the file is greater than 60 seconds, use asynchronous speech recognition
        _transcriber = (
            self._client.long_running_recognize if video.audio_data.duration > self.SYNC_THRESHOLD else self._client.recognize
        )

        from collections import defaultdict

        word_times = defaultdict(list)

        response = _transcriber(config=self._config, audio=audio)
        for result in response.results:
            print("Transcript: {}".format(result.alternatives[0].transcript))
            for word_info in result.alternatives[0].words:
                word = word_info.word
                start_time = word_info.start_time
                end_time = word_info.end_time

                word_times[word].append((start_time, end_time))

                print(f"Word: {word}, start_time: {start_time.total_seconds()}, end_time: {end_time.total_seconds()}")
        print(word_times)
