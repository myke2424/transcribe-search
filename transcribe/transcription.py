""" Transcription data-structure """

import json
import logging
from collections import defaultdict, namedtuple
from datetime import timedelta
from pathlib import Path
from typing import Dict, List, Optional

from . import utils

logger = logging.getLogger(__name__)
Timestamp = namedtuple("Timestamp", "start end")

# Store list of timestamps for each word, i.e. transcription[word] = [(timestamp), (timestamp), ...]
# use for word search
Words = Dict[str, List[Timestamp]]


class Transcription:
    def __init__(self, save_path: Path, words: Optional[Words] = None) -> None:
        self.save_path = save_path
        self._words: Words = words or defaultdict(list)

    def __eq__(self, other: 'Transcription') -> bool:
        if isinstance(other, self.__class__):
            return self._words == other._words
        else:
            return False

    @classmethod
    def from_json_file(cls, json_file_path: str) -> "Transcription":
        """Constructor, create transcription object from transcription json file"""
        path = Path(json_file_path)

        if not path.is_file():
            raise FileNotFoundError(f"Transcription JSON File: {json_file_path} doesnt exist")

        if path.suffix != ".json":
            logger.error("Failed to create transcription object from json, file isn't of type json")
            raise ValueError(f"File: {json_file_path} is not a valid json file")

        words = cls._deserialize_words_from_json_file(json_file_path)
        return cls(save_path=json_file_path, words=words)

    @staticmethod
    def _deserialize_words_from_json_file(json_file_path: str) -> Words:
        """Deserialize transcription json file to build the words' data structure"""
        with open(str(json_file_path)) as file:
            words = json.load(file)

        for word, timestamps in words.items():
            for i in range(len(timestamps)):
                start_str, end_str = timestamps[i]
                start, end = utils.create_timedelta_from_timestamp(start_str), utils.create_timedelta_from_timestamp(
                    end_str)
                timestamps[i] = Timestamp(start, end)
        return words

    def add_word_and_timestamp(self, word: str, start_time: timedelta, end_time: timedelta) -> None:
        """Append word with timestamp to dict"""
        logger.debug(f"Adding to transcription: Word=({word}), start=({start_time}), end=({end_time})")
        self._words[word].append((start_time, end_time))

    def search_word(self, word: str) -> None:
        """Search the transcription for the word and display the results"""
        logger.info(f"Searching for word: {word}")

        if self._words[word] is None:
            logger.debug(f"Word: {word} doesn't exist in transcription")
            return

        logger.info(f"Found {len(self._words[word])} results for ({word}) search")
        table = utils.build_result_table(word)

        for i, timestamp in enumerate(self._words[word]):
            start, end = timestamp
            table.add_row(f"{i + 1}", f"{start}", f"{end}")
        utils.print_table(table)

    def search_phrase(self, phrase: str) -> None:
        """Search the transcription for the phrase and display the results"""
        # Implement trie data structure for phrase search
        raise NotImplementedError

    def to_json_file(self) -> None:
        """Save transcription to json file"""
        with self.save_path.open(mode="w") as f:
            json.dump(self._words, f, default=str)  # default str so datetime is serializable
