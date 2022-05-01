import logging
import sys
from pathlib import Path

from . import utils
from .commands import get_cmd_arguments
from .config import Config
from .transcriber import GoogleVideoTranscriber, Transcription

logging.basicConfig(level=Config.LOG_LEVEL)
logger = logging.getLogger(__name__)
logger.setLevel(Config.LOG_LEVEL)


def main() -> None:
    args = get_cmd_arguments()
    file = Path(args.file)
    utils.make_dir(Config.GENERATED_FILES_DIR)
    transcription = None

    if not file.is_file():
        logger.error(f"Invalid file path: {file.absolute()}")
        return

    if args.word is None and args.phrase is None:
        logger.error("Search for word or phrase cmd line arg required (--word or --phrase)")
        return

    if args.cache:
        transcription_json_path = Path(f"{Config.GENERATED_FILES_DIR}/{file.stem}.json")
        if transcription_json_path:
            logger.debug(f"Generated transcription already exists, using: {transcription_json_path} for search")
            transcription = Transcription.from_json(json_file_path=transcription_json_path)

    if transcription is None:
        transcriber = GoogleVideoTranscriber()
        transcription = transcriber.transcribe(file)

    if args.word is not None:
        transcription.search_word(args.word)

    if args.phrase is not None:
        transcription.search_phrase(args.phrase)


if __name__ == "__main__":
    sys.exit(main())
