import datetime
import os
from contextlib import contextmanager
from pathlib import Path

from rich.console import Console
from rich.table import Table


@contextmanager
def open_then_remove(path: str, mode: str) -> None:
    """Get the file contents then remove the file"""
    file = open(path, mode)

    try:
        yield file
    finally:
        file.close()
        os.remove(path)


def build_result_table(
    word: str,
) -> Table:
    """Build table for CLI output"""
    table = Table(title=f"Search Results For Word: ({word})")
    table.add_column("Occurrence", style="cyan")
    table.add_column("Start Time", style="green")
    table.add_column("End Time", justify="right", style="green")
    return table


def print_table(table: Table) -> None:
    """Print the table to the terminal"""
    console = Console()
    console.print(table)


def make_dir(dirname: str) -> None:
    """Create directory if it doesn't exist"""
    if not Path(dirname).is_dir():
        os.mkdir(dirname)


def create_timedelta_from_timestamp(timestamp: str) -> datetime.timedelta:
    """Create timedelta object from "0:00:00" timestamp format"""
    time = datetime.datetime.strptime(timestamp, "%H:%M:%S")
    delta = datetime.timedelta(hours=time.hour, minutes=time.minute, seconds=time.second)
    return delta
