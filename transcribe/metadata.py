from dataclasses import dataclass
from pathlib import Path
from moviepy.editor import AudioFileClip
from contextlib import contextmanager
from pymediainfo import MediaInfo
import os
from errors import ZeroAudioTracksError

Milliseconds = int
DEFAULT_AUDIO_EXTENSION = "wav"


@contextmanager
def open_then_remove(path: str, mode: str) -> None:
    """ Open the file and remove it once done """
    file = open(path, mode)

    try:
        yield file
    finally:
        file.close()
        os.remove(path)


class VideoFile:
    def __init__(self, file_path):
        self.file_path = file_path
        self.audio_data = AudioData.from_file(file_path)

    @property
    def filename_no_ext(self):
        return self.filename.split(".")[0]

    # TODO: Move this somewhere else
    def get_audio_content(self, format_: str = DEFAULT_AUDIO_EXTENSION) -> str:
        """ Generate audio file from video, read file, return contents and delete audio file """
        audio_clip = AudioFileClip(self.file_path)
        audio_file_name = f"{self.filename_no_ext}.{format_}"
        audio_clip.write_audiofile(audio_file_name)

        # ctx manager will delete wav file after we read
        with open_then_remove(audio_file_name, "rb") as audio_file:
            content = audio_file.read()

        return content


@dataclass(frozen=True)
class AudioData:
    duration: Milliseconds
    channels: int
    sampling_rate: int

    @classmethod
    def from_file(cls, filename: str) -> "AudioData":
        media_info = MediaInfo.parse(Path(filename))
        audio_tracks = media_info.audio_tracks

        if not audio_tracks:
            raise ZeroAudioTracksError(f"File: {filename} - has no audio tracks")

        audio_track = audio_tracks[0]
        return cls(audio_track.duration, audio_track.channel_s, audio_track.sampling_rate)
