import logging
import sys
from pathlib import Path

from . import utils
from .commands import get_cmd_arguments
from .transcriber import GoogleVideoTranscriber
from .transcription import Transcription

LOG_LEVEL = "DEBUG"
GENERATED_FILES_DIR = "generated"

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)


def main() -> None:
    args = get_cmd_arguments()
    file = Path(args.file)
    utils.make_dir(GENERATED_FILES_DIR)
    transcription = None

    if not file.is_file():
        logger.error(f"Invalid file path: {file.absolute()}")
        return

    if args.word is None and args.phrase is None:
        logger.error("Search for word or phrase cmd line arg required (--word or --phrase)")
        return

    if args.cache:
        transcription_json_path = Path(f"{GENERATED_FILES_DIR}/{file.stem}.json")
        if transcription_json_path.is_file():
            logger.debug(f"Generated transcription already exists, using: {transcription_json_path} for search")
            transcription = Transcription.from_json_file(json_file_path=transcription_json_path)

    if transcription is None:
        transcriber = GoogleVideoTranscriber(generated_dir=GENERATED_FILES_DIR)
        transcription = transcriber.transcribe(file)

    if args.word is not None:
        transcription.search_word(args.word)

    if args.phrase is not None:
        transcription.search_phrase(args.phrase)


if __name__ == "__main__":
    sys.exit(main())
