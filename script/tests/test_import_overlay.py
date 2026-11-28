"""Tests for script/import-overlay, with an already initialised stand-in blueprint (--from)."""

import json
from pathlib import Path
import shutil
import subprocess

import pytest

SCRIPT_DIR = Path(__file__).parents[1]


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=test", "-c", "user.email=test@example.com", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def _write(root: Path, files: dict[str, str]) -> None:
    for name, content in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(content, encoding="utf-8")


@pytest.fixture
def blueprint(tmp_path: Path) -> Path:
    """Return a folder holding script/import-overlay and its libraries, as the blueprint does."""
    root = tmp_path / "blueprint"
    shutil.copytree(SCRIPT_DIR / ".lib", root / "script" / ".lib")
    shutil.copy2(SCRIPT_DIR / "import-overlay", root / "script" / "import-overlay")
    return root


@pytest.fixture
def initialised(tmp_path: Path) -> Path:
    """Return a git repository standing in for a blueprint initialised with the domain demo."""
    root = tmp_path / "initialised"
    _write(
        root,
        {
            "custom_components/demo/manifest.json": json.dumps({"domain": "demo", "version": "0.1.0"}),
            "custom_components/demo/__init__.py": '"""Example."""\n',
            "custom_components/.gitignore": "!demo/\n",
            "tests/test_example.py": "def test_example() -> None: ...\n",
            "README.md": "# Demo from the blueprint\n",
            "script/lint": "#!/bin/bash\n",
        },
    )
    _git(root, "init", "-q")
    _git(root, "add", "-A")
    return root


@pytest.fixture
def target(tmp_path: Path) -> Path:
    """Return an existing integration repository with one commit."""
    root = tmp_path / "target"
    _write(
        root,
        {
            "custom_components/demo/manifest.json": json.dumps({"domain": "demo", "version": "2.3.4"}),
            "custom_components/demo/__init__.py": '"""The real integration."""\n',
            "tests/test_mine.py": "def test_mine() -> None: ...\n",
            "README.md": "# Demo\n",
            ".github/workflows/old.yml": "name: old\n",
        },
    )
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "init")
    return root


def _overlay(blueprint: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(blueprint / "script" / "import-overlay"), *args], capture_output=True, text=True, check=False
    )


def _staged(target: Path, change: str) -> set[str]:
    return set(_git(target, "diff", "--cached", "--name-only", f"--diff-filter={change}", "HEAD").split())


@pytest.mark.unit
def test_overlay_keeps_the_integration_and_sorts_the_rest(blueprint: Path, initialised: Path, target: Path) -> None:
    """The integration stays byte-identical, nothing is committed, and every other file lands in one of the groups."""
    head = _git(target, "rev-parse", "HEAD")

    result = _overlay(blueprint, "--target", str(target), "--from", str(initialised))

    assert result.returncode == 0, result.stdout + result.stderr
    assert _git(target, "rev-parse", "HEAD") == head
    assert _git(target, "branch", "--show-current").strip() == "chore/adopt-blueprint"
    assert (target / "custom_components" / "demo" / "__init__.py").read_text(encoding="utf-8") == (
        '"""The real integration."""\n'
    )
    assert _staged(target, "D") == {".github/workflows/old.yml", "tests/test_mine.py"}
    assert _staged(target, "M") == {"README.md"}
    assert _staged(target, "A") == {"custom_components/.gitignore", "script/lint"}
    assert "tests/test_mine.py" in (target / ".agents" / "scratch" / "import-overlay.md").read_text(encoding="utf-8")


@pytest.mark.unit
def test_dirty_target_is_refused(blueprint: Path, initialised: Path, target: Path) -> None:
    """Uncommitted work in the target would be mixed into the overlay."""
    (target / "README.md").write_text("# Changed\n", encoding="utf-8")

    result = _overlay(blueprint, "--target", str(target), "--from", str(initialised))

    assert result.returncode != 0
    assert "uncommitted changes" in result.stdout + result.stderr


@pytest.mark.unit
def test_domain_comes_from_the_target(blueprint: Path, initialised: Path, target: Path) -> None:
    """--domain is never taken from the caller: a different one would orphan every installation."""
    result = _overlay(blueprint, "--target", str(target), "--from", str(initialised), "--", "--domain", "other")

    assert result.returncode != 0
    assert "--domain is set by script/import-overlay" in result.stdout + result.stderr


@pytest.mark.unit
def test_relative_target_is_taken_from_the_callers_folder(blueprint: Path, initialised: Path, target: Path) -> None:
    """`--target .` from inside the project means the project, not the blueprint the script lives in."""
    result = subprocess.run(
        ["bash", str(blueprint / "script" / "import-overlay"), "--target", ".", "--from", str(initialised)],
        cwd=target,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert _git(target, "branch", "--show-current").strip() == "chore/adopt-blueprint"


@pytest.mark.unit
def test_target_with_only_the_integration(blueprint: Path, initialised: Path, tmp_path: Path) -> None:
    """A target that tracks nothing but its integration has nothing to remove, which is not a failure."""
    root = tmp_path / "bare"
    _write(root, {"custom_components/demo/manifest.json": json.dumps({"domain": "demo"})})
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "init")

    result = _overlay(blueprint, "--target", str(root), "--from", str(initialised))

    assert result.returncode == 0, result.stdout + result.stderr
    assert _staged(root, "A") == {"README.md", "custom_components/.gitignore", "script/lint"}


@pytest.mark.unit
def test_similar_files_are_not_hidden_as_renames(blueprint: Path, initialised: Path, target: Path) -> None:
    """A file the old repository had and a near-identical one from the blueprint each land in their own group."""
    content = "".join(f"line {n}\n" for n in range(50))
    _write(target, {"docs/old.md": content})
    _git(target, "add", "-A")
    _git(target, "commit", "-qm", "docs")
    _write(initialised, {"docs/new.md": content + "extra\n"})
    _git(initialised, "add", "-A")

    result = _overlay(blueprint, "--target", str(target), "--from", str(initialised))

    assert result.returncode == 0, result.stdout + result.stderr
    report = (target / ".agents" / "scratch" / "import-overlay.md").read_text(encoding="utf-8")
    assert "- docs/old.md" in report
    assert "- docs/new.md" in report


@pytest.mark.unit
def test_two_integrations_are_refused(blueprint: Path, initialised: Path, target: Path) -> None:
    """The overlay keeps one integration folder; a second one would be deleted without a word."""
    _write(target, {"custom_components/other/manifest.json": json.dumps({"domain": "other"})})
    _git(target, "add", "-A")
    _git(target, "commit", "-qm", "other")

    result = _overlay(blueprint, "--target", str(target), "--from", str(initialised))

    assert result.returncode != 0
    assert "more than one integration" in result.stdout + result.stderr


@pytest.mark.unit
def test_agent_instructions_get_a_group_of_their_own(blueprint: Path, initialised: Path, target: Path) -> None:
    """Old agent instructions are sorted rule by rule, never restored or merged like an ordinary file."""
    _write(target, {"CLAUDE.md": "# Rules\n", ".github/copilot-instructions.md": "# Rules\n", "AGENTS.md": "# Old\n"})
    _git(target, "add", "-A")
    _git(target, "commit", "-qm", "agents")
    _write(initialised, {"AGENTS.md": "# Blueprint\n"})
    _git(initialised, "add", "-A")

    result = _overlay(blueprint, "--target", str(target), "--from", str(initialised))

    assert result.returncode == 0, result.stdout + result.stderr
    report = (target / ".agents" / "scratch" / "import-overlay.md").read_text(encoding="utf-8")
    groups = dict(part.split("\n", 1) for part in report.split("\n## ")[1:])
    agent_group = next(body for title, body in groups.items() if title.startswith("Agent instructions"))
    for path in ("CLAUDE.md", ".github/copilot-instructions.md", "AGENTS.md"):
        assert f"- {path}\n" in agent_group
        assert all(f"- {path}\n" not in body for title, body in groups.items() if body is not agent_group)
    assert (target / "AGENTS.md").read_text(encoding="utf-8") == "# Blueprint\n"
