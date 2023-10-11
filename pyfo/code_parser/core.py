"""
Created on Aug 3, 2023

@author: osi
"""
from __future__ import annotations

from .datatypes import FileInfo, SyntaxTreeElementRoot, node_alias

import ast
from pathlib import Path
from rich.padding import Padding
from rich.tree import Tree

from typing_extensions import override


class SyntaxTree:
    file_info: FileInfo
    root: SyntaxTreeElementRoot

    def __init__(self, file: Path | str) -> None:
        if isinstance(file, str):
            file = Path(file)

        self.file_info = FileInfo(file=file, lines=file.open("r").readlines())
        self.reload()

    def reload(self) -> None:
        self.file_info = FileInfo(
            file=self.file_info.file, lines=self.file_info.file.open("r").readlines()
        )
        self.root = SyntaxTreeElementRoot.build(
            self.file_info,
            ast.parse(
                self.file_info.file.open("r").read(),
                filename=str(self.file_info.file),
                type_comments=True,
                feature_version=(3, 11),
            ),
        )

    def rich_tree(self) -> Tree:
        tree = Tree(
            ":classical_building: root",
            guide_style="bright_blue",
            highlight=True,
        )
        self._rich_tree(tree, self.root.nodes)
        return Padding(tree)

    def _rich_tree(self, tree, nodes) -> None:
        for node in nodes:
            branch = tree.add(str(node))
            if node.nodes:
                self._rich_tree(branch, node.nodes)
                if hasattr(node, "else_nodes") and node.else_nodes:
                    branch = tree.add(node_alias("else", "cyclone"))
                    self._rich_tree(branch, node.else_nodes)

    @override
    def __str__(self) -> str:
        return f"SyntaxTree<{list(self).__str__()}>"


__all__ = ("SyntaxTree",)
