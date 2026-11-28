"""
Install the agent plugins this repository enables, at the version it pins, and check that the agents agree.

The pin has one source: the ``ref`` of the GitHub marketplace in ``.claude/settings.json`` →
``extraKnownMarketplaces``, with the plugins its ``enabledPlugins`` turns on. ``.github/copilot/settings.json`` and
``.codex/config.toml`` repeat both, and ``opencode.json`` → ``skills`` names one raw.githubusercontent.com catalog URL
per enabled plugin at the same tag; ``--check`` fails when any of them does not match it. ``opencode.json`` is compared
only when it exists.

Without ``--check``, this installs for the agent CLIs found on ``PATH``:

- Claude Code reads a marketplace declared in project settings only after the folder is trusted interactively, so the
  marketplace and each enabled plugin are added at local scope, which writes the gitignored
  ``.claude/settings.local.json`` and leaves ``.claude/settings.json`` alone. A plugin set to ``false`` there stays off.
- Codex reads its marketplace from ``.codex/config.toml`` once the project is trusted; refreshing that one marketplace
  installs the enabled plugins.
- Copilot installs from ``.github/copilot/settings.json`` itself.
- OpenCode fetches the catalogs in ``opencode.json`` itself when it starts.

A failed install is reported and skipped; it never fails the caller.

Invoked by script/setup/agent-plugins; not intended to be run directly.
"""

from dataclasses import dataclass
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tomllib

CLAUDE_SETTINGS = Path(".claude/settings.json")
CLAUDE_LOCAL = Path(".claude/settings.local.json")
COPILOT_SETTINGS = Path(".github/copilot/settings.json")
CODEX_CONFIG = Path(".codex/config.toml")
OPENCODE_CONFIG = Path("opencode.json")
CATALOG_URL = re.compile(
    r"https://raw\.githubusercontent\.com/(?P<repo>[^/]+/[^/]+)/(?P<ref>[^/]+)/plugins/(?P<plugin>[^/]+)/skills/?"
)
TIMEOUT = 180
UNTRUSTED_CODEX = "is not configured as a Git marketplace"


@dataclass(frozen=True)
class Pin:
    """One GitHub marketplace at one ref, and the plugins enabled from it."""

    marketplace: str
    repo: str
    ref: str
    plugins: tuple[str, ...]

    @property
    def git_url(self) -> str:
        """The clone URL Codex records for the marketplace."""
        return f"https://github.com/{self.repo}.git"


def _json(path: Path) -> dict:
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def pins_from_settings(settings: dict) -> list[Pin]:
    """Read every pinned GitHub marketplace, with its enabled plugins, from Claude-format settings."""
    pins = []
    enabled = [key for key, value in settings.get("enabledPlugins", {}).items() if value is True]
    for name, entry in settings.get("extraKnownMarketplaces", {}).items():
        source = entry.get("source", {}) if isinstance(entry, dict) else {}
        if source.get("source") != "github" or not source.get("repo") or not source.get("ref"):
            continue
        plugins = tuple(sorted(key.split("@", 1)[0] for key in enabled if key.endswith(f"@{name}")))
        pins.append(Pin(name, source["repo"], source["ref"], plugins))
    return pins


def codex_pins(config: dict) -> list[Pin]:
    """Read the same information from a Codex ``config.toml``."""
    pins = []
    enabled = [key for key, value in config.get("plugins", {}).items() if value.get("enabled") is True]
    for name, entry in config.get("marketplaces", {}).items():
        url = entry.get("source", "")
        repo = url.removeprefix("https://github.com/").removesuffix(".git")
        plugins = tuple(sorted(key.split("@", 1)[0] for key in enabled if key.endswith(f"@{name}")))
        pins.append(Pin(name, repo, entry.get("ref", ""), plugins))
    return pins


def _skill_entries(skills: object) -> list[str]:
    if isinstance(skills, str):
        return [skills]
    if isinstance(skills, list):
        return [entry for entry in skills if isinstance(entry, str)]
    if isinstance(skills, dict):
        return [entry for value in skills.values() for entry in _skill_entries(value)]
    return []


def opencode_pins(config: dict, expected: list[Pin]) -> list[Pin]:
    """Read the plugin catalogs an ``opencode.json`` loads skills from, one pin per repository and ref.

    Only raw.githubusercontent.com catalog URLs count; a local path or another URL is not a pin. Each pin takes the
    marketplace name of the expected pin for the same repository, or the repository itself when none pins it.
    """
    names = {pin.repo: pin.marketplace for pin in expected}
    plugins: dict[tuple[str, str], set[str]] = {}
    for entry in _skill_entries(config.get("skills")):
        if match := CATALOG_URL.fullmatch(entry):
            plugins.setdefault((match["repo"], match["ref"]), set()).add(match["plugin"])
    return [Pin(names.get(repo, repo), repo, ref, tuple(sorted(found))) for (repo, ref), found in plugins.items()]


def mismatches(
    expected: list[Pin], copilot: list[Pin], codex: list[Pin], opencode: list[Pin] | None = None
) -> list[str]:
    """Name every way the Copilot, Codex or OpenCode settings differ from the Claude Code pins.

    ``opencode`` is None when the repository has no ``opencode.json``, which is then not compared.
    """
    problems = []
    sources = [(str(COPILOT_SETTINGS), copilot), (str(CODEX_CONFIG), codex)]
    if opencode is not None:
        sources.append((str(OPENCODE_CONFIG), opencode))
    for label, actual in sources:
        refs: dict[str, list[str]] = {}
        for pin in actual:
            refs.setdefault(pin.marketplace, []).append(pin.ref)
        doubled = {name for name, found in refs.items() if len(found) > 1}
        problems.extend(
            f"{label}: marketplace {name} is pinned at more than one ref: {', '.join(sorted(refs[name]))}"
            for name in sorted(doubled)
        )
        by_name = {pin.marketplace: pin for pin in actual}
        for pin in expected:
            other = by_name.get(pin.marketplace)
            if pin.marketplace in doubled:
                continue
            if other is None:
                problems.append(f"{label}: marketplace {pin.marketplace} is missing")
            elif other != pin:
                problems.append(f"{label}: {other} differs from {CLAUDE_SETTINGS}: {pin}")
        names = {pin.marketplace for pin in expected}
        problems.extend(
            f"{label}: marketplace {pin.marketplace} is not pinned in {CLAUDE_SETTINGS}, the one source of the version"
            for pin in actual
            if pin.marketplace not in names and pin.marketplace not in doubled
        )
    return problems


def claude_commands(pin: Pin, local: dict, installed: set[str]) -> list[list[str]]:
    """The Claude Code CLI calls that bring this checkout to the pin, respecting a plugin turned off locally."""
    known = local.get("extraKnownMarketplaces", {}).get(pin.marketplace, {}).get("source", {})
    moved = bool(known) and known.get("ref") != pin.ref
    commands = [["claude", "plugin", "marketplace", "add", f"{pin.repo}@{pin.ref}", "--scope", "local"]]
    for plugin in pin.plugins:
        plugin_id = f"{plugin}@{pin.marketplace}"
        if local.get("enabledPlugins", {}).get(plugin_id) is False:
            continue
        if plugin_id not in installed:
            commands.append(["claude", "plugin", "install", plugin_id, "--scope", "local"])
        elif moved:
            commands.append(["claude", "plugin", "update", plugin_id, "--scope", "local"])
    return commands


def _run(command: list[str], *, report: bool = True) -> str | None:
    """Run one CLI call; return why it failed, or None when it succeeded."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=TIMEOUT, check=False)
    except (OSError, subprocess.TimeoutExpired) as err:
        error = str(err)
    else:
        if result.returncode == 0:
            return None
        detail = (result.stderr or result.stdout).strip().splitlines()
        error = detail[-1] if detail else f"exit {result.returncode}"
    if report:
        print(f"⚠ {' '.join(command)}: {error}", file=sys.stderr)
    return error


def _claude_installed() -> set[str]:
    try:
        result = subprocess.run(
            ["claude", "plugin", "list", "--json"], capture_output=True, text=True, timeout=TIMEOUT, check=False
        )
        entries = json.loads(result.stdout) if result.returncode == 0 else []
    except OSError, subprocess.TimeoutExpired, json.JSONDecodeError:
        return set()
    cwd = str(Path.cwd())
    return {
        entry["id"]
        for entry in entries
        if isinstance(entry, dict) and entry.get("scope") == "local" and entry.get("projectPath") == cwd
    }


def install(pins: list[Pin]) -> None:
    """Install for every agent CLI on PATH; report what was skipped or failed."""
    if shutil.which("claude"):
        installed = _claude_installed()
        failed = [
            command
            for pin in pins
            for command in claude_commands(pin, _json(CLAUDE_LOCAL), installed)
            if _run(command) is not None
        ]
        if failed:
            print(f"⚠ Claude Code: {len(failed)} step(s) failed, see above; rerun script/setup/agent-plugins")
        else:
            print("✓ Claude Code: " + ", ".join(f"{p.marketplace}@{p.ref}" for p in pins))
    else:
        print("· Claude Code: claude not on PATH, skipped")
    if shutil.which("codex") and CODEX_CONFIG.is_file():
        errors = [
            error
            for pin in pins
            if (error := _run(["codex", "plugin", "marketplace", "upgrade", pin.marketplace], report=False))
        ]
        if not errors:
            print(f"✓ Codex: refreshed from {CODEX_CONFIG}")
        elif all(UNTRUSTED_CODEX in error for error in errors):
            print(
                f"⚠ Codex: not installed; Codex reads {CODEX_CONFIG} only in a trusted project."
                " Trust this folder in Codex, then rerun script/setup/agent-plugins"
            )
        else:
            print(f"⚠ Codex: not refreshed: {errors[0]}; rerun script/setup/agent-plugins")
    print(f"· Copilot: installs from {COPILOT_SETTINGS} itself")
    if OPENCODE_CONFIG.is_file():
        print(f"· OpenCode: fetches the catalogs in {OPENCODE_CONFIG} itself when it starts")


def main(argv: list[str]) -> int:
    """Check, then install unless ``--check`` was given."""
    pins = pins_from_settings(_json(CLAUDE_SETTINGS))
    codex = codex_pins(tomllib.loads(CODEX_CONFIG.read_text(encoding="utf-8"))) if CODEX_CONFIG.is_file() else []
    copilot = pins_from_settings(_json(COPILOT_SETTINGS))
    opencode = opencode_pins(_json(OPENCODE_CONFIG), pins) if OPENCODE_CONFIG.is_file() else None
    if not (pins or copilot or codex or opencode):
        print(f"· {CLAUDE_SETTINGS} pins no GitHub marketplace; nothing to do")
        return 0
    problems = mismatches(pins, copilot, codex, opencode)
    for problem in problems:
        print(f"✗ {problem}", file=sys.stderr)
    if problems:
        return 1
    files = [str(CLAUDE_SETTINGS), str(COPILOT_SETTINGS), str(CODEX_CONFIG)]
    if opencode is not None:
        files.append(str(OPENCODE_CONFIG))
    print(f"✓ {', '.join(files[:-1])} and {files[-1]} pin the same plugins")
    if "--check" not in argv:
        install(pins)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
