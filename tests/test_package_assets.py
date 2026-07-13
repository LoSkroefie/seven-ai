from seven import __version__, config
from seven.agent.prompt import _read_identity


def test_runtime_version_matches_project_metadata():
    import tomllib
    from pathlib import Path
    metadata = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8"))
    assert __version__ == metadata["project"]["version"]


def test_all_identity_files_are_present_and_loaded():
    expected = {"SOUL.md", "IDENTITY.md", "USER.md", "TOOLS.md"}
    assert expected == {path.name for path in config.IDENTITY_DIR.glob("*.md")}
    identity = _read_identity()
    for name in expected:
        assert f"### {name}" in identity
