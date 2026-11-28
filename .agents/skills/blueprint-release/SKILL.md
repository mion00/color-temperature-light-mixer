---
name: blueprint-release
description: >-
  Cut a release of this Home Assistant custom integration, or prepare the commits that feed it. Use when asked to
  "release", "bump the version", "prepare release notes", "write a commit message", "why didn't release-please pick
  this up", "update my branch", "rebase", "stacked PR", "release a beta", "the release is stuck as a draft", "the ZIP
  asset is missing", or when reviewing whether a change is user-facing. Covers commitlint's rules, how release-please
  versions and writes the changelog, betas, the release scripts, branch upkeep, the ZIP asset and the catalog gates.
  SYMPTOMS — load this if you are about to: commit without an explicit request; offer to `git push`; force-push
  without a lease; merge a pull request another one is stacked on; label a user-facing fix as `chore`; write a commit
  subject over 100 characters; edit the version in `manifest.json` by hand; name a beta `1.2.0b1`; edit `hacs.json`,
  `script/build` or the HACS job in `validate.yml`; or re-run a failed release with "Re-run all jobs".
---

# Releases and commit messages

Releases are driven entirely by commit messages. A sloppy commit subject is not a cosmetic issue here — it decides the
version number and what users read in the changelog.

## Commit rules for agents (non-negotiable)

- **Never commit automatically.** Only commit when the developer explicitly asks, in that message.
- A previous commit request is **not** standing permission. Each commit needs a fresh instruction.
- **Push only when asked** — for a push or a pull request — and never offer to otherwise. The developer handles
  `git push`.
- Always run `git diff` (and `git status`) before writing a message. Describe what is actually staged, not what you
  remember doing.

## Reference files

| File                                                                                   | When to read                                                                   |
| -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| [`references/branches-and-pull-requests.md`](references/branches-and-pull-requests.md) | Updating a branch, a conflict, splitting mixed work, or a stacked pull request |

## Commit message format

The format, the allowed types and scopes, the rules commitlint enforces, and the scope-versus-type trap are all in
[`blueprint.commit-message.instructions.md`](../../instructions/blueprint.commit-message.instructions.md),
which Copilot loads for every file. Read it before writing a message.

What that file does not tell you is what your choice costs at release time: **a user-facing change committed under a
hidden type (`refactor`, `chore`, `docs`, `test`, `ci`) never reaches the changelog and never triggers a release** —
only `feat`, `fix`, `perf`, and breaking changes do. If a change matters to a user, pick one of those honestly instead
of reaching for `chore`.

When you tell someone which type to use, say this consequence out loud — "X, because Y is hidden from the changelog
and never ships a release" — don't just name the type and cite the instructions file's definition of it.

## What each type does to the release

| Type                                      | Changelog section       | Version effect (pre-1.0)           |
| ----------------------------------------- | ----------------------- | ---------------------------------- |
| `feat`                                    | 🎉 What's new           | patch bump (`0.1.0` → `0.1.1`)     |
| `fix`                                     | 🐛 Fixed                | patch bump                         |
| `perf`                                    | ⚡ More reliable        | patch bump                         |
| `build`                                   | 📦 Updated dependencies | patch bump                         |
| `feat!` / `BREAKING CHANGE:`              | What's new + notice     | **minor** bump (`0.1.0` → `0.2.0`) |
| `refactor`, `chore`, `docs`, `test`, `ci` | hidden                  | no release                         |

After `1.0.0`, standard SemVer applies: `feat` → minor, `fix` → patch, breaking → major.

Breaking changes need both markers, and the footer text is what users read:

```text
feat(config_flow)!: require an API key instead of username and password

BREAKING CHANGE: Existing entries are migrated automatically, but users who
authenticated with a username must generate an API key in the vendor portal and
re-authenticate when prompted.
```

See `haci-breaking-changes` before writing one.

## How a release happens

```text
commits on main → release-please opens/updates "chore(main): release X.Y.Z"
               → developer reviews, optionally enhances the notes
               → developer merges the PR
               → release-please tags and publishes the GitHub Release
```

`manifest.json` → `version` is the source of truth and is bumped inside the release PR by release-please
(`release-please-config.json` → `extra-files`). Never edit it by hand. The Marketplace depends on that: it offers the tag of the latest published GitHub Release — a bare tag is not enough — expects
`version` to equal it, and shows the release body as the notes in the update dialog. It joins the notes of every
release since the installed one only within the last five releases, so the `release-asset` job adds a link to the
changelog to each body.

**Text on every release** — a support link, a standing notice — goes into `.github/release-notes/header.md` or
`footer.md`; the `release-asset` job puts it around each body, and `CHANGELOG.md` never sees it. Not into
`release-please.yml`, which template sync replaces, nor into `changelog-sections` or a `release-notes` hook, which both
land in `CHANGELOG.md`. A support link takes its handle from `.github/FUNDING.yml`. Keep it to a line: the dialog
repeats it for every release it joins. **How the notes read** — what the integration does, its own jargon, a title —
goes into `prompt.md` in the same folder, which `script/release-notes` adds to its prompt; edit that file, never the
template-managed script.

There is no automatic merge. The developer decides when to release — in batches rather than per change, so a user who
updates now and then stays inside those five.

## A beta

**A beta is a GitHub pre-release, or it is not a beta.** The Marketplace never reads the tag: it offers a release
marked as pre-release only to users who turned on the repository's **Pre-release** switch, and every other release to
everyone. The `release-asset` job marks the release as a pre-release when its version has a pre-release part.

release-please plans a normal release unless told otherwise. Set the version with a footer as the **last line of the
description** of the pull request that should trigger it — squash merging makes the description the commit body:

```text
Release-As: 1.2.0-beta.1
```

- **Always the hyphen form** — `1.2.0-beta.1`, `1.2.0-rc.1`. release-please reads `1.2.0b1` as `1.2.0` and ships
  a regular release to every user.
- **Every version of the beta series takes its own footer** — `-beta.2`, then `Release-As: 1.2.0` for the release
  itself. Without one, release-please derives the next version from the commits again.
- ❌ Do not set `prerelease: true` in `release-please-config.json`: before `1.0.0` it marks every release as a
  pre-release, so nobody without the switch gets an update.

How a published release reaches users, and getting the repository into the catalog in the first place, is
`haci-marketplace`.

## Commands

```bash
script/version              # 0.1.0
script/version --tag        # v0.1.0
script/version --check      # manifest.json vs .release-please-manifest.json

script/release-notes              # preview AI-enhanced notes on stdout
script/release-notes --apply      # write them into the open release PR body
script/release-notes --interactive # write context to .agents/scratch/ and open a session
script/release-notes --prompt     # only write the prompt to .agents/scratch/, print its path
script/release-notes --apply-file NOTES # write finished notes into the open release PR body
```

`script/release-notes` needs a signed-in coding agent CLI — Claude Code, Codex, GitHub Copilot or OpenCode;
`AGENT_CLI` picks one, `AGENT_MODEL` its model — and `gh auth login`. It rewrites the notes of the PR labelled
`autorelease: pending` for users, from the commits and a compact diff since the last tag, with the sections of
`release-please-config.json`.

**Run `--apply` or `--apply-file` last, right before merging the release PR.** release-please rewrites that body whenever another
commit reaches `main`, and the rewritten notes are gone without a word. `--apply` replaces only the notes under the
version heading and leaves the rest of the body as release-please reads it back; the release takes its notes from
there, while `CHANGELOG.md` keeps release-please's own wording.

**Asked for the notes inside an agent session, never write them in that session.** It knows the work behind each
change, and that knowledge leaks into text meant for people who do not. Run `--apply`: it starts a separate agent CLI
in an empty folder, with nothing but the prompt. Where that cannot run — a sandbox, no CLI signed in — run `--prompt`,
hand the file to a **fresh** subagent with no other context (not a fork, which inherits this session), show the
developer its answer, and write it with `--apply-file` once they agree.

**The generated notes are a draft.** Whoever publishes the release is accountable for their technical accuracy, so
they get read before the release PR is merged — not after ([`AI_POLICY.md`](../../../AI_POLICY.md)).

To keep an internal commit out of the notes, add a trailer to its body:

```text
Release-Notes: skip
```

or `User-Impact: none`.

## Publishing through HACS here

What a listing needs and how it reaches users is `haci-marketplace` (plugin `haci-publish`); this is how this
repository provides it.

- **The ZIP asset.** `hacs.json` ships `name`, `homeassistant`, `hacs`, `zip_release`, `filename` (`initialize.sh`
  sets the domain in it) and `hide_default_branch`; it validates against `schemas/json/hacs_schema.json`.
  release-please creates the release as a **draft** (`draft` and `force-tag-creation` in `release-please-config.json`).
  The `release-asset` job in `release-please.yml` runs `script/build` — the tracked files of `custom_components/<domain>/`
  at the archive root, the build hooks, and a check that the manifest version equals the tag — attaches the ZIP under
  the name `filename` gives, and only then publishes. The file name lives only in `hacs.json`; the workflow reads it
  from there and must never repeat it. `script/tests/test_hacs_json.py` fails CI when `zip_release` lacks
  `filename`, `hide_default_branch` or the draft settings.
- **A release stuck as a draft** means that job failed. Run the workflow by hand with the tag; "Re-run all jobs"
  creates no release and skips the job.
- **Build-time files** — a bundled frontend card, generated assets — come from `script/hooks/build.post.sh`
  ([`hooks.md`](../blueprint-tooling/references/hooks.md#the-build-hook)), never from files committed into the
  integration.
- **The catalog's gates** run in `.github/workflows/validate.yml`: on pull requests, weekly and on demand
  (`gh workflow run validate.yml --ref main`), not on every push to `main`, and its `changes` job skips both gates on a pull
  request that touches neither the integration, `README.md`, `hacs.json` nor the workflow. Its `hacs` job skips itself with a notice on a private repository and
  adds `ignore: brands` with a warning while `brand/icon.png` is missing; the other gate is the `Hassfest validation`
  job. Replacing the placeholder icon is a `blueprint-scaffold` step.
- **The README** is generated once by `initialize.sh` from `README.template.md`, which already wraps the Codespaces
  blurb, the install badge with its fallbacks and the contributing section in the Marketplace exclude markers, and
  carries the My links `marketplace_repository` and `config_flow_start` — keep their parameters in step with a
  repository rename. `tests/test_readme_markers.py` holds every exclude marker to its end.
- **Raising `hacs.json` → `homeassistant`**: `script/ha-version-sync` makes the development and test pins follow
  ([`blueprint-tooling`](../blueprint-tooling/SKILL.md#bumping-the-home-assistant-version)).

## Pre-release checklist

Before suggesting the release PR be merged:

```bash
script/check          # type-check + lint-check + spell-check
script/hassfest
script/test
script/version --check
```

Also confirm:

- The changelog entries read as user-facing statements, not commit titles.
- Every breaking change has a `BREAKING CHANGE:` footer and a migration note.
- `docs/user/` and the README match the released behaviour.
- `hacs.json` → `homeassistant` is still the minimum this release needs
  (`haci-marketplace`), and a raised one is named in the
  changelog — it is not a breaking change (`haci-breaking-changes`).
- `custom_components/<domain>/brand/icon.png` is the product's icon, not the blueprint's placeholder.

## Troubleshooting

| Symptom                                | Cause                                                                    |
| -------------------------------------- | ------------------------------------------------------------------------ |
| No release PR appeared                 | Only hidden types (`chore`, `docs`, …) landed — nothing to release       |
| A change is missing from the changelog | It was committed under a hidden type, or carries `Release-Notes: skip`   |
| Version bumped in the wrong direction  | `bump-patch-for-minor-pre-major` is on until 1.0.0 — this is intentional |
| `script/version --check` fails         | `manifest.json` was edited by hand; let release-please own it            |
| release-please cannot open a PR        | Repository Actions permissions — see `docs/development/RELEASE.md`       |

One-time GitHub repository setup (Actions permissions, branch protection, required checks) is documented in
[`docs/development/RELEASE.md`](../../../docs/development/RELEASE.md); it cannot be configured from the repository.
