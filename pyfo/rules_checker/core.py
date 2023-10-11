"""
Created on Aug 4, 2023

@author: osi
"""
from __future__ import annotations

from pyfo.code_parser.core import SyntaxTree
from pyfo.code_parser.datatypes import (
    SyntaxTreeElement,
    SyntaxTreeElementAnnotation,
    SyntaxTreeElementAssign,
    SyntaxTreeElementClass,
    SyntaxTreeElementFunction,
    SyntaxTreeElementImport,
    SyntaxTreeElementImportFrom,
)
from pyfo.console import (
    Group,
    Padding,
    Panel,
    RenderableType,
    console,
)

from abc import ABC, abstractmethod
from importlib import import_module
from pathlib import Path
from shutil import move
from tempfile import NamedTemporaryFile
from typing import Any, Callable, Dict, List, Sequence, TextIO, Tuple, Type


class RulesCheckerFindingReportedError(RuntimeError):
    rich_rows: List[RenderableType]

    def __init__(self) -> None:
        self.rich_rows = list()

    def add(self, item: RenderableType) -> None:
        self.rich_rows.append(Padding(item))

    def __iadd__(self, item: RenderableType) -> None:
        self.add(item)
        return self


class RuleChecker(ABC):
    st: SyntaxTree
    nodes: Tuple[SyntaxTreeElement, ...]
    args: Dict[str, Any]
    id: str  # Filled in by RuleChecker.register decorator
    title: str  # Filled in by RuleChecker.register decorator
    checkers: Dict[
        str, Type[RuleChecker]
    ] = dict()  # Updated by RuleChecker.register decorator
    _finding: _FindingReporter | None = None

    def __init__(self, st: SyntaxTree, **kwargs) -> None:
        self.st = st
        self.nodes = st.root.nodes
        self.args = kwargs

    @abstractmethod
    def run_check(self) -> None:
        """Rule checker execution method."""
        raise NotImplementedError()

    @abstractmethod
    def report_finding(
        self,
        st_elm: SyntaxTreeElement,
        txt: RenderableType,
    ) -> None:
        raise NotImplementedError()

    def report(self, file: Path, st_elm: SyntaxTreeElement) -> _FindingReporter:
        if self._finding:
            return self._finding.clone()
        else:
            self._finding = _FindingReporter(file, st_elm)
            return self._finding

    def resolver(self, st_elm: SyntaxTreeElement) -> _LinesResolver:
        return _LinesResolver(self, st_elm)

    def resolve_finding(
        self,
        st_elm: SyntaxTreeElement,
        txt: RenderableType,
        refactor: Callable[[SyntaxTreeElement], None],
    ) -> None:
        try:
            self.report_finding(st_elm, txt)
        except RulesCheckerFindingReportedError as e:
            if self.args["refactor"]:
                refactor(st_elm)
            raise

    @classmethod
    def register(cls, *, id: str, title: str) -> None:
        def wrapper(registered_cls) -> None:
            registered_cls.id = id
            registered_cls.title = title
            cls.checkers[id] = registered_cls
            return registered_cls

        return wrapper

    def public_members(self, *, sort: bool = False) -> Tuple[SyntaxTreeElement, ...]:
        def is_public_root(name: str) -> bool:
            return not name.startswith("_") and not any(
                map(lambda i: i in name, (".", "["))
            )

        public_members = list()

        for member in self.nodes:
            match member:
                case SyntaxTreeElementClass() | SyntaxTreeElementFunction() | SyntaxTreeElementAnnotation():
                    if is_public_root(member.name):
                        public_members.append(member)
                case SyntaxTreeElementImport() | SyntaxTreeElementImportFrom():
                    for alias in member.nodes:
                        if is_public_root(alias.name):
                            public_members.append(alias)
                case SyntaxTreeElementAssign():
                    for var in member.vars:
                        if is_public_root(var.name):
                            public_members.append(var)

        if sort:
            public_members = sorted(public_members, key=lambda l: l.name)

        return tuple(public_members)

    def refactor_none(self, st_elm: SyntaxTreeElement) -> None:
        with self.report(self.st.file_info.file, st_elm) as report:
            report += (
                "[bright_reg bold]!!! REFACTORING UNAVAILABLE FOR THIS FINDING !!![/]\n"
            )

    def refactor_remove(self, st_elm: SyntaxTreeElement) -> None:
        with self.resolver(st_elm) as resolver:
            resolver.remove()

    def _print(self, file: TextIO, txt: str) -> None:
        lines = txt.split("\n")
        for line in lines:
            print(line, file=file)


def check_rules(st: SyntaxTree, **kwargs) -> None:
    """Run set of checks on syntax tree.

    :param st:    Syntax tree to be checked.

    :return:      `True` on success, `False` if some of tests failed.
    """
    rules_checker = import_module("pyfo.rules_checker")
    for attr_name in dir(rules_checker):
        attr = getattr(rules_checker, attr_name)
        try:
            # Try another if attribute is not rule checker
            if not issubclass(attr, RuleChecker) or attr is RuleChecker:
                continue
        except TypeError:
            continue  # Only classes may have subclasses

        # Run check
        descr = getattr(attr, "title", attr_name)
        console.print(
            f"\t:white_small_square: Checking [b green]{descr}[/] ...", end=""
        )

        try:
            rc = attr(st, **kwargs)
            rc.run_check()
            console.print("[blue] :thumbs_up: PASSED")
        except RulesCheckerFindingReportedError as e:
            console.print("[red] :prohibited: FAILED")
            console.print(
                Panel(
                    Group(*e.rich_rows),
                    title="Finding",
                    title_align="left",
                    border_style="bold red",
                    style="bright_red",
                )
            )
            raise


class _FindingReporter:
    file: Path | None
    st_elm: SyntaxTreeElement
    finding_report: RulesCheckerFindingReportedError

    def __init__(
        self,
        file: Path,
        st_elm: SyntaxTreeElement,
        finding_report: RulesCheckerFindingReportedError | None = None,
    ) -> None:
        if finding_report:
            self.file = None
            self.finding_report = finding_report
        else:
            self.file = file
            self.st_elm = st_elm
            self.finding_report = RulesCheckerFindingReportedError()

    def __enter__(self) -> None:
        if self.file:
            self.finding_report += f"Reported in [repr.filename]{self.file}[/]:[repr.number]{self.st_elm.lineno}[/]\n\n"
        return self.finding_report

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.file:
            self.finding_report.add("\n\n")
            raise self.finding_report

    def clone(self) -> _FindingReporter:
        return _FindingReporter(None, self.st_elm, self.finding_report)


class _Lines:
    def __init__(self) -> None:
        self.lines = list()

    def __getitem__(self, idx: int) -> str:
        return self.lines[idx - 1]

    def __setitem__(self, idx: int, val: str) -> None:
        self.lines[idx - 1] = val


class _LinesResolver:
    def __init__(self, rc: RuleChecker, st_elm: SyntaxTreeElement) -> None:
        self.rc = rc
        self.st = rc.st
        self.st_elm = st_elm
        self.line = _Lines()

    def __enter__(self) -> None:
        with self.st.file_info.file.open("r") as f:
            self.original = f.readlines()
            self.line.lines = self.original[:]
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if not exc_type:
            with self.rc.report(self.st.file_info.file, self.st_elm) as report:
                if self != self.original:
                    report += "[logging.level.info]Wring fix into file ...[/]"

                    with NamedTemporaryFile("w", delete=False) as f:
                        f.writelines(self.line.lines)

                    move(f.name, self.st.file_info.file)
                    self.st.reload()
                else:
                    report += "[logging.level.info]Nothing has changed ...[/]"

    def append_to_end(self, lines: Sequence[str]) -> None:
        self.line.lines += ["\n", "\n"] + lines

    def remove(self, st_elm: SyntaxTreeElement | None = None) -> None:
        lineno, end_lineno = self._range(st_elm)
        del self.line.lines[lineno - 1 : end_lineno]

    def replace(
        self, lines: Sequence[str], st_elm: SyntaxTreeElement | None = None
    ) -> None:
        self.replace_lines(lines, *self._range(st_elm))

    def replace_lines(self, lines: Sequence[str], lineno: int, end_lineno: int) -> None:
        above, bellow = self.line.lines[: lineno - 1], self.line.lines[end_lineno:]
        self.line.lines = above + lines + bellow

    def insert_above(self, lines: Sequence[str]) -> None:
        lineno = max(self._range_with_zero()[0], 1)
        above, bellow = self.line.lines[: lineno - 1], self.line.lines[lineno - 1 :]
        self.line.lines = above + lines + bellow

    def insert_bellow(self, lines: Sequence[str]) -> None:
        _, end_lineno = self._range()
        above, bellow = self.line.lines[:end_lineno], self.line.lines[end_lineno:]
        self.line.lines = above + lines + bellow

    def _range(self, st_elm: SyntaxTreeElement | None = None) -> None:
        if not st_elm:
            st_elm = self.st_elm

        lineno, end_lineno = st_elm.lineno, st_elm.end_lineno

        assert (
            lineno > 0 and end_lineno > 0
        ), f"Irrelevant line numbers ({lineno=}, {end_lineno=})"

        return lineno, end_lineno

    def _range_with_zero(self) -> None:
        lineno, end_lineno = self.st_elm.lineno, self.st_elm.end_lineno
        assert (
            lineno >= 0 and end_lineno >= 0
        ), f"Irrelevant line numbers ({lineno=}, {end_lineno=})"
        return lineno, end_lineno


__all__ = (
    "RuleChecker",
    "RulesCheckerFindingReportedError",
    "check_rules",
)
