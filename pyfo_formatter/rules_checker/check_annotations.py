"""
Created on Aug 4, 2023

@author: osi
"""
from __future__ import annotations

from .core import RuleChecker

from pyfo_formatter.code_parser.datatypes import (
    SyntaxTreeElement,
    SyntaxTreeElementFunction,
    SyntaxTreeElementImportFrom,
    SyntaxTreeElementString,
)
from pyfo_formatter.console import Markdown, RenderableType

from typing import Tuple


@RuleChecker.register(
    id="annotations", title="Presence of annotations (not their validity)"
)
class CheckAnnotations(RuleChecker):
    def run_check(self) -> None:
        self._check_return_annotations()
        self._check_future_import_annotations()

    def report_finding(
        self,
        st_elm: SyntaxTreeElement,
        txt: RenderableType,
    ) -> None:
        with self.report(self.st.file_info.file, st_elm) as report:
            report += txt

    def _check_return_annotations(self) -> None:
        for node in self.st.root:
            if isinstance(node, SyntaxTreeElementFunction) and node.returns is None:
                self.resolve_finding(
                    node,
                    Markdown(
                        f"There is missing `-> None` return annotation in function `{node.name}` definition.\n"
                    ),
                    self._refactor_apend_return_annotation,
                )

    def _check_future_import_annotations(self) -> None:
        if not self._from_future_import_annotations:
            node = (
                self.st.root.nodes[0] if len(self.st.root.nodes) > 0 else self.st.root
            )
            self.resolve_finding(
                node,
                Markdown(
                    "There shall be import of annotations from `__future__` package at the beginning.\n"
                ),
                self._refactor_apend_import
                if isinstance(node, SyntaxTreeElementString)
                else self._refactor_prepend_import,
            )

    @property
    def _from_future_import_annotations(
        self,
    ) -> Tuple[SyntaxTreeElementImportFrom, ...]:
        return tuple(
            filter(
                lambda i: isinstance(i, SyntaxTreeElementImportFrom)
                and "__future__" == i.name
                and "annotations" in i.names,
                self.nodes,
            )
        )

    def _refactor_apend_return_annotation(self, st_elm: SyntaxTreeElement) -> None:
        with self.resolver(st_elm) as resolver:
            for line_no in reversed(range(st_elm.lineno, st_elm.nodes[0].lineno)):
                last_line = resolver.line[line_no].rstrip()
                ll = last_line.strip()
                if ll.startswith("#"):
                    continue
                if ll.endswith("):"):
                    break

            if last_line.endswith("):"):
                resolver.line[line_no] = last_line[:-2] + ") -> None:\n"
            else:
                self.refactor_none(st_elm)

    def _refactor_apend_import(self, st_elm: SyntaxTreeElement) -> None:
        with self.resolver(st_elm) as resolver:
            resolver.insert_bellow(["from __future__ import annotations\n\n"])

    def _refactor_prepend_import(self, st_elm: SyntaxTreeElement) -> None:
        with self.resolver(st_elm) as resolver:
            resolver.insert_above(["from __future__ import annotations\n\n"])


__all__ = ("CheckAnnotations",)
