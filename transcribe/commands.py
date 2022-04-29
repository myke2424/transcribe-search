import argparse
from typing import Protocol, List


class Command(Protocol):
    def prepare_parser(self, parser: argparse.ArgumentParser) -> None:
        """ Add parser arguments """


class FileCommand:
    """ Video file path used for transcription"""

    def prepare_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument('-f', '--file', help=self.__doc__, required=True)


class WordSearchCommand:
    """ Search for word in transcription and display results"""

    def prepare_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument('-w', '--word', help=self.__doc__)


class PhraseSearchCommand:
    """Search for phrase in transcription and display results'"""

    def prepare_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument('-p', '--phrase', help=self.__doc__)


COMMANDS: List[Command] = [
    FileCommand(),
    WordSearchCommand(),
    PhraseSearchCommand()
]


def get_cmd_arguments() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Search transcription root parser')

    for command in COMMANDS:
        assert command.__class__.__name__.endswith("Command")
        command.prepare_parser(parser)

    args = parser.parse_args()
    return args
