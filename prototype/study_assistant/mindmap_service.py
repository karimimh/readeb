"""Mind map generation and graphviz rendering."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .llm_client import LLMClient, load_prompt
from .models import MindMapNode

SYSTEM = "You design clear, hierarchical mind maps. Always reply with valid JSON."


def _coerce_node(data: dict) -> MindMapNode:
    return MindMapNode(
        root=str(data.get("root", "")).strip() or "Root",
        children=[_coerce_node(c) for c in data.get("children", []) if isinstance(c, dict)],
    )


def generate_mindmap(client: LLMClient, material: str, cache_tag: str = "mindmap") -> MindMapNode:
    template = load_prompt("mindmap")
    user = template.replace("{material}", material)
    data = client.complete_json(SYSTEM, user, cache_key_extra=cache_tag)
    return _coerce_node(data)


def render_mindmap(
    node: MindMapNode,
    output_path: str | Path,
    fmt: str = "png",
    rankdir: str = "LR",
) -> Path:
    """Render a mind map to an image file using graphviz. Returns the file path."""
    from graphviz import Digraph

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    dot = Digraph(comment="MindMap", format=fmt)
    dot.attr(rankdir=rankdir, splines="true", overlap="false")
    dot.attr("node", shape="box", style="rounded,filled", fillcolor="#EEF3FF",
             fontname="Helvetica")

    counter = {"i": 0}

    def add(node: MindMapNode, parent_id: Optional[str]) -> str:
        counter["i"] += 1
        nid = f"n{counter['i']}"
        dot.node(nid, node.root)
        if parent_id is not None:
            dot.edge(parent_id, nid)
        for child in node.children:
            add(child, nid)
        return nid

    add(node, None)

    # graphviz appends the format extension; strip it from output_path if present.
    stem = output_path.with_suffix("")
    rendered = dot.render(filename=str(stem), cleanup=True)
    return Path(rendered)
