import sys
from transcriber import GoogleVideoTranscriber
from commands import get_cmd_arguments



# Thoughts - How to store and search for words?
# Maybe use a trie, each node will be a word
# Search for a word in the transcription; show all timestamps in the video that word was said


import argparse


def main() -> None:
    args = get_cmd_arguments()

    if args.word is None and args.phrase is None:
        print("Search for word or phrase cmd line arg required")
        return

    transcriber = GoogleVideoTranscriber()
    transcription = transcriber.transcribe(args.file)

    if args.word is not None:
        transcription.search_word(args.word)

    if args.phrase is not None:
        transcription.search_phrase(args.phrase)


if __name__ == "__main__":
    sys.exit(main())
