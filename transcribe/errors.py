""" Custom Exceptions """


class ZeroAudioTracksError(Exception):
    """Raise exception when video file has no audio tracks"""


class FileNotAVideoError(Exception):
    """Raise exception when the file isn't a valid video"""
