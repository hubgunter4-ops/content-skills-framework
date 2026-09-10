"""Demostración del descubrimiento que implementaría el runtime del framework."""
from __future__ import annotations

from importlib.metadata import entry_points


def discover_tools() -> list[object]:
    discovered = entry_points(group="content_skills_toolkit.tools")
    tools = []
    for entry_point in discovered:
        factory = entry_point.load()
        tool = factory()
        metadata = tool.metadata()
        if metadata.id != entry_point.name and metadata.id.rsplit("/", 1)[-1] != entry_point.name:
            raise ValueError(f"Identidad inconsistente: {entry_point.name} != {metadata.id}")
        tools.append(tool)
    return tools


if __name__ == "__main__":
    for tool in discover_tools():
        print(tool.metadata().id, tool.metadata().version)
