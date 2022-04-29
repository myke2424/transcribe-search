import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from google.cloud import speech
from moviepy.editor import AudioFileClip
from pymediainfo import MediaInfo
from rich.progress import track
from metadata import AudioData
from transcriber import GoogleVideoTranscriber


class Player(Protocol):
    def play(self) -> None:
        """Play a video source"""


#
# class Root:
#     def __init__(self, filename: str):
#         self.filename: str = filename
#         self.player: Player = Player()
#         self.transcriber: Transcriber = GoogleVideoTranscriber()


# Thoughts - How to store and search for words?
# Maybe use a trie, each node will be a word


def main() -> None:
    audio_data = AudioData.from_file("../test.mp4")
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


if __name__ == "__main__":
    sys.exit(main())
