"""Tests for script/.lib/agent_plugins.py, which installs the pinned agent plugins and checks the settings agree."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).parents[2]
MODULE = Path(__file__).parents[1] / ".lib" / "agent_plugins.py"
SPEC = importlib.util.spec_from_file_location("agent_plugins", MODULE)
assert SPEC is not None
assert SPEC.loader is not None
agent_plugins = importlib.util.module_from_spec(SPEC)
sys.modules["agent_plugins"] = agent_plugins
SPEC.loader.exec_module(agent_plugins)

MARKET = "example-skills"
SETTINGS = {
    "extraKnownMarketplaces": {
        MARKET: {"source": {"source": "github", "repo": "someone/example-skills", "ref": "v1.2.0"}},
        "unpinned": {"source": {"source": "github", "repo": "someone/other"}},
    },
    "enabledPlugins": {f"plan@{MARKET}": True, f"review@{MARKET}": True, f"triage@{MARKET}": False},
}
CODEX = f"""
[marketplaces.{MARKET}]
source_type = "git"
source = "https://github.com/someone/example-skills.git"
ref = "v1.2.0"

[plugins."plan@{MARKET}"]
enabled = true

[plugins."review@{MARKET}"]
enabled = true
"""
RAW = "https://raw.githubusercontent.com/someone/example-skills"
OPENCODE = {"skills": [f"{RAW}/v1.2.0/plugins/plan/skills/", f"{RAW}/v1.2.0/plugins/review/skills/"]}


def _write(root: Path, claude: dict, copilot: dict, codex: str, opencode: dict | None = None) -> None:
    (root / ".claude").mkdir()
    (root / ".claude/settings.json").write_text(json.dumps(claude), encoding="utf-8")
    (root / ".github/copilot").mkdir(parents=True)
    (root / ".github/copilot/settings.json").write_text(json.dumps(copilot), encoding="utf-8")
    (root / ".codex").mkdir()
    (root / ".codex/config.toml").write_text(codex, encoding="utf-8")
    if opencode is not None:
        (root / "opencode.json").write_text(json.dumps(opencode), encoding="utf-8")


def _check(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(MODULE), "--check"], cwd=root, capture_output=True, text=True, check=False
    )


@pytest.mark.unit
def test_only_pinned_github_marketplaces_and_enabled_plugins_count() -> None:
    """A marketplace without a ref pins nothing, and a plugin set to false is not enabled."""
    assert agent_plugins.pins_from_settings(SETTINGS) == [
        agent_plugins.Pin(MARKET, "someone/example-skills", "v1.2.0", ("plan", "review"))
    ]


@pytest.mark.unit
def test_check_passes_when_all_three_agree(tmp_path: Path) -> None:
    """The same marketplace, ref and plugins in all three files pass."""
    _write(tmp_path, SETTINGS, SETTINGS, CODEX)
    assert _check(tmp_path).returncode == 0


@pytest.mark.unit
@pytest.mark.parametrize(
    ("copilot_ref", "codex"),
    [("v1.1.0", CODEX), ("v1.2.0", CODEX.replace('ref = "v1.2.0"', 'ref = "v1.1.0"')), ("v1.2.0", "")],
)
def test_check_fails_on_a_ref_or_marketplace_that_differs(tmp_path: Path, copilot_ref: str, codex: str) -> None:
    """A tag bumped in one file but not the others, or a marketplace missing for Codex, is reported."""
    copilot = json.loads(json.dumps(SETTINGS))
    copilot["extraKnownMarketplaces"][MARKET]["source"]["ref"] = copilot_ref
    _write(tmp_path, SETTINGS, copilot, codex)
    result = _check(tmp_path)
    assert result.returncode == 1
    assert MARKET in result.stderr


@pytest.mark.unit
def test_opencode_catalogs_are_read_as_pins_and_local_paths_ignored() -> None:
    """Each raw catalog URL counts toward the pin of its repository; a local skills folder pins nothing."""
    config = {"skills": [*OPENCODE["skills"], ".agents/skills", "https://example.com/skills/"]}
    expected = agent_plugins.pins_from_settings(SETTINGS)
    assert agent_plugins.opencode_pins(config, expected) == expected


@pytest.mark.unit
def test_check_passes_when_opencode_agrees_too(tmp_path: Path) -> None:
    """opencode.json with one catalog per enabled plugin at the same tag is the fourth matching source."""
    _write(tmp_path, SETTINGS, SETTINGS, CODEX, OPENCODE)
    result = _check(tmp_path)
    assert result.returncode == 0, result.stderr
    assert "opencode.json" in result.stdout


@pytest.mark.unit
@pytest.mark.parametrize(
    ("skills", "message"),
    [
        ([url.replace("v1.2.0", "v1.1.0") for url in OPENCODE["skills"]], "differs"),
        ([OPENCODE["skills"][0], OPENCODE["skills"][1].replace("v1.2.0", "v1.1.0")], "more than one ref"),
        (OPENCODE["skills"][:1], "differs"),
        (None, "is missing"),
        (
            [*OPENCODE["skills"], "https://raw.githubusercontent.com/someone/other/v1.0.0/plugins/x/skills/"],
            "not pinned in .claude/settings.json",
        ),
    ],
    ids=["wrong-ref", "two-refs", "missing-plugin", "no-skills", "unpinned-repo"],
)
def test_check_fails_when_opencode_differs(tmp_path: Path, skills: list[str] | None, message: str) -> None:
    """A catalog at another tag, a plugin without its catalog, or a catalog nobody pins is reported."""
    _write(tmp_path, SETTINGS, SETTINGS, CODEX, {} if skills is None else {"skills": skills})
    result = _check(tmp_path)
    assert result.returncode == 1
    assert "opencode.json" in result.stderr
    assert message in result.stderr


@pytest.mark.unit
def test_check_fails_when_a_plugin_is_enabled_for_one_agent_only(tmp_path: Path) -> None:
    """Enabling a plugin for Claude Code alone is a mismatch, not a per-agent choice."""
    copilot = json.loads(json.dumps(SETTINGS))
    copilot["enabledPlugins"][f"review@{MARKET}"] = False
    _write(tmp_path, SETTINGS, copilot, CODEX)
    assert _check(tmp_path).returncode == 1


@pytest.mark.unit
def test_check_fails_when_only_copilot_or_codex_pins(tmp_path: Path) -> None:
    """A pin outside .claude/settings.json has no source of truth, so it is reported rather than passed as nothing."""
    _write(tmp_path, {}, SETTINGS, CODEX)
    result = _check(tmp_path)
    assert result.returncode == 1
    assert "not pinned in .claude/settings.json" in result.stderr


@pytest.mark.unit
def test_no_pin_is_nothing_to_do(tmp_path: Path) -> None:
    """A repository that pins no marketplace passes and installs nothing."""
    result = _check(tmp_path)
    assert result.returncode == 0
    assert "nothing to do" in result.stdout


@pytest.mark.unit
def test_claude_installs_missing_plugins_at_local_scope() -> None:
    """A fresh checkout adds the marketplace at the pinned ref and installs each plugin locally, never at project scope."""
    pin = agent_plugins.pins_from_settings(SETTINGS)[0]
    commands = agent_plugins.claude_commands(pin, {}, set())
    assert commands == [
        ["claude", "plugin", "marketplace", "add", "someone/example-skills@v1.2.0", "--scope", "local"],
        ["claude", "plugin", "install", f"plan@{MARKET}", "--scope", "local"],
        ["claude", "plugin", "install", f"review@{MARKET}", "--scope", "local"],
    ]
    assert all("project" not in command for command in commands)


@pytest.mark.unit
def test_claude_respects_a_plugin_turned_off_locally() -> None:
    """A developer who set a plugin to false in settings.local.json does not get it back on the next bootstrap."""
    pin = agent_plugins.pins_from_settings(SETTINGS)[0]
    local = {"enabledPlugins": {f"plan@{MARKET}": False}}
    commands = agent_plugins.claude_commands(pin, local, set())
    assert ["claude", "plugin", "install", f"plan@{MARKET}", "--scope", "local"] not in commands
    assert ["claude", "plugin", "install", f"review@{MARKET}", "--scope", "local"] in commands


@pytest.mark.unit
def test_claude_updates_installed_plugins_only_when_the_ref_moved() -> None:
    """Installed plugins are left alone on a rerun and updated after a tag bump."""
    pin = agent_plugins.pins_from_settings(SETTINGS)[0]
    installed = {f"plan@{MARKET}", f"review@{MARKET}"}
    same = {"extraKnownMarketplaces": {MARKET: {"source": {"ref": "v1.2.0"}}}}
    older = {"extraKnownMarketplaces": {MARKET: {"source": {"ref": "v1.1.0"}}}}
    assert len(agent_plugins.claude_commands(pin, same, installed)) == 1
    assert ["claude", "plugin", "update", f"review@{MARKET}", "--scope", "local"] in agent_plugins.claude_commands(
        pin, older, installed
    )


@pytest.mark.unit
def test_this_repository_agrees_with_itself() -> None:
    """The settings files of this repository, opencode.json among them when present, pin the same plugins."""
    result = _check(ROOT)
    assert result.returncode == 0, result.stderr


@pytest.mark.unit
def test_renovate_finds_the_pin_in_every_settings_file() -> None:
    """Renovate raises the tag only where its patterns match, so a reformatted settings file must not hide the pin."""
    spec = importlib.util.spec_from_file_location(
        "version_guard", Path(__file__).parents[1] / ".lib" / "version_guard.py"
    )
    assert spec is not None
    assert spec.loader is not None
    version_guard = importlib.util.module_from_spec(spec)
    sys.modules["version_guard"] = version_guard
    spec.loader.exec_module(version_guard)
    readers = version_guard.readers(json.loads((ROOT / ".github" / "renovate.json").read_text(encoding="utf-8")))
    pins = agent_plugins.pins_from_settings(
        json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    )
    expected = {pin.repo: pin.ref for pin in pins}
    names = [".claude/settings.json", ".github/copilot/settings.json", ".codex/config.toml", "opencode.json"]
    for name in (name for name in names if (ROOT / name).is_file()):
        text = (ROOT / name).read_text(encoding="utf-8")
        found = {
            dep: occurrences[0][0]
            for reader in readers
            if any(pattern.search(name) for pattern in reader.files)
            for dep, occurrences in version_guard.pins(text, reader).items()
        }
        assert found == expected, name


UNTRUSTED = f"Error: marketplace `{MARKET}` is not configured as a Git marketplace"


def _install(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fail: dict[str, str],
    opencode: dict | None = None,
) -> str:
    """Run ``install`` with fake agent CLIs; a call whose first four words are a key of ``fail`` fails with its value."""
    _write(tmp_path, SETTINGS, SETTINGS, CODEX, opencode)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_plugins.shutil, "which", lambda name: f"/bin/{name}")

    def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        if command[:3] == ["claude", "plugin", "list"]:
            return subprocess.CompletedProcess(command, 0, "[]", "")
        error = fail.get(" ".join(command[:4]))
        return subprocess.CompletedProcess(command, 1 if error else 0, "", error or "")

    monkeypatch.setattr(agent_plugins.subprocess, "run", fake_run)
    agent_plugins.install(agent_plugins.pins_from_settings(SETTINGS))
    return capsys.readouterr().out


@pytest.mark.unit
def test_install_reports_success_only_when_every_step_succeeded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """With every CLI call succeeding, both agents get their success line."""
    out = _install(tmp_path, monkeypatch, capsys, {})
    assert "✓ Claude Code" in out
    assert "✓ Codex" in out
    assert "· OpenCode" not in out


@pytest.mark.unit
def test_install_says_opencode_fetches_its_own_catalogs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """OpenCode needs no install step, so the run only says where it reads the catalogs from."""
    out = _install(tmp_path, monkeypatch, capsys, {}, OPENCODE)
    assert "· OpenCode: fetches the catalogs in opencode.json itself when it starts" in out


@pytest.mark.unit
def test_codex_in_an_untrusted_project_is_not_reported_as_refreshed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Codex ignores .codex/config.toml until the project is trusted, so the upgrade fails and says how to finish."""
    out = _install(tmp_path, monkeypatch, capsys, {"codex plugin marketplace upgrade": UNTRUSTED})
    assert "✓ Codex" not in out
    assert "⚠ Codex" in out
    assert "trusted" in out
    assert "script/setup/agent-plugins" in out


@pytest.mark.unit
def test_codex_failure_for_another_reason_shows_the_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A network failure is not mistaken for an untrusted project."""
    out = _install(tmp_path, monkeypatch, capsys, {"codex plugin marketplace upgrade": "fatal: unable to access"})
    assert "✓ Codex" not in out
    assert "fatal: unable to access" in out


@pytest.mark.unit
def test_failed_claude_install_is_not_reported_as_done(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A failed marketplace add or plugin install withholds the Claude Code success line."""
    out = _install(tmp_path, monkeypatch, capsys, {"claude plugin install plan@example-skills": "network down"})
    assert "✓ Claude Code" not in out
    assert "⚠ Claude Code" in out
