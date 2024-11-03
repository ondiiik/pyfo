"""
Created on Aug 4, 2023

@author: osi
"""
from __future__ import annotations

from .core import RuleChecker

from pyfo_formatter.code_parser.datatypes import (
    SyntaxTreeElement,
    SyntaxTreeElementAlias,
    SyntaxTreeElementAssign,
    SyntaxTreeElementCall,
    SyntaxTreeElementTuple,
    SyntaxTreeElementAsyncFunction,
)
from pyfo_formatter.console import Markdown, RenderableType

from typing import List, Tuple


@RuleChecker.register(
    id="export_all", title="Correctly filled in __all__ at the end of module"
)
class CheckAllAtTheEnd(RuleChecker):
    def run_check(self) -> None:
        if self.st.file_info.file.name == "__init__.py":
            self._check_init()  # Special rules applied for __init__.py
        else:
            self._check_regular()

    def report_finding(
        self,
        st_elm: SyntaxTreeElement,
        txt: RenderableType,
    ) -> None:
        with self.report(self.st.file_info.file, st_elm) as report:
            report += txt
            report += Markdown(
                f"""
Suggesting to put following to the end of file:

```python
{"".join(self._suggested_fix(st_elm))}
```
"""
            )

    def _check_init(self) -> None:
        all_occurences = self._all_occurences

        if len(all_occurences) > 0:
            self.resolve_finding(
                all_occurences[0],
                Markdown("There shall be no `__all__` in `__init__.py`.\n"),
                self.refactor_remove,
            )

    def _public_members(self) -> tuple:
        return tuple(
            filter(
                lambda i: not isinstance(i, SyntaxTreeElementAlias)
                or "public" in i.tags,
                self.public_members(sort=True),
            )
        )

    def _check_regular(self) -> None:
        # Checks if we have __all__ variable in root
        all_occurences = self._all_occurences
        public_names = tuple(map(lambda i: i.name, self._public_members()))

        match len(all_occurences):
            case 0:
                # No __all__
                if public_names:
                    self.resolve_finding(
                        self.st.root,
                        Markdown(
                            "There is no `__all__` at the end of file when there are public members declared.\n"
                        ),
                        self._refactor_append,
                    )
            case 1:
                # Exactly one __all__ - do we have something to publish?
                variable_last = self.st.root.nodes[-1]
                variable_all = all_occurences[0]

                if not public_names:
                    self.resolve_finding(
                        variable_all.ast_inst,
                        Markdown(
                            "There shall be no `__all__` when there are no public members declared.\n"
                        ),
                        self.refactor_remove,
                    )

                if (
                    not isinstance(variable_last, SyntaxTreeElementAssign)
                    or variable_last.names[0] != "__all__"
                ):
                    # __all__ is not at the end of file
                    self.resolve_finding(
                        variable_all.ast_inst,
                        Markdown("`__all__` is not at the end of file.\n"),
                        self._refactor_move,
                    )
                else:
                    # Checks that type assigned to __all__ is tuple
                    all_var = variable_all.nodes[0]
                    if not (
                        (
                            isinstance(all_var, SyntaxTreeElementCall)
                            and all_var.name == "tuple"
                        )
                        or isinstance(all_var, SyntaxTreeElementTuple)
                    ):
                        self.resolve_finding(
                            variable_all.ast_inst,
                            Markdown("`__all__` shall be tuple.\n"),
                            self._refactor_replace,
                        )
                        return

                    # Just check if there are all classes
                    if public_names:
                        all_members = (
                            tuple()
                            if isinstance(all_var, SyntaxTreeElementCall)
                            else tuple(map(lambda i: i.value, all_var.nodes))
                        )

                        if public_names != all_members:
                            # It seems there is not exact match - lets have a look what is different
                            for member in all_members:
                                if member not in public_names:
                                    self.resolve_finding(
                                        variable_all.ast_inst,
                                        Markdown(
                                            f"`__all__` points on non-existing member `{member}`.\n"
                                        ),
                                        self._refactor_replace,
                                    )
                            if len(public_names) < len(all_members):
                                self.resolve_finding(
                                    variable_all.ast_inst,
                                    Markdown(
                                        "It seems that `__all__` contains more members then those defined here.\n"
                                    ),
                                    self._refactor_replace,
                                )
                            elif len(public_names) > len(all_members):
                                missing_members = tuple(
                                    filter(lambda i: i not in all_members, public_names)
                                )
                                self.resolve_finding(
                                    variable_all.ast_inst,
                                    Markdown(
                                        f"It seems that `__all__` does not contain all members (missing {', '.join(map(lambda i: '`'+i+'`', missing_members))}).\n"
                                    ),
                                    self._refactor_replace,
                                )
                            else:
                                self.resolve_finding(
                                    variable_all.ast_inst,
                                    Markdown(
                                        f"It seems that `__all__` is not alphabetically sorted.\n"
                                    ),
                                    self._refactor_replace,
                                )
                    else:
                        if variable_all.nodes[0].nodes:
                            self.resolve_finding(
                                variable_all.ast_inst,
                                Markdown(
                                    f"There are not members to put into `__all__`.\n"
                                ),
                                self._refactor_replace,
                            )

            case _:
                # Multiple __all__
                self.resolve_finding(
                    all_occurences[0].ast_inst,
                    Markdown(
                        "There is multiple assignments to `__all__`, first is here.\n"
                    ),
                    self.refactor_remove,
                )

    @property
    def _all_occurences(self) -> Tuple[SyntaxTreeElementAssign, ...]:
        return tuple(
            filter(
                lambda i: isinstance(i, SyntaxTreeElementAssign)
                and "__all__" in i.names,
                self.nodes,
            )
        )

    def _suggested_fix(self, st_elm: SyntaxTreeElement) -> List[str]:
        public_names = self._public_members()

        if public_names:
            fix = ["__all__ = (\n"]

            for member in public_names:
                fix.append(f'    "{member.name}",\n')

            fix.append(f")\n")
        else:
            fix = []

        return fix

    def _refactor_append(self, st_elm: SyntaxTreeElement) -> None:
        with self.resolver(st_elm) as resolver:
            resolver.append_to_end(self._suggested_fix(st_elm))

    def _refactor_move(self, st_elm: SyntaxTreeElement) -> None:
        self.refactor_remove(st_elm)
        self._refactor_append(st_elm)

    def _refactor_replace(self, st_elm: SyntaxTreeElement) -> None:
        with self.resolver(st_elm) as resolver:
            resolver.replace(self._suggested_fix(st_elm))


__all__ = ("CheckAllAtTheEnd",)
