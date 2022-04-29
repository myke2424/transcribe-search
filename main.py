from typing import Protocol
from google.cloud import speech
from pymediainfo import MediaInfo
import sys
from dataclasses import dataclass

from moviepy.editor import AudioFileClip
from pathlib import Path


class Transcriber(Protocol):
    def transcribe(self, filename: str) -> None:
        """Transcribe audio to text"""


class Player(Protocol):
    def play(self) -> None:
        """Play a video source"""


class Root:
    def __init__(self, filename: str):
        self.filename: str = filename
        self.player: Player = Player()
        self.transcriber: Transcriber = GoogleVideoTranscriber()


Milliseconds = int


@dataclass(frozen=True)
class AudioData:
    duration: Milliseconds
    channels: int
    sampling_rate: int


class NoAudioChannelsException(Exception):
    """No audio channels"""


class MediaParser:
    @classmethod
    def get_audio_data(cls, filename: str) -> AudioData:
        media_info = MediaInfo.parse(Path(filename))
        audio_tracks = media_info.audio_tracks

        if not audio_tracks:
            raise NoAudioChannelsException("File has no audio channels")

        audio_track = audio_tracks[0]
        return AudioData(audio_track.duration, audio_track.channel_s, audio_track.sampling_rate)


class GoogleVideoTranscriber:
    SYNC_CUT_OFF = 60000

    def __init__(self, config: dict):
        self.client = speech.SpeechClient()
        self.config = speech.RecognitionConfig(**config)

    def transcribe(self, filename: str):
        audioclip = AudioFileClip(filename)
        filename_without_ext = filename.split('.')[0]
        audio_file_name = f"{filename_without_ext}.wav"
        audioclip.write_audiofile(audio_file_name)

        with open(audio_file_name, "rb") as audio_file:
            content = audio_file.read()

        audio = speech.RecognitionAudio(content=content)

        audio_data = MediaParser.get_audio_data(filename)
        # If the file is greater than 60 seconds, use asynchronous speech recognition
        _transcriber = (
            self.client.long_running_recognize if audio_data.duration > self.SYNC_CUT_OFF else self.client.recognize
        )

        response = _transcriber(config=self.config, audio=audio)
        for result in response.results:
            print("Transcript: {}".format(result.alternatives[0].transcript))


def main() -> None:
    audio_data = MediaParser.get_audio_data("test.mp4")
    config = {
        "encoding": speech.RecognitionConfig.AudioEncoding.LINEAR16,
        "sample_rate_hertz": audio_data.sampling_rate,
        "language_code": "en-US",
        "audio_channel_count": audio_data.channels,
        "enable_word_time_offsets": True,
    }

    transcriber = GoogleVideoTranscriber(config)
    transcriber.transcribe("test.mp4")
    print()
    pass


if __name__ == "__main__":
    sys.exit(main())
