import logging
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from moviepy.editor import AudioFileClip
from pymediainfo import MediaInfo

from .errors import FileNotAVideoError, ZeroAudioTracksError

logger = logging.getLogger(__name__)

Milliseconds = int
DEFAULT_AUDIO_EXTENSION = "wav"


@dataclass(frozen=True)
class _AudioData:
    duration_ms: Milliseconds
    channels: int
    sampling_rate: int

    @property
    def duration_minutes(self) -> float:
        return (self.duration_ms / (1000 * 60)) % 60

    @classmethod
    def from_video_file(cls, video_file_path: Path) -> "_AudioData":
        """Create class instance using mediainfo on the video file"""
        media_info = MediaInfo.parse(video_file_path)

        if not media_info.video_tracks:
            raise FileNotAVideoError(f"File: {video_file_path.name} isn't a valid video file. Zero video tracks found.")

        if not media_info.audio_tracks:
            raise ZeroAudioTracksError(f"File: {video_file_path.name} - has no audio tracks")

        audio_track = media_info.audio_tracks[0]
        logger.debug(f"Audio track: {audio_track}")

        return cls(audio_track.duration, audio_track.channel_s, audio_track.sampling_rate)


@dataclass
class VideoFile:
    file_path: Path
    audio_data: _AudioData = field(init=False)

    def __post_init__(self) -> None:
        self.audio_data = _AudioData.from_video_file(self.file_path)

    def _generate_and_save_audio_file(self, save_dir: Path, format_: str = DEFAULT_AUDIO_EXTENSION) -> Path:
        """Generate audio file from video and save it to disk, default 'wav' format, return path to generated file"""
        audio_clip = AudioFileClip(str(self.file_path))
        audio_file_name = f"{self.file_path.stem}.{format_}"

        logger.debug(f"Generating audio file {audio_file_name}")
        audio_clip.write_audiofile(audio_file_name, verbose=False, logger=None)

        dest_audio_file_path = f"{str(save_dir)}/{audio_file_name}"
        shutil.move(audio_file_name, dest_audio_file_path)  # move audio file to save directory (generated)

        return Path(dest_audio_file_path)

    def generate_audio_file_and_get_content(self, save_dir: Path) -> bytes:
        """Generate audio file from video and extract the audio data bytes."""
        audio_file_path = self._generate_and_save_audio_file(save_dir)

        with audio_file_path.open(mode='rb') as audio_file:
            content = audio_file.read()

        return content, audio_file_path
