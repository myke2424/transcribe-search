from typing import Protocol

from google.cloud import speech
from moviepy.editor import AudioFileClip
from metadata import AudioData

class Transcriber(Protocol):
    def transcribe(self, filename: str) -> None:
        """Transcribe audio file to text"""


class GoogleVideoTranscriber:
    SYNC_CUT_OFF = 60000

    def __init__(self, config: dict):
        self.client = speech.SpeechClient()
        self.config = speech.RecognitionConfig(**config)

    def transcribe(self, filename: str):
        audioclip = AudioFileClip(filename)
        filename_without_ext = filename.split(".")[0]
        audio_file_name = f"{filename_without_ext}.wav"
        audioclip.write_audiofile(audio_file_name)

        with open(audio_file_name, "rb") as audio_file:
            content = audio_file.read()

        audio = speech.RecognitionAudio(content=content)

        audio_data = AudioData.from_file(filename)
        # If the file is greater than 60 seconds, use asynchronous speech recognition
        _transcriber = (
            self.client.long_running_recognize if audio_data.duration > self.SYNC_CUT_OFF else self.client.recognize
        )

        from collections import defaultdict

        word_times = defaultdict(list)

        response = _transcriber(config=self.config, audio=audio)
        for result in response.results:
            print("Transcript: {}".format(result.alternatives[0].transcript))
            for word_info in result.alternatives[0].words:
                word = word_info.word
                start_time = word_info.start_time
                end_time = word_info.end_time

                word_times[word].append((start_time, end_time))

                print(f"Word: {word}, start_time: {start_time.total_seconds()}, end_time: {end_time.total_seconds()}")
        print(word_times)
