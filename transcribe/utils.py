import os
from contextlib import contextmanager

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
    #   os.remove(path)


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
