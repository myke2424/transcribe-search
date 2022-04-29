import logging
import sys

from commands import get_cmd_arguments
from transcriber import GoogleVideoTranscriber

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def main() -> None:
    args = get_cmd_arguments()

    if args.word is None and args.phrase is None:
        logger.error("Search for word or phrase cmd line arg required (--word or --phrase)")
        return

    transcriber = GoogleVideoTranscriber()
    transcription = transcriber.transcribe(args.file)

    if args.word is not None:
        transcription.search_word(args.word)

    if args.phrase is not None:
        transcription.search_phrase(args.phrase)


if __name__ == "__main__":
    sys.exit(main())
