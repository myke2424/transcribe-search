from dataclasses import dataclass
from pathlib import Path

from pymediainfo import MediaInfo

from errors import ZeroAudioTracksError

Milliseconds = int


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
