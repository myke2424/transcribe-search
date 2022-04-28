from typing import Protocol
from google.cloud import speech
from pymediainfo import MediaInfo
import sys
from dataclasses import dataclass
from pathlib import Path


class Transcriber(Protocol):
    def transcribe(self) -> None:
        """ Transcribe audio to text """


class Player(Protocol):
    def play(self) -> None:
        """ Play a video source"""


class VideoTranscription:
    def transcribe(self):
        pass

    def foo(self):
        pass


@dataclass(frozen=True)
class AudioData:
    channels: int
    sampling_rate: int


class NoAudioChannelsException(Exception):
    """ No audio channels """


class MediaParser:
    @classmethod
    def get_audio_data(cls, filename: str) -> AudioData:
        media_info = MediaInfo.parse(Path(filename))
        audio_tracks = media_info.audio_tracks

        if not audio_tracks:
            raise NoAudioChannelsException("File has no audio channels")

        audio_track = audio_tracks[0]
        return AudioData(audio_track.channel_s, audio_track.sampling_rate)


def main() -> None:
    audio_data = MediaParser.get_audio_data('presentation.mp4')
    print()
    pass


if __name__ == "__main__":
    sys.exit(main())
