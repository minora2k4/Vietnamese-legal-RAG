"""
Utilities for building a legal document scaffolder.

Supported document structures:

type_1: Phần -> Chương -> Mục -> Tiểu mục -> Điều -> Khoản -> Điểm
type_2: Phần -> Chương -> Mục -> Điều -> Khoản -> Điểm
type_3: Chương -> Mục -> Tiểu mục -> Điều -> Khoản -> Điểm
type_4: Chương -> Mục -> Điều -> Khoản -> Điểm
type_5: Chương -> Điều -> Khoản -> Điểm
type_6: Điều -> Khoản -> Điểm
"""

from typing import Any, List

LEGAL_DOC_ARCS = {
    "type_1": ["phần", "chương", "mục", "tiểuMục", "điều", "khoản", "điểm"],
    "type_2": ["phần", "chương", "mục", "điều", "khoản", "điểm"],
    "type_3": ["chương", "mục", "tiểuMục", "điều", "khoản", "điểm"],
    "type_4": ["chương", "mục", "điều", "khoản", "điểm"],
    "type_5": ["chương", "điều", "khoản", "điểm"],
    "type_6": ["điều", "khoản", "điểm"],
}


def build_scaffolder(parts: List[Any]) -> List[str]:
    scaffold = []

    def dfs(nodes: List[Any]) -> None:
        for node in nodes:
            tree_id = (
                node["treeId"] if isinstance(node, dict)
                else getattr(node, "treeId", None)
            )

            children = (
                node.get("children", []) if isinstance(node, dict)
                else getattr(node, "children", [])
            )

            if tree_id:
                scaffold.append(tree_id)

            if children:
                dfs(children)

    dfs(parts)
    return scaffold