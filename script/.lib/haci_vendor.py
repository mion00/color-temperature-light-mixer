"""
Copy the rules of the pinned haci skills into path-scoped instructions files.

A haci skill keeps its rules in ``references/rules.md``. A plugin cannot ship path-scoped rules, so this writes each one
to ``.agents/instructions/haci.<topic>.instructions.md`` with the patterns from ``TOPICS`` — they are this repository's
layout, not the skill's — and the marketplace tag ``.claude/settings.json`` pins. Copilot, VS Code and Claude Code then
load the rules whenever an agent opens a matching file, with or without the skill.

The tag is read from the settings and nowhere else; the run stops when the Copilot, Codex or OpenCode settings pin
another one.
``HACI_VENDOR_SOURCE`` names a local checkout to read instead of cloning the tag; the marker then says ``<tag>+local``,
which script/skills-check rejects, so such a file is for trying out a rules change and never passes the gates. The
marker also carries a digest of the text below it, so a hand edit fails the same check.

Invoked by script/haci-vendor; not intended to be run directly.
"""

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib

from agent_plugins import (
    CLAUDE_SETTINGS,
    CODEX_CONFIG,
    COPILOT_SETTINGS,
    OPENCODE_CONFIG,
    Pin,
    _json,
    codex_pins,
    mismatches,
    opencode_pins,
    pins_from_settings,
)

MARKETPLACE = "ha-custom-integration-skills"
OUTPUT_DIR = Path(".agents/instructions")
PREFIX = "haci."
SUFFIX = ".instructions.md"


@dataclass(frozen=True)
class Topic:
    """One rules file of one haci skill, and the files in this repository it applies to."""

    name: str
    plugin: str
    skill: str
    patterns: tuple[str, ...]
    rules: str = "rules"

    @property
    def source(self) -> str:
        """The path of the rules file inside the marketplace repository."""
        return f"plugins/{self.plugin}/skills/{self.skill}/references/{self.rules}.md"

    @property
    def target(self) -> Path:
        """The instructions file this topic is written to."""
        return OUTPUT_DIR / f"{PREFIX}{self.name}{SUFFIX}"


TOPICS = (
    Topic(
        "config-flow",
        "haci-build",
        "haci-config-flow",
        (
            "custom_components/**/config_flow_handler/**/*.py",
            "custom_components/**/config_flow.py",
        ),
    ),
    Topic(
        "coordinator",
        "haci-build",
        "haci-coordinator-debug",
        (
            "custom_components/**/coordinator/**/*.py",
            "custom_components/**/api/**/*.py",
        ),
    ),
    Topic(
        "diagnostics",
        "haci-build",
        "haci-coordinator-debug",
        ("custom_components/**/diagnostics.py",),
        rules="rules.diagnostics",
    ),
    Topic(
        "entities",
        "haci-build",
        "haci-entity-platform",
        (
            "custom_components/**/alarm_control_panel/**/*.py",
            "custom_components/**/binary_sensor/**/*.py",
            "custom_components/**/button/**/*.py",
            "custom_components/**/camera/**/*.py",
            "custom_components/**/climate/**/*.py",
            "custom_components/**/cover/**/*.py",
            "custom_components/**/date/**/*.py",
            "custom_components/**/datetime/**/*.py",
            "custom_components/**/device_tracker/**/*.py",
            "custom_components/**/event/**/*.py",
            "custom_components/**/fan/**/*.py",
            "custom_components/**/humidifier/**/*.py",
            "custom_components/**/image/**/*.py",
            "custom_components/**/lawn_mower/**/*.py",
            "custom_components/**/light/**/*.py",
            "custom_components/**/lock/**/*.py",
            "custom_components/**/media_player/**/*.py",
            "custom_components/**/notify/**/*.py",
            "custom_components/**/number/**/*.py",
            "custom_components/**/scene/**/*.py",
            "custom_components/**/select/**/*.py",
            "custom_components/**/sensor/**/*.py",
            "custom_components/**/siren/**/*.py",
            "custom_components/**/switch/**/*.py",
            "custom_components/**/text/**/*.py",
            "custom_components/**/time/**/*.py",
            "custom_components/**/todo/**/*.py",
            "custom_components/**/update/**/*.py",
            "custom_components/**/vacuum/**/*.py",
            "custom_components/**/valve/**/*.py",
            "custom_components/**/water_heater/**/*.py",
            "custom_components/**/entity/**/*.py",
            "custom_components/**/entity_utils/**/*.py",
        ),
    ),
    Topic("manifest", "haci-build", "haci-config-flow", ("**/manifest.json",), rules="rules.manifest"),
    Topic("repairs", "haci-quality", "haci-breaking-changes", ("custom_components/**/repairs.py",)),
    Topic("service-actions", "haci-build", "haci-service-action", ("custom_components/**/service_actions/**/*.py",)),
    Topic("services-yaml", "haci-build", "haci-service-action", ("**/services.yaml",), rules="rules.services-yaml"),
    Topic("tests", "haci-quality", "haci-testing", ("tests/**/*.py",)),
    Topic("translations", "haci-build", "haci-translations", ("**/translations/*.json",)),
)


class VendorError(Exception):
    """The pin or the source cannot produce the rules files."""


def pinned() -> Pin:
    """Return the marketplace pin from the Claude settings, after checking the other agents pin the same."""
    pins = pins_from_settings(_json(CLAUDE_SETTINGS))
    codex = codex_pins(tomllib.loads(CODEX_CONFIG.read_text(encoding="utf-8"))) if CODEX_CONFIG.is_file() else []
    opencode = opencode_pins(_json(OPENCODE_CONFIG), pins) if OPENCODE_CONFIG.is_file() else None
    problems = mismatches(pins, pins_from_settings(_json(COPILOT_SETTINGS)), codex, opencode)
    if problems:
        raise VendorError("; ".join(problems))
    for pin in pins:
        if pin.marketplace == MARKETPLACE:
            return pin
    raise VendorError(f"{CLAUDE_SETTINGS} pins no {MARKETPLACE} marketplace")


def split_frontmatter(text: str, origin: str) -> tuple[list[str], str]:
    """Return the frontmatter lines and the body of a rules file."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\n") != "---":
        raise VendorError(f"{origin}: no frontmatter")
    for index, line in enumerate(lines[1:], start=1):
        if line.rstrip("\n") == "---":
            return [entry.rstrip("\n") for entry in lines[1:index]], "".join(lines[index + 1 :]).lstrip("\n")
    raise VendorError(f"{origin}: frontmatter is not closed")


def digest(body: str) -> str:
    """Return the short digest of the text below the marker, which script/skills-check recomputes."""
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]


def render(topic: Topic, text: str, pin: Pin) -> str:
    """Turn one rules file into the instructions file for this repository."""
    fields, body = split_frontmatter(text, topic.source)
    keys = {line.split(":", 1)[0] for line in fields if line and not line.startswith(" ")}
    if keys != {"name", "description"}:
        raise VendorError(f"{topic.source}: frontmatter must hold exactly name and description, has {sorted(keys)}")
    patterns = ", ".join(topic.patterns)
    header = [
        "---",
        *fields,
        f'applyTo: "{patterns}"',
        "paths:",
        *(f'  - "{pattern}"' for pattern in topic.patterns),
        "---",
        "",
        (
            f"<!-- haci-vendor: {pin.repo}@{pin.ref} {topic.source} sha256:{digest(body)}"
            " — written by script/haci-vendor, do not edit -->"
        ),
        "",
    ]
    return "\n".join(header) + "\n" + body


def expected(source: Path, pin: Pin) -> dict[Path, str]:
    """Render every topic from a checkout of the marketplace."""
    files: dict[Path, str] = {}
    for topic in TOPICS:
        rules = source / topic.source
        if not rules.is_file():
            raise VendorError(f"{pin.repo}@{pin.ref} has no {topic.source}")
        files[topic.target] = render(topic, rules.read_text(encoding="utf-8"), pin)
    return files


def present() -> dict[Path, str]:
    """Return the haci instructions files this repository has now."""
    return {path: path.read_text(encoding="utf-8") for path in sorted(OUTPUT_DIR.glob(f"{PREFIX}*{SUFFIX}"))}


def checkout(pin: Pin, into: Path) -> Path:
    """Return a directory holding the marketplace at the pinned tag."""
    local = os.environ.get("HACI_VENDOR_SOURCE")
    if local:
        return Path(local)
    command = ["git", "clone", "--quiet", "--depth", "1", "--branch", pin.ref, pin.git_url, str(into)]
    result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=120)
    if result.returncode:
        raise VendorError(f"cloning {pin.git_url} at {pin.ref} failed: {result.stderr.strip()}")
    return into


def main(argv: list[str]) -> int:
    """Write the rules files, or with ``--check`` report where they differ from the pinned tag."""
    try:
        pin = pinned()
        with tempfile.TemporaryDirectory() as scratch:
            source = checkout(pin, Path(scratch) / "marketplace")
            if os.environ.get("HACI_VENDOR_SOURCE"):
                pin = Pin(pin.marketplace, pin.repo, f"{pin.ref}+local", pin.plugins)
            wanted = expected(source, pin)
    except VendorError as err:
        print(f"✗ {err}", file=sys.stderr)
        return 1
    have = present()
    changed = sorted(path for path, text in wanted.items() if have.get(path) != text)
    stale = sorted(set(have) - set(wanted))
    if "--check" in argv:
        for path in changed:
            print(f"✗ {path} differs from {pin.repo}@{pin.ref}", file=sys.stderr)
        for path in stale:
            print(f"✗ {path} belongs to no haci topic", file=sys.stderr)
        if changed or stale:
            print("  run script/haci-vendor and commit the result", file=sys.stderr)
            return 1
        print(f"✓ {len(wanted)} haci rules files match {pin.repo}@{pin.ref}")
        return 0
    for path in changed:
        path.write_text(wanted[path], encoding="utf-8")
        print(f"✓ wrote {path}")
    for path in stale:
        path.unlink()
        print(f"✓ removed {path}")
    if not (changed or stale):
        print(f"✓ {len(wanted)} haci rules files already match {pin.repo}@{pin.ref}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
