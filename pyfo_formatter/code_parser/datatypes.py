"""
Created on Aug 3, 2023

@author: osi
"""
from __future__ import annotations

import ast_comments as ast
from dataclasses import dataclass
from pathlib import Path
from typing import (
    Dict,
    List,
    Sequence,
    Tuple,
    Type,
)
from typing_extensions import override

_ast2ste: Dict[
    Type[ast.stmt], Type[RuleChecker]
] = dict()  # Updated by _register_ast decorator

_ESC_TAG = "# :~PYFO~: "


def node_alias(name: str, icon: str = "small_blue_diamond") -> str:
    return f":{icon}: [bold yellow]{name}[/]"


def _register_ast(ast_type: Type[ast.stmt]) -> None:
    def wrapper(registered_cls) -> None:
        global _ast2ste
        _ast2ste[ast_type] = registered_cls
        return registered_cls

    return wrapper


@dataclass(frozen=True)
class FileInfo:
    file: Path
    lines: List[str]


@dataclass(frozen=True)
class SyntaxTreeElement:
    rich_alias: str
    ast_inst: ast.stmt
    nodes: Tuple[SyntaxTreeElement] | None
    tags: Tuple[str, ...]
    file_info: FileInfo

    def __iter__(self) -> None:
        if self.nodes is not None:
            for node in self.nodes:
                yield node
                yield from iter(node)
            if hasattr(self, "else_nodes") and self.else_nodes:
                for node in self.else_nodes:
                    yield node
                    yield from iter(node)

    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=":globe_with_meridians:",
            nodes=None,
            tags=tuple(),
            file_info=file_info,
        )

    @property
    def lineno(self) -> None:
        return getattr(self.ast_inst, "lineno", 0)

    @property
    def end_lineno(self) -> None:
        return getattr(self.ast_inst, "end_lineno", 0)

    @property
    def lines(self) -> None:
        lineno, end_lineno = self.lineno, self.end_lineno

        if not lineno or not end_lineno:
            return []

        return self.file_info.lines[lineno - 1 : end_lineno]

    @classmethod
    def register_ast(cls, *, ast_type: Type[ast.stmt]) -> None:
        def wrapper(registered_cls) -> None:
            registered_cls.id = id
            registered_cls.title = title
            cls.checkers[id] = registered_cls
            return registered_cls

        return wrapper

    @override
    def __str__(self) -> str:
        return self.rich_alias


@dataclass(frozen=True)
class SyntaxTreeElementRoot(SyntaxTreeElement):
    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=":classical_building:",
            nodes=_build_elements(file_info, ast_inst.body),
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
        )


@_register_ast(ast.Constant)
@dataclass(frozen=True)
class SyntaxTreeElementConstant(SyntaxTreeElement):
    value: str | bytes | int | float | None

    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        match ast_inst.value:
            case str():
                return SyntaxTreeElementString.build(file_info, ast_inst)
            case bytes():
                return SyntaxTreeElementBytes.build(file_info, ast_inst)
            case int():
                return SyntaxTreeElementInt.build(file_info, ast_inst)
            case float():
                return SyntaxTreeElementFloat.build(file_info, ast_inst)
            case None:
                return SyntaxTreeElementNone.build(file_info, ast_inst)
            case _:
                if ast_inst.value == Ellipsis:
                    return SyntaxTreeElementEllipsis.build(file_info, ast_inst)
                else:
                    raise RuntimeError(f"Constant of {type(ast_inst.value)} type?")

    @override
    def __str__(self) -> str:
        return f"{self.rich_alias} {self.value=}"


@dataclass(frozen=True)
class SyntaxTreeElementString(SyntaxTreeElementConstant):
    value: str

    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("str", "input_latin_letters"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            value=ast_inst.value,
            file_info=file_info,
        )

    @override
    def __str__(self) -> str:
        string = self.value.replace("\n", "\\n").replace("[", "\\[")
        return f'{self.rich_alias} "{string}"'


@dataclass(frozen=True)
class SyntaxTreeElementBytes(SyntaxTreeElementConstant):
    value: bytes

    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("bytes", "input_latin_uppercase"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            value=ast_inst.value,
            file_info=file_info,
        )

    @override
    def __str__(self) -> str:
        return f'{self.rich_alias} "{self.value}"'


@dataclass(frozen=True)
class SyntaxTreeElementInt(SyntaxTreeElementConstant):
    value: int

    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("int", "input_numbers"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            value=ast_inst.value,
            file_info=file_info,
        )

    @override
    def __str__(self) -> str:
        return f'{self.rich_alias} "{self.value}"'


@dataclass(frozen=True)
class SyntaxTreeElementFloat(SyntaxTreeElementConstant):
    value: float

    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("float", "input_numbers"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            value=ast_inst.value,
            file_info=file_info,
        )

    @override
    def __str__(self) -> str:
        return f'{self.rich_alias} "{self.value}"'


@dataclass(frozen=True)
class SyntaxTreeElementNone(SyntaxTreeElementConstant):
    value: float

    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("None", "no_entry"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            value=None,
            file_info=file_info,
        )


@_register_ast(ast.JoinedStr)
@dataclass(frozen=True)
class SyntaxTreeElementJoinedString(SyntaxTreeElement):
    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("joined str", "input_latin_letters"),
            nodes=_build_elements(file_info, ast_inst.values),
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
        )


@_register_ast(ast.FormattedValue)
@dataclass(frozen=True)
class SyntaxTreeElementFormatedStringValue(SyntaxTreeElement):
    name: str

    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("fstr", "input_latin_letters"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            name=_build_names(ast_inst.value),
            file_info=file_info,
        )

    @override
    def __str__(self) -> str:
        return f"{self.rich_alias} -> {self.name}"


@_register_ast(ast.Import)
@dataclass(frozen=True)
class SyntaxTreeElementImport(SyntaxTreeElement):
    names: Tuple[str]

    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        nodes = _build_elements(file_info, ast_inst.names)
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("import", "package"),
            nodes=nodes,
            tags=_build_tags(file_info, ast_inst),
            names=tuple(map(lambda i: i.source_name, nodes)),
            file_info=file_info,
        )

    @override
    def __str__(self) -> str:
        names = ", ".join(self.names)
        return f"{self.rich_alias} {names}"


@_register_ast(ast.ImportFrom)
@dataclass(frozen=True)
class SyntaxTreeElementImportFrom(SyntaxTreeElement):
    name: str
    names: Tuple[str]

    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        nodes = _build_elements(file_info, ast_inst.names)
        name = ast_inst.module if ast_inst.module else ""
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("import from", "package"),
            nodes=nodes,
            tags=_build_tags(file_info, ast_inst),
            name="." * ast_inst.level + name,
            names=tuple(map(lambda i: i.name, nodes)),
            file_info=file_info,
        )

    @override
    def __str__(self) -> str:
        names = ", ".join(self.names)
        return f"{self.rich_alias} {self.name} -> {names}"


@_register_ast(ast.alias)
@dataclass(frozen=True)
class SyntaxTreeElementAlias(SyntaxTreeElement):
    name: str
    source_name: str
    repr: str

    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        name = ast_inst.asname or ast_inst.name
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("as", "right_arrow"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
            name=name,
            source_name=ast_inst.name,
            repr=name if name == ast_inst.name else f"{ast_inst.name} as {name}",
        )

    @override
    def __str__(self) -> str:
        return f"{self.rich_alias} {self.name}"


@_register_ast(ast.ClassDef)
@dataclass(frozen=True)
class SyntaxTreeElementClass(SyntaxTreeElement):
    name: str
    decorators: Tuple[SyntaxTreeElementCall | SyntaxTreeElementAttribute, ...]

    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("class", "star"),
            nodes=_build_elements(file_info, ast_inst.body),
            tags=_build_tags(file_info, ast_inst),
            name=ast_inst.name,
            decorators=_build_elements(file_info, ast_inst.decorator_list),
            file_info=file_info,
        )

    @override
    def __str__(self) -> str:
        if self.decorators:
            decorators = " ~ " + ", ".join(
                map(
                    lambda i: f"@{_build_names(i)}"
                    if isinstance(i, SyntaxTreeElementAttribute)
                    else f"[blue]@{i.name}[/]",
                    self.decorators,
                )
            )
        else:
            decorators = ""
        return f"{self.rich_alias} [bold bright_blue]{self.name}[/]{decorators}"


@_register_ast(ast.FunctionDef)
@dataclass(frozen=True)
class SyntaxTreeElementFunction(SyntaxTreeElement):
    name: str
    returns: SyntaxTreeElement | None
    decorators: Tuple[SyntaxTreeElementCall | SyntaxTreeElementAttribute, ...]

    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("def", "regional_indicator_f"),
            nodes=_build_elements(file_info, ast_inst.body),
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
            name=ast_inst.name,
            returns=_build_elements(file_info, ast_inst.returns)
            if ast_inst.returns
            else None,
            decorators=_build_elements(file_info, ast_inst.decorator_list),
        )

    @override
    def __str__(self) -> str:
        if self.decorators:
            decorators = " ~ " + ", ".join(
                map(
                    lambda i: f"@{_build_names(i)}"
                    if isinstance(i, SyntaxTreeElementAttribute)
                    else f"[blue]@{i.name}[/]",
                    self.decorators,
                )
            )
        else:
            decorators = ""
        return f"{self.rich_alias} [bold bright_blue]{self.name}[/]{decorators} -> {_build_names(self.returns) or ''}"


@_register_ast(ast.AsyncFunctionDef)
@dataclass(frozen=True)
class SyntaxTreeElementAsyncFunction(SyntaxTreeElement):
    name: str

    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("async def", "regional_indicator_a"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
            name=ast_inst.name,
        )

    @override
    def __str__(self) -> str:
        return f"{self.rich_alias} {self.name}"


@_register_ast(ast.Compare)
@dataclass(frozen=True)
class SyntaxTreeElementCompare(SyntaxTreeElement):
    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("==<>"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
        )


@_register_ast(ast.Assign)
@dataclass(frozen=True)
class SyntaxTreeElementAssign(SyntaxTreeElement):
    names: str
    vars: Tuple[SyntaxTreeElementVariable, ...]

    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("=", "record_button"),
            nodes=_build_elements(file_info, [ast_inst.value]),
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
            names=tuple(map(_build_names, ast_inst.targets)),
            vars=tuple(
                map(
                    lambda ai: SyntaxTreeElementVariable.build(file_info, ai),
                    ast_inst.targets,
                )
            ),
        )

    @override
    def __str__(self) -> str:
        names = ", ".join(self.names)
        return f"{names} {self.rich_alias}"


@_register_ast(ast.AugAssign)
@dataclass(frozen=True)
class SyntaxTreeElementOperateAndAssign(SyntaxTreeElement):
    name: str
    var: Tuple[SyntaxTreeElementVariable, ...]

    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("?=", "record_button"),
            nodes=_build_elements(file_info, [ast_inst.value]),
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
            name=_build_names(ast_inst.target),
            var=SyntaxTreeElementVariable.build(file_info, ast_inst.target),
        )

    @override
    def __str__(self) -> str:
        return f"{self.name} {self.rich_alias}"


@_register_ast(ast.Name)
@dataclass(frozen=True)
class SyntaxTreeElementVariable(SyntaxTreeElement):
    name: str

    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("var", "right_arrow"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
            name=_build_names(ast_inst),
        )

    @override
    def __str__(self) -> str:
        return f"{self.rich_alias} {self.name}"


@_register_ast(ast.Starred)
@dataclass(frozen=True)
class SyntaxTreeElementStarredVariable(SyntaxTreeElement):
    name: str

    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("*"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
            name=_build_names(ast_inst.value),
        )


@_register_ast(ast.Call)
@dataclass(frozen=True)
class SyntaxTreeElementCall(SyntaxTreeElement):
    name: str
    args: Tuple[SyntaxTreeElement, ...]
    kwargs: Dict[str, SyntaxTreeElement]

    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("call", "play_button"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
            name=_build_names(ast_inst),
            args=_build_elements(file_info, ast_inst.args),
            kwargs={
                kw.arg: _build_elements(file_info, kw.value) for kw in ast_inst.keywords
            },
        )

    @override
    def __str__(self) -> str:
        args = ", ".join(map(lambda i: str(_build_names(i)), self.args))
        args += ", ".join(
            map(lambda i: f"{i[0]}={_build_names(i[1])}", self.kwargs.items())
        )
        return f"{self.rich_alias} {self.name}({args})"


@_register_ast(ast.Expr)
@dataclass(frozen=True)
class SyntaxTreeElementExpression(SyntaxTreeElement):
    name: str

    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        match ast_inst.value:
            case ast.Constant():
                return SyntaxTreeElementConstant.build(file_info, ast_inst.value)
            case ast.Call():
                return SyntaxTreeElementCall.build(file_info, ast_inst.value)
            case _:
                return cls(
                    ast_inst=ast_inst,
                    rich_alias=node_alias("expr"),
                    nodes=None,
                    tags=_build_tags(file_info, ast_inst),
                    file_info=file_info,
                    name=str(ast_inst.value),
                )

    @override
    def __str__(self) -> str:
        return f"{self.rich_alias} {self.name}"


@dataclass(frozen=True)
class SyntaxTreeElementEllipsis(SyntaxTreeElement):
    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("...", "no_entry"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
        )

    @override
    def __str__(self) -> str:
        return self.rich_alias


@_register_ast(ast.Tuple)
@dataclass(frozen=True)
class SyntaxTreeElementTuple(SyntaxTreeElement):
    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("(tuple)", "pushpin"),
            nodes=_build_elements(file_info, ast_inst.elts),
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
        )


@_register_ast(ast.AnnAssign)
@dataclass(frozen=True)
class SyntaxTreeElementAnnotation(SyntaxTreeElement):
    name: str
    annotation: str

    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("annotate", "pencil"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            name=_build_names(ast_inst.target),
            annotation=_build_names(ast_inst.annotation),
            file_info=file_info,
        )

    @override
    def __str__(self) -> str:
        return f"{self.rich_alias} {self.name} -> {self.annotation}"


@_register_ast(ast.If)
@dataclass(frozen=True)
class SyntaxTreeElementIf(SyntaxTreeElement):
    else_nodes: Tuple[SyntaxTreeElement] | None

    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("if", "question"),
            nodes=_build_elements(file_info, ast_inst.body),
            else_nodes=_build_elements(file_info, ast_inst.orelse)
            if ast_inst.orelse
            else None,
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
        )


@_register_ast(ast.IfExp)
@dataclass(frozen=True)
class SyntaxTreeElementTernaryExpression(SyntaxTreeElement):
    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("if expr", "question"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
        )


@_register_ast(ast.Match)
@dataclass(frozen=True)
class SyntaxTreeElementMatch(SyntaxTreeElement):
    name: str

    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("match", "question"),
            nodes=_build_elements(file_info, ast_inst.cases),
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
            name=_build_names(ast_inst.subject),
        )

    @override
    def __str__(self) -> str:
        return f"{self.rich_alias} {self.name}"


@_register_ast(ast.match_case)
@dataclass(frozen=True)
class SyntaxTreeElementCase(SyntaxTreeElement):
    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("case", "white_check_mark"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
        )


@_register_ast(ast.Pass)
@dataclass(frozen=True)
class SyntaxTreeElementPass(SyntaxTreeElement):
    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("pass"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
        )


@_register_ast(ast.GeneratorExp)
@dataclass(frozen=True)
class SyntaxTreeElementGenerator(SyntaxTreeElement):
    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("generator"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
        )


@_register_ast(ast.Subscript)
@dataclass(frozen=True)
class SyntaxTreeElementSubscription(SyntaxTreeElement):
    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("\\[subscription]", "right_arrow"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
        )


@_register_ast(ast.Slice)
@dataclass(frozen=True)
class SyntaxTreeElementSlice(SyntaxTreeElement):
    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("\\[::]"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
        )


@_register_ast(ast.List)
@dataclass(frozen=True)
class SyntaxTreeElementList(SyntaxTreeElement):
    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("\\[list]"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
        )


@_register_ast(ast.ListComp)
@dataclass(frozen=True)
class SyntaxTreeElementListComprehension(SyntaxTreeElement):
    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("\\[list comprehension]"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
        )


@_register_ast(ast.Set)
@dataclass(frozen=True)
class SyntaxTreeElementSet(SyntaxTreeElement):
    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("{set}"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
        )


@_register_ast(ast.SetComp)
@dataclass(frozen=True)
class SyntaxTreeElementSetComprehension(SyntaxTreeElement):
    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("{set comprehension}"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
        )


@_register_ast(ast.Dict)
@dataclass(frozen=True)
class SyntaxTreeElementDictionary(SyntaxTreeElement):
    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("{dict}", "books"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
        )


@_register_ast(ast.DictComp)
@dataclass(frozen=True)
class SyntaxTreeElementDictionaryComprehension(SyntaxTreeElement):
    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("{dict comprehension}", "books"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
        )


@_register_ast(ast.Attribute)
@dataclass(frozen=True)
class SyntaxTreeElementAttribute(SyntaxTreeElement):
    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("attr", "right_arrow"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
        )


@_register_ast(ast.UnaryOp)
@dataclass(frozen=True)
class SyntaxTreeElementUnaryOperator(SyntaxTreeElement):
    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("unary operation"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
        )


@_register_ast(ast.BoolOp)
@dataclass(frozen=True)
class SyntaxTreeElementBooleanOperator(SyntaxTreeElement):
    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("bool operation"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
        )


@_register_ast(ast.BinOp)
@dataclass(frozen=True)
class SyntaxTreeElementBinaryOperator(SyntaxTreeElement):
    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("binary operation", "play_button"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
        )


@_register_ast(ast.For)
@dataclass(frozen=True)
class SyntaxTreeElementForCycle(SyntaxTreeElement):
    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("for", "repeat_button"),
            nodes=_build_elements(file_info, ast_inst.body),
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
        )


@_register_ast(ast.AsyncFor)
@dataclass(frozen=True)
class SyntaxTreeElementAsyncForCycle(SyntaxTreeElement):
    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("afor", "repeat_button"),
            nodes=_build_elements(file_info, ast_inst.body),
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
        )


@_register_ast(ast.While)
@dataclass(frozen=True)
class SyntaxTreeElementWhileCycle(SyntaxTreeElement):
    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("while", "repeat_button"),
            nodes=_build_elements(file_info, ast_inst.body),
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
        )


@_register_ast(ast.Break)
@dataclass(frozen=True)
class SyntaxTreeElementBreak(SyntaxTreeElement):
    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("break", "right_arrow_curving_left"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
        )


@_register_ast(ast.Continue)
@dataclass(frozen=True)
class SyntaxTreeElementContinue(SyntaxTreeElement):
    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("continue", "right_arrow_curving_up"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
        )


@_register_ast(ast.Try)
@dataclass(frozen=True)
class SyntaxTreeElementTry(SyntaxTreeElement):
    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("try", "eyes"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
        )


@_register_ast(ast.Raise)
@dataclass(frozen=True)
class SyntaxTreeElementRaise(SyntaxTreeElement):
    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("raise", "warning"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
        )


@_register_ast(ast.Assert)
@dataclass(frozen=True)
class SyntaxTreeElementAssert(SyntaxTreeElement):
    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("assert", "question"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
        )


@_register_ast(ast.With)
@dataclass(frozen=True)
class SyntaxTreeElementContext(SyntaxTreeElement):
    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("with", "clamp"),
            nodes=_build_elements(file_info, ast_inst.body),
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
        )


@_register_ast(ast.Return)
@dataclass(frozen=True)
class SyntaxTreeElementReturn(SyntaxTreeElement):
    value: SyntaxTreeElement

    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("return", "right_arrow_curving_left"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            value=_build_elements(file_info, ast_inst.value),
            file_info=file_info,
        )


@_register_ast(ast.Delete)
@dataclass(frozen=True)
class SyntaxTreeElementDelete(SyntaxTreeElement):
    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("delete", "trashcan"),
            nodes=_build_elements(file_info, ast_inst.targets),
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
        )


@_register_ast(ast.Lambda)
@dataclass(frozen=True)
class SyntaxTreeElementLambda(SyntaxTreeElement):
    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("lambda"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
        )


@_register_ast(ast.Global)
@dataclass(frozen=True)
class SyntaxTreeElementGlobal(SyntaxTreeElement):
    names: Tuple[str, ...]

    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("global", "regional_indicator_g"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
            names=ast_inst.names,
        )


@_register_ast(ast.Nonlocal)
@dataclass(frozen=True)
class SyntaxTreeElementNonlocal(SyntaxTreeElement):
    names: Tuple[str, ...]

    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias("nonlocal"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
            names=ast_inst.names,
        )


@_register_ast(ast.Comment)  # Comes form ast_comments
@dataclass(frozen=True)
class SyntaxTreeElementComment(SyntaxTreeElement):
    value: str

    @classmethod
    def build(cls, file_info: FileInfo, ast_inst: ast.stmt) -> SyntaxTreeElement:
        return cls(
            ast_inst=ast_inst,
            rich_alias=node_alias(" #", "label"),
            nodes=None,
            tags=_build_tags(file_info, ast_inst),
            file_info=file_info,
            value=ast_inst.value,
        )

    @override
    def __str__(self) -> str:
        return f"{self.rich_alias} [i #808080]{self.value.split('#', 1)[1].strip()}[/]"


def _build_elements(
    file_info: FileInfo,
    ast_inst: Sequence[ast.stmt] | ast.stmt,
) -> Tuple[SyntaxTreeElement, ...] | SyntaxTreeElement:
    try:
        return tuple(map(lambda ai: _build_elements(file_info, ai), ast_inst))
    except TypeError:
        return (
            None
            if ast_inst is None
            else _ast2ste[type(ast_inst)].build(file_info, ast_inst)
        )


def _build_tags(
    file_info: FileInfo,
    ast_inst: ast.stmt,
) -> Tuple[str, ...]:
    if not hasattr(ast_inst, "lineno"):
        return tuple()

    line = file_info.lines[ast_inst.lineno - 1]

    if _ESC_TAG not in line:
        return tuple()

    return tuple(line.split(_ESC_TAG, 1)[-1].strip().split())


def _build_names(
    ast_inst: Sequence[SyntaxTreeElement | ast.stmt] | SyntaxTreeElement | ast.stmt,
    name: str = "",
) -> Tuple[str, ...] | str:
    try:
        return tuple(map(_build_names, ast_inst))
    except TypeError:
        if isinstance(ast_inst, SyntaxTreeElement):
            ast_inst = ast_inst.ast_inst

        if ast_inst is None:
            return "None"
        else:
            return ast.unparse(ast_inst).replace("\n", "\\n").replace("[", "\\[")


__all__ = (
    "FileInfo",
    "SyntaxTreeElement",
    "SyntaxTreeElementAlias",
    "SyntaxTreeElementAnnotation",
    "SyntaxTreeElementAssert",
    "SyntaxTreeElementAssign",
    "SyntaxTreeElementAsyncFunction",
    "SyntaxTreeElementAttribute",
    "SyntaxTreeElementBinaryOperator",
    "SyntaxTreeElementBooleanOperator",
    "SyntaxTreeElementBreak",
    "SyntaxTreeElementBytes",
    "SyntaxTreeElementCall",
    "SyntaxTreeElementCase",
    "SyntaxTreeElementClass",
    "SyntaxTreeElementComment",
    "SyntaxTreeElementCompare",
    "SyntaxTreeElementConstant",
    "SyntaxTreeElementContext",
    "SyntaxTreeElementContinue",
    "SyntaxTreeElementDelete",
    "SyntaxTreeElementDictionary",
    "SyntaxTreeElementDictionaryComprehension",
    "SyntaxTreeElementEllipsis",
    "SyntaxTreeElementExpression",
    "SyntaxTreeElementFloat",
    "SyntaxTreeElementForCycle",
    "SyntaxTreeElementFormatedStringValue",
    "SyntaxTreeElementFunction",
    "SyntaxTreeElementGenerator",
    "SyntaxTreeElementGlobal",
    "SyntaxTreeElementIf",
    "SyntaxTreeElementImport",
    "SyntaxTreeElementImportFrom",
    "SyntaxTreeElementInt",
    "SyntaxTreeElementJoinedString",
    "SyntaxTreeElementLambda",
    "SyntaxTreeElementList",
    "SyntaxTreeElementListComprehension",
    "SyntaxTreeElementMatch",
    "SyntaxTreeElementNone",
    "SyntaxTreeElementNonlocal",
    "SyntaxTreeElementOperateAndAssign",
    "SyntaxTreeElementPass",
    "SyntaxTreeElementRaise",
    "SyntaxTreeElementReturn",
    "SyntaxTreeElementRoot",
    "SyntaxTreeElementSet",
    "SyntaxTreeElementSetComprehension",
    "SyntaxTreeElementSlice",
    "SyntaxTreeElementStarredVariable",
    "SyntaxTreeElementString",
    "SyntaxTreeElementSubscription",
    "SyntaxTreeElementTernaryExpression",
    "SyntaxTreeElementTry",
    "SyntaxTreeElementTuple",
    "SyntaxTreeElementUnaryOperator",
    "SyntaxTreeElementVariable",
    "SyntaxTreeElementWhileCycle",
    "node_alias",
)
