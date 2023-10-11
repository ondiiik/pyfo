"""
Created on Aug 4, 2023

@author: osi
"""
from __future__ import annotations

from .core import RuleChecker

from pyfo.code_parser.datatypes import (
    SyntaxTreeElement,
    SyntaxTreeElementImport,
    SyntaxTreeElementImportFrom,
    SyntaxTreeElementString,
)
from pyfo.console import Markdown, RenderableType


@RuleChecker.register(id="imports", title="Imports ordering")
class CheckImports(RuleChecker):
    def run_check(self) -> None:
        self._prepare_nodes()
        self._check_imports_at_beginning()
        self._check_imports_one_name_per_line()
        self._check_imports_one_from_only_once()
        self._check_imports_sort()
        self._check_imports_from_sort()

    def report_finding(
        self,
        st_elm: SyntaxTreeElement,
        txt: RenderableType,
    ) -> None:
        with self.report(self.st.file_info.file, st_elm) as report:
            report += txt

    def _prepare_nodes(self) -> None:
        root = list(self.st.root.nodes)
        for idx, node in enumerate(root):
            if not isinstance(node, SyntaxTreeElementString):
                break
        self.nodes = root[idx:]
        self.imports_only = False

        for idx, node in enumerate(self.nodes):
            if not isinstance(
                node, (SyntaxTreeElementImport, SyntaxTreeElementImportFrom)
            ):
                break
        else:
            self.imports_only = True

        self.imports = self.nodes[:idx]
        all_nodes = list(self.st.root)
        self.rest = all_nodes[all_nodes.index(self.imports[-1]) + 1 :] if self.imports else []

    def _check_imports_at_beginning(self) -> None:
        if self.imports_only:
            return

        for node in self.rest:
            if isinstance(node, (SyntaxTreeElementImport, SyntaxTreeElementImportFrom)):
                names = ", ".join([f"`{name}`" for name in node.names])
                self.resolve_finding(
                    node,
                    Markdown(f"Found import of {names} inside script body.\n"),
                    self._refactor_move_to_imports,
                )

    def _check_imports_one_name_per_line(self) -> None:
        for node in self.imports:
            if isinstance(node, SyntaxTreeElementImport) and len(node.names) > 1:
                names = ", ".join([f"`{name}`" for name in node.names])
                self.resolve_finding(
                    node,
                    Markdown(
                        f"Found import with multiple modules {names} on one line.\n"
                    ),
                    self._refactor_split_into_more_lines,
                )

    def _check_imports_one_from_only_once(self) -> None:
        imports = list(
            filter(
                lambda node: isinstance(node, SyntaxTreeElementImportFrom), self.imports
            )
        )

        for node in imports:
            same_nodes = list(filter(lambda n: n.name == node.name, imports))
            if len(same_nodes) != 1:
                # Generate list of imported items
                self.fix_data = same_nodes[1]
                aliasses = [alias for node in same_nodes for alias in node.nodes]
                aliasses.sort(key=lambda node: node.name)
                names = [
                    alias.name
                    if alias.name == alias.source_name
                    else f"{alias.source_name} as {alias.name}"
                    for alias in aliasses
                ]

                # Report about finding
                self.resolve_finding(
                    node,
                    Markdown(
                        f"""There seems to be import from {node.name} on multiple places.

Suggesting to replace all of them by following import structure:

```python
from {node.name} import {", ".join(names)}
```
"""
                    ),
                    self._refactor_merge_import_from,
                )

    def _check_imports_sort(self) -> None:
        # Sort imports by module names
        pairs = []
        for node in self.imports:
            name = node.name if hasattr(node, "name") else node.names[0]
            match name:
                case s if s.startswith("_"):
                    name = "0_" + name
                case s if s.startswith("."):
                    name = "1_" + name
                case _:
                    if any([name.startswith(mn) for mn in self.args["custom_modules"]]):
                        name = "2_" + name
                    else:
                        name = "3_" + name
            pairs.append((name, node))
        sorted = list(dict(pairs[:]).items())
        sorted.sort(key=lambda i: i[0])

        # Checks if imports are alphabetically sorted
        if pairs != sorted:
            suggested_fix = []
            key_old = "0"
            for key, node in sorted:
                if key[0] != key_old:
                    suggested_fix += "\n"
                    key_old = key[0]
                suggested_fix += node.lines

            self.fix_data = suggested_fix
            self.resolve_finding(
                node,
                Markdown(
                    f"""Import seems not to be alphabetically sorted.

Suggesting following import structure:

```python
{"".join(suggested_fix)}
```
"""
                ),
                self._refactor_sort_modules,
            )

    def _check_imports_from_sort(self) -> None:
        imports = list(
            filter(
                lambda node: isinstance(node, SyntaxTreeElementImportFrom), self.imports
            )
        )

        for node in imports:
            names = [alias.repr for alias in node.nodes]
            sorted = list(set(names))
            sorted.sort()
            if names != sorted:
                suggested_fix = [f"from {node.name} import {', '.join(sorted)}\n"]
                self.fix_data = suggested_fix
                self.resolve_finding(
                    node,
                    Markdown(
                        f"""Elements imported from module `{node.name}` seems not to be alphabetically sorted.

Suggesting following import structure:

```python
{"".join(suggested_fix)}
```
"""
                    ),
                    self._refactor_sort_imported_from_items,
                )

    def _refactor_move_to_imports(self, st_elm: SyntaxTreeElement) -> None:
        with self.resolver(self.imports[-1]) as resolver:
            # Remove position of import
            lines = st_elm.lines
            resolver.remove(st_elm)

            # Fix indent
            indent = len(lines[0]) - len(lines[0].lstrip())
            lines = [line[indent:] for line in lines]

            # Append import to the end of imports section
            resolver.insert_bellow(lines)

    def _refactor_split_into_more_lines(self, st_elm: SyntaxTreeElement) -> None:
        with self.resolver(st_elm) as resolver:
            lines = [
                f"import {alias.name}\n"
                if alias.source_name == alias.name
                else f"import {alias.source_name} as {alias.name}\n"
                for alias in st_elm.nodes
            ]
            resolver.replace(lines)

    def _refactor_merge_import_from(self, st_elm: SyntaxTreeElement) -> None:
        aliasses = [alias for node in [st_elm, self.fix_data] for alias in node.nodes]
        names = list(
            {
                alias.name
                if alias.name == alias.source_name
                else f"{alias.source_name} as {alias.name}"
                for alias in aliasses
            }
        )
        names.sort()

        with self.resolver(st_elm) as resolver:
            resolver.remove(self.fix_data)
            resolver.replace([f"from {st_elm.name} import {', '.join(names)}\n"])

    def _refactor_sort_modules(self, st_elm: SyntaxTreeElement) -> None:
        with self.resolver(st_elm) as resolver:
            resolver.replace_lines(
                self.fix_data, self.imports[0].lineno, self.imports[-1].end_lineno
            )

    def _refactor_sort_imported_from_items(self, st_elm: SyntaxTreeElement) -> None:
        with self.resolver(st_elm) as resolver:
            resolver.replace(self.fix_data)


__all__ = ("CheckImports",)
