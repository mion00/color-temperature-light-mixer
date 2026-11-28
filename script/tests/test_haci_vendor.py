"""Tests for script/.lib/haci_vendor.py, which copies the pinned haci rules into path-scoped instructions files."""

import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).parents[2]
LIB = Path(__file__).parents[1] / ".lib"
sys.path.insert(0, str(LIB))
SPEC = importlib.util.spec_from_file_location("haci_vendor", LIB / "haci_vendor.py")
assert SPEC is not None
assert SPEC.loader is not None
haci_vendor = importlib.util.module_from_spec(SPEC)
sys.modules["haci_vendor"] = haci_vendor
SPEC.loader.exec_module(haci_vendor)

REPO = "someone/ha-custom-integration-skills"
RULES = """---
name: "Example rules"
description: "What the rules cover"
---

# Example rules

- A rule.
"""


def pin_settings(ref: str) -> dict:
    """Return Claude-format settings pinning the haci marketplace at ``ref``."""
    return {
        "extraKnownMarketplaces": {
            haci_vendor.MARKETPLACE: {"source": {"source": "github", "repo": REPO, "ref": ref}},
        },
        "enabledPlugins": {f"haci-quality@{haci_vendor.MARKETPLACE}": True},
    }


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Return a project pinned at v1.0.0, with a marketplace checkout that holds every topic's rules."""
    for settings in (haci_vendor.CLAUDE_SETTINGS, haci_vendor.COPILOT_SETTINGS):
        (tmp_path / settings).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / settings).write_text(json.dumps(pin_settings("v1.0.0")), encoding="utf-8")
    (tmp_path / haci_vendor.CODEX_CONFIG).parent.mkdir(parents=True)
    (tmp_path / haci_vendor.CODEX_CONFIG).write_text(
        f'[marketplaces.{haci_vendor.MARKETPLACE}]\nsource = "https://github.com/{REPO}.git"\nref = "v1.0.0"\n\n'
        f'[plugins."haci-quality@{haci_vendor.MARKETPLACE}"]\nenabled = true\n',
        encoding="utf-8",
    )
    (tmp_path / haci_vendor.OUTPUT_DIR).mkdir(parents=True)
    source = tmp_path / "marketplace"
    for topic in haci_vendor.TOPICS:
        (source / topic.source).parent.mkdir(parents=True, exist_ok=True)
        (source / topic.source).write_text(RULES, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HACI_VENDOR_SOURCE", str(source))
    return tmp_path


def test_render_adds_the_project_paths_and_the_pinned_tag() -> None:
    """The rendered file carries both frontmatter shapes, the marker, and the body unchanged."""
    topic = haci_vendor.Topic("example", "haci-quality", "haci-testing", ("tests/**/*.py", "conftest.py"))
    pin = haci_vendor.Pin(haci_vendor.MARKETPLACE, REPO, "v1.0.0", ("haci-quality",))

    text = haci_vendor.render(topic, RULES, pin)

    assert text.startswith('---\nname: "Example rules"\ndescription: "What the rules cover"\n')
    assert 'applyTo: "tests/**/*.py, conftest.py"\npaths:\n  - "tests/**/*.py"\n  - "conftest.py"\n---\n' in text
    assert (
        f"<!-- haci-vendor: {REPO}@v1.0.0 {topic.source} sha256:{haci_vendor.digest('# Example rules\n\n- A rule.\n')}"
        in text
    )
    assert text.endswith("# Example rules\n\n- A rule.\n")


def test_render_rejects_a_rules_file_that_sets_its_own_paths() -> None:
    """Paths are the project's layout; a rules file that brings some is refused."""
    topic = haci_vendor.TOPICS[0]
    pin = haci_vendor.Pin(haci_vendor.MARKETPLACE, REPO, "v1.0.0", ())

    with pytest.raises(haci_vendor.VendorError, match="exactly name and description"):
        haci_vendor.render(topic, RULES.replace("---\n\n#", 'paths: ["x"]\n---\n\n#'), pin)


@pytest.mark.usefixtures("project")
def test_write_then_check_round_trip(capsys: pytest.CaptureFixture[str]) -> None:
    """A written file passes the check and names its local source; an edited one fails it."""
    target = haci_vendor.TOPICS[0].target

    assert haci_vendor.main([]) == 0
    assert haci_vendor.main(["--check"]) == 0
    assert "@v1.0.0+local " in target.read_text(encoding="utf-8")

    target.write_text(target.read_text(encoding="utf-8") + "- An edit by hand.\n", encoding="utf-8")
    assert haci_vendor.main(["--check"]) == 1
    assert "differs from" in capsys.readouterr().err


@pytest.mark.usefixtures("project")
def test_write_removes_a_file_no_topic_produces() -> None:
    """A rules file for a topic that was dropped is removed, not left loading stale rules."""
    stale = haci_vendor.OUTPUT_DIR / "haci.retired.instructions.md"
    stale.write_text(RULES, encoding="utf-8")

    assert haci_vendor.main(["--check"]) == 1
    assert haci_vendor.main([]) == 0
    assert not stale.exists()


def test_a_different_copilot_pin_stops_the_run(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """The tag has one source; another agent pinning a different one is an error, not a silent choice."""
    (project / haci_vendor.COPILOT_SETTINGS).write_text(json.dumps(pin_settings("v0.9.0")), encoding="utf-8")

    assert haci_vendor.main([]) == 1
    assert "v0.9.0" in capsys.readouterr().err
    assert not haci_vendor.TOPICS[0].target.exists()


def test_the_committed_rules_files_follow_the_topics_and_the_pin() -> None:
    """This repository's haci.* files carry the TOPICS patterns and the tag .claude/settings.json pins."""
    settings = json.loads((ROOT / haci_vendor.CLAUDE_SETTINGS).read_text(encoding="utf-8"))
    source = settings["extraKnownMarketplaces"][haci_vendor.MARKETPLACE]["source"]
    for topic in haci_vendor.TOPICS:
        text = (ROOT / topic.target).read_text(encoding="utf-8")
        assert f'applyTo: "{", ".join(topic.patterns)}"' in text
        assert f"<!-- haci-vendor: {source['repo']}@{source['ref']} {topic.source} sha256:" in text


def test_initialize_leaves_every_rules_file_alone() -> None:
    """initialize.sh would rewrite the marker's repository name and break its digest, so it skips every topic's file."""
    script = (ROOT / "initialize.sh").read_text(encoding="utf-8")
    for topic in haci_vendor.TOPICS:
        assert f'"./{topic.target}"' in script


def test_a_topic_can_name_a_second_rules_file_of_its_skill() -> None:
    """A skill that governs two kinds of file ships rules.<topic>.md beside rules.md."""
    default = haci_vendor.Topic("example", "haci-build", "haci-service-action", ("**/x.py",))
    second = haci_vendor.Topic("other", "haci-build", "haci-service-action", ("**/x.yaml",), rules="rules.other")

    assert default.source == "plugins/haci-build/skills/haci-service-action/references/rules.md"
    assert second.source == "plugins/haci-build/skills/haci-service-action/references/rules.other.md"
    assert second.target.name == "haci.other.instructions.md"
