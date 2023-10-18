"""
Created on Aug 8, 2023

@author: osi
"""
from __future__ import annotations

from pyfo_formatter.code_parser import SyntaxTree
from pyfo_formatter.console import Group, Panel, RenderableType, console
from pyfo_formatter.rules_checker.core import (
    RulesCheckerFindingReportedError,
    check_rules,
)

from glob import glob
from os import system
from pathlib import Path
from sys import executable
from typing import List, Sequence, Tuple


def run_checker(
    files: Sequence[str],
    *,
    recursive: bool = True,
    refactor: bool = False,
    autoformat: bool = False,
    print_tree: bool = False,
    print_decorations: bool = True,
    custom_modules: List[str],
) -> Tuple[RenderableType, ...]:
    """Run rules checker on selected files.

    :param recursive:      Do recursive files search.
    :param print_tree:     Print syntax tree of each file.
    :param refactor:       Do refactoring instead of just check.
    :param autoformat:     Reformat each file by black.
    :param files:          Glob wildcard of files or directory.
    :param custom_modules: List of modules considered as non-3rd party.

    :return:               Count of failures tests
    """
    failures = list()
    panel = Panel if print_decorations else _PannelDummy

    for wildcard in files:
        if Path(wildcard).is_dir():
            wildcard += "/**/*.py"

        for file in glob(wildcard, recursive=recursive):
            console.print("")
            console.print(
                panel(
                    f"Processing file {file}",
                    border_style="bold bright_blue",
                    expand=False,
                    highlight=True,
                )
            )
            st = SyntaxTree(file)

            if print_decorations and print_tree:
                console.print(st.rich_tree())
                console.print("")

            try:
                check_rules(st, refactor=refactor, custom_modules=custom_modules)

                if autoformat:
                    # Run black as subprocess because it does not have stable python API - https://black.readthedocs.io/en/stable/faq.html#does-black-have-an-api
                    system(f"{executable} -m black '{file}'")
            except RulesCheckerFindingReportedError as e:
                failures.append(Group(*e.rich_rows))

    return failures


class _PannelDummy(str):
    def __init__(self, txt, *args, **kw) -> None:
        super().__init__(txt)


__all__ = ("run_checker",)
