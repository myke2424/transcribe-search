import datetime
import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

from moviepy.editor import AudioFileClip
from pymediainfo import MediaInfo

from .config import Config
from .errors import FileNotAVideoError, ZeroAudioTracksError

logger = logging.getLogger(__name__)

Milliseconds = int
DEFAULT_AUDIO_EXTENSION = "wav"


class VideoFile:
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.audio_data = _AudioData.from_file(file_path)

    @property
    def filename_no_ext(self) -> str:
        """Filename without its extension"""
        return self.file_path.name.split(".")[0]

    def generate_audio_content(self, format_: str = DEFAULT_AUDIO_EXTENSION) -> bytes:
        """Generate audio file from video and extract the audio data bytes."""
        audio_clip = AudioFileClip(str(self.file_path))
        audio_file_name = f"{self.filename_no_ext}.{format_}"

        logger.debug(f"Generating audio file {audio_file_name}")
        audio_clip.write_audiofile(audio_file_name, verbose=False, logger=None)

        audio_file_path = f"{Config.GENERATED_FILES_DIR}/{audio_file_name}"
        shutil.move(audio_file_name, audio_file_path)  # move to generated dir

        with open(audio_file_path, "rb") as audio_file:
            content = audio_file.read()

        return content, audio_file_path


@dataclass(frozen=True)
class _AudioData:
    duration_ms: Milliseconds
    channels: int
    sampling_rate: int

    @property
    def timestamp(self) -> datetime.timedelta:
        return datetime.timedelta(seconds=(self.duration_ms / 1000) % 60)  # convert ms to seconds

    @property
    def duration_minutes(self) -> int:
        return (self.duration_ms / (1000 * 60)) % 60

    @classmethod
    def from_file(cls, file_path: Path) -> "_AudioData":
        """Create class instance using mediainfo on the video file"""
        media_info = MediaInfo.parse(file_path)

        if not media_info.video_tracks:
            raise FileNotAVideoError(f"File: {file_path.name} isn't a valid video file. Zero video tracks found.")

        if not media_info.audio_tracks:
            raise ZeroAudioTracksError(f"File: {file_path.name} - has no audio tracks")

        audio_track = media_info.audio_tracks[0]
        logger.debug(f"Audio track: {audio_track}")

        return cls(audio_track.duration, audio_track.channel_s, audio_track.sampling_rate)
