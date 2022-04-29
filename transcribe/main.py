import logging
import sys
from pathlib import Path

from commands import get_cmd_arguments
from transcriber import GoogleVideoTranscriber

LOG_LEVEL = logging.INFO
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)


def main() -> None:
    args = get_cmd_arguments()
    file = Path(args.file)

    if not file.is_file():
        logger.error(f"Invalid file path: {file.absolute()}")
        return

    if args.word is None and args.phrase is None:
        logger.error("Search for word or phrase cmd line arg required (--word or --phrase)")
        return

    transcriber = GoogleVideoTranscriber()
    transcription = transcriber.transcribe(file)

    if args.word is not None:
        transcription.search_word(args.word)

    if args.phrase is not None:
        transcription.search_phrase(args.phrase)


if __name__ == "__main__":
    sys.exit(main())
