from dataclasses import dataclass
from pathlib import Path

from errors import ZeroAudioTracksError
from moviepy.editor import AudioFileClip
from pymediainfo import MediaInfo
from utils import open_then_remove

Milliseconds = int
DEFAULT_AUDIO_EXTENSION = "wav"


class VideoFile:
    def __init__(self, file_path):
        self.file_path = file_path
        self.audio_data = _AudioData.from_file(file_path)

    @property
    def filename_no_ext(self):
        """Filename without its extension"""
        return self.file_path.split(".")[0]

    def get_audio_content(self, format_: str = DEFAULT_AUDIO_EXTENSION) -> bytes:
        """Generate audio file from video and extract the audio data bytes."""
        audio_clip = AudioFileClip(self.file_path)
        audio_file_name = f"{self.filename_no_ext}.{format_}"
        audio_clip.write_audiofile(audio_file_name, verbose=False, logger=None)

        # ctx manager will delete audio file after we read
        with open_then_remove(audio_file_name, "rb") as audio_file:
            content = audio_file.read()

        return content


@dataclass(frozen=True)
class _AudioData:
    duration: Milliseconds
    channels: int
    sampling_rate: int

    @classmethod
    def from_file(cls, filename: str) -> "_AudioData":
        """Create class instance using mediainfo on the file"""
        media_info = MediaInfo.parse(Path(filename))
        audio_tracks = media_info.audio_tracks

        if not audio_tracks:
            raise ZeroAudioTracksError(f"File: {filename} - has no audio tracks")

        audio_track = audio_tracks[0]
        return cls(audio_track.duration, audio_track.channel_s, audio_track.sampling_rate)
