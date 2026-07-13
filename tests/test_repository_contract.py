import re
from pathlib import Path

from seven.memory.store import Memory
from seven.tools.registry import build_default_registry
from scripts.verify_repository_contract import broken_local_links, production_legacy_imports, unresolved_inventory


def test_production_never_imports_quarantined_legacy_modules():
    assert production_legacy_imports() == []


def test_inventory_has_final_dispositions_only():
    assert unresolved_inventory() == []


def test_documentation_local_links_resolve():
    assert broken_local_links() == []


def test_readme_registered_tool_count_matches_runtime(tmp_path):
    registry = build_default_registry(Memory(tmp_path / "tools.db"), tier="full")
    readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")
    match = re.search(r"\*\*(\d+) built-in registered tools\*\*", readme)
    assert match, "README tool-count claim missing"
    assert int(match.group(1)) == len(registry.all_names())
