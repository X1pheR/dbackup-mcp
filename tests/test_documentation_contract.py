from __future__ import annotations

import asyncio
import re
from pathlib import Path

from dbackup_mcp.server import list_tools


ROOT = Path(__file__).resolve().parents[1]


def test_public_mcp_docs_use_progressive_disclosure() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    tools_doc = (ROOT / "docs" / "tools.md").read_text(encoding="utf-8")
    tools = asyncio.run(list_tools())
    tool_names = {tool.name for tool in tools}

    assert "[Tool reference](docs/tools.md)" in readme
    assert len(readme.split()) <= 900

    documented = set(re.findall(r"^\| `([^`]+)` \|", tools_doc, flags=re.MULTILINE))
    assert documented == tool_names

    readme_tool_mentions = {name for name in tool_names if f"`{name}`" in readme}
    assert len(readme_tool_mentions) <= max(8, len(tool_names) // 4)

    assert "| Tool | Access | Destructive | Purpose |" in tools_doc
