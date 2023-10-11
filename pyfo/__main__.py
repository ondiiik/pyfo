"""
Created on Aug 3, 2023

@author: osi
"""
from __future__ import annotations

from pyfo.console import Table, console, console_err
from pyfo.rules_checker import run_checker

import rich_click as click
from sys import exit


@click.command()
@click.option("--recursive", "-r", is_flag=True, help="Search for files recursively.")
@click.option(
    "--refactor",
    "-f",
    default=0,
    help="Modify target files instead of checking them. Number specifies maximal count of recursive refactor calls.",
)
@click.option(
    "--autoformat",
    "-a",
    is_flag=True,
    help="Reformat each file by black.",
)
@click.option(
    "--custom-modules",
    "-m",
    multiple=True,
    type=str,
    help="Modules with this name are considered as custom (non 3rd party) modules.",
)
@click.option("--print-tree", "-t", is_flag=True, help="Print syntax tree.")
@click.argument("files", required=True, nargs=-1)
def main(*args, **kwargs) -> None:
    for try_idx in range(1, max(kwargs["refactor"], 1) + 1):
        failures = run_checker(*args, **kwargs)

        if failures:
            console_err.print(f"\n\n[red bold]{len(failures)} CHECKS FAILED[/]\n\n")
            table = Table(border_style="bold red", show_lines=True)
            table.add_column(
                "Findings summary", header_style="bold red", style="bright_red"
            )

            for failure in failures:
                table.add_row(failure)

            console_err.print(table)

            if try_idx == kwargs["refactor"]:
                console_err.print(f"Is suggested to re-run tests after refactoring\n\n")
                exit(1)
        else:
            console.print("\n\nSUCCESS\n\n")
            exit(0)


main()


__all__ = ("main",)
