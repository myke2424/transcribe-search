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
from commands import get_cmd_arguments

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
# Search for a word in the transcription; show all timestamps in the video that word was said


import argparse


def main() -> None:
    args = get_cmd_arguments()
    # parser = argparse.ArgumentParser(description="Search transcription")
    # parser.add_argument('-f', '--file', help='Video file path used for transcription', required=True)
    # args = parser.parse_args()
    # parser.add_argument('--word', help='Search for word in transcription and display results')
    # parser.add_argument('--phrase', help='Search for phrase in transcription and display results')
    #transcriber = GoogleVideoTranscriber()
    #transcriber.transcribe("test.mp4")
    print()


if __name__ == "__main__":
    sys.exit(main())
