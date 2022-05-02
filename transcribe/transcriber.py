import concurrent.futures
import datetime
import functools
import logging
import math
from pathlib import Path
from typing import List, Protocol

import speech_recognition as sr
from google.cloud import speech
from google.cloud.speech_v1.types import RecognizeResponse

from . import utils
from .transcription import Transcription
from .video import VideoFile

logger = logging.getLogger(__name__)


class Transcriber(Protocol):
    def transcribe(self, video_file_path: Path) -> Transcription:
        """Transcribe video to text"""


class GoogleVideoTranscriber:
    AUDIO_CHUNK_TIME_LIMIT = 60

    def __init__(self, generated_dir: str) -> None:
        """
        :param generated_dir: Directory path used to store generated transcription json files
        """
        self.generated_dir = Path(generated_dir)
        self._client = speech.SpeechClient()
        self.default_cfg_kwargs = {
            "encoding": speech.RecognitionConfig.AudioEncoding.LINEAR16,
            "language_code": "en-US",
            "enable_word_time_offsets": True,
        }

    def _chunk_audio_file(self, audio_file_path: str, total_duration: int) -> List[sr.AudioData]:
        """
        Google speech-to-text has a 60second time limit for local file transcription
        Use this to create a list of file chunks, where each chunk is chunk_time_limit in length, default 60seconds
        """
        recorder = sr.Recognizer()
        chunks = []

        for i in range(total_duration):
            with sr.AudioFile(audio_file_path) as source:
                # offset is the time the audio chunk starts in the original source, i.e. 2 * 60 = start chunk @ 2min
                chunk = recorder.record(
                    source, offset=i * self.AUDIO_CHUNK_TIME_LIMIT, duration=self.AUDIO_CHUNK_TIME_LIMIT
                )
                chunks.append(chunk)
        return chunks

    def _build_transcription_obj_from_response(
            self, response: RecognizeResponse, transcription: Transcription, chunk_id: int
    ) -> None:
        """Build the transcription data structure"""
        for result in response.results:
            for res in result.alternatives[0].words:
                # chunk_id * audio chunk time limit = current time in video
                start = utils.trunc_microseconds(
                    res.start_time + datetime.timedelta(seconds=(chunk_id * self.AUDIO_CHUNK_TIME_LIMIT))
                )
                end = utils.trunc_microseconds(
                    res.end_time + datetime.timedelta(seconds=(chunk_id * self.AUDIO_CHUNK_TIME_LIMIT))
                )
                transcription.add_word_and_timestamp(word=res.word, start_time=start, end_time=end)

    def _make_transcription(
            self, audio_chunk: sr.AudioData, chunk_id: int, transcription: Transcription, config: dict
    ) -> None:
        """Make the request to transcribe the audio to text and build the transcription data structure"""
        audio = speech.RecognitionAudio(content=audio_chunk.frame_data)
        logger.debug(f"Making request for audio file chunk {chunk_id}")
        response = self._client.recognize(config=config, audio=audio)
        self._build_transcription_obj_from_response(response, transcription, chunk_id)

    def transcribe(self, video_file_path: Path) -> Transcription:
        """Use Google speech-to-text recognize API to transcribe video to text"""
        logger.debug(f"Transcribing file: '{video_file_path}'")
        video = VideoFile(video_file_path)
        audio_content, audio_file_path = video.generate_audio_file_and_get_content(self.generated_dir)
        config = {
            **self.default_cfg_kwargs,
            "sample_rate_hertz": video.audio_data.sampling_rate,
        }

        audio_chunks = self._chunk_audio_file(
            audio_file_path=str(audio_file_path), total_duration=math.ceil(video.audio_data.duration_minutes)
        )
        chunk_ids = list(range(len(audio_chunks)))

        transcription_json_save_path = Path(f"{str(self.generated_dir)}/{video.file_path.stem}.json")
        transcription = Transcription(save_path=transcription_json_save_path)
        make_transcription_fn = functools.partial(self._make_transcription, transcription=transcription, config=config)

        # Make transcription requests in parallel using thread pool
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(make_transcription_fn, audio_chunks, chunk_ids)

        transcription.to_json_file()
        return transcription
